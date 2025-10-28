import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
STOCKFISH_PATH = os.path.join(ROOT, 'stockfish', 'stockfish.exe')
TESSERACT_CMD = 'tesseract'  # override on systems where tesseract is in a custom location
