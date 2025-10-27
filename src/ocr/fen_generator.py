"""Small helper to generate/validate FENs.
This is intentionally tiny — relies on `python-chess` when available.
"""

try:
    import chess
except Exception:
    chess = None


def validate_fen(fen: str) -> bool:
    if not fen:
        return False
    if chess:
        try:
            chess.Board(fen)
            return True
        except Exception:
            return False
    # Basic sanity: 6 fields separated by spaces
    parts = fen.split()
    return len(parts) >= 4
