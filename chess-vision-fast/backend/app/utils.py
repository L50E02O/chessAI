from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    # Stockfish engine
    stockfish_path: str = ''
    stockfish_depth: int = 15
    stockfish_auto_download: bool = True

    # Google Gemini API (removed in Task 8; kept for existing code paths)
    gemini_api_key: str = ''
    gemini_model: str = 'gemini-2.0-flash'

    # General
    allowed_origins: List[str] = ['*']
    max_upload_size: int = 5 * 1024 * 1024
    detection_confidence_threshold: float = 0.45
    frame_throttle_ms: int = 500

    model_config = SettingsConfigDict(
        env_file='.env', 
        env_file_encoding='utf-8',
        extra='ignore'  # Ignorar campos extra en .env que ya no se usan
    )


def get_settings() -> AppSettings:
    return AppSettings()
