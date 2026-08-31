import os
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

        clean_text = text.strip()
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
        def _speak():
            try:
                with self._sapi_lock:
                    engine = self._get_sapi_engine()
                    if engine:
                        engine.say(text)
                        engine.runAndWait()
            except Exception as e:
                logger.error(f"Offline direct speak error: {e}")

        t = threading.Thread(target=_speak, daemon=True)
        t.start()

tts_service = TTSService()
