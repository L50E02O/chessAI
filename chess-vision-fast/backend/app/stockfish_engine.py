"""Stockfish binary discovery, download, and UCI analysis."""
import logging
import os
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path
from typing import Optional

import chess
import chess.engine

logger = logging.getLogger(__name__)

STOCKFISH_DOWNLOAD_URL = 'https://github.com/official-stockfish/Stockfish/releases/latest/download/stockfish-windows-x86-64-avx2.zip'
BIN_DIR = Path(__file__).resolve().parent / 'bin'

COMMON_PATHS = [
    r'C:\Program Files\Stockfish\stockfish.exe',
    r'C:\Program Files (x86)\Stockfish\stockfish.exe',
    os.path.expanduser(r'~\Desktop\stockfish.exe'),
    r'C:\stockfish\stockfish.exe',
]


def find_stockfish(configured_path: Optional[str] = None, auto_download: bool = True) -> Optional[str]:
    candidates = []
    if configured_path and os.path.exists(configured_path):
        candidates.append(configured_path)
    local = BIN_DIR / 'stockfish.exe'
    if local.exists():
        candidates.append(str(local))
    for path in COMMON_PATHS:
        if os.path.exists(path):
            candidates.append(path)
    downloads = os.path.expanduser('~/Downloads')
    if os.path.isdir(downloads):
        for root, dirs, files in os.walk(downloads):
            if root[len(downloads):].count(os.sep) > 2:
                dirs[:] = []
            for file in files:
                if file.lower().startswith('stockfish') and file.lower().endswith('.exe'):
                    candidates.append(os.path.join(root, file))
    if candidates:
        return candidates[0]
    if auto_download and sys.platform == 'win32':
        return download_and_extract_stockfish()
    return None


def download_and_extract_stockfish() -> Optional[str]:
    exe = BIN_DIR / 'stockfish.exe'
    if exe.exists():
        return str(exe)
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = BIN_DIR / 'stockfish.zip'
    try:
        logger.info('Downloading Stockfish for Windows...')
        urllib.request.urlretrieve(STOCKFISH_DOWNLOAD_URL, zip_path)
        with zipfile.ZipFile(zip_path) as zf:
            for member in zf.namelist():
                if member.lower().endswith('.exe'):
                    with zf.open(member) as src, open(exe, 'wb') as dst:
                        dst.write(src.read())
                    return str(exe)
        return None
    except Exception as e:
        logger.error(f'Stockfish download failed: {e}')
        return None
    finally:
        try:
            zip_path.unlink()
        except OSError:
            pass


class StockfishEngine:
    def __init__(self, path: Optional[str] = None, depth: int = 15,
                 auto_download: bool = True, command: Optional[list] = None) -> None:
        self.path = path
        self.depth = depth
        self.auto_download = auto_download
        self._command = command

    def ensure_available(self) -> str:
        if self._command is not None:
            return ''
        if self.path and os.path.exists(self.path):
            return self.path
        found = find_stockfish(self.path, self.auto_download)
        if not found:
            raise RuntimeError(
                'Stockfish not found. Install it or set STOCKFISH_PATH. '
                'Download: https://stockfishchess.org/download/'
            )
        self.path = found
        return found

    def _command_list(self) -> list:
        if self._command is not None:
            return self._command
        return [self.ensure_available()]

    def analyze_position(self, fen: str, depth: Optional[int] = None) -> dict:
        board = chess.Board(fen)
        engine = chess.engine.SimpleEngine.popen_uci(self._command_list())
        try:
            limit = chess.engine.Limit(depth=depth or self.depth)
            info = engine.analyse(board, limit=limit)
            white_score = info['score'].white()
            if white_score.is_mate():
                score_cp, score_mate = None, white_score.mate()
            else:
                score_cp, score_mate = white_score.cp, None
            pv = []
            walk = chess.Board(fen)
            for move in info.get('pv', [])[:6]:
                pv.append(walk.san(move))
                walk.push(move)
            return {
                'uci': info['pv'][0].uci() if info.get('pv') else None,
                'score_cp': score_cp,
                'score_mate': score_mate,
                'pv': pv,
                'depth': depth or self.depth,
                'source': 'stockfish',
            }
        finally:
            engine.quit()
