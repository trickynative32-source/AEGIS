import io
import os
import re
import tempfile
import logging
from typing import Optional
from pathlib import Path
from backend.config import settings

logger = logging.getLogger("AEGIS.STT")

def normalize_transcription_text(text: str) -> str:
    """Cleans up transcription artifacts such as times (12/7 AM -> 12:07 AM) and spoken math (x square -> x^2, 3x square plus 5 -> 3x^2 + 5)."""
    if not text:
        return ""
    
    t = text.strip()

    # 1. Fix slash or dot time formats e.g. 12/7 AM, 12/07AM, 5.30 PM
    def fix_time_match(m):
        hh = m.group(1)
        mm = int(m.group(2))
        ampm = m.group(3) if m.group(3) else ""
        return f"{hh}:{mm:02d} {ampm.upper()}".strip()

    t = re.sub(r'\b(\d{1,2})[/.](\d{1,2})\s*(am|pm|AM|PM)\b', fix_time_match, t)
    t = re.sub(r'\b(\d{1,2})\s+(\d{1,2})\s*(am|pm|AM|PM)\b', fix_time_match, t)
    
    # Fix standalone 12/7 when representing hour/min
    def fix_slash_standalone(m):
        hh = int(m.group(1))
        mm = int(m.group(2))
        if 1 <= hh <= 12 and 0 <= mm <= 59:
            return f"{hh}:{mm:02d}"
        return m.group(0)

    t = re.sub(r'\b(\d{1,2})/(\d{1,2})\b', fix_slash_standalone, t)

    # 2. Fix common spoken/phonetic math artifacts and typos
    t = re.sub(r'\b(squre|squar|sqr)\b', 'square', t, flags=re.IGNORECASE)
    t = re.sub(r'\b(squred)\b', 'squared', t, flags=re.IGNORECASE)

    # Roots: "under root", "underroot", "square root of", "cube root of"
    t = re.sub(r'\bunder\s*root\s*(?:of\s+)?(\d+|[a-zA-Z])\b', r'sqrt(\1)', t, flags=re.IGNORECASE)
    t = re.sub(r'\bsquare\s*root\s*of\s+(\d+|[a-zA-Z])\b', r'sqrt(\1)', t, flags=re.IGNORECASE)
    t = re.sub(r'\bcube\s*root\s*of\s+(\d+|[a-zA-Z])\b', r'cbrt(\1)', t, flags=re.IGNORECASE)

    # Calculus: "d by dx" -> "d/dx"
    t = re.sub(r'\bd\s+by\s+d\s*x\b', 'd/dx', t, flags=re.IGNORECASE)

    # Powers: "x to the power of 4", "x raised to 3", "2 power 8"
    t = re.sub(r'(\b\d*[a-zA-Z]\b|\b\d+\b)\s*(?:to\s+the\s+power\s+(?:of\s+)?|power\s+|raised\s+to\s+(?:the\s+power\s+of\s+)?)\s*(\d+|[a-zA-Z])\b', r'\1^\2', t, flags=re.IGNORECASE)

    # Squares: "x square", "3x square", "x squared", "3x squared" -> "x^2", "3x^2"
    t = re.sub(r'(\b\d*[a-zA-Z]\b|\b\d+\b)\s+(?:square|squared)\b', r'\1^2', t, flags=re.IGNORECASE)

    # Cubes: "x cube", "3x cube", "x cubed" -> "x^3", "3x^3"
    t = re.sub(r'(\b\d*[a-zA-Z]\b|\b\d+\b)\s+(?:cube|cubed)\b', r'\1^3', t, flags=re.IGNORECASE)

    # Spoken operators between terms: "3x^2 plus 5" -> "3x^2 + 5"
    operator_replacements = [
        (r'(?<=\S)\s+plus\s+(?=\S)', ' + '),
        (r'(?<=\S)\s+minus\s+(?=\S)', ' - '),
        (r'(?<=\S)\s+(?:multiplied\s+by|into|times)\s+(?=\S)', ' * '),
        (r'(?<=\S)\s+divided\s+by\s+(?=\S)', ' / '),
        (r'(?<=\S)\s+(?:is\s+equal\s+to|equals|equal\s+to)\s+(?=\S)', ' = '),
    ]
    for pat, repl in operator_replacements:
        t = re.sub(pat, repl, t, flags=re.IGNORECASE)

    # Standalone math context conversions
    if any(c in t for c in ['^', '=', 'x', 'y', '+', '-', '*', '/']) or re.search(r'\b(solve|calculate|evaluate|find)\b', t, re.IGNORECASE):
        t = re.sub(r'\bplus\b', '+', t, flags=re.IGNORECASE)
        t = re.sub(r'\bminus\b', '-', t, flags=re.IGNORECASE)
        t = re.sub(r'\b(equals|equal to|is equal to)\b', '=', t, flags=re.IGNORECASE)

    t = re.sub(r'\s+', ' ', t).strip()
    return t

class STTService:
    def __init__(self):
        self.model = None
        self._model_loading = False

    def _ensure_model(self):
        if self.model is None and not self._model_loading:
            self._model_loading = True
            try:
                from faster_whisper import WhisperModel
                logger.info(f"Loading Faster-Whisper model ({settings.WHISPER_MODEL_SIZE})...")
                self.model = WhisperModel(
                    settings.WHISPER_MODEL_SIZE,
                    device=settings.WHISPER_DEVICE,
                    compute_type=settings.WHISPER_COMPUTE_TYPE
                )
                logger.info("Faster-Whisper model loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load Faster-Whisper: {e}")
            finally:
                self._model_loading = False

    def transcribe_audio_bytes(self, audio_bytes: bytes) -> str:
        """Transcribes raw audio bytes (WAV/MP3/WebM) into text with normalization."""
        self._ensure_model()
        if not self.model:
            logger.warning("Whisper model not initialized, cannot transcribe locally.")
            return ""

        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name

            segments, _ = self.model.transcribe(
                tmp_path,
                beam_size=3,
                language="en",
                condition_on_previous_text=False
            )
            raw_text = " ".join([segment.text for segment in segments]).strip()

            try:
                os.remove(tmp_path)
            except Exception:
                pass

            clean_text = normalize_transcription_text(raw_text)
            logger.info(f"Transcribed audio: '{clean_text}' (raw: '{raw_text}')")
            return clean_text
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return ""

stt_service = STTService()
