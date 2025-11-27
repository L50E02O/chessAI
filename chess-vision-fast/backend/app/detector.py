import base64
import io
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import chess
from PIL import Image, ImageDraw, ImageFont

from .fen import fen_from_squares
from .utils import AppSettings

logger = logging.getLogger(__name__)

# Mapeo de etiquetas Roboflow/YOLO a notacion FEN
PieceMap = {
    'white-pawn': 'P', 'white_pawn': 'P', 'wp': 'P',
    'white-rook': 'R', 'white_rook': 'R', 'wr': 'R',
    'white-knight': 'N', 'white_knight': 'N', 'wn': 'N', 'wkn': 'N',
    'white-bishop': 'B', 'white_bishop': 'B', 'wb': 'B',
    'white-queen': 'Q', 'white_queen': 'Q', 'wq': 'Q',
    'white-king': 'K', 'white_king': 'K', 'wk': 'K',
    'black-pawn': 'p', 'black_pawn': 'p', 'bp': 'p',
    'black-rook': 'r', 'black_rook': 'r', 'br': 'r',
    'black-knight': 'n', 'black_knight': 'n', 'bn': 'n', 'bkn': 'n',
    'black-bishop': 'b', 'black_bishop': 'b', 'bb': 'b',
    'black-queen': 'q', 'black_queen': 'q', 'bq': 'q',
    'black-king': 'k', 'black_king': 'k', 'bk': 'k',
}

@dataclass
class SquareDetection:
    square: str
    bbox: Tuple[float, float, float, float]
    piece: Optional[str]
    confidence: float = 1.0


@dataclass
class DetectionResult:
    fen: str
    board_image_base64: str
    squares: List[SquareDetection]
    confidence: float


class BaseDetector:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings

    def detect(self, image: Image.Image) -> DetectionResult:
        raise NotImplementedError

    def _image_to_base64(self, image: Image.Image) -> str:
        buffered = io.BytesIO()
        image.save(buffered, format='PNG')
        return base64.b64encode(buffered.getvalue()).decode('ascii')

    def _normalize_bbox(self, square: Tuple[int, int], size: Tuple[int, int]) -> Tuple[float, float, float, float]:
        row, col = square
        width, height = size
        x = col * (width / 8)
        y = row * (height / 8)
        return (x, y, width / 8, height / 8)


