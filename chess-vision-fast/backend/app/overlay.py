import base64
from io import BytesIO
from typing import Iterable, List, Optional, Tuple

from PIL import Image, ImageDraw


class OverlayCoords:
    def __init__(self, from_xy: Tuple[float, float], to_xy: Tuple[float, float]) -> None:
        self.from_xy = from_xy
        self.to_xy = to_xy


def _normalize_point(point: Tuple[float, float], size: Tuple[int, int]) -> Tuple[float, float]:
    width, height = size
    return point[0] / width, point[1] / height


def _square_centers(squares: Iterable[dict]) -> dict:
    centers = {}
    for square in squares:
        x, y, w, h = square['bbox']
        centers[square['square']] = (x + w / 2, y + h / 2)
    return centers


def draw_overlay(
    base_image: Image.Image,
    squares: Iterable[dict],
    best_move: Optional[str] = None,
) -> Tuple[str, List[float]]:
    overlay = Image.new('RGBA', base_image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    centers = _square_centers(squares)
    size = base_image.size

    for square in squares:
        x, y, w, h = square['bbox']
        draw.rectangle([x, y, x + w, y + h], outline=(255, 255, 255, 180), width=1)
        draw.rectangle([x, y, x + w, y + h], outline=(255, 0, 0, 180), width=1)

    arrow_coords: List[float] = []
    if best_move:
        from_sq = best_move[:2]
        to_sq = best_move[2:4]
        if from_sq in centers and to_sq in centers:
            from_center = centers[from_sq]
            to_center = centers[to_sq]
            draw.line([*from_center, *to_center], fill=(0, 255, 0, 200), width=4)
            arrow_coords = [*_normalize_point(from_center, size), *_normalize_point(to_center, size)]

    combined = Image.alpha_composite(base_image.convert('RGBA'), overlay)
    buffer = BytesIO()
    combined.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode('ascii'), arrow_coords
