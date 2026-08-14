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

# Mapping of piece labels to FEN notation (for compatibility)
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
    board_image: Optional[Image.Image] = None
    error: Optional[str] = None


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
    """Detector factory. Uses the local CV pipeline for board detection."""

    def __init__(self, settings: AppSettings, override_backend: Optional[str] = None) -> None:
        self.settings = settings

    def create(self) -> BaseDetector:
        from .cv_detector import CVBoardDetector
        return CVBoardDetector(self.settings)


class GeminiVisionDetector(BaseDetector):
    """Detector using Google Gemini Vision. Ideal for screenshots."""
    
    def __init__(self, settings: AppSettings) -> None:
        super().__init__(settings)
        self._detector = None
        self._cached_model = None
    
    def _get_detector(self):
        # Recreate detector if model changed
        if self._detector is None or self._cached_model != self.settings.gemini_model:
            from .gemini_detector import GeminiDetector
            self._detector = GeminiDetector(
                api_key=self.settings.gemini_api_key,
                model=self.settings.gemini_model
            )
            self._cached_model = self.settings.gemini_model
        return self._detector
    
    def detect(self, image: Image.Image) -> DetectionResult:
        if not self.settings.gemini_api_key:
            logger.warning("Gemini API key not configured")
            return self._empty_result(image)
        
        try:
            detector = self._get_detector()
            fen = detector.detect_fen(image, timeout=15.0)
            
            if not fen:
                logger.warning("Gemini could not detect FEN")
                return self._empty_result(image)
            
            # Create overlay with detected board
            overlay = self._create_overlay(image, fen)
            
            return DetectionResult(
                fen=fen,
                board_image_base64=self._image_to_base64(overlay),
                squares=[],  # Gemini does not return individual bboxes
                confidence=0.9,
            )
        except Exception as e:
            logger.error(f"Error in GeminiVisionDetector: {e}")
            return self._empty_result(image)
    
    def _create_overlay(self, image: Image.Image, fen: str) -> Image.Image:
        """Creates overlay showing detected FEN."""
        overlay = image.convert('RGBA')
        draw = ImageDraw.Draw(overlay)
        
        # Draw text with FEN
        try:
            font = ImageFont.load_default()
        except Exception:
            font = None
        
        # Semi-transparent background for text
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
