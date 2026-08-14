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


def _inner_cell(board: np.ndarray, r: int, c: int, ratio: float = 0.6) -> np.ndarray:
    side = int(CELL * ratio)
    x = int(c * CELL + (CELL - side) / 2)
    y = int(r * CELL + (CELL - side) / 2)
    return board[y:y + side, x:x + side]


def _verify_board(board: np.ndarray) -> bool:
    cells = np.empty((8, 8), dtype=float)
    for r in range(8):
        for c in range(8):
            cells[r, c] = _luminance(np.mean(_inner_cell(board, r, c), axis=(0, 1)))
    violations = 0
    for r in range(7):
        for c in range(8):
            if abs(cells[r, c] - cells[r + 1, c]) < 15:
                violations += 1
    return violations <= 4


def _crop_frame(warped: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    border = float(np.mean([gray[h // 2, 10], gray[h // 2, w - 10], gray[10, w // 2], gray[h - 10, w // 2]]))
    mask = np.abs(gray.astype(np.float32) - border) > 20
    ys, xs = np.where(mask)
    if len(ys) == 0:
        return warped
    return warped[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def find_board(image: np.ndarray) -> Optional[np.ndarray]:
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

    dst = np.float32([[0, 0], [TARGET_SIZE, 0], [TARGET_SIZE, TARGET_SIZE], [0, TARGET_SIZE]])
    matrix = cv2.getPerspectiveTransform(best, dst)
    warped = cv2.warpPerspective(image, matrix, (TARGET_SIZE, TARGET_SIZE))
    board = cv2.resize(_crop_frame(warped), (TARGET_SIZE, TARGET_SIZE))
    if not _verify_board(board):
        return None
    return board


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
    _, labels, centers = cv2.kmeans(pixels, k, None, criteria, 3, cv2.KMEANS_PP_CENTERS)
    counts = np.bincount(labels.ravel(), minlength=k)
    order = np.argsort(-counts)
    colors = [centers[order[0]], centers[order[1]]]
    if _luminance(colors[0]) < _luminance(colors[1]):
        colors.reverse()
    return colors[0], colors[1]


def square_state(cell: np.ndarray, light, dark) -> Tuple[bool, Optional[str]]:
    mean = np.mean(_inner_cell(cell, 0, 0), axis=(0, 1))
    d_light = float(np.linalg.norm(mean - light))
    d_dark = float(np.linalg.norm(mean - dark))
    if d_light < 45 or d_dark < 45:
        return False, None
    mid = (_luminance(light) + _luminance(dark)) / 2
    return True, ('w' if _luminance(mean) > mid else 'b')


def _extract_piece(cell: np.ndarray, margin: int = 3) -> Optional[np.ndarray]:
    h, w = cell.shape[:2]
    corners = np.concatenate([
        cell[:5, :5].reshape(-1, 3),
        cell[:5, -5:].reshape(-1, 3),
        cell[-5:, :5].reshape(-1, 3),
        cell[-5:, -5:].reshape(-1, 3),
    ])
    bg = np.mean(corners, axis=0)
    mask = np.linalg.norm(cell.astype(np.float32) - bg, axis=2) > 25
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
        return img[ys.min():ys.max() + 1, xs.min():xs.max() + 1, :3]
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
