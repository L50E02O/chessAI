"""
Module to use Google Gemini Vision API to extract FEN from chess board images.
"""
import google.generativeai as genai
from PIL import Image
import numpy as np
from typing import Optional
from src.utils.config import GEMINI_API_KEY
from src.utils.helpers import short_log


def list_available_models() -> list:
    """
    Lists all available models in the Gemini API.
    Useful for debugging.
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
        short_log(f"❌ Error listing models: {str(e)}")
        return []


def extract_fen_from_image(image_path: str = None, image_array: np.ndarray = None) -> Optional[str]:
    """
    Sends an image to Google Gemini and requests it to identify the FEN of the chess board.
    
    Args:
        image_path: Path to the image (optional if image_array is provided)
        image_array: Numpy array of the RGB image (optional if image_path is provided)
    
    Returns:
        FEN string if detected correctly, None on error
    """
    if not GEMINI_API_KEY:
        short_log("❌ Error: GEMINI_API_KEY not configured in .env")
        return None
    
    try:
        # Configure Gemini
        genai.configure(api_key=GEMINI_API_KEY)
        
        # Use models compatible with current API (Gemini 2.x)
        # Try different models in order of preference
        model_names = [
            'models/gemini-2.5-flash',           # Fast and efficient
            'models/gemini-2.0-flash',           # Fast alternative
            'models/gemini-2.5-pro',             # More powerful
            'models/gemini-flash-latest',        # Latest flash
            'models/gemini-2.0-flash-exp',       # Experimental
            'models/gemini-pro-latest',          # Latest pro
        ]
        
        model = None
        last_error = None
        for model_name in model_names:
            try:
                model = genai.GenerativeModel(model_name)
                short_log(f"✅ Using model: {model_name}")
                break
            except Exception as e:
                last_error = str(e)
                continue
        
        if model is None:
            short_log(f"❌ Error: Could not find a compatible Gemini model")
            short_log(f"   Last error: {last_error}")
            # Try to list available models
            available = list_available_models()
            if available:
                short_log(f"   Available models: {', '.join(available[:3])}")
            return None
        
        # Load image
        if image_array is not None:
            # Convert numpy array to PIL Image
            img = Image.fromarray(image_array)
        elif image_path:
            img = Image.open(image_path)
        else:
            short_log("❌ Error: Must provide image_path or image_array")
            return None
        
        short_log("🤖 Sending image to Google Gemini for analysis...")
        
        # Specific prompt to extract FEN
        prompt = """Analyze this image and extract the chess board position in FEN (Forsyth-Edwards Notation) format.

INSTRUCTIONS:
1. Identify all pieces on the board
2. Determine which side you're viewing the board from (white at bottom or black at bottom)
3. Generate the FEN string following the standard format
4. IMPORTANT: Respond ONLY with the FEN string, without additional explanations
5. If you see the board from black's side, make sure to correctly invert the perspective

FEN format: [position] [turn] [castling] [en passant] [halfmove] [fullmove]

Example of valid response:
rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1

Respond ONLY with the FEN:"""
        
        # Send to Gemini
        response = model.generate_content([prompt, img])
        
        # Extract FEN from response
        fen = response.text.strip()
        
        # Basic FEN validation
        if '/' in fen and len(fen.split()) >= 1:
            short_log(f"✅ FEN extracted by Gemini: {fen}")
            return fen
        else:
            short_log(f"⚠️ Gemini response doesn't seem like a valid FEN: {fen}")
            return fen  # Return anyway for debugging
            
    except Exception as e:
        short_log(f"❌ Error using Gemini Vision: {str(e)}")
        return None


def extract_fen_with_retry(image_path: str = None, image_array: np.ndarray = None, max_retries: int = 2) -> Optional[str]:
    """
    Attempts to extract FEN with retries in case of failure.
    
    Args:
        image_path: Path to the image
        image_array: Numpy array of the image
        max_retries: Maximum number of retries
    
    Returns:
        FEN string or None
    """
    for attempt in range(max_retries):
        fen = extract_fen_from_image(image_path, image_array)
        if fen and '/' in fen:  # Minimum validation
            return fen
        if attempt < max_retries - 1:
            short_log(f"🔄 Retrying... (attempt {attempt + 2}/{max_retries})")
    
    return None
