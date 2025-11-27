import shutil
import sys
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


def _find_stockfish() -> Path:
    """Busca Stockfish en el sistema"""
    # Buscar en PATH
    stockfish_exe = shutil.which('stockfish') or shutil.which('stockfish.exe')
    if stockfish_exe:
        return Path(stockfish_exe)
    
    # Buscar en ubicaciones comunes de Windows
    if sys.platform == 'win32':
        common_paths = [
            Path.home() / 'Downloads' / 'stockfish-windows-x86-64-avx2' / 'stockfish' / 'stockfish-windows-x86-64-avx2.exe',
            Path(r'C:\stockfish\stockfish.exe'),
            Path(r'C:\Program Files\Stockfish\stockfish.exe'),
        ]
        for p in common_paths:
            if p.exists():
                return p
    
    return Path('./stockfish/stockfish')


class AppSettings(BaseSettings):
    detection_backend: str = 'lichess'
    yolo_model_path: Path = Path('./models/yolov8-chess.pt')
    stockfish_path: Path = _find_stockfish()
    allowed_origins: List[str] = ['*']  # Permitir todos los origenes en desarrollo
    max_upload_size: int = 5 * 1024 * 1024
    detection_confidence_threshold: float = 0.45
    frame_throttle_ms: int = 500
    yolo_confidence: float = 0.4

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')


def get_settings() -> AppSettings:
    return AppSettings()
