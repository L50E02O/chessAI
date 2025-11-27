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
GEMINI_PROMPT = """Analyze this chess board image carefully and return ONLY the FEN notation.

IMPORTANT: Pay special attention to ALL 8 rows, especially the top row (rank 8) and bottom row (rank 1).
Make sure you identify BOTH kings (K for white, k for black) - every valid chess position must have both kings.

Rules:
1. Return ONLY the FEN string, nothing else
2. Use standard piece notation: K=King, Q=Queen, R=Rook, B=Bishop, N=Knight, P=Pawn
3. Uppercase = White pieces (usually lighter color), lowercase = Black pieces (usually darker color)
4. Numbers represent consecutive empty squares
5. Rows are separated by /
6. Start from rank 8 (top of board, black's back rank) to rank 1 (bottom, white's back rank)
7. Include the full FEN with turn, castling, en passant, halfmove, fullmove
8. If you cannot determine turn/castling, use: w KQkq - 0 1

CRITICAL: Count all 8 rows carefully. The top row should have black's major pieces (r,n,b,q,k,b,n,r in starting position).

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
            
            # Agregar padding para evitar recorte de bordes
            padding = 10
            padded = Image.new('RGB', (image.width + padding*2, image.height + padding*2), (50, 50, 50))
            padded.paste(image, (padding, padding))
            image = padded
            
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
            
            # Extraer FEN del texto
            fen = self._extract_fen(response.text)
            if not fen:
                logger.warning(f"No se pudo extraer FEN de: {response.text[:100]}")
                return None
            
            # Intentar reparar errores de conteo
            fen = self._try_fix_fen(fen)
            
            # Validar FEN reparado
            if self._validate_fen(fen):
                logger.info(f"FEN detectado: {fen}")
                return fen
            
            logger.warning(f"FEN invalido despues de reparacion: {fen}")
            return None
            
        except Exception as e:
            logger.error(f"Error en Gemini: {e}")
            return None
    
    def _extract_fen(self, text: str) -> Optional[str]:
        """Extrae el FEN del texto de respuesta."""
        text = text.strip()
        
        # Si es solo el FEN
        if self._looks_like_fen(text):
            # Agregar partes faltantes si es necesario
            parts = text.split()
            if len(parts) == 1:
                text += " w KQkq - 0 1"
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
    
    def _try_fix_fen(self, fen: str) -> str:
        """Intenta reparar errores comunes en el FEN."""
        parts = fen.split()
        board_part = parts[0]
        rows = board_part.split('/')
        
        fixed_rows = []
        for row in rows:
            count = 0
            for char in row:
                if char.isdigit():
                    count += int(char)
                elif char in 'rnbqkpRNBQKP':
                    count += 1
            
            if count == 8:
                fixed_rows.append(row)
            elif count > 8:
                # Fila tiene mas de 8, intentar corregir reduciendo numeros
                new_row = self._fix_row_too_long(row, count)
                fixed_rows.append(new_row)
            else:
                # Fila tiene menos de 8, agregar espacios vacios al final
                diff = 8 - count
                fixed_rows.append(row + str(diff))
        
        parts[0] = '/'.join(fixed_rows)
        return ' '.join(parts)
    
    def _fix_row_too_long(self, row: str, current_count: int) -> str:
        """Corrige una fila que suma mas de 8."""
        excess = current_count - 8
        new_row = []
        remaining_excess = excess
        
        for char in row:
            if remaining_excess > 0 and char.isdigit():
                val = int(char)
                if val > remaining_excess:
                    new_row.append(str(val - remaining_excess))
                    remaining_excess = 0
                else:
                    remaining_excess -= val
                    # No agregar este digito
            else:
                new_row.append(char)
        
        result = ''.join(new_row)
        
        # Verificar que ahora suma 8
        count = sum(int(c) if c.isdigit() else 1 for c in result if c.isdigit() or c in 'rnbqkpRNBQKP')
        if count != 8:
            # Si aun no suma 8, devolver fila original (se rechazara en validacion)
            return row
        return result
    
    def _looks_like_fen(self, text: str) -> bool:
        """Verifica si el texto parece un FEN."""
        parts = text.split('/')
        return len(parts) == 8 and all(
            re.match(r'^[rnbqkpRNBQKP1-8]+$', p.split()[0] if ' ' in p else p)
            for p in parts
        )
    
    def _validate_fen(self, fen: str) -> bool:
        """Valida que el FEN sea parseable (no necesariamente legal)."""
        try:
            parts = fen.split()
            board_part = parts[0]
            
            # Verificar estructura basica: 8 filas
            rows = board_part.split('/')
            if len(rows) != 8:
                return False
            
            # Verificar que cada fila sume 8 (piezas + espacios)
            for row in rows:
                count = 0
                for char in row:
                    if char.isdigit():
                        count += int(char)
                    elif char in 'rnbqkpRNBQKP':
                        count += 1
                    else:
                        return False
                if count != 8:
                    return False
            
            return True
        except Exception:
            return False


def image_to_base64(image: Image.Image, format: str = 'PNG') -> str:
    """Convierte imagen PIL a base64."""
    buffered = io.BytesIO()
    image.save(buffered, format=format)
    return base64.b64encode(buffered.getvalue()).decode('utf-8')
