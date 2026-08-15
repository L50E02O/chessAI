import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import numpy as np

from backend.app.cv_detector import CVBoardDetector
from tests.helpers.board_renderer import render_board, render_green_theme_board

START = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
MIDGAME = 'r1bq1rk1/ppp2ppp/2np1n2/2b1p3/2B1P3/2NP1N2/PPP2PPP/R1BQ1RK1 w - - 0 1'


def _detect(fen, white_top=False):
    detector = CVBoardDetector(None)
    img = render_board(fen, white_top=white_top)
    return detector.detect(img)


def test_detect_starting_position():
    result = _detect(START)
    assert result.fen.startswith('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR')
    assert result.confidence > 0.8
    assert len(result.squares) == 32


def test_detect_midgame():
    result = _detect(MIDGAME)
    board_part = result.fen.split()[0]
    assert board_part == 'r1bq1rk1/ppp2ppp/2np1n2/2b1p3/2B1P3/2NP1N2/PPP2PPP/R1BQ1RK1'


def test_detect_flipped_board():
    result = _detect(START, white_top=True)
    board_part = result.fen.split()[0]
    assert board_part == 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR'


def test_detect_returns_warped_board_image():
    result = _detect(START)
    assert result.board_image is not None
    assert result.board_image.size == (480, 480)


def test_detect_starting_position_framed_large_cells():
    # Regression: boards whose cells are larger than 60px (e.g. a 640x640
    # chess.com screenshot with a visible frame) used to be warped from a
    # misaligned centered 480px window, breaking piece classification.
    detector = CVBoardDetector(None)
    img = render_board(START, square=80, frame=16, page_margin=40)
    result = detector.detect(img)
    assert result.fen.startswith('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR')
    assert len(result.squares) == 32
    assert result.confidence > 0.8


def test_detect_starting_position_back_orientation_w_top():
    detector = CVBoardDetector(None)
    img = render_board(START, white_top=True)
    result = detector.detect(img, orientation='back')
    assert result.fen.startswith('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR')
    assert result.orientation == 'w-top'
    a1_entry = next(s for s in result.squares if s.square == 'a1')
    assert a1_entry is not None
    assert a1_entry.piece == 'R'


def test_detect_starting_position_front_orientation_w_bottom():
    detector = CVBoardDetector(None)
    img = render_board(START)
    result = detector.detect(img, orientation='front')
    assert result.fen.startswith('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR')
    assert result.orientation == 'w-bottom'


def test_detect_green_theme_board_with_highlighted_empty_square():
    # Regression: chess.com green theme (dark squares are green, no frame) plus
    # a last-move highlight on an empty square used to fail board detection and
    # treat the highlighted empty square as occupied.
    fen = '6k1/pppppppp/8/8/8/8/PPPPPPPP/6K1 w - - 0 1'
    detector = CVBoardDetector(None)
    img = render_green_theme_board(fen, highlight_squares=('h8',))
    result = detector.detect(img)
    assert result.fen.startswith('6k1/pppppppp/8/8/8/8/PPPPPPPP/6K1')
    assert len(result.squares) == 18
    assert all(s.square != 'h8' for s in result.squares)
