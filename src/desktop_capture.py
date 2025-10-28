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
    """Capture all monitors as a single screenshot and return as RGB numpy array.
    
    Captura todos los monitores combinados en una sola imagen. Si tienes múltiples
    monitores, la imagen resultante incluirá todos.
    """
    with mss() as sct:
        # monitors[0] es la combinación de todos los monitores
        monitor = sct.monitors[0]
        
        short_log(f"📐 Capturando pantalla: {monitor['width']}x{monitor['height']}px")
        short_log(f"   Posición: ({monitor['left']}, {monitor['top']})")
        
        raw = sct.grab(monitor)
        img = Image.frombytes('RGB', raw.size, raw.rgb)
        return np.array(img)


def _find_chessboard_by_grid(gray: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
    """Detecta tablero usando patrones de cuadrícula y líneas."""
    h, w = gray.shape
    
    # Método 1: Detección de líneas con Hough
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 50, 150)
    
    # Detectar líneas horizontales y verticales
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, minLineLength=100, maxLineGap=10)
    
    if lines is not None and len(lines) > 20:
        # Agrupar líneas horizontales y verticales
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
            # Encontrar límites del tablero
            h_lines = sorted(h_lines)
            v_lines = sorted(v_lines)
            
            y_min, y_max = h_lines[0], h_lines[-1]
            x_min, x_max = v_lines[0], v_lines[-1]
            
            # Validar que sea aproximadamente cuadrado
            width = x_max - x_min
            height = y_max - y_min
            ratio = min(width, height) / max(width, height)
            
            if ratio > 0.85 and width > w * 0.2:  # Al menos 20% del ancho
                return (x_min, y_min, width, height)
    
    return None


def _largest_square_contour(gray: np.ndarray) -> Optional[np.ndarray]:
    """Detecta contorno cuadrado más grande (método de respaldo)."""
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
        
        # Aceptar cuadriláteros (4 lados) o polígonos cercanos
        if len(approx) < 4 or len(approx) > 8:
            continue
            
        area = cv2.contourArea(approx)
        if area < img_area * 0.05:  # Al menos 5% del área
            continue
            
        x, y, ww, hh = cv2.boundingRect(approx)
        
        # Validar que sea aproximadamente cuadrado
        ratio = min(ww, hh) / max(ww, hh)
        if ratio < 0.85:  # Muy rectangular, no es tablero
            continue
            
        # Score basado en área y cuadratura
        squareness = ratio
        score = area * squareness
        
        if score > best_score:
            best = approx
            best_score = score

    return best


def detect_board_bbox(image_rgb: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
    """Try to find a chessboard-like square and return bounding box (x, y, w, h) in pixels.
    
    Usa múltiples métodos:
    1. Detección por cuadrícula (Hough lines)
    2. Detección por color (tableros con cuadros claros/oscuros)
    3. Detección por contornos (método de respaldo)
    """
    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
    h, w = gray.shape[:2]
    
    # Método 1: Detección por cuadrícula (mejor para chess.com/lichess)
    bbox = _find_chessboard_by_grid(gray)
    if bbox is not None:
        x, y, ww, hh = bbox
        # Validar tamaño razonable
        if ww > w * 0.15 and hh > h * 0.15:
            short_log(f"✓ Tablero detectado por cuadrícula: {ww}x{hh}px")
            # Expandir ligeramente para capturar bordes
            pad = int(0.02 * max(ww, hh))
            x = max(0, x - pad)
            y = max(0, y - pad)
            ww = min(w - x, ww + 2 * pad)
            hh = min(h - y, hh + 2 * pad)
            return (x, y, ww, hh)
    
    # Método 2: Detección por contornos (respaldo)
    quad = _largest_square_contour(gray)
    if quad is not None:
        x, y, ww, hh = cv2.boundingRect(quad)
        if ww > w * 0.15 and hh > h * 0.15:
            short_log(f"✓ Tablero detectado por contorno: {ww}x{hh}px")
            # Expandir ligeramente
            pad = int(0.02 * max(ww, hh))
            x = max(0, x - pad)
            y = max(0, y - pad)
            ww = min(w - x, ww + 2 * pad)
            hh = min(h - y, hh + 2 * pad)
            return (x, y, ww, hh)
    
    short_log("⚠ No se detectó tablero, usando recorte central")
    return None


def crop_board(image_rgb: np.ndarray) -> np.ndarray:
    """Detecta y recorta el tablero de ajedrez de la imagen.
    
    Si no detecta el tablero, usa un recorte central inteligente.
    """
    bbox = detect_board_bbox(image_rgb)
    h, w = image_rgb.shape[:2]
    
    if bbox is None:
        # Fallback mejorado: buscar región más cuadrada en el centro
        # Asumir que el tablero está en algún lugar del centro
        side = min(w, h)
        
        # Buscar en la mitad superior/izquierda (común en chess.com)
        search_w = int(w * 0.7)
        search_h = int(h * 0.8)
        
        # Centrar búsqueda pero favorecer parte superior
        cx = search_w // 2
        cy = search_h // 2
        
        half = min(search_w, search_h) // 2
        x = max(0, cx - half)
        y = max(0, cy - half)
        side = min(half * 2, w - x, h - y)
        
        crop = image_rgb[y:y+side, x:x+side]
        short_log(f"⚠ Recorte central aplicado: {side}x{side}px desde ({x},{y})")
        return crop
    
    x, y, ww, hh = bbox
    # Forzar a cuadrado tomando el menor lado
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
    
    # Upload with upsert=True to allow overwriting
    try:
        result = supa.storage.from_(bucket).upload(
            path=key, 
            file=data,
            file_options={"content-type": "image/png", "upsert": "true"}
        )
        short_log(f"Subida exitosa: {key}")
    except Exception as e:
        short_log(f"Error en upload: {e}")
        raise

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
    """Captura pantalla, detecta tablero, recorta y sube ambas versiones a Supabase.
    
    Retorna la URL firmada del recorte del tablero.
    """
    try:
        short_log("📸 Capturando pantalla completa...")
        rgb = capture_fullscreen()
        
        # Guardar captura completa localmente
        ensure_dir(os.path.abspath(captures_dir))
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        full_path = os.path.join(os.path.abspath(captures_dir), f"full_{ts}.png")
        Image.fromarray(rgb).save(full_path)
        short_log(f"💾 Captura completa guardada: full_{ts}.png")
        
        # Detectar y recortar tablero
        short_log("🔍 Detectando tablero...")
        board = crop_board(rgb)
        
        # Guardar recorte localmente
        board_path = os.path.join(os.path.abspath(captures_dir), f"board_{ts}.png")
        Image.fromarray(board).save(board_path)
        short_log(f"✂️ Tablero recortado: {board.shape[1]}x{board.shape[0]}px")
        
        # Subir ambas versiones a Supabase
        short_log("☁️ Subiendo a Supabase Storage...")
        
        # Subir captura completa (opcional, comentar si no quieres)
        try:
            upload_image_to_supabase(full_path, prefix="full")
            short_log("✓ Captura completa subida")
        except Exception as e:
            short_log(f"⚠ Error subiendo captura completa: {e}")
        
        # Subir recorte del tablero (principal)
        url = upload_image_to_supabase(board_path, prefix="boards")
        short_log(f"✓ Tablero subido. URL firmada (24h): {url}")
        
        return url
    except Exception as e:
        short_log(f"❌ Error en captura/subida: {e}")
        import traceback
        traceback.print_exc()
        return None