class RoboflowDetector(BaseDetector):
    """Detector usando Roboflow Inference API con modelo pre-entrenado de ajedrez."""
    
    def __init__(self, settings: AppSettings) -> None:
        super().__init__(settings)
        self.api_key = settings.roboflow_api_key
        self.model_id = settings.roboflow_model_id
        self._client = None
    
    def _get_client(self):
        if self._client is None:
            try:
                from inference_sdk import InferenceHTTPClient
                self._client = InferenceHTTPClient(
                    api_url="https://detect.roboflow.com",
                    api_key=self.api_key
                )
            except ImportError:
                logger.warning("inference_sdk no instalado, usando fallback")
                return None
        return self._client
    
    def detect(self, image: Image.Image) -> DetectionResult:
        client = self._get_client()
        if not client or not self.api_key:
            logger.warning("Roboflow no configurado")
            return self._empty_result(image)
        
        try:
            # Convertir imagen a bytes
            buffered = io.BytesIO()
            image.save(buffered, format='JPEG')
            img_bytes = buffered.getvalue()
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            
            # Llamar API de Roboflow
            result = client.infer(img_base64, model_id=self.model_id)
            
            squares = []
            overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            
            for pred in result.get('predictions', []):
                label = pred.get('class', '').lower().replace(' ', '-')
                score = pred.get('confidence', 0)
                if score < self.settings.yolo_confidence:
                    continue
                
                piece_letter = PieceMap.get(label, '')
                if not piece_letter:
                    logger.debug(f"Etiqueta no reconocida: {label}")
                    continue
                
                # Roboflow devuelve x, y (centro), width, height
                cx = pred.get('x', 0)
                cy = pred.get('y', 0)
                w = pred.get('width', 0)
                h = pred.get('height', 0)
                x1, y1, x2, y2 = cx - w/2, cy - h/2, cx + w/2, cy + h/2
                
                draw.rectangle([x1, y1, x2, y2], outline='lime', width=2)
                draw.text((x1, y1 - 12), piece_letter, fill='lime')
                
                square_name = self._guess_square_from_bbox((x1, y1, x2, y2), image.size)
                squares.append(SquareDetection(
                    square=square_name,
                    bbox=(x1, y1, w, h),
                    piece=piece_letter,
                    confidence=score
                ))
            
            fen = fen_from_squares(squares)
            combined = Image.alpha_composite(image.convert('RGBA'), overlay)
            
            return DetectionResult(
                fen=fen,
                board_image_base64=self._image_to_base64(combined),
                squares=squares,
                confidence=min([s.confidence for s in squares], default=0.3),
            )
        except Exception as exc:
            logger.error(f"Error en Roboflow API: {exc}")
            return self._empty_result(image)
    
    def _empty_result(self, image: Image.Image) -> DetectionResult:
        """Devuelve resultado vacio cuando no se puede detectar."""
        return DetectionResult(
            fen=chess.STARTING_FEN,
            board_image_base64=self._image_to_base64(image),
            squares=[],
            confidence=0.0,
        )
    
    def _guess_square_from_bbox(self, bbox: Tuple[float, float, float, float], size: Tuple[int, int]) -> str:
        x1, y1, x2, y2 = bbox
        width, height = size
        col = int((x1 + x2) / 2 * 8 / width)
        row = 7 - int((y1 + y2) / 2 * 8 / height)
        col = max(0, min(7, col))
        row = max(0, min(7, row))
        return chess.square_name(row * 8 + col)


class YoloDetector(BaseDetector):
    """Detector usando modelo YOLO local."""
    
    def __init__(self, settings: AppSettings) -> None:
        super().__init__(settings)
        self.model = None
        model_path = Path(settings.yolo_model_path)
        if model_path.exists():
            try:
                from ultralytics import YOLO
                self.model = YOLO(str(model_path))
                logger.info(f"Modelo YOLO cargado desde {model_path}")
            except Exception as exc:
                logger.warning(f'Error cargando modelo YOLO: {exc}')
        else:
            logger.warning(f'Modelo YOLO no encontrado en {model_path}')

    def detect(self, image: Image.Image) -> DetectionResult:
        if not self.model:
            # Sin modelo, devolver resultado vacio
            return DetectionResult(
                fen=chess.STARTING_FEN,
                board_image_base64=self._image_to_base64(image),
                squares=[],
                confidence=0.0,
            )

        results = self.model(image)
        squares = []
        overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        for pred in results:
            boxes = pred.boxes
            names = pred.names
            for box in boxes:
                cls = int(box.cls[0])
                score = float(box.conf[0])
                if score < self.settings.yolo_confidence:
                    continue
                label = names.get(cls, '').lower()
                piece_letter = PieceMap.get(label, '')
                if not piece_letter:
                    continue
                x1, y1, x2, y2 = map(float, box.xyxy[0])
                draw.rectangle([x1, y1, x2, y2], outline='lime', width=2)
                draw.text((x1, y1), piece_letter, fill='white')
                square_name = self._guess_square_from_bbox((x1, y1, x2, y2), image.size)
                squares.append(SquareDetection(square=square_name, bbox=(x1, y1, x2 - x1, y2 - y1), piece=piece_letter, confidence=score))

        fen = fen_from_squares(squares)
        combined = Image.alpha_composite(image.convert('RGBA'), overlay)
        return DetectionResult(
            fen=fen,
            board_image_base64=self._image_to_base64(combined),
            squares=squares,
            confidence=min([s.confidence for s in squares], default=0.3),
        )

    def _guess_square_from_bbox(self, bbox: Tuple[float, float, float, float], size: Tuple[int, int]) -> str:
        x1, y1, x2, y2 = bbox
        width, height = size
        col = int((x1 + x2) / 2 * 8 / width)
        row = 7 - int((y1 + y2) / 2 * 8 / height)
        col = max(0, min(7, col))
        row = max(0, min(7, row))
        return chess.square_name(row * 8 + col)


