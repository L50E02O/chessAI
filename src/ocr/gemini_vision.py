"""
Module to use Google Gemini Vision API to extract FEN from chess board images.
"""
import re
import time
import google.generativeai as genai
from PIL import Image, ImageEnhance
import numpy as np
import cv2
from typing import Optional
from src.utils.config import GEMINI_API_KEY
from src.utils.helpers import short_log
from src.ocr.fen_generator import validate_fen


def _try_fix_fen(fen: str) -> Optional[str]:
    """
    Attempts to fix common FEN errors from Gemini.
    Returns fixed FEN or None if can't fix.
    """
    try:
        parts = fen.split()
        if len(parts) < 6:
            return None
        
        position_part = parts[0]
        rows = position_part.split('/')
        
        if len(rows) != 8:
            return None
        
        # Try to fix rows that don't sum to 8
        fixed_rows = []
        for row in rows:
            square_count = 0
            for char in row:
                if char.isdigit():
                    square_count += int(char)
                elif char in 'rnbqkpRNBQKP':
                    square_count += 1
            
            if square_count == 8:
                fixed_rows.append(row)
            elif square_count == 7:
                # Add one empty square - try to add at the end
                if row and row[-1].isdigit():
                    # Increment last number
                    new_row = row[:-1] + str(int(row[-1]) + 1)
                elif row and row[0].isdigit():
                    # Increment first number
                    new_row = str(int(row[0]) + 1) + row[1:]
                else:
                    # Add '1' at the end
                    new_row = row + '1'
                fixed_rows.append(new_row)
            elif square_count == 9:
                # Remove one square - try multiple strategies
                fixed = False
                
                # Strategy 1: If last char is a digit, try to reduce it
                if row and row[-1].isdigit() and int(row[-1]) > 1:
                    new_row = row[:-1] + str(int(row[-1]) - 1)
                    fixed_rows.append(new_row)
                    fixed = True
                # Strategy 2: If first char is a digit, try to reduce it
                elif row and row[0].isdigit() and int(row[0]) > 1:
                    new_row = str(int(row[0]) - 1) + row[1:]
                    fixed_rows.append(new_row)
                    fixed = True
                # Strategy 3: Try to merge consecutive digits
                elif len(row) >= 2:
                    import re
                    # Find pattern like "2Bp1P3" and try to reduce last digit
                    match = re.search(r'(\d+)$', row)
                    if match and int(match.group(1)) > 1:
                        new_row = row[:match.start()] + str(int(match.group(1)) - 1)
                        fixed_rows.append(new_row)
                        fixed = True
                
                if not fixed:
                    # Can't auto-fix this row
                    return None
            else:
                # Too far off (more than 1 square difference), can't auto-fix
                return None
        
        fixed_position = '/'.join(fixed_rows)
        
        # Verify the fixed position has correct square counts
        for row in fixed_rows:
            count = sum(int(c) if c.isdigit() else 1 for c in row if c.isdigit() or c in 'rnbqkpRNBQKP')
            if count != 8:
                return None
        
        fixed_fen = f"{fixed_position} {' '.join(parts[1:])}"
        
        # Verify kings are correct
        if fixed_position.count('K') == 1 and fixed_position.count('k') == 1:
            return fixed_fen
        
        return None
    except Exception as e:
        return None


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
        
        # Load and preprocess image
        if image_array is not None:
            # Convert numpy array to PIL Image
            # Check if image is BGR (from OpenCV) and convert to RGB
            if len(image_array.shape) == 3 and image_array.shape[2] == 3:
                # Assume BGR if coming from OpenCV, convert to RGB
                img = Image.fromarray(cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB))
            else:
                img = Image.fromarray(image_array)
        elif image_path:
            img = Image.open(image_path)
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
        else:
            short_log("❌ Error: Must provide image_path or image_array")
            return None
        
        # Optimize image size (Gemini works well with 1024px max dimension)
        # This reduces API costs and improves speed
        max_dimension = 1024
        width, height = img.size
        if width > max_dimension or height > max_dimension:
            ratio = min(max_dimension / width, max_dimension / height)
            new_size = (int(width * ratio), int(height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            short_log(f"📐 Image resized to {new_size[0]}x{new_size[1]}px for optimization")
        
        # Enhance image for better recognition, especially in mid-game
        # Increase contrast slightly to make pieces stand out
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.15)  # Slightly more contrast for mid-game
        
        # Sharpen slightly to make piece edges clearer
        from PIL import ImageFilter
        img = img.filter(ImageFilter.SHARPEN)
        
        short_log("🤖 Sending image to Google Gemini for analysis...")
        
        # Improved prompt to extract FEN - optimized for accuracy
        prompt = """You are a chess position analyzer. Extract the exact FEN (Forsyth-Edwards Notation) from this chess board image.

CRITICAL VALIDATION RULES (MUST FOLLOW):
1. Each of the 8 rows MUST have exactly 8 squares total (pieces + empty squares = 8)
2. There MUST be exactly 1 white king (K) and exactly 1 black king (k) on the board
3. Count empty squares carefully: use single digits (1-8) for consecutive empty squares
4. NEVER use double digits like "11" for two empty squares - use "2" instead
5. Verify each row sums to exactly 8 before writing the FEN

STEP-BY-STEP PROCESS:
1. Identify the board orientation (white on bottom or black on bottom)
2. Read from top rank (rank 8) to bottom rank (rank 1)
3. For each rank:
   - Count all pieces (R, N, B, Q, K, P for white; r, n, b, q, k, p for black)
   - Count all empty squares (represented by numbers 1-8)
   - Verify: pieces + empty squares = 8
4. Determine active color (w = white to move, b = black to move)
5. Determine castling rights (KQkq for all, or specific letters, or - for none)
6. Determine en passant square (specific square like e3, or - for none)
7. Count halfmove clock (number of halfmoves since last capture/pawn move)
8. Count fullmove number (starts at 1, increments after black's move)

FEN FORMAT (6 fields separated by spaces):
[position: 8 rows separated by /] [turn: w or b] [castling: KQkq or -] [en passant: square or -] [halfmove: number] [fullmove: number]

FINAL VALIDATION CHECKLIST (verify before responding):
✓ Exactly 8 rows separated by /
✓ Each row contains exactly 8 squares
✓ Exactly 1 white king (K) found
✓ Exactly 1 black king (k) found
✓ 6 space-separated fields total
✓ No invalid characters
✓ No double-digit empty square notation (use single digits only)

Example starting position:
rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1

IMPORTANT: Respond with ONLY the FEN string, no explanations, no markdown, no code blocks, just the raw FEN string."""
        
        # Send to Gemini
        response = model.generate_content([prompt, img])
        
        # Extract FEN from response
        # Try to extract FEN from response (might have extra text)
        response_text = response.text.strip()
        
        # Try to find FEN pattern in response (might have explanations)
        # Look for FEN pattern: 8 fields separated by spaces, with '/' in first field
        fen_pattern = r'([rnbqkpRNBQKP1-8]+/[rnbqkpRNBQKP1-8/]+)\s+([bw])\s+([KQkq-]+)\s+([a-h1-8-]+)\s+(\d+)\s+(\d+)'
        match = re.search(fen_pattern, response_text)
        
        if match:
            fen = match.group(0).strip()
        else:
            # Fallback: use first line or whole response
            fen = response_text.split('\n')[0].strip()
        
        # Validate FEN using proper validation function
        if validate_fen(fen):
            short_log(f"✅ FEN extracted and validated by Gemini: {fen}")
            return fen
        else:
            # Log more details about why validation failed
            short_log(f"⚠️ Gemini response doesn't seem like a valid FEN: {fen}")
            short_log(f"   FEN length: {len(fen)}, Parts: {len(fen.split())}")
            
            # Try to clean up common issues
            # Remove markdown code blocks if present
            fen_cleaned = fen.replace('```', '').replace('`', '').strip()
            # Remove any leading/trailing punctuation
            fen_cleaned = fen_cleaned.strip('.,;:!?')
            
            if validate_fen(fen_cleaned):
                short_log(f"✅ FEN validated after cleaning: {fen_cleaned}")
                return fen_cleaned
            
            # If python-chess is available, try to get more specific error info
            try:
                import chess
                try:
                    chess.Board(fen_cleaned)
                except ValueError as e:
                    short_log(f"   Validation error: {str(e)}")
            except:
                pass
            
            # Last resort: validate FEN format manually and try to fix common errors
            parts = fen_cleaned.split()
            if '/' in fen_cleaned and len(parts) >= 6:
                position_part = parts[0]
                rows = position_part.split('/')
                
                if len(rows) == 8:
                    # Check each row has exactly 8 squares
                    valid_rows = True
                    row_errors = []
                    
                    for i, row in enumerate(rows):
                        square_count = 0
                        for char in row:
                            if char.isdigit():
                                square_count += int(char)
                            elif char in 'rnbqkpRNBQKP':
                                square_count += 1
                            else:
                                valid_rows = False
                                row_errors.append(f"Row {8-i}: invalid character '{char}'")
                                break
                        
                        if square_count != 8:
                            valid_rows = False
                            row_errors.append(f"Row {8-i}: has {square_count} squares (need 8): '{row}'")
                    
                    # Check for correct number of kings
                    white_kings = position_part.count('K')
                    black_kings = position_part.count('k')
                    
                    if white_kings != 1:
                        valid_rows = False
                        row_errors.append(f"Has {white_kings} white king(s), need exactly 1")
                    if black_kings != 1:
                        valid_rows = False
                        row_errors.append(f"Has {black_kings} black king(s), need exactly 1")
                    
                    # Check for invalid piece positions (kings in wrong positions)
                    # Kings should be on e1 (white) and e8 (black) in starting position, but can be anywhere in game
                    # However, check for obvious errors like multiple kings of same color
                    if white_kings > 1 or black_kings > 1:
                        valid_rows = False
                        row_errors.append(f"Multiple kings of same color detected")
                    
                    # Check for invalid piece characters
                    valid_pieces = set('rnbqkpRNBQKP12345678')
                    for i, row in enumerate(rows):
                        invalid_chars = [c for c in row if c not in valid_pieces]
                        if invalid_chars:
                            valid_rows = False
                            row_errors.append(f"Row {8-i}: invalid characters {set(invalid_chars)}")
                            break
                    
                    if valid_rows:
                        short_log(f"⚠️ FEN format validated manually (python-chess rejected it). Returning: {fen_cleaned}")
                        return fen_cleaned
                    else:
                        short_log(f"❌ FEN validation failed:")
                        for error in row_errors[:3]:  # Show first 3 errors
                            short_log(f"   - {error}")
                        
                        # Try to auto-fix common issues
                        fen_fixed = _try_fix_fen(fen_cleaned)
                        if fen_fixed:
                            # Validate the fixed FEN
                            if validate_fen(fen_fixed):
                                short_log(f"🔧 Auto-fixed FEN and validated: {fen_fixed}")
                                return fen_fixed
                            else:
                                # Try manual validation
                                fixed_parts = fen_fixed.split()
                                if len(fixed_parts) >= 6:
                                    fixed_pos = fixed_parts[0]
                                    fixed_rows_check = fixed_pos.split('/')
                                    if len(fixed_rows_check) == 8:
                                        all_valid = True
                                        for r in fixed_rows_check:
                                            count = sum(int(c) if c.isdigit() else 1 for c in r if c.isdigit() or c in 'rnbqkpRNBQKP')
                                            if count != 8:
                                                all_valid = False
                                                break
                                        if all_valid and fixed_pos.count('K') == 1 and fixed_pos.count('k') == 1:
                                            short_log(f"🔧 Auto-fixed FEN (manual validation): {fen_fixed}")
                                            return fen_fixed
                else:
                    short_log(f"❌ FEN has {len(rows)} rows instead of 8.")
            
            return None  # Don't return invalid FEN
            
    except Exception as e:
        error_msg = str(e)
        # Handle specific API errors
        if '429' in error_msg or 'quota' in error_msg.lower() or 'rate limit' in error_msg.lower():
            short_log(f"❌ Error: API rate limit exceeded. Please wait before retrying.")
        elif '401' in error_msg or '403' in error_msg or 'unauthorized' in error_msg.lower():
            short_log(f"❌ Error: Invalid API key or unauthorized access.")
        elif 'timeout' in error_msg.lower():
            short_log(f"❌ Error: Request timeout. The API took too long to respond.")
        else:
            short_log(f"❌ Error using Gemini Vision: {error_msg}")
        return None


def extract_fen_with_retry(image_path: str = None, image_array: np.ndarray = None, max_retries: int = 2) -> Optional[str]:
    """
    Attempts to extract FEN with retries in case of failure.
    Uses exponential backoff and improved error handling.
    
    Args:
        image_path: Path to the image
        image_array: Numpy array of the image
        max_retries: Maximum number of retries (default 2, recommended 2-3)
    
    Returns:
        FEN string or None
    """
    last_error = None
    
    for attempt in range(max_retries):
        try:
            fen = extract_fen_from_image(image_path, image_array)
            
            if fen:
                # Validate FEN before returning
                if validate_fen(fen):
                    short_log(f"✅ FEN validated successfully on attempt {attempt + 1}")
                    return fen
                else:
                    # Try to fix common issues
                    fixed_fen = _try_fix_fen(fen)
                    if fixed_fen and validate_fen(fixed_fen):
                        short_log(f"🔧 FEN auto-fixed and validated on attempt {attempt + 1}")
                        return fixed_fen
                    else:
                        short_log(f"⚠️ FEN from attempt {attempt + 1} failed validation")
                        if attempt < max_retries - 1:
                            short_log(f"🔄 Retrying with improved prompt...")
            
            # If we get here, extraction failed or validation failed
            if attempt < max_retries - 1:
                # Exponential backoff: 0.5s, 1s, 2s...
                delay = 0.5 * (2 ** attempt)
                short_log(f"🔄 Retrying in {delay:.1f}s... (attempt {attempt + 2}/{max_retries})")
                time.sleep(delay)
                
        except Exception as e:
            last_error = str(e)
            error_msg = str(e)
            
            # Handle specific API errors
            if '429' in error_msg or 'quota' in error_msg.lower() or 'rate limit' in error_msg.lower():
                short_log(f"❌ API rate limit exceeded. Waiting longer before retry...")
                if attempt < max_retries - 1:
                    time.sleep(2.0 * (2 ** attempt))  # Longer wait for rate limits
                continue
            elif '401' in error_msg or '403' in error_msg or 'unauthorized' in error_msg.lower():
                short_log(f"❌ API authentication error. Check your GEMINI_API_KEY")
                return None  # Don't retry auth errors
            elif 'timeout' in error_msg.lower():
                short_log(f"⚠️ Request timeout on attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    time.sleep(1.0)
                continue
            else:
                short_log(f"⚠️ Error on attempt {attempt + 1}: {error_msg[:100]}")
                if attempt < max_retries - 1:
                    time.sleep(0.5 * (2 ** attempt))
                continue
    
    if last_error:
        short_log(f"❌ All {max_retries} attempts failed. Last error: {last_error[:200]}")
    else:
        short_log(f"❌ All {max_retries} attempts failed to extract valid FEN")
    
    return None
