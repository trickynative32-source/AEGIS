import os
import re
import asyncio
import base64
import logging
import threading
from pathlib import Path
from typing import Optional, Dict, Any
import edge_tts
import pyttsx3
from backend.config import settings

logger = logging.getLogger("AEGIS.TTS")

def clean_text_for_speech(text: str) -> str:
    """
    Strips all markdown symbols (###, ##, #, *, **, __, code blocks, emojis, URLs, etc.)
    so that Edge-TTS and SAPI produce 100% natural, human-like voice synthesis without
    pronouncing symbols like 'hash hash hash', 'number sign', or 'asterisk'.
    """
    if not text or not text.strip():
        return ""

    s = text.strip()

    # 1. Replace multiline code blocks (```...```) with a spoken placeholder
    s = re.sub(r"```[\s\S]*?```", " Here is the code. ", s)

    # 2. Strip inline code backticks `code` -> code
    s = re.sub(r"`([^`]+)`", r"\1", s)

    # 3. Strip all markdown headers: ### Header, ## Header, # Header
    s = re.sub(r"(?m)^\s*#{1,6}\s*", "", s)
    # Strip any remaining standalone or repeated hash symbols anywhere in the text
    s = re.sub(r"#+", "", s)

    # 4. Strip blockquote alerts (> [!NOTE], > [!TIP], etc.) and blockquotes
    s = re.sub(r">\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]", "", s, flags=re.IGNORECASE)
    s = re.sub(r"(?m)^\s*>\s*", "", s)

    # 5. Convert markdown links [title](url) -> title
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)

    # 6. Simplify raw URLs: https://domain.com/path -> domain.com
    s = re.sub(r"https?://(?:www\.)?([a-zA-Z0-9.-]+)(?:/[^\s]*)?", r"\1", s)

    # 7. Strip bold, italic, strikethrough markers
    s = re.sub(r"\*\*([^*]+)\*\*", r"\1", s)
    s = re.sub(r"\*([^*]+)\*", r"\1", s)
    s = re.sub(r"__([^_]+)__", r"\1", s)
    s = re.sub(r"_([^_]+)_", r"\1", s)
    s = re.sub(r"~~([^~]+)~~", r"\1", s)

    # 8. Strip bullet point markers (- , * , + )
    s = re.sub(r"(?m)^\s*[-*+]\s+", "", s)

    # 9. Strip emojis so speech synthesizer doesn't pronounce emoji names (e.g. '💡' -> 'light bulb')
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "\U0001F900-\U0001F9FF"
        "\U0001FA00-\U0001FA6F"
        "\U0001FA70-\U0001FAFF"
        "]+",
        flags=re.UNICODE
    )
    s = emoji_pattern.sub("", s)

    # 10. Normalize multiple line breaks and dots into clean sentence pauses
    s = re.sub(r"[\r\n]+", ". ", s)
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\.{2,}", ".", s)
    s = re.sub(r"\.\s*\.", ".", s)

    return s.strip()

class TTSService:
    def __init__(self):
        self.is_speaking: bool = False
        self.cancel_requested: bool = False
        self.audio_cache_dir = Path(settings.BASE_DIR) / "data" / "tts_cache"
        self.audio_cache_dir.mkdir(parents=True, exist_ok=True)
        self._sapi_engine = None
        self._sapi_lock = threading.Lock()

    def _get_sapi_engine(self):
        if self._sapi_engine is None:
            try:
                self._sapi_engine = pyttsx3.init()
                self._sapi_engine.setProperty('rate', 185)
            except Exception as e:
                logger.warning(f"pyttsx3 init failed: {e}")
        return self._sapi_engine

    def cancel(self):
        """Immediately interrupts any in-progress speech (barge-in)."""
        self.cancel_requested = True
        self.is_speaking = False
        try:
            if self._sapi_engine:
                with self._sapi_lock:
                    self._sapi_engine.stop()
        except Exception:
            pass
        logger.info("TTS playback cancelled.")

    async def generate_speech_audio_base64(self, text: str) -> Optional[str]:
        """Generates MP3 audio from text using Edge-TTS or pyttsx3 and returns base64 string."""
        if not text or not text.strip():
            return None

        clean_text = clean_text_for_speech(text)
        if not clean_text:
            return None

        self.cancel_requested = False
        self.is_speaking = True

        out_file = self.audio_cache_dir / f"speech_{abs(hash(clean_text)) % 100000}.mp3"

        # Try Edge-TTS first (neural high-quality voice)
        try:
            communicate = edge_tts.Communicate(
                text=clean_text,
                voice=settings.TTS_VOICE,
                rate=settings.TTS_SPEED,
                pitch=settings.TTS_PITCH
            )
            await communicate.save(str(out_file))

            if out_file.exists():
                with open(out_file, "rb") as f:
                    audio_bytes = f.read()
                return base64.b64encode(audio_bytes).decode("utf-8")
        except Exception as e:
            logger.warning(f"Edge-TTS failed ({e}), falling back to offline pyttsx3...")

        # Fallback to offline pyttsx3
        try:
            wav_file = self.audio_cache_dir / f"speech_{abs(hash(clean_text)) % 100000}.wav"
            with self._sapi_lock:
                engine = self._get_sapi_engine()
                if engine:
                    engine.save_to_file(clean_text, str(wav_file))
                    engine.runAndWait()

            if wav_file.exists():
                with open(wav_file, "rb") as f:
                    audio_bytes = f.read()
                return base64.b64encode(audio_bytes).decode("utf-8")
        except Exception as ex:
            logger.error(f"pyttsx3 fallback failed: {ex}")

        return None

    def speak_offline_direct(self, text: str):
        """Direct 100% offline speech via Windows SAPI in background thread."""
        clean_text = clean_text_for_speech(text)
        if not clean_text:
            return

        def _speak():
            try:
                with self._sapi_lock:
                    engine = self._get_sapi_engine()
                    if engine:
                        engine.say(clean_text)
                        engine.runAndWait()
            except Exception as e:
                logger.error(f"Offline direct speak error: {e}")

        t = threading.Thread(target=_speak, daemon=True)
        t.start()

tts_service = TTSService()