def fen_from_detections(squares: List[SquareDetection]) -> str:
    board = [['' for _ in range(8)] for _ in range(8)]
    for det in squares:
        try:
            square_index = chess.SQUARE_NAMES.index(det.square)
            row = square_index // 8
            col = square_index % 8
            board[7 - row][col] = det.piece or ''
        except ValueError:
            continue
    fen_rows = []
    for row in board:
        count = 0
        row_fen = ''
        for cell in row:
            if not cell:
                count += 1
                continue
            if count:
                row_fen += str(count)
                count = 0
            row_fen += cell
        if count:
            row_fen += str(count)
        fen_rows.append(row_fen or '8')
    return '/'.join(fen_rows) + ' w KQkq - 0 1'


class DetectorFactory:
    """Fabrica de detectores. Usa Gemini por defecto (mejor para capturas de pantalla)."""
    
    def __init__(self, settings: AppSettings, override_backend: Optional[str] = None) -> None:
        self.settings = settings
        self.override_backend = override_backend

    def create(self) -> BaseDetector:
        backend = (self.override_backend or self.settings.detection_backend).lower()
        if backend == 'yolo':
            return YoloDetector(self.settings)
        if backend == 'roboflow':
            return RoboflowDetector(self.settings)
        # Por defecto usar Gemini (mejor para capturas de pantalla)
        return GeminiVisionDetector(self.settings)


class GeminiVisionDetector(BaseDetector):
    """Detector usando Google Gemini Vision. Ideal para capturas de pantalla."""
    
    def __init__(self, settings: AppSettings) -> None:
        super().__init__(settings)
        self._detector = None
    
    def _get_detector(self):
        if self._detector is None:
            from .gemini_detector import GeminiDetector
            self._detector = GeminiDetector(
                api_key=self.settings.gemini_api_key,
                model=self.settings.gemini_model
            )
        return self._detector
    
    def detect(self, image: Image.Image) -> DetectionResult:
        if not self.settings.gemini_api_key:
            logger.warning("Gemini API key no configurada")
            return self._empty_result(image)
        
        try:
            detector = self._get_detector()
            fen = detector.detect_fen(image, timeout=15.0)
            
            if not fen:
                logger.warning("Gemini no pudo detectar FEN")
                return self._empty_result(image)
            
            # Crear overlay con el tablero detectado
            overlay = self._create_overlay(image, fen)
            
            return DetectionResult(
                fen=fen,
                board_image_base64=self._image_to_base64(overlay),
                squares=[],  # Gemini no devuelve bboxes individuales
                confidence=0.9,
            )
        except Exception as e:
            logger.error(f"Error en GeminiVisionDetector: {e}")
            return self._empty_result(image)
    
    def _create_overlay(self, image: Image.Image, fen: str) -> Image.Image:
        """Crea overlay mostrando el FEN detectado."""
        overlay = image.convert('RGBA')
        draw = ImageDraw.Draw(overlay)
        
        # Dibujar texto con el FEN
        try:
            font = ImageFont.load_default()
        except Exception:
            font = None
        
        # Fondo semi-transparente para el texto
        text = f"FEN: {fen.split()[0][:30]}..."
        draw.rectangle([0, 0, overlay.width, 25], fill=(0, 0, 0, 180))
        draw.text((5, 5), text, fill='lime', font=font)
        
        return overlay
    
    def _empty_result(self, image: Image.Image) -> DetectionResult:
        return DetectionResult(
            fen=chess.STARTING_FEN,
            board_image_base64=self._image_to_base64(image),
            squares=[],
            confidence=0.0,
        )
