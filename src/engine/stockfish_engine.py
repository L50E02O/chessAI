"""Engine wrapper. Tries to use python-stockfish or the bundled binary; falls back to a mock.
Keep this module as the single contract point.

Contract (small):
- get_best_move_for_fen(fen: str, depth: int=15) -> str | None
"""
import os
import shutil
import subprocess

from src.utils.config import STOCKFISH_PATH


def _try_python_stockfish(fen: str, depth: int = 15):
    try:
        from stockfish import Stockfish
        sf = Stockfish(path=STOCKFISH_PATH if os.path.exists(STOCKFISH_PATH) else None)
        sf.set_fen_position(fen)
        best = sf.get_best_move()
        return best
    except Exception as e:
        # not available or failed
        return None


def _try_cli_stockfish(fen: str, depth: int = 15):
    if not os.path.exists(STOCKFISH_PATH):
        return None
    try:
        # Use simple UCI commands
        p = subprocess.Popen([STOCKFISH_PATH], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        p.stdin.write('uci\n')
        p.stdin.write(f'position fen {fen}\n')
        p.stdin.write(f'go depth {depth}\n')
        p.stdin.flush()
        best_move = None
        while True:
            line = p.stdout.readline()
            if not line:
                break
            if line.startswith('bestmove'):
                parts = line.split()
                if len(parts) >= 2:
                    best_move = parts[1]
                break
        p.kill()
        return best_move
    except Exception:
        return None


def get_best_move_for_fen(fen: str, depth: int = 15) -> str:
    """Return best move string like 'e2e4' or algebraic like 'Nf3'. Could be None if not found."""
    # Usar solo el método CLI
    ans = _try_cli_stockfish(fen, depth)
    if ans:
        return ans
    print('Stockfish no disponible o error en CLI, devolviendo jugada mock Nf3')
    return 'Nf3'
