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

from src.utils.supabase_client import get_supabase, get_bucket_name
from src.utils.helpers import short_log


def capture_fullscreen() -> np.ndarray:
    """Capture the primary monitor and return as RGB numpy array."""
    with mss() as sct:
        monitor = sct.monitors[1]
        raw = sct.grab(monitor)
        img = Image.frombytes('RGB', raw.size, raw.rgb)
        return np.array(img)


def _largest_square_contour(gray: np.ndarray) -> Optional[np.ndarray]:
    # Edge detection and contour extraction
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 60, 180)
    edges = cv2.dilate(edges, None, iterations=1)

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    best = None
    best_score = 0.0
    h, w = gray.shape[:2]
    img_area = w * h

    for cnt in contours:
        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
        if len(approx) != 4:
            continue
        area = cv2.contourArea(approx)
        if area < img_area * 0.02:  # ignore tiny
            continue
        x, y, ww, hh = cv2.boundingRect(approx)
        ratio = min(ww, hh) / max(ww, hh)
        squareness = ratio  # 1.0 is perfect square
        score = area * squareness
        if score > best_score:
            best = approx
            best_score = score

    return best


def detect_board_bbox(image_rgb: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
    """Try to find a chessboard-like square and return bounding box (x, y, w, h) in pixels."""
    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
    quad = _largest_square_contour(gray)
    if quad is None:
        return None
    x, y, w, h = cv2.boundingRect(quad)
    # Inflate slightly to include outer border
    pad = int(0.02 * max(w, h))
    x = max(0, x - pad)
    y = max(0, y - pad)
    return x, y, min(image_rgb.shape[1] - x, w + 2 * pad), min(image_rgb.shape[0] - y, h + 2 * pad)


def crop_board(image_rgb: np.ndarray) -> np.ndarray:
    bbox = detect_board_bbox(image_rgb)
    h, w = image_rgb.shape[:2]
    if bbox is None:
        # Fallback: central square crop
        side = min(w, h)
        cx, cy = w // 2, h // 2
        half = side // 2
        x, y = max(0, cx - half), max(0, cy - half)
        crop = image_rgb[y:y+side, x:x+side]
        return crop
    x, y, ww, hh = bbox
    side = min(ww, hh)
    return image_rgb[y:y+side, x:x+side]


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def save_temp_board(image_rgb: np.ndarray, folder: str) -> str:
    ensure_dir(folder)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    fn = f"board_{ts}.png"
    full = os.path.join(folder, fn)
    Image.fromarray(image_rgb).save(full)
    return full


# ---------------- Supabase storage helpers ----------------

def upload_image_to_supabase(local_path: str, prefix: str = "boards") -> str:
    """Upload image to Supabase Storage bucket and return a signed URL.

    Bucket is read from SUPABASE_BUCKET (default 'boards'). Files stored under prefix/filename.
    Also enforces retention of max 10 images (delete oldest by name).
    """
    supa = get_supabase()
    bucket = get_bucket_name()
    name = os.path.basename(local_path)
    key = f"{prefix}/{name}"

    with open(local_path, 'rb') as f:
        data = f.read()
    # Upload (overwrite = False)
    supa.storage.from_(bucket).upload(file=data, path=key, file_options={"contentType": "image/png", "upsert": False})

    # Prune to last 10 by filename (timestamp-based)
    _prune_supabase(bucket, prefix, keep=10)

    # Create a signed URL valid for 24h
    signed = supa.storage.from_(bucket).create_signed_url(path=key, expires_in=60 * 60 * 24)
    return signed.get('signedURL') or signed.get('signed_url') or ''


def _prune_supabase(bucket: str, prefix: str, keep: int = 10) -> None:
    supa = get_supabase()
    items = supa.storage.from_(bucket).list(path=prefix)
    if not isinstance(items, list) or len(items) <= keep:
        return
    # Sort by name (board_YYYYMMDD_HHMMSS.png -> lexicographic order equals chronological)
    names: List[str] = sorted([it.get('name') for it in items if isinstance(it, dict) and it.get('name')])
    to_delete = names[:-keep]
    for nm in to_delete:
        path = f"{prefix}/{nm}"
        try:
            supa.storage.from_(bucket).remove(path)
        except Exception as e:
            short_log(f"Failed to delete {path}: {e}")


# ---------------- Hotkey flow ----------------

def handle_capture_and_upload(captures_dir: str = os.path.join(os.path.dirname(__file__), '..', '..', 'captures')) -> Optional[str]:
    try:
        rgb = capture_fullscreen()
        board = crop_board(rgb)
        local = save_temp_board(board, os.path.abspath(captures_dir))
        url = upload_image_to_supabase(local)
        short_log(f"Imagen subida. URL firmada: {url}")
        return url
    except Exception as e:
        short_log(f"Error en captura/subida: {e}")
        return None
