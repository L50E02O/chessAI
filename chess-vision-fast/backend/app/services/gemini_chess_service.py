"""
Chess analysis service using Google Gemini as Grandmaster.
Maintains game context and provides analysis and recommendations.
"""
import json
import logging
from typing import Dict, List, Optional

import chess
from PIL import Image

from ..gemini_detector import GeminiDetector

logger = logging.getLogger(__name__)


class GeminiChessService:
    """
    Service that uses Gemini as chess GM.
    Maintains game context and provides continuous analysis.
    """
    
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self.gemini = GeminiDetector(api_key, model)
        self.conversation_history: List[Dict[str, str]] = []
        self.move_history: List[str] = []
        self.current_fen: Optional[str] = None
        
    def _get_system_prompt(self) -> str:
        """Returns the system prompt that defines the GM role."""
        return """You are a Grandmaster chess player (GM) with over 20 years of experience.
Your task is to analyze chess positions and provide:
1. The best move in UCI format (e.g., e2e4)
2. Standard algebraic notation (SAN) of the move (e.g., e4)
3. A brief and clear explanation of why it's the best move
4. Analysis of the current position
5. Strategic and tactical considerations

Maintain the context of the complete game. When presented with a new position,
analyze how we got here from the previous position.

ALWAYS respond in valid JSON format with this exact structure:
{
    "move": "e2e4",
    "san": "e4",
    "explanation": "Controls the center and frees the bishop and queen",
    "position_analysis": "Balanced position, normal development",
    "strategic_notes": "Continue with minor piece development"
}

IMPORTANT: 
- "move" must be in UCI format (e.g., e2e4, g1f3, e1g1 for castling)
- "san" is standard algebraic notation
- Be concise but informative in explanations
- Analyze the position considering the game context"""
    
    def _build_context_message(self, fen: str, image: Optional[Image.Image] = None) -> str:
        """Builds the message with game context."""
        context_parts = []
        
        if self.move_history:
            context_parts.append(f"Move history: {', '.join(self.move_history[-10:])}")
        
        if self.current_fen and self.current_fen != fen:
            context_parts.append(f"Previous position (FEN): {self.current_fen}")
            context_parts.append("Analyze what changed in the position.")
        
        context_parts.append(f"Current position (FEN): {fen}")
        
        try:
            board = chess.Board(fen)
            turn = "White" if board.turn == chess.WHITE else "Black"
            context_parts.append(f"Turn: {turn}")
            
            # Additional position information
            if board.is_check():
                context_parts.append("CHECK!")
            if board.is_checkmate():
                context_parts.append("CHECKMATE!")
            elif board.is_stalemate():
                context_parts.append("STALEMATE")
            elif board.is_insufficient_material():
                context_parts.append("Insufficient material to checkmate")
        except Exception as e:
            logger.warning(f"Error analyzing FEN: {e}")
        
        return "\n".join(context_parts)
    
    def analyze_position(
        self, 
        fen: str, 
        image: Optional[Image.Image] = None,
        timeout: float = 20.0
    ) -> Optional[Dict]:
        """
        Analyzes current position and suggests best move.
        
        Args:
            fen: FEN of current position
            image: Optional board image
            timeout: Timeout in seconds
            
        Returns:
            Dict with move, san, explanation, position_analysis, strategic_notes
            or None if it fails
        """
        try:
            # Build message with context
            context_message = self._build_context_message(fen, image)
            
            # Prepare content for Gemini
            content_parts = [self._get_system_prompt()]
            content_parts.append("\n---\n")
            content_parts.append(context_message)
            
            # If there's an image, include it
            if image:
                content_parts.append("\nHere is the board image:")
            
            # Add to conversation history
            self.conversation_history.append({
                "role": "user",
                "content": context_message
            })
            
            # Call Gemini
            model = self.gemini._get_model()
            
            if image:
                response = model.generate_content(
                    content_parts + [image],
                    request_options={"timeout": timeout}
                )
            else:
                full_prompt = "\n".join(content_parts)
                response = model.generate_content(
                    full_prompt,
                    request_options={"timeout": timeout}
                )
            
            # Check if response was blocked
            if not response.candidates:
                logger.warning("Gemini did not return candidates in analyze_position")
                return None
            
            candidate = response.candidates[0]
            if candidate.finish_reason != 1:  # 1 = STOP (normal)
                reason_map = {2: "SAFETY", 3: "RECITATION", 4: "OTHER"}
                reason = reason_map.get(candidate.finish_reason, f"CODE_{candidate.finish_reason}")
                logger.warning(f"Gemini blocked response in analyze_position: {reason}")
                return None
            
            if not response.text:
                logger.warning("Gemini did not return response")
                return None
            
            # Parse JSON response
            text = response.text.strip()
            # Clean possible code markers
            if text.startswith('```json'):
                text = text[7:]
            elif text.startswith('```'):
                text = text[3:]
            if text.endswith('```'):
                text = text[:-3]
            text = text.strip()
            
            result = json.loads(text)
            
            # Validate that it has required fields
            if 'move' not in result or 'san' not in result:
                logger.warning(f"Gemini response incomplete: {result}")
                return None
            
            # Add response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": response.text
            })
            
            # Update state
            self.current_fen = fen
            if result.get('move'):
                self.move_history.append(result.get('san', result.get('move')))
            
            return {
                'move': result.get('move', ''),
                'uci': result.get('move', ''),
                'san': result.get('san', ''),
                'explanation': result.get('explanation', 'Analysis provided by Gemini AI'),
                'position_analysis': result.get('position_analysis', ''),
                'strategic_notes': result.get('strategic_notes', ''),
                'score': {'cp': None, 'mate': None},  # Gemini does not provide numerical score
            }
            
        except json.JSONDecodeError as e:
            response_text = response.text if hasattr(response, 'text') and response.text else ''
            logger.error(f"Error parsing JSON from Gemini: {e}. Response: {response_text[:200]}")
            # Try to extract basic information from text
            return self._fallback_parse(response_text, fen)
        except Exception as e:
            logger.error(f"Error in analyze_position: {e}")
            return None
    
    def _fallback_parse(self, text: str, fen: str) -> Optional[Dict]:
        """Attempts to extract basic information if JSON fails."""
        import re
        # Search for UCI moves
        uci_match = re.search(r'\b([a-h][1-8][a-h][1-8])\b', text)
        # Search for SAN notation
        san_match = re.search(r'\b([KQRNB]?[a-h]?[1-8]?x?[a-h][1-8][+#]?|O-O|O-O-O)\b', text)
        
        if uci_match:
            return {
                'move': uci_match.group(1),
                'uci': uci_match.group(1),
                'san': san_match.group(1) if san_match else uci_match.group(1),
                'explanation': text[:200],
                'position_analysis': '',
                'strategic_notes': '',
                'score': {'cp': None, 'mate': None},
            }
        return None
    
    def get_retrospective(self) -> Optional[str]:
        """
        Gets a retrospective of the complete game.
        
        Returns:
            String with retrospective analysis or None if it fails
        """
        if not self.move_history:
            return "No move history to analyze."
        
        try:
            prompt = f"""As a Grandmaster chess player, provide a complete retrospective of this game.

Move history: {', '.join(self.move_history)}
Final position (FEN): {self.current_fen or 'Not available'}

Analyze:
1. Overall game quality
2. Key moments and notable moves
3. Errors or missed opportunities
4. Lessons learned
5. Recommendations for improvement

Be detailed but concise. Respond in English."""
            
            model = self.gemini._get_model()
            response = model.generate_content(
                prompt,
                request_options={"timeout": 30.0}
            )
            
            if response.text:
                return response.text.strip()
            return None
            
        except Exception as e:
            logger.error(f"Error getting retrospective: {e}")
            return None
    
    def clear_context(self) -> None:
        """Clears game context."""
        self.conversation_history = []
        self.move_history = []
        self.current_fen = None
        logger.info("Game context cleared")

