"""
API routes for chess detection and analysis using local CV + Stockfish.
"""
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, List, Optional

import chess
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from PIL import Image
from pydantic import BaseModel

from ..detector import DetectorFactory, SquareDetection
from ..overlay import draw_overlay
from ..services import StockfishService
from ..stockfish_engine import StockfishEngine
from ..utils import AppSettings, get_settings

router = APIRouter()

_chess_service: Optional[StockfishService] = None


def get_chess_service(settings: AppSettings) -> StockfishService:
    global _chess_service
    if _chess_service is None:
        engine = StockfishEngine(
            path=settings.stockfish_path,
            depth=settings.stockfish_depth,
            auto_download=settings.stockfish_auto_download,
        )
        _chess_service = StockfishService(engine)
    return _chess_service


class BestMoveRequest(BaseModel):
    fen: str
    turn: Optional[str] = None
    depth: Optional[int] = None


def _validate_file(file: UploadFile, settings: AppSettings) -> bytes:
    contents = file.file.read()
    if len(contents) > settings.max_upload_size:
        raise HTTPException(status_code=413, detail='File too large')
    return contents


def _open_image(payload: bytes) -> Image.Image:
    try:
        return Image.open(BytesIO(payload)).convert('RGB')
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f'Could not read image: {exc}')


def _squares_to_response(squares: List[SquareDetection]) -> List[Dict[str, Any]]:
    return [
        {
            'square': square.square,
            'bbox': [square.bbox[0], square.bbox[1], square.bbox[2], square.bbox[3]],
            'piece': square.piece,
            'confidence': square.confidence,
        }
        for square in squares
    ]


@router.post('/api/detect')
def detect(
    file: UploadFile = File(...),
    orientation: Optional[str] = Query(None),
    settings: AppSettings = Depends(get_settings),
) -> Dict[str, Any]:
    detector = DetectorFactory(settings).create()
    result = detector.detect(_open_image(_validate_file(file, settings)))
    if result.confidence < settings.detection_confidence_threshold:
        return {
            'fen': '',
            'board_image_base64': result.board_image_base64,
            'squares': [],
            'confidence': result.confidence,
            'orientation': result.orientation if hasattr(result, 'orientation') else 'w-bottom',
            'error': f'Low detection confidence ({result.confidence:.2f}); could not reliably detect the board.',
        }
    return {
        'fen': result.fen,
        'board_image_base64': result.board_image_base64,
        'squares': _squares_to_response(result.squares),
        'confidence': result.confidence,
        'orientation': result.orientation if hasattr(result, 'orientation') else 'w-bottom',
        'error': result.error,
    }


@router.post('/api/best_move')
def best_move(
    payload: BestMoveRequest,
    settings: AppSettings = Depends(get_settings),
) -> Dict[str, Any]:
    try:
        service = get_chess_service(settings)
        result = service.analyze_position(payload.fen, turn=payload.turn, depth=payload.depth)
        return {
            'uci': result['uci'],
            'san': result['san'],
            'score': result['score'],
            'pv': result['pv'],
            'evaluation_text': result['evaluation_text'],
            'turn': result['turn'],
            'depth': result['depth'],
            'source': result['source'],
        }
    except Exception as e:
        return {
            'uci': None, 'san': None,
            'score': {'cp': None, 'mate': None},
            'pv': [], 'evaluation_text': None,
            'turn': None, 'depth': None, 'source': 'stockfish',
            'error': f'Error in analysis: {str(e)}',
        }


@router.post('/api/detect_and_move')
def detect_and_move(
    file: UploadFile = File(...),
    orientation: Optional[str] = Query(None),
    turn: Optional[str] = Query(None),
    depth: Optional[int] = Query(None),
    settings: AppSettings = Depends(get_settings),
) -> Dict[str, Any]:
    detector = DetectorFactory(settings).create()
    detection = detector.detect(_open_image(_validate_file(file, settings)))
    squares = _squares_to_response(detection.squares)
    overlay_image_base64 = detection.board_image_base64
    overlay_coords: List[float] = []

    if not detection.fen or detection.confidence < settings.detection_confidence_threshold:
        return {
            'fen': '', 'best_move': None, 'uci': None, 'san': None,
            'score': {'cp': None, 'mate': None}, 'pv': [],
            'evaluation_text': None, 'overlay_image_base64': overlay_image_base64,
            'squares': squares, 'confidence': detection.confidence,
            'error': detection.error or (
                f'Low detection confidence ({detection.confidence:.2f}); could not reliably detect the board.'
            ),
        }

    try:
        service = get_chess_service(settings)
        result = service.analyze_position(detection.fen, turn=turn, depth=depth)
        if detection.board_image is not None:
            overlay_png, overlay_coords = draw_overlay(detection.board_image, squares, result['uci'])
            overlay_image_base64 = overlay_png
        return {
            'fen': detection.fen,
            'best_move': result['uci'],
            'uci': result['uci'],
            'san': result['san'],
            'score': result['score'],
            'pv': result['pv'],
            'evaluation_text': result['evaluation_text'],
            'overlay_image_base64': overlay_image_base64,
            'overlay_coords': overlay_coords,
            'squares': squares,
            'confidence': detection.confidence,
            'orientation': detection.orientation if hasattr(detection, 'orientation') else 'w-bottom',
            'source': 'stockfish',
            'timestamp': datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {
            'fen': detection.fen, 'best_move': None, 'uci': None, 'san': None,
            'score': {'cp': None, 'mate': None}, 'pv': [],
            'evaluation_text': None, 'overlay_image_base64': overlay_image_base64,
            'squares': squares, 'confidence': detection.confidence,
            'error': f'Error in analysis: {str(e)}',
        }


@router.post('/api/clear_context')
def clear_context(settings: AppSettings = Depends(get_settings)) -> Dict[str, Any]:
    try:
        get_chess_service(settings).clear_context()
        return {'status': 'success', 'message': 'Game context cleared'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error clearing context: {str(e)}')


@router.get('/api/context')
def get_context(settings: AppSettings = Depends(get_settings)) -> Dict[str, Any]:
    try:
        return get_chess_service(settings).get_context()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error getting context: {str(e)}')
