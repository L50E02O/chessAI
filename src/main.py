import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pynput import keyboard
from src.desktop_capture import capture_fullscreen
from src.ocr.board_detection import detect_board_from_image
from src.ocr.gemini_vision import extract_fen_with_retry
from src.engine.stockfish_engine import get_best_move_for_fen
from src.utils.helpers import short_log

HOTKEY = '<ctrl>+q'

def on_activate():
    short_log('=' * 60)
    short_log('🎯 Capturando pantalla...')
    
    # 1. Capturar pantalla
    img = capture_fullscreen()
    short_log(f'✅ Captura completada: {img.shape}')
    
    # 2. Intentar extraer FEN con Gemini Vision
    short_log('🤖 Enviando imagen a Google Gemini para análisis...')
    fen = extract_fen_with_retry(image_array=img, max_retries=2)
    
    # 3. Si Gemini falla, usar el método tradicional de detección
    if not fen or '/' not in fen:
        short_log('⚠️ Gemini no pudo extraer FEN, usando método tradicional de detección...')
        import tempfile
        import cv2
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            cv2.imwrite(tmp.name, img)
            image_path = tmp.name
        short_log(f'📁 Imagen guardada temporalmente en: {image_path}')
        fen = detect_board_from_image(image_path)
        try:
            os.unlink(image_path)
        except:
            pass
    
    if not fen:
        short_log('❌ No se pudo detectar ningún tablero de ajedrez en la imagen')
        short_log('=' * 60)
        return
    
    short_log(f'♟️ FEN detectado: {fen}')
    
    # 4. Obtener mejor jugada con Stockfish
    short_log('🧠 Analizando posición con Stockfish...')
    move = get_best_move_for_fen(fen)
    
    if move:
        short_log(f'✨ Mejor jugada sugerida: {move}')
    else:
        short_log('❌ No se pudo obtener una jugada de Stockfish')
    
    short_log('=' * 60)

def main():
    short_log('🚀 ChessAI iniciado')
    short_log(f'⌨️ Escuchando atajo {HOTKEY}. Presiona ESC para salir.')
    short_log('=' * 60)
    
    with keyboard.GlobalHotKeys({HOTKEY: on_activate}) as h:
        def on_press(key):
            if key == keyboard.Key.esc:
                short_log('👋 Saliendo...')
                h.stop()
                return False
        with keyboard.Listener(on_press=on_press):
            h.join()

if __name__ == '__main__':
    main()
