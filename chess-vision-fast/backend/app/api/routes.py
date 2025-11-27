"""
Rutas de la API para detección y análisis de ajedrez usando Gemini.
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

# Instancia global del servicio de Gemini (mantiene contexto)
_chess_service: Optional[GeminiChessService] = None


def get_chess_service(settings: AppSettings) -> GeminiChessService:
    """Obtiene o crea la instancia del servicio de ajedrez."""
    global _chess_service
    if _chess_service is None:
        if not settings.gemini_api_key:
            raise HTTPException(
                status_code=500,
                detail="GEMINI_API_KEY no configurada. Configúrala en .env"
            )
        _chess_service = GeminiChessService(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model
        )
    return _chess_service


class BestMoveRequest(BaseModel):
    fen: str


class DetectionPayload(BaseModel):
    timestamp: datetime
    fen: str
    board_image_base64: str
    squares: List[Dict[str, Any]]
    confidence: float


def _validate_file(file: UploadFile, settings: AppSettings) -> bytes:
    contents = file.file.read()
    if len(contents) > settings.max_upload_size:
        raise HTTPException(status_code=413, detail='Archivo demasiado grande')
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


def _create_detector(settings: AppSettings) -> DetectorFactory:
    return DetectorFactory(settings)


@router.post('/api/detect')
def detect(
    file: UploadFile = File(...),
    settings: AppSettings = Depends(get_settings),
) -> Dict[str, Any]:
    """Detecta la posición del tablero y retorna el FEN."""
    payload = _validate_file(file, settings)
    try:
        image = Image.open(BytesIO(payload)).convert('RGB')
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f'No se pudo leer la imagen: {exc}')

    detector = _create_detector(settings).create()
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
    """Obtiene la mejor jugada usando Gemini como GM."""
    # Validar FEN antes de enviar a Gemini
    try:
        import chess
        board = chess.Board(payload.fen)
        has_kings = (
            len(board.pieces(chess.KING, chess.WHITE)) == 1 and
            len(board.pieces(chess.KING, chess.BLACK)) == 1
        )
        if not has_kings:
            raise ValueError("Falta al menos un rey")
    except Exception as e:
        return {
            'best_move': None,
            'uci': None,
            'san': None,
            'explanation': None,
            'position_analysis': None,
            'strategic_notes': None,
            'score': {'cp': None, 'mate': None},
            'error': f'FEN inválido: {str(e)}',
        }
    
    try:
        service = get_chess_service(settings)
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
                'error': 'No se pudo obtener análisis de Gemini',
            }
        
        return {
            'best_move': result.get('move', ''),
            'uci': result.get('uci', ''),
            'san': result.get('san', ''),
            'explanation': result.get('explanation', ''),
            'position_analysis': result.get('position_analysis', ''),
            'strategic_notes': result.get('strategic_notes', ''),
            'score': result.get('score', {'cp': None, 'mate': None}),
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
    settings: AppSettings = Depends(get_settings),
) -> Dict[str, Any]:
    """Detecta la posición y obtiene la mejor jugada en una sola llamada."""
    payload = _validate_file(file, settings)
    try:
        image = Image.open(BytesIO(payload)).convert('RGB')
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f'No se pudo leer la imagen: {exc}')

    detector = _create_detector(settings).create()
    detection = detector.detect(image)
    squares = _squares_to_response(detection.squares)

    # Validar FEN
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
            validation_error = "FEN inválido: falta al menos un rey"
        else:
            fen_valid = True
    except ValueError as e:
        validation_error = f"FEN inválido: {str(e)}"
    except Exception as e:
        validation_error = f"Error validando FEN: {str(e)}"

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
            'error': validation_error or 'FEN inválido detectado',
        }

    # Obtener análisis de Gemini
    try:
        service = get_chess_service(settings)
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
            'error': f'Error en análisis: {str(e)}',
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
            'error': 'No se pudo obtener análisis de Gemini',
        }

    # Crear overlay con la mejor jugada
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
        'timestamp': datetime.utcnow().isoformat(),
    }


@router.post('/api/clear_context')
def clear_context(settings: AppSettings = Depends(get_settings)) -> Dict[str, Any]:
    """Limpia el contexto de la partida actual."""
    try:
        service = get_chess_service(settings)
        service.clear_context()
        return {
            'status': 'success',
            'message': 'Contexto de partida limpiado',
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error limpiando contexto: {str(e)}')


@router.get('/api/retrospective')
def get_retrospective(settings: AppSettings = Depends(get_settings)) -> Dict[str, Any]:
    """Obtiene una retrospectiva de la partida actual."""
    try:
        service = get_chess_service(settings)
        retrospective = service.get_retrospective()
        
        if not retrospective:
            return {
                'retrospective': 'No hay suficiente información para generar una retrospectiva.',
                'move_history': service.move_history,
            }
        
        return {
            'retrospective': retrospective,
            'move_history': service.move_history,
            'total_moves': len(service.move_history),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error obteniendo retrospectiva: {str(e)}')
