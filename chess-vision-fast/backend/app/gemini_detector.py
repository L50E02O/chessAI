"""
Detector de tableros de ajedrez usando Google Gemini Vision.
Optimizado para evitar cuelgues y manejar errores graciosamente.
"""
import base64
import io
import logging
import re
from typing import Optional

import chess
from PIL import Image

logger = logging.getLogger(__name__)

# Prompt optimizado para Gemini
GEMINI_PROMPT = """Analyze this chess board image and return ONLY the FEN notation.

Rules:
1. Return ONLY the FEN string, nothing else
2. Use standard piece notation: K=King, Q=Queen, R=Rook, B=Bishop, N=Knight, P=Pawn
3. Uppercase = White pieces, lowercase = Black pieces
4. Numbers represent empty squares
5. Rows are separated by /
6. Start from rank 8 (top) to rank 1 (bottom)
7. Include the full FEN with turn, castling, en passant, halfmove, fullmove
8. If you cannot determine turn/castling, use: w KQkq - 0 1

Example output: rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1

Return ONLY the FEN string:"""


class GeminiDetector:
    """Detector usando Google Gemini Vision API."""
    
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model_name = model
        self._model = None
        self._generation_config = {
            "temperature": 0.1,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 256,
        }
    
    def _get_model(self):
        """Inicializa el modelo de forma lazy."""
        if self._model is None:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self._model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=self._generation_config,
            )
        return self._model
    
    def detect_fen(self, image: Image.Image, timeout: float = 15.0) -> Optional[str]:
        """
        Detecta el FEN de una imagen de tablero.
        
        Args:
            image: Imagen PIL del tablero
            timeout: Timeout en segundos (default 15s)
            
        Returns:
            FEN string o None si falla
        """
        try:
            model = self._get_model()
            
            # Redimensionar imagen si es muy grande (evita cuelgues)
            max_size = 1024
            if max(image.size) > max_size:
                ratio = max_size / max(image.size)
                new_size = (int(image.width * ratio), int(image.height * ratio))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            # Convertir a RGB si es necesario
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Generar respuesta
            response = model.generate_content(
                [GEMINI_PROMPT, image],
                request_options={"timeout": timeout}
            )
            
            if not response.text:
                logger.warning("Gemini no devolvio texto")
                return None
            
            # Extraer y validar FEN
            fen = self._extract_fen(response.text)
            if fen and self._validate_fen(fen):
                return fen
            
            logger.warning(f"FEN invalido: {response.text[:100]}")
            return None
            
        except Exception as e:
            logger.error(f"Error en Gemini: {e}")
            return None
    
    def _extract_fen(self, text: str) -> Optional[str]:
        """Extrae el FEN del texto de respuesta."""
        text = text.strip()
        
        # Si es solo el FEN
        if self._looks_like_fen(text):
            return text
        
        # Buscar patron FEN en el texto
        fen_pattern = r'([rnbqkpRNBQKP1-8]+/){7}[rnbqkpRNBQKP1-8]+(\s+[wb]\s+[KQkq-]+\s+[a-h1-8-]+\s+\d+\s+\d+)?'
        match = re.search(fen_pattern, text)
        if match:
            fen = match.group(0)
            # Agregar partes faltantes si es necesario
            parts = fen.split()
            if len(parts) == 1:
                fen += " w KQkq - 0 1"
            return fen
        
        return None
    
    def _looks_like_fen(self, text: str) -> bool:
        """Verifica si el texto parece un FEN."""
        parts = text.split('/')
        return len(parts) == 8 and all(
            re.match(r'^[rnbqkpRNBQKP1-8]+$', p.split()[0] if ' ' in p else p)
            for p in parts
        )
    
    def _validate_fen(self, fen: str) -> bool:
        """Valida que el FEN sea correcto usando python-chess."""
        try:
            board = chess.Board(fen)
            return board.is_valid()
        except Exception:
            # Intentar solo la parte del tablero
            try:
                parts = fen.split()
                board = chess.Board(parts[0] + " w KQkq - 0 1")
                return True
            except Exception:
                return False


def image_to_base64(image: Image.Image, format: str = 'PNG') -> str:
    """Convierte imagen PIL a base64."""
    buffered = io.BytesIO()
    image.save(buffered, format=format)
    return base64.b64encode(buffered.getvalue()).decode('utf-8')
