"""Classical computer-vision chess board detection for chess.com screenshots."""
import logging
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)

TARGET_SIZE = 480
CELL = TARGET_SIZE // 8


def _order_points(pts: np.ndarray) -> np.ndarray:
    rect = np.zeros((4, 2), dtype=np.float32)
    s = pts.sum(axis=1)
    d = np.diff(pts, axis=1).ravel()
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    rect[1] = pts[np.argmin(d)]
    rect[3] = pts[np.argmax(d)]
    return rect


def _luminance(bgr) -> float:
    return 0.114 * float(bgr[0]) + 0.587 * float(bgr[1]) + 0.299 * float(bgr[2])


def _verify_board(board: np.ndarray) -> bool:
    """Return True when the warped board is an aligned 8x8 checkerboard.

    Samples the four corners of every cell rather than its center, because
    pieces occupy the middle of cells and would otherwise break the
    luminance alternation check even on a correctly aligned board."""
    p = 6
    cells = np.empty((8, 8), dtype=float)
    for r in range(8):
        for c in range(8):
            x, y = c * CELL, r * CELL
            pts = [
                (y, x),
                (y, x + CELL - p),
                (y + CELL - p, x),
                (y + CELL - p, x + CELL - p),
            ]
            vals = [_luminance(np.mean(board[yy:yy + p, xx:xx + p], axis=(0, 1))) for yy, xx in pts]
            cells[r, c] = np.mean(vals)
    violations = 0
    for r in range(7):
        for c in range(8):
            if abs(cells[r, c] - cells[r + 1, c]) < 15:
                violations += 1
    for r in range(8):
        for c in range(7):
            if abs(cells[r, c] - cells[r, c + 1]) < 15:
                violations += 1
    return violations <= 8


def _interior_quad(image: np.ndarray) -> Optional[np.ndarray]:
    """Detect the board interior (the playable 8x8 area) via its non-green
    extent and return its four corners. The full detected square is used (not
    a fixed-size window) so boards with any cell size are warped with their
    grid aligned."""
    b = image[:, :, 0].astype(np.int32)
    g = image[:, :, 1].astype(np.int32)
    r = image[:, :, 2].astype(np.int32)
    is_green = (g > r + 12) & (g > b + 12)
    non_green = (~is_green).astype(np.uint8)
    eroded = cv2.erode(non_green, np.ones((3, 3), np.uint8), iterations=2)
    n, labels, stats, cents = cv2.connectedComponentsWithStats(eroded, 8)
    if n <= 1:
        return None
    big = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    # Recover the true board extent: grow the eroded component back by the
    # erosion radius and keep only original non-green pixels, so the quad
    # lands exactly on the board boundary instead of a shifted estimate.
    grown = cv2.dilate((labels == big).astype(np.uint8), np.ones((3, 3), np.uint8), iterations=2)
    ys, xs = np.where((grown > 0) & (non_green > 0))
    if len(ys) < TARGET_SIZE * CELL:
        return None
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    side = min(x1 - x0, y1 - y0)
    if side < TARGET_SIZE // 2:
        return None
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    x0, x1 = int(round(cx - side / 2)), int(round(cx + side / 2))
    y0, y1 = int(round(cy - side / 2)), int(round(cy + side / 2))
    if x0 < 0 or y0 < 0 or x1 > image.shape[1] or y1 > image.shape[0]:
        return None
    return np.float32([[x0, y0], [x1, y0], [x1, y1], [x0, y1]])


def _largest_square_quad(image: np.ndarray) -> Optional[np.ndarray]:
    """Fallback quad covering the largest centered square of the image,
    used for tight edge-to-edge board screenshots with no green frame."""
    h, w = image.shape[:2]
    side = min(h, w)
    if side < TARGET_SIZE // 2:
        return None
    x0, y0 = (w - side) // 2, (h - side) // 2
    return np.float32([[x0, y0], [x0 + side, y0], [x0 + side, y0 + side], [x0, y0 + side]])


