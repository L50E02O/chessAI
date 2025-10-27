import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
STOCKFISH_PATH = os.path.join(ROOT, 'stockfish', 'stockfish.exe')
# On Android this path will not be valid: mobile apps should bundle a native engine or call a service.
TESSERACT_CMD = 'tesseract'  # override on systems where tesseract is in a custom location
