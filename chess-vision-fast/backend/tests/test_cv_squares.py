import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import numpy as np

from backend.app.cv_detector import classify_piece, empty_colors, square_state
from tests.helpers.board_renderer import render_board, LIGHT, DARK


def _empty_cell(color):
    cell = np.zeros((60, 60, 3), dtype=np.uint8)
    cell[:] = color
    return cell


def test_empty_colors_on_synthetic_board():
    img = np.array(render_board('4k3/8/8/8/8/8/8/4K3 w - - 0 1').convert('RGB'))[:, :, ::-1]
    light, dark = empty_colors(img)
    assert light.shape == (3,)
    assert dark.shape == (3,)


def test_square_state_empty():
    light = np.array(LIGHT, dtype=np.float32)
    dark = np.array(DARK, dtype=np.float32)
    occupied, color = square_state(_empty_cell(LIGHT), light, dark)
    assert occupied is False
    assert color is None


def test_square_state_occupied():
    light = np.array(LIGHT, dtype=np.float32)
    dark = np.array(DARK, dtype=np.float32)
    cell = _empty_cell(LIGHT)
    cell[10:50, 10:50] = (30, 30, 30)
    occupied, color = square_state(cell, light, dark)
    assert occupied is True
    assert color == 'b'


def test_square_state_highlighted_empty_square_is_empty():
    # chess.com tints the last-move/check square, changing its color so it no
    # longer matches either board color; an empty highlighted square must not
    # be reported as occupied.
    light = np.array(LIGHT, dtype=np.float32)
    dark = np.array(DARK, dtype=np.float32)
    cell = _empty_cell((67, 202, 185))
    occupied, color = square_state(cell, light, dark)
    assert occupied is False
    assert color is None


def test_classify_piece_white_queen():
    img = np.array(render_board('8/8/8/8/8/8/8/3QK3 w - - 0 1').convert('RGB'))[:, :, ::-1]
    # d1 square: renderer offsets board interior by (frame + page_margin) = 56, so cell rows 476:536, cols 236:296
    cell = img[476:536, 236:296]
    letter, score = classify_piece(cell, 'w')
    assert letter == 'Q'
    assert score > 0.5
