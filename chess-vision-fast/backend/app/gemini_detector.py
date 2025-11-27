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
    
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
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
            
            # Validar FEN reparado con python-chess para mejor feedback
            try:
                import chess
                board = chess.Board(fen)
                # Verificar que tenga ambos reyes
                has_kings = (
                    len(board.pieces(chess.KING, chess.WHITE)) == 1 and
                    len(board.pieces(chess.KING, chess.BLACK)) == 1
                )
                if has_kings:
                    logger.info(f"FEN detectado y validado: {fen}")
                    return fen
                else:
                    logger.warning(f"FEN sin ambos reyes: {fen}")
            except ValueError as e:
                logger.warning(f"FEN inválido (python-chess): {fen} - Error: {str(e)}")
            except Exception as e:
                logger.warning(f"Error validando FEN con python-chess: {fen} - Error: {str(e)}")
            
            # Si falla validación con python-chess, intentar validación básica
            if self._validate_fen(fen):
                logger.info(f"FEN detectado (validación básica): {fen}")
                return fen
            
            logger.warning(f"FEN inválido después de reparación: {fen}")
            return None
            
        except Exception as e:
            logger.error(f"Error en Gemini: {e}")
            return None
    
    def _extract_fen(self, text: str) -> Optional[str]:
        """Extrae el FEN del texto de respuesta."""
        text = text.strip()
        
        # Limpiar posibles marcadores de código o texto adicional
        if text.startswith('```'):
            text = text.split('\n', 1)[1] if '\n' in text else text[3:]
        if text.endswith('```'):
            text = text[:-3]
        text = text.strip()
        
        # Limpiar caracteres no válidos del tablero (solo permitir rnbqkpRNBQKP12345678/)
        # Primero extraer el tablero
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Buscar patrón de tablero (8 filas separadas por /)
            parts = line.split()
            if len(parts) >= 1:
                board_part = parts[0]
                
                # Limpiar caracteres inválidos del tablero
                # Reemplazar caracteres problemáticos comunes que Gemini puede confundir
                # 'h' podría ser confundido con 'b' (bishop) o 'n' (knight)
                # 'H' podría ser confundido con 'B' o 'N'
                # Intentar corregir errores comunes
                board_part = board_part.replace('h', 'b')  # 'h' minúscula probablemente es 'b' (bishop)
                board_part = board_part.replace('H', 'B')  # 'H' mayúscula probablemente es 'B'
                board_part = board_part.replace('0', '')  # Eliminar ceros (no válidos en FEN)
                board_part = re.sub(r'[^rnbqkpRNBQKP12345678/]', '', board_part)  # Solo caracteres válidos
                
                if '/' in board_part:
                    rows = board_part.split('/')
                    if len(rows) == 8:
                        # Validar que cada fila tenga solo caracteres válidos
                        valid_rows = []
                        for row in rows:
                            # Limpiar cada fila
                            clean_row = re.sub(r'[^rnbqkpRNBQKP12345678]', '', row)
                            if clean_row:
                                valid_rows.append(clean_row)
                        
                        if len(valid_rows) == 8:
                            board_part = '/'.join(valid_rows)
                            
                            # Construir FEN completo
                            if len(parts) >= 6:
                                # Ya tiene todas las partes
                                return f"{board_part} {' '.join(parts[1:6])}"
                            else:
                                # Agregar partes faltantes
                                fen_parts = [board_part]
                                if len(parts) > 1:
                                    fen_parts.extend(parts[1:])
                                
                                # Completar partes faltantes
                                while len(fen_parts) < 6:
                                    if len(fen_parts) == 1:
                                        fen_parts.append('w')
                                    elif len(fen_parts) == 2:
                                        fen_parts.append('KQkq')
                                    elif len(fen_parts) == 3:
                                        fen_parts.append('-')
                                    elif len(fen_parts) == 4:
                                        fen_parts.append('0')
                                    elif len(fen_parts) == 5:
                                        fen_parts.append('1')
                                
                                return ' '.join(fen_parts)
        
        # Si no se encontró en líneas separadas, buscar patrón FEN en el texto completo
        fen_pattern = r'([rnbqkpRNBQKP1-8]+/){7}[rnbqkpRNBQKP1-8]+(?:\s+[wb]\s+[KQkq-]+\s+[a-h1-8-]+\s+\d+\s+\d+)?'
        match = re.search(fen_pattern, text)
        if match:
            fen = match.group(0).strip()
            # Limpiar caracteres inválidos
            parts = fen.split()
            if len(parts) >= 1:
                board_part = parts[0]
                # Limpiar tablero - corregir errores comunes
                board_part = board_part.replace('h', 'b')  # 'h' probablemente es 'b'
                board_part = board_part.replace('H', 'B')  # 'H' probablemente es 'B'
                board_part = re.sub(r'[^rnbqkpRNBQKP12345678/]', '', board_part)
                rows = board_part.split('/')
                if len(rows) == 8:
                    # Limpiar cada fila
                    clean_rows = [re.sub(r'[^rnbqkpRNBQKP12345678]', '', row) for row in rows]
                    board_part = '/'.join(clean_rows)
                    
                    if len(parts) >= 6:
                        return f"{board_part} {' '.join(parts[1:6])}"
                    else:
                        fen_parts = [board_part]
                        if len(parts) > 1:
                            fen_parts.extend(parts[1:])
                        while len(fen_parts) < 6:
                            if len(fen_parts) == 1:
                                fen_parts.append('w')
                            elif len(fen_parts) == 2:
                                fen_parts.append('KQkq')
                            elif len(fen_parts) == 3:
                                fen_parts.append('-')
                            elif len(fen_parts) == 4:
                                fen_parts.append('0')
                            elif len(fen_parts) == 5:
                                fen_parts.append('1')
                        return ' '.join(fen_parts)
        
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

    def suggest_best_move(self, image: Image.Image, timeout: float = 15.0) -> Optional[dict]:
        """
        Pide a Gemini que sugiera el mejor movimiento basado en la imagen.
        Sugiere el mejor movimiento basado en análisis de Gemini.
        
        Returns:
            dict con 'move' (UCI), 'san', 'explanation' o None si falla
        """
        try:
            model = self._get_model()
            
            # Preparar imagen
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            prompt = """Analyze this chess board image and suggest the best move.

Return your answer in this exact JSON format:
{"move": "e2e4", "san": "e4", "explanation": "Controls the center"}

Rules:
1. "move" must be in UCI format (e.g., e2e4, g1f3, e1g1 for castling)
2. "san" is standard algebraic notation (e.g., e4, Nf3, O-O)
3. "explanation" is a brief reason for the move
4. Determine whose turn it is based on the position
5. Choose a strong, logical move

Return ONLY the JSON, no other text:"""
            
            response = model.generate_content(
                [prompt, image],
                request_options={"timeout": timeout}
            )
            
            if not response.text:
                return None
            
            # Parsear JSON de respuesta
            import json
            text = response.text.strip()
            # Limpiar posibles marcadores de codigo
            if text.startswith('```'):
                text = text.split('\n', 1)[1] if '\n' in text else text[3:]
            if text.endswith('```'):
                text = text[:-3]
            text = text.strip()
            
            result = json.loads(text)
            return {
                'move': result.get('move', ''),
                'san': result.get('san', ''),
                'explanation': result.get('explanation', 'Sugerido por Gemini AI'),
                'source': 'gemini'
            }
            
        except Exception as e:
            logger.error(f"Error en Gemini suggest_best_move: {e}")
            return None


def image_to_base64(image: Image.Image, format: str = 'PNG') -> str:
    """Convierte imagen PIL a base64."""
    buffered = io.BytesIO()
    image.save(buffered, format=format)
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

