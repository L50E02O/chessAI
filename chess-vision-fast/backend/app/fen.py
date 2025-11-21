from typing import Iterable

import chess


def build_matrix_from_squares(squares: Iterable['SquareDetection']) -> list[list[str]]:
    empty = [['' for _ in range(8)] for _ in range(8)]
    for detection in squares:
        if not detection.piece:
            continue
        rank = int(detection.square[1])
        file = detection.square[0]
        row = 8 - rank
        col = ord(file) - ord('a')
        if 0 <= row < 8 and 0 <= col < 8:
            empty[row][col] = detection.piece
    return empty


def matrix_to_fen(matrix: list[list[str]], active_color: str = 'w', castling: str = 'KQkq', en_passant: str = '-', halfmove_clock: int = 0, fullmove_number: int = 1) -> str:
    rows = []
    for row in matrix:
        empties = 0
        row_parts = []
        for cell in row:
            if not cell:
                empties += 1
                continue
            if empties:
                row_parts.append(str(empties))
                empties = 0
            row_parts.append(cell)
        if empties:
            row_parts.append(str(empties))
        rows.append(''.join(row_parts) or '8')
    return '/'.join(rows) + f' {active_color} {castling} {en_passant} {halfmove_clock} {fullmove_number}'


def fen_from_squares(squares: Iterable['SquareDetection']) -> str:
    matrix = build_matrix_from_squares(squares)
    if all(all(cell == '' for cell in row) for row in matrix):
        return chess.STARTING_FEN
    return matrix_to_fen(matrix)


def confidence_from_squares(squares: Iterable['SquareDetection']) -> float:
    confidences = [det.confidence for det in squares if det.confidence]
    if not confidences:
        return 0.0
    return sum(confidences) / len(confidences)
