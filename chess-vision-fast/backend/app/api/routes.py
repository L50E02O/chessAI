from datetime import datetime
from io import BytesIO
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel
from PIL import Image

from ..detector import DetectorFactory, SquareDetection
from ..overlay import draw_overlay
from ..stockfish_engine import StockfishEngine
from ..utils import AppSettings, get_settings

router = APIRouter()


class BestMoveOptions(BaseModel):
    depth: Optional[int]
    time_ms: Optional[int]


class BestMoveRequest(BaseModel):
    fen: str
    options: Optional[BestMoveOptions]


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


def _create_detector(settings: AppSettings, backend: Optional[str] = None) -> DetectorFactory:
    return DetectorFactory(settings, backend)


def _create_stockfish(settings: AppSettings) -> StockfishEngine:
    engine = StockfishEngine(settings.stockfish_path)
    engine.start()
    return engine


@router.post('/api/detect')
def detect(
    file: UploadFile = File(...),
    backend: Optional[str] = Query(None),
    settings: AppSettings = Depends(get_settings),
) -> Dict[str, Any]:
    payload = _validate_file(file, settings)
    try:
        image = Image.open(BytesIO(payload)).convert('RGB')
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f'No se pudo leer la imagen: {exc}')

    detector = _create_detector(settings, backend).create()
    result = detector.detect(image)
    return {
        'fen': result.fen,
        'board_image_base64': result.board_image_base64,
        'squares': _squares_to_response(result.squares),
        'confidence': result.confidence,
        'timestamp': datetime.utcnow().isoformat(),
    }


@router.post('/api/best_move')
def best_move(payload: BestMoveRequest, settings: AppSettings = Depends(get_settings)) -> Dict[str, Any]:
    # Validar FEN antes de enviar a Stockfish
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
            'score': {'cp': None, 'mate': None},
            'error': f'FEN invalido: {str(e)}',
        }
    
    try:
        engine = _create_stockfish(settings)
        engine.set_fen(payload.fen)
        options = payload.options or BestMoveOptions()
        move = engine.get_best_move(depth=options.depth, time_ms=options.time_ms)
        return {
            'best_move': move.best_move,
            'uci': move.uci,
            'san': move.san,
            'score': move.score,
        }
    except Exception as e:
        return {
            'best_move': None,
            'uci': None,
            'san': None,
            'score': {'cp': None, 'mate': None},
            'error': f'Error Stockfish: {str(e)}',
        }
    finally:
        try:
            engine.close()
        except Exception:
            pass


@router.post('/api/detect_and_move')
def detect_and_move(
    file: UploadFile = File(...),
    backend: Optional[str] = Query(None),
    settings: AppSettings = Depends(get_settings),
) -> Dict[str, Any]:
    payload = _validate_file(file, settings)
    try:
        image = Image.open(BytesIO(payload)).convert('RGB')
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f'No se pudo leer la imagen: {exc}')

    detector = _create_detector(settings, backend).create()
    detection = detector.detect(image)
    squares = _squares_to_response(detection.squares)

    # Validar FEN antes de enviar a Stockfish (solo sintaxis, no legalidad)
    try:
        import chess
        board = chess.Board(detection.fen)
        # Solo verificar que tenga ambos reyes (minimo necesario para Stockfish)
        has_kings = (
            len(board.pieces(chess.KING, chess.WHITE)) == 1 and
            len(board.pieces(chess.KING, chess.BLACK)) == 1
        )
        if not has_kings:
            raise ValueError("Falta al menos un rey")
    except Exception as e:
        # FEN invalido, devolver sin mejor jugada
        return {
            'fen': detection.fen,
            'best_move': None,
            'uci': None,
            'san': None,
            'score': {'cp': None, 'mate': None},
            'overlay_image_base64': detection.board_image_base64,
            'squares': squares,
            'confidence': detection.confidence,
            'error': f'FEN detectado no es valido para analisis: {str(e)}',
        }

    engine = _create_stockfish(settings)
    engine.set_fen(detection.fen)
    
    try:
        move = engine.get_best_move()
    except Exception as e:
        return {
            'fen': detection.fen,
            'best_move': None,
            'uci': None,
            'san': None,
            'score': {'cp': None, 'mate': None},
            'overlay_image_base64': detection.board_image_base64,
            'squares': squares,
            'confidence': detection.confidence,
            'error': f'Error calculando jugada: {str(e)}',
        }
    finally:
        engine.close()

    overlay_png, coords = draw_overlay(image, squares, move.best_move)

    return {
        'fen': detection.fen,
        'best_move': move.best_move,
        'uci': move.uci,
        'san': move.san,
        'score': move.score,
        'overlay_image_base64': overlay_png,
        'squares': squares,
        'overlay_coords': coords,
        'confidence': detection.confidence,
        'timestamp': datetime.utcnow().isoformat(),
    }