def _green_board_quad(image: np.ndarray) -> Optional[np.ndarray]:
    """Detect a board whose dark squares are green (chess.com green theme).

    In that theme there is no green frame to segment; the green mask itself is
    the checkerboard. Its largest 8-connected component spans the whole board,
    so the component bbox is the board extent. A sparse/ring-shaped green mask
    (e.g. a green frame, or incidental green page elements) is rejected by the
    fill-ratio guard and falls through to the other candidates."""
    b = image[:, :, 0].astype(np.int32)
    g = image[:, :, 1].astype(np.int32)
    r = image[:, :, 2].astype(np.int32)
    is_green = (g > r + 12) & (g > b + 12)
    n, labels, stats, cents = cv2.connectedComponentsWithStats(is_green.astype(np.uint8), 8)
    if n <= 1:
        return None
    big = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    x0 = int(stats[big, cv2.CC_STAT_LEFT])
    y0 = int(stats[big, cv2.CC_STAT_TOP])
    x1 = x0 + int(stats[big, cv2.CC_STAT_WIDTH])
    y1 = y0 + int(stats[big, cv2.CC_STAT_HEIGHT])
    bbox_area = (x1 - x0) * (y1 - y0)
    if stats[big, cv2.CC_STAT_AREA] < 0.3 * bbox_area:
        return None
    side = min(x1 - x0, y1 - y0)
    if side < TARGET_SIZE // 2:
        return None
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    x0, x1 = int(round(cx - side / 2)), int(round(cx + side / 2))
    y0, y1 = int(round(cy - side / 2)), int(round(cy + side / 2))
    if x0 < 0 or y0 < 0 or x1 > image.shape[1] or y1 > image.shape[0]:
        return None
    return np.float32([[x0, y0], [x1, y0], [x1, y1], [x0, y1]])


def _warp_board(image: np.ndarray, quad: np.ndarray) -> np.ndarray:
    dst = np.float32([[0, 0], [TARGET_SIZE, 0], [TARGET_SIZE, TARGET_SIZE], [0, TARGET_SIZE]])
    matrix = cv2.getPerspectiveTransform(quad, dst)
    return cv2.warpPerspective(image, matrix, (TARGET_SIZE, TARGET_SIZE), flags=cv2.INTER_NEAREST)


