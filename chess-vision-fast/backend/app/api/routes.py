"""
API routes for chess detection and analysis using Gemini.
"""
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel
from PIL import Image

from ..detector import DetectorFactory, SquareDetection
from ..overlay import draw_overlay
from ..services import GeminiChessService
from ..utils import AppSettings, get_settings

router = APIRouter()

# Global instance of Gemini service (maintains context)
_chess_service: Optional[GeminiChessService] = None
_current_model: str = 'gemini-2.0-flash'


def get_chess_service(settings: AppSettings, model: Optional[str] = None) -> GeminiChessService:
    """Gets or creates the chess service instance."""
    global _chess_service, _current_model
    
    # If a different model is requested, recreate the service
    requested_model = model or settings.gemini_model
    if _chess_service is None or _current_model != requested_model:
        if not settings.gemini_api_key:
            raise HTTPException(
                status_code=500,
                detail="GEMINI_API_KEY not configured. Configure it in .env"
            )
        _chess_service = GeminiChessService(
            api_key=settings.gemini_api_key,
            model=requested_model
        )
        _current_model = requested_model
    
    return _chess_service


class BestMoveRequest(BaseModel):
    fen: str
    model: Optional[str] = None


class DetectionPayload(BaseModel):
    timestamp: datetime
    fen: str
    board_image_base64: str
    squares: List[Dict[str, Any]]
    confidence: float


class ChangeModelRequest(BaseModel):
    model: str


def _validate_file(file: UploadFile, settings: AppSettings) -> bytes:
    contents = file.file.read()
    if len(contents) > settings.max_upload_size:
        raise HTTPException(status_code=413, detail='File too large')
    return contents


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


def _create_detector(settings: AppSettings, model: Optional[str] = None) -> DetectorFactory:
    # Create a temporary copy of settings with the selected model if provided
    if model:
        from copy import deepcopy
        temp_settings = deepcopy(settings)
        temp_settings.gemini_model = model
        return DetectorFactory(temp_settings)
    return DetectorFactory(settings)


@router.post('/api/detect')
def detect(
    file: UploadFile = File(...),
    model: Optional[str] = Query(None),
    settings: AppSettings = Depends(get_settings),
) -> Dict[str, Any]:
    """Detects board position and returns FEN."""
    payload = _validate_file(file, settings)
    try:
        image = Image.open(BytesIO(payload)).convert('RGB')
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f'Could not read image: {exc}')

    detector = _create_detector(settings, model).create()
    result = detector.detect(image)
    return {
        'fen': result.fen,
        'board_image_base64': result.board_image_base64,
        'squares': _squares_to_response(result.squares),
        'confidence': result.confidence,
        'timestamp': datetime.utcnow().isoformat(),
    }


@router.post('/api/best_move')
def best_move(
    payload: BestMoveRequest,
    settings: AppSettings = Depends(get_settings),
) -> Dict[str, Any]:
    """Gets best move using Gemini as GM."""
    # Validate FEN before sending to Gemini
    try:
        import chess
        board = chess.Board(payload.fen)
        has_kings = (
            len(board.pieces(chess.KING, chess.WHITE)) == 1 and
            len(board.pieces(chess.KING, chess.BLACK)) == 1
        )
        if not has_kings:
            raise ValueError("At least one king is missing")
    except Exception as e:
        return {
            'best_move': None,
            'uci': None,
            'san': None,
            'explanation': None,
            'position_analysis': None,
            'strategic_notes': None,
            'score': {'cp': None, 'mate': None},
            'error': f'Invalid FEN: {str(e)}',
        }
    
    try:
        service = get_chess_service(settings, payload.model)
        result = service.analyze_position(payload.fen, timeout=20.0)
        
        if not result:
            return {
                'best_move': None,
                'uci': None,
                'san': None,
                'explanation': None,
                'position_analysis': None,
                'strategic_notes': None,
                'score': {'cp': None, 'mate': None},
                'error': 'Could not get analysis from Gemini',
            }
        
        return {
            'best_move': result.get('move', ''),
            'uci': result.get('uci', ''),
            'san': result.get('san', ''),
            'explanation': result.get('explanation', ''),
            'position_analysis': result.get('position_analysis', ''),
            'strategic_notes': result.get('strategic_notes', ''),
            'score': result.get('score', {'cp': None, 'mate': None}),
            'model_used': _current_model,
        }
    except HTTPException:
        raise
    except Exception as e:
        return {
            'best_move': None,
            'uci': None,
            'san': None,
            'explanation': None,
            'position_analysis': None,
            'strategic_notes': None,
            'score': {'cp': None, 'mate': None},
            'error': f'Error en análisis: {str(e)}',
        }


