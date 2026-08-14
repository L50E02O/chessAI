import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import numpy as np

from backend.app.cv_detector import find_board
from tests.helpers.board_renderer import render_board


def test_find_board_on_synthetic_start_position():
    img = render_board('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1')
    board = find_board(np.array(img.convert('RGB'))[:, :, ::-1])
    assert board is not None
    assert board.shape == (480, 480, 3)
