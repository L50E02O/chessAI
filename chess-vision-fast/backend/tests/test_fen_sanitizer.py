import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.app.fen_sanitizer import compute_castling


def test_compute_castling():
    assert compute_castling('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR') == 'KQkq'
    assert compute_castling('r3k3/8/8/8/8/8/8/R3K3') == 'Qq'
    assert compute_castling('4k3/8/8/8/8/8/8/4K3') == '-'


from backend.app.fen_sanitizer import (
    FenSanitizeResult,
    INVALID_FEN_MESSAGE,
    compute_castling,
    sanitize_fen,
)

START_FEN = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'


def test_valid_fen_passes_unchanged():
    result = sanitize_fen(START_FEN)
    assert result.valid is True
    assert result.fen == START_FEN
    assert result.warnings == []


def test_castling_pruned_when_rook_missing():
    fen = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBN1 w KQkq - 0 1'
    result = sanitize_fen(fen)
    assert result.valid is True
    assert result.fen == 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBN1 w Qkq - 0 1'
    assert any('castling' in w.lower() for w in result.warnings)


def test_castling_without_king_unrecoverable():
    result = sanitize_fen('rnbqbnr1/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1')
    assert result.valid is False
    assert result.fen == ''
    assert result.error == INVALID_FEN_MESSAGE


def test_board_only_fen_normalized():
    result = sanitize_fen('4k3/8/8/8/8/8/8/4K3')
    assert result.valid is True
    assert result.fen == '4k3/8/8/8/8/8/8/4K3 w - - 0 1'
    assert result.warnings == []


def test_backrank_pawn_replaced_and_castling_recovered():
    # a1 is a misdetected pawn; the missing rook is restored, which in turn
    # makes the declared castling right Q valid. Proves pawn fix runs first.
    result = sanitize_fen('4k3/8/8/8/8/8/8/P3K3 w KQkq - 0 1')
    assert result.valid is True
    assert result.fen == '4k3/8/8/8/8/8/8/R3K3 w Q - 0 1'
    assert any('a1' in w for w in result.warnings)


def test_backrank_black_pawn_replaced_with_rook():
    result = sanitize_fen('7p/8/8/8/8/8/8/4K2k w - - 0 1')
    assert result.valid is True
    assert result.fen == '7r/8/8/8/8/8/8/4K2k w - - 0 1'
    assert any('h8' in w for w in result.warnings)


def test_backrank_pawn_e1_with_full_material_unrecoverable():
    # e1 pawn while the white king is already on g2 and all other pieces are at
    # their initial counts: no piece type has a deficit, so the pawn is a
    # contradiction -> unrecoverable.
    fen = '4k3/8/8/8/8/8/6K1/RNBQPBNR w - - 0 1'
    result = sanitize_fen(fen)
    assert result.valid is False
    assert result.fen == ''


def test_two_backrank_pawns_single_deficit_unrecoverable():
    # a1 and h1 are pawns but only one rook is missing; the second pawn has no
    # piece type to restore into.
    fen = '4k3/8/8/8/8/8/R7/PNBQKBNP w - - 0 1'
    result = sanitize_fen(fen)
    assert result.valid is False
    assert result.fen == ''


def test_garbage_fen_unrecoverable():
    result = sanitize_fen('not a fen at all')
    assert result.valid is False
    assert result.fen == ''
    assert result.error == INVALID_FEN_MESSAGE