def _find_board_contours(image: np.ndarray) -> Optional[np.ndarray]:
    """Fallback board detection based on the outer 4-corner contour."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY_INV, 11, 2)
    thresh = cv2.dilate(thresh, np.ones((5, 5), np.uint8), iterations=1)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    best = None
    best_area = 0
    for contour in contours:
        peri = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
        if len(approx) != 4:
            continue
        pts = approx.reshape(4, 2).astype(np.float32)
        pts = _order_points(pts)
        side1 = float(np.linalg.norm(pts[1] - pts[0]))
        side2 = float(np.linalg.norm(pts[2] - pts[1]))
        if side1 == 0 or side2 == 0:
            continue
        aspect = max(side1, side2) / min(side1, side2)
        area = cv2.contourArea(approx)
        if 0.8 <= aspect <= 1.25 and area > best_area:
            best_area = area
            best = pts

    if best is None:
        return None
    return _warp_board(image, best)


def find_board(image: np.ndarray) -> Optional[np.ndarray]:
    candidates = []
    quad = _interior_quad(image)
    if quad is not None:
        candidates.append(_warp_board(image, quad))
    green = _green_board_quad(image)
    if green is not None:
        candidates.append(_warp_board(image, green))
    square = _largest_square_quad(image)
    if square is not None:
        candidates.append(_warp_board(image, square))
    contour = _find_board_contours(image)
    if contour is not None:
        candidates.append(contour)
    for board in candidates:
        if _verify_board(board):
            return board
    return candidates[0] if candidates else None


PIECES_DIR = Path(__file__).resolve().parent / 'assets' / 'pieces'
TEMPLATE_SIZE = 128
PIECE_LETTERS = ['P', 'N', 'B', 'R', 'Q', 'K']
_TEMPLATES = {}


def _load_templates() -> dict:
    global _TEMPLATES
    if _TEMPLATES:
        return _TEMPLATES
    for letter in PIECE_LETTERS:
        for color in ('w', 'b'):
            path = PIECES_DIR / f'{color}{letter}.png'
            img = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
            if img is not None:
                _TEMPLATES.setdefault(letter, {})[color] = img
    return _TEMPLATES


def empty_colors(board: np.ndarray, k: int = 4) -> Tuple[np.ndarray, np.ndarray]:
    pixels = board.reshape(-1, 3).astype(np.float32)[::4]
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    cv2.setRNGSeed(42)
    _, labels, centers = cv2.kmeans(pixels, k, None, criteria, 10, cv2.KMEANS_PP_CENTERS)
    counts = np.bincount(labels.ravel(), minlength=k)
    order = np.argsort(-counts)
    colors = [centers[order[0]], centers[order[1]]]
    if _luminance(colors[0]) < _luminance(colors[1]):
        colors.reverse()
    return colors[0], colors[1]


def square_state(cell: np.ndarray, light, dark) -> Tuple[bool, Optional[str]]:
    bg = np.median(cell.reshape(-1, 3), axis=0)
    sq = light if np.linalg.norm(bg - light) < np.linalg.norm(bg - dark) else dark
    mask = np.linalg.norm(cell.astype(np.float32) - sq, axis=2) > 25
    # The cell must also differ from its own median: chess.com highlights the
    # last-move/check squares with a tint that changes the square color, which
    # would otherwise look "occupied" even when empty.
    non_uniform = np.linalg.norm(cell.astype(np.float32) - bg, axis=2) > 25
    if mask.mean() < 0.05 or non_uniform.mean() < 0.05:
        return False, None
    mean = np.mean(cell[non_uniform], axis=0)
    mid = (_luminance(light) + _luminance(dark)) / 2
    return True, ('w' if _luminance(mean) > mid else 'b')


def _extract_piece(cell: np.ndarray, margin: int = 3) -> Optional[np.ndarray]:
    h, w = cell.shape[:2]
    bg = np.median(cell.reshape(-1, 3), axis=0)
    mask = np.linalg.norm(cell.astype(np.float32) - bg, axis=2) > 25
    # Remove thin boundary strips left by residual grid misalignment so the
    # cropped silhouette matches the clean template despite ~1px warping error.
    mask = cv2.erode(mask.astype(np.uint8), np.ones((3, 3), np.uint8), iterations=1) > 0
    ys, xs = np.where(mask)
    if len(ys) < 20:
        return None
    y0, y1 = max(0, ys.min() - margin), min(h, ys.max() + margin + 1)
    x0, x1 = max(0, xs.min() - margin), min(w, xs.max() + margin + 1)
    piece = cell[y0:y1, x0:x1].copy()
    piece[~mask[y0:y1, x0:x1]] = 0
    return piece


def _template_piece(img: np.ndarray) -> Optional[np.ndarray]:
    if img.shape[2] == 4:
        alpha = img[:, :, 3]
        ys, xs = np.where(alpha > 30)
        if len(ys) == 0:
            return None
        crop = img[ys.min():ys.max() + 1, xs.min():xs.max() + 1].copy()
        transparent = alpha[ys.min():ys.max() + 1, xs.min():xs.max() + 1] <= 30
        crop[transparent] = 0
        return crop
    return img


def classify_piece(cell: np.ndarray, piece_color: str) -> Optional[Tuple[str, float]]:
    extracted = _extract_piece(cell)
    if extracted is None:
        return None
    extracted = cv2.resize(extracted, (TEMPLATE_SIZE, TEMPLATE_SIZE))
    extracted_gray = cv2.cvtColor(extracted, cv2.COLOR_BGR2GRAY)
    best_letter = None
    best_score = -1.0
    for letter, by_color in _load_templates().items():
        tpl = by_color.get(piece_color)
        if tpl is None:
            continue
        tpiece = _template_piece(tpl)
        if tpiece is None:
            continue
        tpiece = cv2.resize(tpiece, (TEMPLATE_SIZE, TEMPLATE_SIZE))
        tpiece_gray = cv2.cvtColor(tpiece, cv2.COLOR_BGR2GRAY)
        score = float(cv2.matchTemplate(extracted_gray, tpiece_gray, cv2.TM_CCOEFF_NORMED)[0][0])
        if score > best_score:
            best_score = score
            best_letter = letter
    if best_letter is None or best_score < 0.5:
        return None
    return best_letter, best_score


import chess
from PIL import Image

from .detector import BaseDetector, DetectionResult, SquareDetection
from .fen import confidence_from_squares, matrix_to_fen


def _square_at(r: int, c: int) -> str:
    file = chr(ord('a') + c)
    rank = 8 - r
    return f'{file}{rank}'


def _detect_orientation(squares: list) -> str:
    top_white = sum(1 for s in squares if s.piece and s.piece.isupper() and s.bbox[1] < 4 * CELL)
    bot_white = sum(1 for s in squares if s.piece and s.piece.isupper() and s.bbox[1] >= 4 * CELL)
    if top_white > bot_white:
        return 'w-top'
    return 'w-bottom'


class CVBoardDetector(BaseDetector):
    def detect(self, image: Image.Image) -> DetectionResult:
        img = cv2.cvtColor(np.array(image.convert('RGB')), cv2.COLOR_RGB2BGR)
        board = find_board(img)
        if board is None:
            return self._error_result(
                image,
                'Could not detect the chess board. Make sure the screenshot shows the full board facing forward.',
            )
        colors = empty_colors(board)
        if colors is None:
            return self._error_result(image, 'Could not determine board colors.')
        light, dark = colors

        squares = []
        matrix = [['' for _ in range(8)] for _ in range(8)]
        unknown = []
        for r in range(8):
            for c in range(8):
                cell = board[r * CELL:(r + 1) * CELL, c * CELL:(c + 1) * CELL]
                occupied, piece_color = square_state(cell, light, dark)
                if not occupied:
                    continue
                classified = classify_piece(cell, piece_color)
                if classified is None:
                    unknown.append(_square_at(r, c))
                    continue
                letter, conf = classified
                fen_letter = letter if piece_color == 'w' else letter.lower()
                squares.append(SquareDetection(square=_square_at(r, c), bbox=(c * CELL, r * CELL, CELL, CELL), piece=fen_letter, confidence=conf))
                matrix[r][c] = fen_letter

        if unknown:
            return self._error_result(
                image,
                f'Could not classify pieces on squares: {", ".join(unknown)}. Try flipping the board or using a cleaner screenshot.',
            )

        orientation = _detect_orientation(squares)
        fen = matrix_to_fen(matrix, active_color='w', orientation=orientation)
        try:
            chess.Board(fen)
        except ValueError:
            return self._error_result(image, f'Invalid position detected: {fen}. Please try again.')

        board_pil = Image.fromarray(cv2.cvtColor(board, cv2.COLOR_BGR2RGB))
        return DetectionResult(
            fen=fen,
            board_image_base64=self._image_to_base64(board_pil),
            squares=squares,
            confidence=confidence_from_squares(squares),
            board_image=board_pil,
            orientation=orientation,
        )

    def _error_result(self, image: Image.Image, message: str) -> DetectionResult:
        return DetectionResult(
            fen='',
            board_image_base64=self._image_to_base64(image),
            squares=[],
            confidence=0.0,
            error=message,
        )
