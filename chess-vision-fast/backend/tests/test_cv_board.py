import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import numpy as np

from backend.app.cv_detector import _green_board_quad, _verify_board, find_board
from tests.helpers.board_renderer import render_board, render_green_theme_board

START = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'


def _to_bgr(img):
    return np.array(img.convert('RGB'))[:, :, ::-1]


def test_find_board_on_synthetic_start_position():
    img = render_board(START)
    board = find_board(_to_bgr(img))
    assert board is not None
    assert board.shape == (480, 480, 3)


def test_find_board_edge_to_edge_large_board():
    # A chess.com screenshot cropped tight to the board (no green frame,
    # 80px cells filling a 640x640 image) must still be detected and warped
    # with its 8x8 grid aligned to the cells.
    img = render_board(START, square=80, frame=0, page_margin=0)
    board = find_board(_to_bgr(img))
    assert board is not None
    assert board.shape == (480, 480, 3)
    assert _verify_board(board)


def test_find_board_framed_large_board():
    # A board with a visible green frame but larger-than-480 cells must be
    # warped using its real interior, not a misaligned centered 480 window.
    img = render_board(START, square=80, frame=16, page_margin=40)
    board = find_board(_to_bgr(img))
    assert board is not None
    assert board.shape == (480, 480, 3)
    assert _verify_board(board)


def test_green_theme_board_detection():
    # chess.com green theme: dark squares are green and there is no frame, so
    # the board is detected from the green checkerboard extent.
    img = _to_bgr(render_green_theme_board(START))
    quad = _green_board_quad(img)
    assert quad is not None
    board = find_board(img)
    assert board is not None
    assert board.shape == (480, 480, 3)
    assert _verify_board(board)
