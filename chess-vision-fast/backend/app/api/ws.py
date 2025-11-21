import asyncio
import base64
from io import BytesIO
from typing import Dict, List, Optional

from fastapi import WebSocket
from fastapi.websockets import WebSocketDisconnect
from PIL import Image

from ..detector import DetectorFactory
from ..overlay import draw_overlay
from ..stockfish_engine import StockfishEngine
from ..utils import AppSettings, get_settings


async def websocket_stream(websocket: WebSocket, settings: AppSettings = get_settings()):
    await websocket.accept()
    engine = StockfishEngine(settings.stockfish_path)
    engine.start()
    last_move = None
    last_sent = 0.0
    current_backend: Optional[str] = None
    detector_instance = None

    def _ensure_detector(backend_choice: Optional[str]):
        nonlocal detector_instance, current_backend
        normalized = backend_choice.lower() if backend_choice else None
        if normalized != current_backend or detector_instance is None:
            current_backend = normalized
            detector_instance = DetectorFactory(settings, normalized).create()
        return detector_instance

    try:
        while True:
            if settings.frame_throttle_ms:
                await asyncio.sleep(settings.frame_throttle_ms / 1000)
            message = await websocket.receive_json()
            frame_b64 = message.get('frame')
            backend_hint = message.get('backend')
            detector_instance = _ensure_detector(backend_hint)
            if not frame_b64:
                continue
            if not frame_b64.startswith('data:image'):
                frame_b64 = 'data:image/png;base64,' + frame_b64
            header, encoded = frame_b64.split('base64,')
            data = base64.b64decode(encoded)
            image = Image.open(BytesIO(data)).convert('RGB')
            detection = detector_instance.detect(image)
            squares = [
                {
                    'square': square.square,
                    'bbox': [square.bbox[0], square.bbox[1], square.bbox[2], square.bbox[3]],
                    'piece': square.piece,
                    'confidence': square.confidence,
                }
                for square in detection.squares
            ]
            engine.set_fen(detection.fen)
            move = engine.get_best_move()
            if move.uci == last_move:
                continue
            overlay_png, coords = draw_overlay(image, squares, move.best_move)
            payload: Dict[str, object] = {
                'fen': detection.fen,
                'best_move': move.best_move,
                'uci': move.uci,
                'san': move.san,
                'score': move.score,
                'squares': squares,
                'overlay_coords': coords,
                'confidence': detection.confidence,
            }
            await websocket.send_json(payload)
            last_move = move.uci

    except WebSocketDisconnect:
        await websocket.close()
    finally:
        engine.close()
