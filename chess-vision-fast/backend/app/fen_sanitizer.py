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


@dataclass
class FenSanitizeResult:
    fen: str
    valid: bool
    warnings: List[str] = field(default_factory=list)
    error: Optional[str] = None


DEFAULT_FIELDS = ['w', '-', '-', '0', '1']

UNRECOVERABLE_MASK = (
    chess.STATUS_NO_WHITE_KING
    | chess.STATUS_NO_BLACK_KING
    | chess.STATUS_TOO_MANY_KINGS
    | chess.STATUS_TOO_MANY_WHITE_PAWNS
    | chess.STATUS_TOO_MANY_BLACK_PAWNS
    | chess.STATUS_TOO_MANY_WHITE_PIECES
    | chess.STATUS_TOO_MANY_BLACK_PIECES
    | chess.STATUS_PAWNS_ON_BACKRANK
    | chess.STATUS_BAD_CASTLING_RIGHTS
)


def _counts_for(board: chess.Board, color: bool) -> dict:
    counts = {p: 0 for p in 'RNBQK'}
    for piece in board.piece_map().values():
        if piece.color == color and piece.piece_type != chess.PAWN:
            counts[piece.symbol().upper()] += 1
    return counts


def _backrank_pawns(board: chess.Board) -> list:
    return sorted(
        chess.square_name(sq)
        for sq, piece in board.piece_map().items()
        if piece.piece_type == chess.PAWN and chess.square_rank(sq) in (0, 7)
    )


def _fix_backrank_pawns(board: chess.Board, warnings: list) -> bool:
    for sq_name in _backrank_pawns(board):
        sq = chess.parse_square(sq_name)
        color = board.piece_at(sq).color
        counts = _counts_for(board, color)
        deficits = [t for t in 'RNBQK' if counts[t] < INITIAL_COUNTS[t]]
        expected = FILE_PIECE[sq_name[0]]

        candidates = []
        if expected in deficits:
            candidates.append(expected)
        if expected != 'K' and 'K' in deficits and 'K' not in candidates:
            candidates.append('K')
        for t in FIX_PRIORITY:
            if t in deficits and t not in candidates:
                candidates.append(t)

        if not candidates:
            return False

        chosen = candidates[0]
        symbol = chosen.lower() if color == chess.BLACK else chosen
        board.set_piece_at(sq, chess.Piece.from_symbol(symbol))
        display = chosen.lower() if color == chess.BLACK else chosen
        warnings.append(f'Back-rank pawn on {sq_name} replaced with {display}.')
    return True


def _fix_castling(parts: list, had_castling: bool, warnings: list) -> None:
    if not had_castling:
        parts[2] = '-'
        return
    declared = parts[2]
    if declared == '-':
        return
    actual = compute_castling(parts[0])
    kept = ''.join(ch for ch in declared if ch in actual)
    if kept != declared:
        parts[2] = kept or '-'
        warnings.append(
            f'Removed invalid castling rights ({declared} -> {parts[2]}).'
        )


def sanitize_fen(fen: str) -> FenSanitizeResult:
    warnings = []
    stripped = fen.strip()
    parts = stripped.split()
    if not stripped or len(parts) > 6:
        return FenSanitizeResult(fen='', valid=False, error=INVALID_FEN_MESSAGE)

    had_castling = len(parts) > 2
    while len(parts) < 6:
        parts.append(DEFAULT_FIELDS[len(parts) - 1])

    try:
        board = chess.Board(' '.join(parts))
    except ValueError:
        return FenSanitizeResult(fen='', valid=False, error=INVALID_FEN_MESSAGE)

    if not _fix_backrank_pawns(board, warnings):
        return FenSanitizeResult(fen='', valid=False, error=INVALID_FEN_MESSAGE)
    parts[0] = board.fen().split()[0]

    _fix_castling(parts, had_castling, warnings)

    if chess.Board(' '.join(parts)).status() & UNRECOVERABLE_MASK:
        return FenSanitizeResult(fen='', valid=False, error=INVALID_FEN_MESSAGE)

    return FenSanitizeResult(fen=' '.join(parts), valid=True, warnings=warnings)
