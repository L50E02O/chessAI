import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pynput import keyboard
from src.desktop_capture import handle_capture_and_upload
from src.utils.helpers import short_log

HOTKEY = '<ctrl>+x'


def on_activate():
    short_log('Atajo presionado: capturando, recortando y subiendo...')
    url = handle_capture_and_upload()
    if url:
        short_log(f'Listo. URL: {url}')
    else:
        short_log('Ocurrió un error durante el proceso.')


def main():
    short_log(f'Escuchando atajo {HOTKEY}. Presiona ESC para salir.')
    with keyboard.GlobalHotKeys({HOTKEY: on_activate}) as h:
        # Listener adicional para salir con ESC
        def on_press(key):
            if key == keyboard.Key.esc:
                h.stop()
                return False
        with keyboard.Listener(on_press=on_press):
            h.join()


if __name__ == '__main__':
    main()
