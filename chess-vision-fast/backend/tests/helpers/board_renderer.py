"""Renders a chess.com-style board image from a FEN, for CV pipeline tests."""
from pathlib import Path

import chess
import numpy as np
from PIL import Image, ImageDraw

LIGHT = (240, 217, 181)
DARK = (181, 136, 99)
FRAME = (81, 105, 81)
PIECES_DIR = Path(__file__).resolve().parents[2] / 'app' / 'assets' / 'pieces'
PIECES = {
    key: Image.open(PIECES_DIR / f'{key}.png').convert('RGBA')
    for key in ['wP', 'wN', 'wB', 'wR', 'wQ', 'wK', 'bP', 'bN', 'bB', 'bR', 'bQ', 'bK']
}


def render_board(fen: str, square: int = 60, frame: int = 16, page_margin: int = 40, white_top: bool = False) -> Image.Image:
    board = chess.Board(fen)
    inner = square * 8
    img = Image.new('RGB', (inner + frame * 2 + page_margin * 2, inner + frame * 2 + page_margin * 2), (250, 250, 250))
    draw = ImageDraw.Draw(img)
    frame_x = page_margin
    frame_y = page_margin
    draw.rectangle([frame_x, frame_y, frame_x + inner + frame * 2, frame_y + inner + frame * 2], fill=FRAME)
    ox, oy = page_margin + frame, page_margin + frame
    for r in range(8):
        for c in range(8):
            color = LIGHT if (r + c) % 2 == 0 else DARK
            x0, y0 = ox + c * square, oy + r * square
            draw.rectangle([x0, y0, x0 + square, y0 + square], fill=color)
    for r in range(8):
        for c in range(8):
            if white_top:
                sq = chess.square(7 - c, r)
            else:
                sq = chess.square(c, 7 - r)
            piece = board.piece_at(sq)
            if piece is None:
                continue
            key = ('w' if piece.color == chess.WHITE else 'b') + piece.symbol().upper()
            pimg = PIECES[key].resize((square, square), Image.Resampling.LANCZOS)
            img.paste(pimg, (ox + c * square, oy + r * square), pimg)
    return img
