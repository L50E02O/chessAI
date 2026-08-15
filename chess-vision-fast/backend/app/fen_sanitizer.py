"""FEN sanitization and validation for the analysis pipeline."""
from dataclasses import dataclass, field
from typing import List, Optional

import chess

INVALID_FEN_MESSAGE = (
    'Invalid FEN generated from board image. '
    'Please check piece placement or re-upload.'
)

INITIAL_COUNTS = {'R': 2, 'N': 2, 'B': 2, 'Q': 1, 'K': 1}
FILE_PIECE = {'a': 'R', 'b': 'N', 'c': 'B', 'd': 'Q', 'e': 'K', 'f': 'B', 'g': 'N', 'h': 'R'}
FIX_PRIORITY = ['R', 'N', 'B', 'Q']


def compute_castling(board_part: str) -> str:
    board = chess.Board(board_part)
    rights = []
    if board.piece_at(chess.parse_square('e1')) == chess.Piece(chess.KING, chess.WHITE):
        if board.piece_at(chess.parse_square('h1')) == chess.Piece(chess.ROOK, chess.WHITE):
            rights.append('K')
        if board.piece_at(chess.parse_square('a1')) == chess.Piece(chess.ROOK, chess.WHITE):
            rights.append('Q')
    if board.piece_at(chess.parse_square('e8')) == chess.Piece(chess.KING, chess.BLACK):
        if board.piece_at(chess.parse_square('h8')) == chess.Piece(chess.ROOK, chess.BLACK):
            rights.append('k')
        if board.piece_at(chess.parse_square('a8')) == chess.Piece(chess.ROOK, chess.BLACK):
            rights.append('q')
    return ''.join(rights) or '-'
