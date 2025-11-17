"""Small helper to generate/validate FENs.
This is intentionally tiny — relies on `python-chess` when available.
"""
from typing import Optional

try:
    import chess
except Exception:
    chess = None


def validate_fen(fen: str) -> bool:
    """
    Validates FEN string. Returns True if valid, False otherwise.
    Uses python-chess if available for strict validation.
    """
    if not fen or not isinstance(fen, str):
        return False
    
    fen = fen.strip()
    if not fen:
        return False
    
    # Basic structure check: must have at least 4 parts
    parts = fen.split()
    if len(parts) < 4:
        return False
    
    # Use python-chess for strict validation if available
    if chess:
        try:
            board = chess.Board(fen)
            # Additional checks
            # Check that position part has 8 rows
            position = parts[0]
            rows = position.split('/')
            if len(rows) != 8:
                return False
            
            # Check each row has exactly 8 squares
            for row in rows:
                square_count = 0
                for char in row:
                    if char.isdigit():
                        square_count += int(char)
                    elif char in 'rnbqkpRNBQKP':
                        square_count += 1
                    else:
                        return False
                if square_count != 8:
                    return False
            
            # Check for exactly one king of each color
            white_kings = position.count('K')
            black_kings = position.count('k')
            if white_kings != 1 or black_kings != 1:
                return False
            
            return True
        except (ValueError, AttributeError, TypeError):
            return False
    
    # Fallback: basic sanity check without python-chess
    # Check that first part has 8 rows separated by /
    position = parts[0]
    if '/' not in position:
        return False
    
    rows = position.split('/')
    if len(rows) != 8:
        return False
    
    # Basic character validation
    valid_chars = set('rnbqkpRNBQKP12345678/')
    for row in rows:
        for char in row:
            if char not in valid_chars:
                return False
    
    return True


def validate_fen_with_error(fen: str):
    """
    Validates FEN string and returns (is_valid, error_message).
    More detailed than validate_fen().
    """
    if not fen or not isinstance(fen, str):
        return False, "FEN is empty or not a string"
    
    fen = fen.strip()
    if not fen:
        return False, "FEN is empty after stripping"
    
    parts = fen.split()
    if len(parts) < 4:
        return False, f"FEN must have at least 4 parts, got {len(parts)}"
    
    position = parts[0]
    rows = position.split('/')
    if len(rows) != 8:
        return False, f"FEN must have 8 rows, got {len(rows)}"
    
    # Validate each row
    for i, row in enumerate(rows):
        square_count = 0
        for char in row:
            if char.isdigit():
                square_count += int(char)
            elif char in 'rnbqkpRNBQKP':
                square_count += 1
            else:
                return False, f"Row {8-i} contains invalid character: '{char}'"
        
        if square_count != 8:
            return False, f"Row {8-i} has {square_count} squares, must be 8"
    
    # Check kings
    white_kings = position.count('K')
    black_kings = position.count('k')
    if white_kings != 1:
        return False, f"Must have exactly 1 white king, found {white_kings}"
    if black_kings != 1:
        return False, f"Must have exactly 1 black king, found {black_kings}"
    
    # Use python-chess for final validation
    if chess:
        try:
            chess.Board(fen)
        except ValueError as e:
            return False, f"python-chess validation failed: {str(e)}"
    
    return True, None
