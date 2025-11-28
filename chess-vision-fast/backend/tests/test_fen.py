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
