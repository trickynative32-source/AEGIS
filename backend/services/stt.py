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
    """Cleans up transcription artifacts such as 12/7 AM -> 12:07 AM."""
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
