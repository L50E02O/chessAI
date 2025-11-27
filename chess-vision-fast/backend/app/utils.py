from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    # Google Gemini API (obtener en https://aistudio.google.com/apikey)
    # REQUERIDO para el análisis de ajedrez
    gemini_api_key: str = ''
    gemini_model: str = 'gemini-1.5-flash'  # Modelo rápido, bueno para visión
    
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
