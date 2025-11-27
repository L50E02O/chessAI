"""
WebSocket para streaming de análisis de ajedrez en tiempo real usando Gemini.
"""
import asyncio
import base64
from io import BytesIO
from typing import Dict, Optional

from fastapi import WebSocket
from fastapi.websockets import WebSocketDisconnect
from PIL import Image

from ..detector import DetectorFactory
from ..overlay import draw_overlay
from ..services import GeminiChessService
from ..utils import AppSettings, get_settings


# Instancia global del servicio (compartida con las rutas HTTP)
_chess_service: Optional[GeminiChessService] = None


def _get_chess_service(settings: AppSettings) -> GeminiChessService:
    """Obtiene o crea la instancia del servicio de ajedrez."""
    global _chess_service
    if _chess_service is None:
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY no configurada")
        _chess_service = GeminiChessService(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model
        )
    return _chess_service


async def websocket_stream(websocket: WebSocket, settings: AppSettings = get_settings()):
    """Maneja el stream de WebSocket para análisis en tiempo real."""
    await websocket.accept()
    
    last_move = None
    last_sent = 0.0
    detector_instance = None
    
    try:
        service = _get_chess_service(settings)
    except Exception as e:
        await websocket.send_json({
            'error': f'Error inicializando servicio: {str(e)}'
        })
        await websocket.close()
        return

    # Inicializar detector una sola vez
    detector_instance = DetectorFactory(settings).create()

    try:
        while True:
            if settings.frame_throttle_ms:
                await asyncio.sleep(settings.frame_throttle_ms / 1000)
            
            message = await websocket.receive_json()
            frame_b64 = message.get('frame')
            
            if not frame_b64:
                continue
            
            if not frame_b64.startswith('data:image'):
                frame_b64 = 'data:image/png;base64,' + frame_b64
            
            header, encoded = frame_b64.split('base64,')
            data = base64.b64decode(encoded)
            image = Image.open(BytesIO(data)).convert('RGB')
            
            # Detectar posición
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
            
            # Analizar posición con Gemini (en thread para no bloquear)
            # Usar run_in_executor para llamadas síncronas
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: service.analyze_position(detection.fen, image=image, timeout=15.0)
            )
            
            if not result:
                continue
            
            move_uci = result.get('move', '')
            if move_uci == last_move:
                continue
            
            # Crear overlay
            overlay_png, coords = draw_overlay(image, detection.squares, move_uci)
            
            payload: Dict[str, object] = {
                'fen': detection.fen,
                'best_move': move_uci,
                'uci': result.get('uci', ''),
                'san': result.get('san', ''),
                'explanation': result.get('explanation', ''),
                'position_analysis': result.get('position_analysis', ''),
                'strategic_notes': result.get('strategic_notes', ''),
                'score': result.get('score', {'cp': None, 'mate': None}),
                'squares': squares,
                'overlay_coords': coords,
                'confidence': detection.confidence,
                'source': 'gemini',
            }
            
            await websocket.send_json(payload)
            last_move = move_uci

    except WebSocketDisconnect:
        await websocket.close()
    except Exception as e:
        await websocket.send_json({
            'error': f'Error en stream: {str(e)}'
        })
        await websocket.close()
