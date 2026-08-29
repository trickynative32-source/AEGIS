import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

BASE_DIR_PATH = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    model_config = ConfigDict(extra="allow", env_file=".env", env_file_encoding="utf-8")

    # Base Paths
    BASE_DIR: str = str(BASE_DIR_PATH)

    # App Settings
    APP_NAME: str = "AEGIS — Assisted Executive Guidance and Intelligence System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # AI Model Settings (OpenRouter & Gemini)
    OPENROUTER_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_MODEL: str = "google/gemini-2.0-flash-001"
    VISION_MODEL: str = "google/gemini-2.0-flash-001"

    # Database
    DATABASE_URL: str = f"sqlite:///{BASE_DIR_PATH / 'aegis.db'}"

    # TTS Settings ('edge-tts' or 'pyttsx3' or 'web')
    TTS_PROVIDER: str = "edge-tts"
    TTS_VOICE: str = "en-US-ChristopherNeural"
    TTS_SPEED: str = "+0%"
    TTS_PITCH: str = "+0Hz"

    # STT Settings ('faster-whisper' or 'web')
    STT_PROVIDER: str = "faster-whisper"
    WHISPER_MODEL_SIZE: str = "base"
    WHISPER_DEVICE: str = "cpu"
    WHISPER_COMPUTE_TYPE: str = "int8"

    # Privacy and Feature Toggles
    CAMERA_ENABLED: bool = False
    CONTINUOUS_CAMERA: bool = False
    LOCATION_ENABLED: bool = True
    AUTOMATION_ENABLED: bool = True
    LEARNING_ENABLED: bool = True
    CLOUD_VISION_ENABLED: bool = True
    WAKE_WORD_ENABLED: bool = False
    VOICE_FIRST_MODE: bool = False

    # Default Paths
    DESKTOP_DIR: str = str(Path.home() / "Desktop")
    DOCUMENTS_DIR: str = str(Path.home() / "Documents")
    DOWNLOADS_DIR: str = str(Path.home() / "Downloads")

settings = Settings()
