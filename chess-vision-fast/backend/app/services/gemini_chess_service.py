"""
Servicio de análisis de ajedrez usando Google Gemini como Gran Maestro.
Mantiene el contexto de la partida y proporciona análisis y recomendaciones.
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
    Servicio que usa Gemini como GM de ajedrez.
    Mantiene el contexto de la partida y proporciona análisis continuo.
    """
    
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self.gemini = GeminiDetector(api_key, model)
        self.conversation_history: List[Dict[str, str]] = []
        self.move_history: List[str] = []
        self.current_fen: Optional[str] = None
        
    def _get_system_prompt(self) -> str:
        """Retorna el prompt del sistema que define el rol de GM."""
        return """Eres un Gran Maestro de ajedrez (GM) con más de 20 años de experiencia.
Tu tarea es analizar posiciones de ajedrez y proporcionar:
1. La mejor jugada en formato UCI (ej: e2e4)
2. Notación algebraica estándar (SAN) de la jugada (ej: e4)
3. Una explicación breve y clara de por qué es la mejor jugada
4. Análisis de la posición actual
5. Consideraciones estratégicas y tácticas

Mantén el contexto de la partida completa. Cuando se te presente una nueva posición,
analiza cómo llegamos aquí desde la posición anterior.

Responde SIEMPRE en formato JSON válido con esta estructura exacta:
{
    "move": "e2e4",
    "san": "e4",
    "explanation": "Controla el centro y libera el alfil y la dama",
    "position_analysis": "Posición equilibrada, desarrollo normal",
    "strategic_notes": "Continuar con desarrollo de piezas menores"
}

IMPORTANTE: 
- "move" debe estar en formato UCI (ej: e2e4, g1f3, e1g1 para enroque)
- "san" es notación algebraica estándar
- Sé conciso pero informativo en las explicaciones
- Analiza la posición considerando el contexto de la partida"""
    
    def _build_context_message(self, fen: str, image: Optional[Image.Image] = None) -> str:
        """Construye el mensaje con el contexto de la partida."""
        context_parts = []
        
        if self.move_history:
            context_parts.append(f"Historial de movimientos: {', '.join(self.move_history[-10:])}")
        
        if self.current_fen and self.current_fen != fen:
            context_parts.append(f"Posición anterior (FEN): {self.current_fen}")
            context_parts.append("Analiza qué cambió en la posición.")
        
        context_parts.append(f"Posición actual (FEN): {fen}")
        
        try:
            board = chess.Board(fen)
            turn = "Blancas" if board.turn == chess.WHITE else "Negras"
            context_parts.append(f"Turno: {turn}")
            
            # Información adicional de la posición
            if board.is_check():
                context_parts.append("¡JAQUE!")
            if board.is_checkmate():
                context_parts.append("¡JAQUE MATE!")
            elif board.is_stalemate():
                context_parts.append("TABLAS por ahogado")
            elif board.is_insufficient_material():
                context_parts.append("Material insuficiente para dar mate")
        except Exception as e:
            logger.warning(f"Error analizando FEN: {e}")
        
        return "\n".join(context_parts)
    
    def analyze_position(
        self, 
        fen: str, 
        image: Optional[Image.Image] = None,
        timeout: float = 20.0
    ) -> Optional[Dict]:
        """
        Analiza la posición actual y sugiere la mejor jugada.
        
        Args:
            fen: FEN de la posición actual
            image: Imagen opcional del tablero
            timeout: Timeout en segundos
            
        Returns:
            Dict con move, san, explanation, position_analysis, strategic_notes
            o None si falla
        """
        try:
            # Construir mensaje con contexto
            context_message = self._build_context_message(fen, image)
            
            # Preparar contenido para Gemini
            content_parts = [self._get_system_prompt()]
            content_parts.append("\n---\n")
            content_parts.append(context_message)
            
            # Si hay imagen, incluirla
            if image:
                content_parts.append("\nAquí está la imagen del tablero:")
            
            # Agregar al historial de conversación
            self.conversation_history.append({
                "role": "user",
                "content": context_message
            })
            
            # Llamar a Gemini
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
            
            if not response.text:
                logger.warning("Gemini no devolvió respuesta")
                return None
            
            # Parsear respuesta JSON
            text = response.text.strip()
            # Limpiar posibles marcadores de código
            if text.startswith('```json'):
                text = text[7:]
            elif text.startswith('```'):
                text = text[3:]
            if text.endswith('```'):
                text = text[:-3]
            text = text.strip()
            
            result = json.loads(text)
            
            # Validar que tenga los campos necesarios
            if 'move' not in result or 'san' not in result:
                logger.warning(f"Respuesta de Gemini incompleta: {result}")
                return None
            
            # Agregar respuesta al historial
            self.conversation_history.append({
                "role": "assistant",
                "content": response.text
            })
            
            # Actualizar estado
            self.current_fen = fen
            if result.get('move'):
                self.move_history.append(result.get('san', result.get('move')))
            
            return {
                'move': result.get('move', ''),
                'uci': result.get('move', ''),
                'san': result.get('san', ''),
                'explanation': result.get('explanation', 'Análisis proporcionado por Gemini AI'),
                'position_analysis': result.get('position_analysis', ''),
                'strategic_notes': result.get('strategic_notes', ''),
                'score': {'cp': None, 'mate': None},  # Gemini no proporciona score numérico
            }
            
        except json.JSONDecodeError as e:
            response_text = response.text if hasattr(response, 'text') and response.text else ''
            logger.error(f"Error parseando JSON de Gemini: {e}. Respuesta: {response_text[:200]}")
            # Intentar extraer información básica del texto
            return self._fallback_parse(response_text, fen)
        except Exception as e:
            logger.error(f"Error en analyze_position: {e}")
            return None
    
    def _fallback_parse(self, text: str, fen: str) -> Optional[Dict]:
        """Intenta extraer información básica si el JSON falla."""
        import re
        # Buscar movimientos UCI
        uci_match = re.search(r'\b([a-h][1-8][a-h][1-8])\b', text)
        # Buscar notación SAN
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
        Obtiene una retrospectiva de la partida completa.
        
        Returns:
            String con análisis retrospectivo o None si falla
        """
        if not self.move_history:
            return "No hay historial de movimientos para analizar."
        
        try:
            prompt = f"""Como Gran Maestro de ajedrez, proporciona una retrospectiva completa de esta partida.

Historial de movimientos: {', '.join(self.move_history)}
Posición final (FEN): {self.current_fen or 'No disponible'}

Analiza:
1. La calidad general de la partida
2. Momentos clave y jugadas destacadas
3. Errores o oportunidades perdidas
4. Lecciones aprendidas
5. Recomendaciones para mejorar

Sé detallado pero conciso. Responde en español."""
            
            model = self.gemini._get_model()
            response = model.generate_content(
                prompt,
                request_options={"timeout": 30.0}
            )
            
            if response.text:
                return response.text.strip()
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo retrospectiva: {e}")
            return None
    
    def clear_context(self) -> None:
        """Limpia el contexto de la partida."""
        self.conversation_history = []
        self.move_history = []
        self.current_fen = None
        logger.info("Contexto de partida limpiado")

