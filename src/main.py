import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pynput import keyboard
from src.desktop_capture import capture_fullscreen
from src.ocr.board_detection import detect_board_from_image
from src.engine.stockfish_engine import get_best_move_for_fen
from src.utils.helpers import short_log

HOTKEY = '<ctrl>+a'

def on_activate():
    short_log('Capturando pantalla y detectando tablero...')
    import tempfile
    import cv2
    img = capture_fullscreen()
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        cv2.imwrite(tmp.name, img)
        image_path = tmp.name
    short_log(f'Imagen guardada temporalmente en: {image_path}')
    fen = detect_board_from_image(image_path)
    short_log(f'FEN detectado: {fen}')
    move = get_best_move_for_fen(fen)
    short_log(f'Mejor jugada sugerida: {move}')

def main():
    short_log(f'Escuchando atajo {HOTKEY}. Presiona ESC o Ctrl+C para salir.')
    with keyboard.GlobalHotKeys({HOTKEY: on_activate}) as h:
        def on_press(key):
            if key == keyboard.Key.esc:
                h.stop()
                return False
        with keyboard.Listener(on_press=on_press):
            h.join()

if __name__ == '__main__':
    main()