@router.post('/api/detect_and_move')
def detect_and_move(
    file: UploadFile = File(...),
    model: Optional[str] = Query(None),
    settings: AppSettings = Depends(get_settings),
) -> Dict[str, Any]:
    """Detects position and gets best move in a single call."""
    payload = _validate_file(file, settings)
    try:
        image = Image.open(BytesIO(payload)).convert('RGB')
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f'Could not read image: {exc}')

    detector = _create_detector(settings, model).create()
    detection = detector.detect(image)
    squares = _squares_to_response(detection.squares)

    # Validate FEN
    fen_valid = False
    validation_error = None
    try:
        import chess
        board = chess.Board(detection.fen)
        has_kings = (
            len(board.pieces(chess.KING, chess.WHITE)) == 1 and
            len(board.pieces(chess.KING, chess.BLACK)) == 1
        )
        if not has_kings:
            validation_error = "Invalid FEN: at least one king is missing"
        else:
            fen_valid = True
    except ValueError as e:
        validation_error = f"Invalid FEN: {str(e)}"
    except Exception as e:
        validation_error = f"Error validating FEN: {str(e)}"

    if not fen_valid:
        return {
            'fen': detection.fen,
            'best_move': None,
            'uci': None,
            'san': None,
            'explanation': None,
            'position_analysis': None,
            'strategic_notes': None,
            'overlay_image_base64': detection.board_image_base64,
            'squares': squares,
            'confidence': detection.confidence,
            'error': validation_error or 'Invalid FEN detected',
        }

    # Get analysis from Gemini
    try:
        service = get_chess_service(settings, model)
        result = service.analyze_position(detection.fen, image=image, timeout=20.0)
    except Exception as e:
        return {
            'fen': detection.fen,
            'best_move': None,
            'uci': None,
            'san': None,
            'explanation': None,
            'position_analysis': None,
            'strategic_notes': None,
            'overlay_image_base64': detection.board_image_base64,
            'squares': squares,
            'confidence': detection.confidence,
            'error': f'Error in analysis: {str(e)}',
        }

    if not result:
        return {
            'fen': detection.fen,
            'best_move': None,
            'uci': None,
            'san': None,
            'explanation': None,
            'position_analysis': None,
            'strategic_notes': None,
            'overlay_image_base64': detection.board_image_base64,
            'squares': squares,
            'confidence': detection.confidence,
            'error': 'Could not get analysis from Gemini',
        }

    # Create overlay with best move
    overlay_png, coords = draw_overlay(image, squares, result.get('move', ''))

    return {
        'fen': detection.fen,
        'best_move': result.get('move', ''),
        'uci': result.get('uci', ''),
        'san': result.get('san', ''),
        'explanation': result.get('explanation', ''),
        'position_analysis': result.get('position_analysis', ''),
        'strategic_notes': result.get('strategic_notes', ''),
        'score': result.get('score', {'cp': None, 'mate': None}),
        'overlay_image_base64': overlay_png,
        'squares': squares,
        'overlay_coords': coords,
        'confidence': detection.confidence,
        'source': 'gemini',
        'model_used': _current_model,
        'timestamp': datetime.utcnow().isoformat(),
    }


@router.post('/api/clear_context')
def clear_context(settings: AppSettings = Depends(get_settings)) -> Dict[str, Any]:
    """Clears context of current game."""
    try:
        service = get_chess_service(settings)
        service.clear_context()
        return {
            'status': 'success',
            'message': 'Game context cleared',
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error clearing context: {str(e)}')


@router.get('/api/retrospective')
def get_retrospective(settings: AppSettings = Depends(get_settings)) -> Dict[str, Any]:
    """Gets a retrospective of the current game."""
    try:
        service = get_chess_service(settings)
        retrospective = service.get_retrospective()
        
        if not retrospective:
            return {
                'retrospective': 'Not enough information to generate a retrospective.',
                'move_history': service.move_history,
            }
        
        return {
            'retrospective': retrospective,
            'move_history': service.move_history,
            'total_moves': len(service.move_history),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error getting retrospective: {str(e)}')


@router.post('/api/change_model')
def change_model(
    payload: ChangeModelRequest,
    settings: AppSettings = Depends(get_settings),
) -> Dict[str, Any]:
    """Changes the Gemini model to use."""
    valid_models = ['gemini-2.0-flash', 'gemini-2.5-flash', 'gemini-2.5-pro']
    
    if payload.model not in valid_models:
        raise HTTPException(
            status_code=400,
            detail=f'Invalid model. Valid models: {", ".join(valid_models)}'
        )
    
    try:
        # Recreate service with new model
        global _chess_service, _current_model
        _chess_service = GeminiChessService(
            api_key=settings.gemini_api_key,
            model=payload.model
        )
        _current_model = payload.model
        
        return {
            'status': 'success',
            'message': f'Model changed to {payload.model}',
            'model': payload.model,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error changing model: {str(e)}')


@router.get('/api/current_model')
def get_current_model() -> Dict[str, Any]:
    """Gets the currently active model."""
    return {
        'model': _current_model,
        'available_models': ['gemini-2.0-flash', 'gemini-2.5-flash', 'gemini-2.5-pro'],
    }
