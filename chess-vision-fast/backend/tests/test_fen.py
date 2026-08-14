import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.app.detector import SquareDetection
from backend.app.fen import fen_from_squares, matrix_to_fen


def test_matrix_to_fen_empty_archive():
    matrix = [['' for _ in range(8)] for _ in range(8)]
    fen = matrix_to_fen(matrix)
    assert fen.startswith('8/8/8/8/8/8/8/8'), 'La fila vacía debe generar 8s'


def test_fen_from_square_detections():
    squares = [
        SquareDetection(square='e2', piece='P', bbox=(0, 0, 0, 0)),
        SquareDetection(square='e7', piece='p', bbox=(0, 0, 0, 0)),
    ]
    fen = fen_from_squares(squares)
    assert 'P' in fen and 'p' in fen
    assert fen.endswith('w KQkq - 0 1')


def test_matrix_to_fen_w_top_orientation():
    matrix = [['' for _ in range(8)] for _ in range(8)]
    matrix[0][0] = 'P'   # image top-left corner
    matrix[7][7] = 'p'   # image bottom-right corner
    fen = matrix_to_fen(matrix, orientation='w-top')
    ranks = fen.split()[0].split('/')
    assert ranks[0] == 'p7', f'rank 8 must start at a8 with the black piece, got {ranks[0]}'
    assert ranks[7] == '7P', f'rank 1 must end at h1 with the white piece, got {ranks[7]}'


def test_matrix_to_fen_w_bottom_default():
    matrix = [['' for _ in range(8)] for _ in range(8)]
    matrix[0][0] = 'k'   # image top-left corner (a8)
    matrix[7][7] = 'K'   # image bottom-right corner (h1)
    fen = matrix_to_fen(matrix)
    ranks = fen.split()[0].split('/')
    assert ranks[0] == 'k7', ranks[0]
    assert ranks[7] == '7K', ranks[7]
