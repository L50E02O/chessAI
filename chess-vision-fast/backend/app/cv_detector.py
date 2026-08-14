"""Classical computer-vision chess board detection for chess.com screenshots."""
import logging
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
