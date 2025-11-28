"""
Chess board detector using Google Gemini Vision.
Optimized to avoid hangs and handle errors gracefully.
"""
import base64
import io
import logging
import re
from typing import Optional

import chess
from PIL import Image

logger = logging.getLogger(__name__)

# Optimized prompt for Gemini
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
    """Detector using Google Gemini Vision API."""
    
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self.api_key = api_key
        self.model_name = model
        self._model = None
        self._generation_config = {
            "temperature": 0.1,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 512,
        }
        # Minimum safety configuration for chess images
        try:
            from google.generativeai.types import HarmCategory, HarmBlockThreshold
            self._safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        except ImportError:
            # Fallback for older versions
            self._safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
            ]
    
    def _get_model(self):
        """Initializes the model lazily."""
        if self._model is None:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self._model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=self._generation_config,
                safety_settings=self._safety_settings,
            )
        return self._model
    
    def detect_fen(self, image: Image.Image, timeout: float = 15.0) -> Optional[str]:
        """
        Detects FEN from a board image.
        
        Args:
            image: PIL image of the board
            timeout: Timeout in seconds (default 15s)
            
        Returns:
            FEN string or None if it fails
        """
        try:
            model = self._get_model()
            
            # Add padding to avoid edge cropping
            padding = 10
            padded = Image.new('RGB', (image.width + padding*2, image.height + padding*2), (50, 50, 50))
            padded.paste(image, (padding, padding))
            image = padded
            
            # Resize image if too large (avoids hangs)
            max_size = 1024
            if max(image.size) > max_size:
                ratio = max_size / max(image.size)
                new_size = (int(image.width * ratio), int(image.height * ratio))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Generate response
            response = model.generate_content(
                [GEMINI_PROMPT, image],
                request_options={"timeout": timeout}
            )
            
            # Check if response was blocked
            if not response.candidates:
                logger.warning("Gemini did not return candidates (possible block)")
                return None
            
            candidate = response.candidates[0]
            if candidate.finish_reason != 1:  # 1 = STOP (normal)
                reason_map = {2: "SAFETY", 3: "RECITATION", 4: "OTHER"}
                reason = reason_map.get(candidate.finish_reason, f"CODE_{candidate.finish_reason}")
                logger.warning(f"Gemini blocked response: {reason}")
                return None
            
            if not response.text:
                logger.warning("Gemini did not return text")
                return None
            
            # Extract FEN from text
            fen = self._extract_fen(response.text)
            if not fen:
                logger.warning(f"Could not extract FEN from: {response.text[:100]}")
                return None
            
            # Try to repair counting errors
            fen = self._try_fix_fen(fen)
            
            # Validate repaired FEN with python-chess for better feedback
            try:
                import chess
                board = chess.Board(fen)
                # Verify it has both kings
                has_kings = (
                    len(board.pieces(chess.KING, chess.WHITE)) == 1 and
                    len(board.pieces(chess.KING, chess.BLACK)) == 1
                )
                if has_kings:
                    logger.info(f"FEN detected and validated: {fen}")
                    return fen
                else:
                    logger.warning(f"FEN without both kings: {fen}")
            except ValueError as e:
                logger.warning(f"Invalid FEN (python-chess): {fen} - Error: {str(e)}")
            except Exception as e:
                logger.warning(f"Error validating FEN with python-chess: {fen} - Error: {str(e)}")
            
            # If python-chess validation fails, try basic validation
            if self._validate_fen(fen):
                logger.info(f"FEN detected (basic validation): {fen}")
                return fen
            
            logger.warning(f"Invalid FEN after repair: {fen}")
            return None
            
        except Exception as e:
            logger.error(f"Error in Gemini: {e}")
            return None
    
    def _extract_fen(self, text: str) -> Optional[str]:
        """Extracts FEN from response text."""
        text = text.strip()
        
        # Clean possible code markers or additional text
        if text.startswith('```'):
            text = text.split('\n', 1)[1] if '\n' in text else text[3:]
        if text.endswith('```'):
            text = text[:-3]
        text = text.strip()
        
        # Clean invalid characters from board (only allow rnbqkpRNBQKP12345678/)
        # First extract the board
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Search for board pattern (8 rows separated by /)
            parts = line.split()
            if len(parts) >= 1:
                board_part = parts[0]
                
                # Clean invalid characters from board
                # Replace common problematic characters that Gemini may confuse
                # 'h' could be confused with 'b' (bishop) or 'n' (knight)
                # 'H' could be confused with 'B' or 'N'
                # Try to correct common errors
                board_part = board_part.replace('h', 'b')  # lowercase 'h' probably is 'b' (bishop)
                board_part = board_part.replace('H', 'B')  # uppercase 'H' probably is 'B'
                board_part = board_part.replace('0', '')  # Remove zeros (not valid in FEN)
                board_part = re.sub(r'[^rnbqkpRNBQKP12345678/]', '', board_part)  # Only valid characters
                
                if '/' in board_part:
                    rows = board_part.split('/')
                    if len(rows) == 8:
                        # Validate that each row has only valid characters
                        valid_rows = []
                        for row in rows:
                            # Clean each row
                            clean_row = re.sub(r'[^rnbqkpRNBQKP12345678]', '', row)
                            if clean_row:
                                valid_rows.append(clean_row)
                        
                        if len(valid_rows) == 8:
                            board_part = '/'.join(valid_rows)
                            
                            # Build complete FEN
                            if len(parts) >= 6:
                                # Already has all parts
                                return f"{board_part} {' '.join(parts[1:6])}"
                            else:
                                # Add missing parts
                                fen_parts = [board_part]
                                if len(parts) > 1:
                                    fen_parts.extend(parts[1:])
                                
                                # Complete missing parts
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
        
        # If not found in separate lines, search for FEN pattern in complete text
        fen_pattern = r'([rnbqkpRNBQKP1-8]+/){7}[rnbqkpRNBQKP1-8]+(?:\s+[wb]\s+[KQkq-]+\s+[a-h1-8-]+\s+\d+\s+\d+)?'
        match = re.search(fen_pattern, text)
        if match:
            fen = match.group(0).strip()
            # Clean invalid characters
            parts = fen.split()
            if len(parts) >= 1:
                board_part = parts[0]
                # Clean board - correct common errors
                board_part = board_part.replace('h', 'b')  # 'h' probably is 'b'
                board_part = board_part.replace('H', 'B')  # 'H' probably is 'B'
                board_part = re.sub(r'[^rnbqkpRNBQKP12345678/]', '', board_part)
                rows = board_part.split('/')
                if len(rows) == 8:
                    # Clean each row
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
        """Attempts to repair common errors in FEN."""
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
                # Row has more than 8, try to correct by reducing numbers
                new_row = self._fix_row_too_long(row, count)
                fixed_rows.append(new_row)
            else:
                # Row has less than 8, add empty spaces at the end
                diff = 8 - count
                fixed_rows.append(row + str(diff))
        
        parts[0] = '/'.join(fixed_rows)
        return ' '.join(parts)
    
    def _fix_row_too_long(self, row: str, current_count: int) -> str:
        """Fixes a row that sums more than 8."""
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
                    # Don't add this digit
            else:
                new_row.append(char)
        
        result = ''.join(new_row)
        
        # Verify that it now sums 8
        count = sum(int(c) if c.isdigit() else 1 for c in result if c.isdigit() or c in 'rnbqkpRNBQKP')
        if count != 8:
            # If still doesn't sum 8, return original row (will be rejected in validation)
            return row
        return result
    
    def _looks_like_fen(self, text: str) -> bool:
        """Checks if text looks like FEN."""
        parts = text.split('/')
        return len(parts) == 8 and all(
            re.match(r'^[rnbqkpRNBQKP1-8]+$', p.split()[0] if ' ' in p else p)
            for p in parts
        )
    
    def _validate_fen(self, fen: str) -> bool:
        """Validates that FEN is parseable (not necessarily legal)."""
        try:
            parts = fen.split()
            board_part = parts[0]
            
            # Verify basic structure: 8 rows
            rows = board_part.split('/')
            if len(rows) != 8:
                return False
            
            # Verify that each row sums 8 (pieces + spaces)
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
        Asks Gemini to suggest the best move based on the image.
        Suggests the best move based on Gemini analysis.
        
        Returns:
            dict with 'move' (UCI), 'san', 'explanation' or None if it fails
        """
        try:
            model = self._get_model()
            
            # Prepare image
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
            
            # Parse JSON response
            import json
            text = response.text.strip()
            # Clean possible code markers
            if text.startswith('```'):
                text = text.split('\n', 1)[1] if '\n' in text else text[3:]
            if text.endswith('```'):
                text = text[:-3]
            text = text.strip()
            
            result = json.loads(text)
            return {
                'move': result.get('move', ''),
                'san': result.get('san', ''),
                'explanation': result.get('explanation', 'Suggested by Gemini AI'),
                'source': 'gemini'
            }
            
        except Exception as e:
            logger.error(f"Error in Gemini suggest_best_move: {e}")
            return None


def image_to_base64(image: Image.Image, format: str = 'PNG') -> str:
    """Converts PIL image to base64."""
    buffered = io.BytesIO()
    image.save(buffered, format=format)
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

