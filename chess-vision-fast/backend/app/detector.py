import base64
import io
import logging
from dataclasses import dataclass
from typing import List, Optional, Tuple

import chess
from PIL import Image, ImageDraw, ImageFont

from .fen import fen_from_squares
from .utils import AppSettings

logger = logging.getLogger(__name__)

PieceMap = {
    'white_pawn': 'P',
    'white_rook': 'R',
    'white_knight': 'N',
    'white_bishop': 'B',
    'white_queen': 'Q',
    'white_king': 'K',
    'black_pawn': 'p',
    'black_rook': 'r',
    'black_knight': 'n',
    'black_bishop': 'b',
    'black_queen': 'q',
    'black_king': 'k',
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


class DemoDetector(BaseDetector):
    def detect(self, image: Image.Image) -> DetectionResult:
        squares = []
        board_image = image.convert('RGBA')
        draw = ImageDraw.Draw(board_image)
        font = ImageFont.load_default()
        square_size = board_image.width / 8

        fen = chess.STARTING_FEN
        board = chess.Board(fen)
        for square in chess.SQUARES:
            row = 7 - (square // 8)
            col = square % 8
            piece = board.piece_at(square)
            piece_letter = piece.symbol() if piece else ''
            bbox = (
                col * square_size,
                row * square_size,
                square_size,
                square_size,
            )
            if piece_letter:
                draw.text((bbox[0] + 2, bbox[1] + 2), piece_letter, fill='red', font=font)
            squares.append(SquareDetection(square=chess.square_name(square), bbox=bbox, piece=piece_letter, confidence=0.5))

        return DetectionResult(
            fen=fen,
            board_image_base64=self._image_to_base64(board_image),
            squares=squares,
            confidence=0.5,
        )


class LichessDetector(BaseDetector):
    def detect(self, image: Image.Image) -> DetectionResult:
        try:
            from chessboard_image_detector import detect_chessboard

            detections = detect_chessboard(image)
        except ImportError as exc:
            logger.warning('Lichess detector unavailable (%s), regresando demo', exc)
            return DemoDetector(self.settings).detect(image)

        squares = []
        for square_info in detections.get('squares', []):
            squares.append(
                SquareDetection(
                    square=square_info['square'],
                    bbox=tuple(square_info['bbox']),
                    piece=PieceMap.get(square_info.get('piece'), ''),
                    confidence=square_info.get('confidence', 0.8),
                )
            )
        fen = detections.get('fen', chess.STARTING_FEN)
        overlay = Image.new('RGBA', image.size)
        draw = ImageDraw.Draw(overlay)
        for square in squares:
            draw.rectangle(square.bbox, outline='red', width=2)
        combined = Image.alpha_composite(image.convert('RGBA'), overlay)
        return DetectionResult(
            fen=fen,
            board_image_base64=self._image_to_base64(combined),
            squares=squares,
            confidence=min([s.confidence for s in squares], default=0.4),
        )


class YoloDetector(BaseDetector):
    def __init__(self, settings: AppSettings) -> None:
        super().__init__(settings)
        try:
            from ultralytics import YOLO
            self.model = YOLO(self.settings.yolo_model_path)
        except Exception as exc:
            logger.warning('YOLO detector no disponible: %s', exc)
            self.model = None

    def detect(self, image: Image.Image) -> DetectionResult:
        if not self.model:
            return DemoDetector(self.settings).detect(image)

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
    def __init__(self, settings: AppSettings, override_backend: Optional[str] = None) -> None:
        self.settings = settings
        self.override_backend = override_backend

    def create(self) -> BaseDetector:
        backend = (self.override_backend or self.settings.detection_backend).lower()
        if backend == 'yolo':
            return YoloDetector(self.settings)
        return LichessDetector(self.settings)
