import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import threading
from pynput import keyboard
from src.desktop_capture import capture_fullscreen
from src.region_selector import select_region, capture_region, has_saved_region
from src.ocr.board_detection import detect_board_from_image
from src.ocr.gemini_vision import extract_fen_with_retry
from src.engine.stockfish_engine import get_best_move_for_fen
from src.utils.helpers import short_log

HOTKEY = '<ctrl>+q'

def process_capture():
    """Processes the capture in a separate thread to avoid blocking the hotkey listener"""
    try:
        short_log('=' * 60)
        
        # Check if there's a saved region
        if not has_saved_region():
            short_log('📌 First time: Select the board region')
            short_log('   1. Drag the mouse over the board')
            short_log('   2. Press ENTER to confirm')
            region = select_region()
            if not region:
                short_log('❌ Selection cancelled')
                short_log('=' * 60)
                return
            short_log('✅ Region saved for future captures')
        
        short_log('🎯 Capturing board...')
        
        # Capture only the board region
        img = capture_region()
        short_log(f'✅ Capture completed: {img.shape}')
        
        # 2. Try to extract FEN with Gemini Vision (improved retry logic)
        fen = extract_fen_with_retry(image_array=img, max_retries=2)  # 2 retries with exponential backoff
        
        # 3. If Gemini fails, use traditional detection method
        if not fen or '/' not in fen:
            short_log('⚠️ Gemini could not extract FEN, using traditional detection method...')
            import tempfile
            import cv2
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                cv2.imwrite(tmp.name, img)
                image_path = tmp.name
            short_log(f'📁 Image saved temporarily at: {image_path}')
            fen = detect_board_from_image(image_path)
            try:
                os.unlink(image_path)
            except:
                pass
        
        if not fen:
            short_log('❌ Could not detect any chess board in the image')
            short_log('=' * 60)
            return
        
        short_log(f'♟️ FEN detected: {fen}')
        
        # 4. Validate FEN before sending to Stockfish (with detailed error messages)
        from src.ocr.fen_generator import validate_fen_with_error
        is_valid, error_msg = validate_fen_with_error(fen)
        if not is_valid:
            short_log(f'❌ FEN is invalid: {error_msg}')
            short_log('=' * 60)
            return
        
        # 5. Get best move with Stockfish
        short_log('🧠 Analyzing position with Stockfish...')
        try:
            move = get_best_move_for_fen(fen, depth=12)  # Slightly reduced depth for faster response
            
            if move:
                short_log(f'✨ Best move suggested: {move}')
            else:
                short_log('❌ Could not get a move from Stockfish')
                short_log('   This might indicate checkmate, stalemate, or an engine error')
        except Exception as e:
            short_log(f'❌ Error during Stockfish analysis: {str(e)}')
            import traceback
            traceback.print_exc()
        
        short_log('=' * 60)
    
    except Exception as e:
        short_log(f'❌ Unexpected error: {str(e)}')
        short_log('=' * 60)
        import traceback
        traceback.print_exc()

def on_activate():
    """Starts processing in a separate thread to avoid blocking the hotkey"""
    thread = threading.Thread(target=process_capture, daemon=True)
    thread.start()

def main():
    short_log('🚀 ChessAI started')
    short_log(f'⌨️ Listening for shortcut {HOTKEY}. Press ESC to exit.')
    
    if not has_saved_region():
        short_log('ℹ️ First time: Press Ctrl+Q to select the board area')
    
    short_log('=' * 60)
    
    # Variable to control the loop
    running = True
    
    def on_press(key):
        nonlocal running
        if key == keyboard.Key.esc:
            short_log('👋 Exiting...')
            running = False
            return False
    
    # Create ESC listener
    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    
    # Create hotkey handler
    try:
        with keyboard.GlobalHotKeys({HOTKEY: on_activate}) as h:
            while running and listener.is_alive():
                # Short sleep to allow ESC to be processed
                import time
                time.sleep(0.1)
    except KeyboardInterrupt:
        short_log('👋 Interrupted by user')
    finally:
        # Stop listener on exit
        listener.stop()

if __name__ == '__main__':
    main()
