import io
import os
import time
from datetime import datetime
from typing import Optional, Tuple, List

import numpy as np

# Screenshot
from mss import mss
from PIL import Image

# CV for board detection
import cv2  # type: ignore

from src.utils.helpers import short_log


def capture_fullscreen() -> np.ndarray:
    """Capture all monitors as a single screenshot and return as RGB numpy array.
    
    Captures all monitors combined into a single image. If you have multiple
    monitors, the resulting image will include all of them.
    """
    with mss() as sct:
        # monitors[0] is the combination of all monitors
        monitor = sct.monitors[0]
        
        short_log(f"📐 Capturing screen: {monitor['width']}x{monitor['height']}px")
        short_log(f"   Position: ({monitor['left']}, {monitor['top']})")
        
        raw = sct.grab(monitor)
        img = Image.frombytes('RGB', raw.size, raw.rgb)
        return np.array(img)


def _find_chessboard_by_grid(gray: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
    """Detects board using grid patterns and lines."""
    h, w = gray.shape
    
    # Method 1: Line detection with Hough
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 50, 150)
    
    # Detect horizontal and vertical lines
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, minLineLength=100, maxLineGap=10)
    
    if lines is not None and len(lines) > 20:
        # Group horizontal and vertical lines
        h_lines = []
        v_lines = []
        
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = np.abs(np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi)
            
            if angle < 10 or angle > 170:  # Horizontal
                h_lines.append((y1 + y2) // 2)
            elif 80 < angle < 100:  # Vertical
                v_lines.append((x1 + x2) // 2)
        
        if len(h_lines) >= 8 and len(v_lines) >= 8:
            # Find board boundaries
            h_lines = sorted(h_lines)
            v_lines = sorted(v_lines)
            
            y_min, y_max = h_lines[0], h_lines[-1]
            x_min, x_max = v_lines[0], v_lines[-1]
            
            # Validate that it's approximately square
            width = x_max - x_min
            height = y_max - y_min
            ratio = min(width, height) / max(width, height)
            
            if ratio > 0.85 and width > w * 0.2:  # At least 20% of width
                return (x_min, y_min, width, height)
    
    return None


def _largest_square_contour(gray: np.ndarray) -> Optional[np.ndarray]:
    """Detects largest square contour (fallback method)."""
    # Edge detection and contour extraction
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 50, 150)
    edges = cv2.dilate(edges, None, iterations=2)
    edges = cv2.erode(edges, None, iterations=1)

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    best = None
    best_score = 0.0
    h, w = gray.shape[:2]
    img_area = w * h

    for cnt in contours:
        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.015 * peri, True)
        
        # Accept quadrilaterals (4 sides) or close polygons
        if len(approx) < 4 or len(approx) > 8:
            continue
            
        area = cv2.contourArea(approx)
        if area < img_area * 0.05:  # At least 5% of area
            continue
            
        x, y, ww, hh = cv2.boundingRect(approx)
        
        # Validate that it's approximately square
        ratio = min(ww, hh) / max(ww, hh)
        if ratio < 0.85:  # Too rectangular, not a board
            continue
            
        # Score based on area and squareness
        squareness = ratio
        score = area * squareness
        
        if score > best_score:
            best = approx
            best_score = score

    return best


def detect_board_bbox(image_rgb: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
    """Try to find a chessboard-like square and return bounding box (x, y, w, h) in pixels.
    
    Uses multiple methods:
    1. Grid detection (Hough lines)
    2. Color detection (boards with light/dark squares)
    3. Contour detection (fallback method)
    """
    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
    h, w = gray.shape[:2]
    
    # Method 1: Grid detection (best for chess.com/lichess)
    bbox = _find_chessboard_by_grid(gray)
    if bbox is not None:
        x, y, ww, hh = bbox
        # Validate reasonable size
        if ww > w * 0.15 and hh > h * 0.15:
            short_log(f"✓ Board detected by grid: {ww}x{hh}px")
            # Expand slightly to capture edges
            pad = int(0.02 * max(ww, hh))
            x = max(0, x - pad)
            y = max(0, y - pad)
            ww = min(w - x, ww + 2 * pad)
            hh = min(h - y, hh + 2 * pad)
            return (x, y, ww, hh)
    
    # Method 2: Contour detection (fallback)
    quad = _largest_square_contour(gray)
    if quad is not None:
        x, y, ww, hh = cv2.boundingRect(quad)
        if ww > w * 0.15 and hh > h * 0.15:
            short_log(f"✓ Board detected by contour: {ww}x{hh}px")
            # Expand slightly
            pad = int(0.02 * max(ww, hh))
            x = max(0, x - pad)
            y = max(0, y - pad)
            ww = min(w - x, ww + 2 * pad)
            hh = min(h - y, hh + 2 * pad)
            return (x, y, ww, hh)
    
    short_log("⚠ No board detected, using central crop")
    return None


def crop_board(image_rgb: np.ndarray) -> np.ndarray:
    """Detects and crops the chess board from the image.
    
    If it doesn't detect the board, uses an intelligent central crop.
    """
    bbox = detect_board_bbox(image_rgb)
    h, w = image_rgb.shape[:2]
    
    if bbox is None:
        # Improved fallback: search for most square region in center
        # Assume the board is somewhere in the center
        side = min(w, h)
        
        # Search in upper/left half (common in chess.com)
        search_w = int(w * 0.7)
        search_h = int(h * 0.8)
        
        # Center search but favor upper part
        cx = search_w // 2
        cy = search_h // 2
        
        half = min(search_w, search_h) // 2
        x = max(0, cx - half)
        y = max(0, cy - half)
        side = min(half * 2, w - x, h - y)
        
        crop = image_rgb[y:y+side, x:x+side]
        short_log(f"⚠ Central crop applied: {side}x{side}px from ({x},{y})")
        return crop
    
    x, y, ww, hh = bbox
    # Force to square by taking the smaller side
    side = min(ww, hh)
    crop = image_rgb[y:y+side, x:x+side]
    return crop


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def save_temp_board(image_rgb: np.ndarray, folder: str) -> str:
    ensure_dir(folder)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    fn = f"board_{ts}.png"
    full = os.path.join(folder, fn)
    Image.fromarray(image_rgb).save(full)
    return full

