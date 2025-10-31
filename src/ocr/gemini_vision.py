"""
Módulo para usar Google Gemini Vision API para extraer FEN de imágenes de tableros de ajedrez.
"""
import google.generativeai as genai
from PIL import Image
import numpy as np
from typing import Optional
from src.utils.config import GEMINI_API_KEY
from src.utils.helpers import short_log


def list_available_models() -> list:
    """
    Lista todos los modelos disponibles en la API de Gemini.
    Útil para debugging.
    """
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        models = genai.list_models()
        available = []
        for model in models:
            if 'generateContent' in model.supported_generation_methods:
                available.append(model.name)
        return available
    except Exception as e:
        short_log(f"❌ Error al listar modelos: {str(e)}")
        return []


def extract_fen_from_image(image_path: str = None, image_array: np.ndarray = None) -> Optional[str]:
    """
    Envía una imagen a Google Gemini y solicita que identifique el FEN del tablero de ajedrez.
    
    Args:
        image_path: Ruta a la imagen (opcional si se proporciona image_array)
        image_array: Array numpy de la imagen RGB (opcional si se proporciona image_path)
    
    Returns:
        String FEN si se detecta correctamente, None en caso de error
    """
    if not GEMINI_API_KEY:
        short_log("❌ Error: GEMINI_API_KEY no configurado en .env")
        return None
    
    try:
        # Configurar Gemini
        genai.configure(api_key=GEMINI_API_KEY)
        
        # Usar modelos compatibles con la API actual (Gemini 2.x)
        # Intentar con diferentes modelos en orden de preferencia
        model_names = [
            'models/gemini-2.5-flash',           # Rápido y eficiente
            'models/gemini-2.0-flash',           # Alternativa rápida
            'models/gemini-2.5-pro',             # Más potente
            'models/gemini-flash-latest',        # Último flash
            'models/gemini-2.0-flash-exp',       # Experimental
            'models/gemini-pro-latest',          # Último pro
        ]
        
        model = None
        last_error = None
        for model_name in model_names:
            try:
                model = genai.GenerativeModel(model_name)
                short_log(f"✅ Usando modelo: {model_name}")
                break
            except Exception as e:
                last_error = str(e)
                continue
        
        if model is None:
            short_log(f"❌ Error: No se pudo encontrar un modelo Gemini compatible")
            short_log(f"   Último error: {last_error}")
            # Intentar listar modelos disponibles
            available = list_available_models()
            if available:
                short_log(f"   Modelos disponibles: {', '.join(available[:3])}")
            return None
        
        # Cargar imagen
        if image_array is not None:
            # Convertir numpy array a PIL Image
            img = Image.fromarray(image_array)
        elif image_path:
            img = Image.open(image_path)
        else:
            short_log("❌ Error: Debe proporcionar image_path o image_array")
            return None
        
        short_log("🤖 Enviando imagen a Google Gemini para análisis...")
        
        # Prompt específico para extraer FEN
        prompt = """Analiza esta imagen y extrae la posición del tablero de ajedrez en formato FEN (Forsyth-Edwards Notation).

INSTRUCCIONES:
1. Identifica todas las piezas en el tablero
2. Determina de qué lado estás viendo el tablero (blancas abajo o negras abajo)
3. Genera el string FEN siguiendo el formato estándar
4. IMPORTANTE: Responde SOLO con el string FEN, sin explicaciones adicionales
5. Si ves el tablero desde las negras, asegúrate de invertir correctamente la perspectiva

Formato FEN: [posición] [turno] [enroque] [en passant] [medio movimiento] [movimiento completo]

Ejemplo de respuesta válida:
rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1

Responde SOLO con el FEN:"""
        
        # Enviar a Gemini
        response = model.generate_content([prompt, img])
        
        # Extraer el FEN de la respuesta
        fen = response.text.strip()
        
        # Validación básica del FEN
        if '/' in fen and len(fen.split()) >= 1:
            short_log(f"✅ FEN extraído por Gemini: {fen}")
            return fen
        else:
            short_log(f"⚠️ Respuesta de Gemini no parece un FEN válido: {fen}")
            return fen  # Devolver de todas formas para debugging
            
    except Exception as e:
        short_log(f"❌ Error al usar Gemini Vision: {str(e)}")
        return None


def extract_fen_with_retry(image_path: str = None, image_array: np.ndarray = None, max_retries: int = 2) -> Optional[str]:
    """
    Intenta extraer FEN con reintentos en caso de fallo.
    
    Args:
        image_path: Ruta a la imagen
        image_array: Array numpy de la imagen
        max_retries: Número máximo de reintentos
    
    Returns:
        String FEN o None
    """
    for attempt in range(max_retries):
        fen = extract_fen_from_image(image_path, image_array)
        if fen and '/' in fen:  # Validación mínima
            return fen
        if attempt < max_retries - 1:
            short_log(f"🔄 Reintentando... (intento {attempt + 2}/{max_retries})")
    
    return None
