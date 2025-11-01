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
    sf = None
    try:
        from stockfish import Stockfish
        sf = Stockfish(path=STOCKFISH_PATH if os.path.exists(STOCKFISH_PATH) else None)
        sf.set_fen_position(fen)
        sf.set_depth(depth)
        best = sf.get_best_move()
        return best
    except Exception as e:
        print(f"Error en python-stockfish: {str(e)}")
        return None
    finally:
        # Clean up stockfish instance
        if sf:
            try:
                del sf
            except:
                pass


def _try_cli_stockfish(fen: str, depth: int = 10):
    if not os.path.exists(STOCKFISH_PATH):
        return None
    
    p = None
    try:
        # Use simple UCI commands
        p = subprocess.Popen(
            [STOCKFISH_PATH], 
            stdin=subprocess.PIPE, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True
        )
        
        # Send UCI commands
        p.stdin.write('uci\n')
        p.stdin.flush()
        
        # Wait for uciok with timeout
        import time
        start = time.time()
        while time.time() - start < 2:
            line = p.stdout.readline()
            if not line:
                break
            if 'uciok' in line:
                break
        
        # Set position and calculate with movetime limit (1 second)
        p.stdin.write(f'position fen {fen}\n')
        p.stdin.write(f'go depth {depth} movetime 2000\n')  # Max 2 segundos
        p.stdin.flush()
        
        best_move = None
        start = time.time()
        while time.time() - start < 5:  # Timeout de 5 segundos total
            line = p.stdout.readline()
            if not line:
                break
            if line.startswith('bestmove'):
                parts = line.split()
                if len(parts) >= 2:
                    best_move = parts[1]
                break
        
        # Properly quit stockfish
        try:
            p.stdin.write('quit\n')
            p.stdin.flush()
            p.wait(timeout=1)
        except:
            pass
        
        return best_move
        
    except Exception as e:
        print(f"Error en Stockfish CLI: {str(e)}")
        return None
    
    finally:
        # Ensure process is terminated
        if p and p.poll() is None:
            try:
                p.kill()
                p.wait(timeout=1)
            except:
                pass


def get_best_move_for_fen(fen: str, depth: int = 10) -> str:
    """Return best move string like 'e2e4' or algebraic like 'Nf3'. Could be None if not found."""
    # Usar solo el método CLI
    ans = _try_cli_stockfish(fen, depth)
    if ans:
        return ans
    print('Stockfish no disponible o error en CLI, devolviendo jugada mock Nf3')
    return 'Nf3'
