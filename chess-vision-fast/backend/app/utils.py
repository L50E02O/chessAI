from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    detection_backend: str = 'lichess'
    yolo_model_path: Path = Path('./models/yolov8-chess.pt')
    stockfish_path: Path = Path('./stockfish/stockfish')
    allowed_origins: List[str] = ['http://localhost:5173']
    max_upload_size: int = 5 * 1024 * 1024
    detection_confidence_threshold: float = 0.45
    frame_throttle_ms: int = 500
    yolo_confidence: float = 0.4

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')


def get_settings() -> AppSettings:
    return AppSettings()
