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
    # Detector backend: 'gemini' (default), 'roboflow' o 'yolo'
    detection_backend: str = 'gemini'
    
    # Google Gemini API (obtener en https://aistudio.google.com/apikey)
    gemini_api_key: str = ''
    gemini_model: str = 'gemini-1.5-flash'  # Modelo rapido, bueno para vision
    
    # Roboflow API (para tableros fisicos reales)
    roboflow_api_key: str = ''
    roboflow_model_id: str = 'chess-pieces-mjzgj/1'
    
    # YOLO local (fallback)
    yolo_model_path: Path = Path('./models/yolov8-chess.pt')
    yolo_confidence: float = 0.4
    
    # Stockfish
    stockfish_path: Path = _find_stockfish()
    
    # General
    allowed_origins: List[str] = ['*']
    max_upload_size: int = 5 * 1024 * 1024
    detection_confidence_threshold: float = 0.45
    frame_throttle_ms: int = 500

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')


def get_settings() -> AppSettings:
    return AppSettings()
