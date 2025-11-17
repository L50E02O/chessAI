import os
from dotenv import load_dotenv

load_dotenv()

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
# Optional explicit path to Stockfish binary (override via .env)
# If left empty, the engine will try to auto-detect it (PATH/external folder).
STOCKFISH_PATH = os.getenv('STOCKFISH_PATH', '')
# Official Windows download for Stockfish (AVX2 build)
STOCKFISH_DOWNLOAD_URL = os.getenv(
	'STOCKFISH_DOWNLOAD_URL',
	'https://github.com/official-stockfish/Stockfish/releases/latest/download/stockfish-windows-x86-64-avx2.zip'
)
TESSERACT_CMD = 'tesseract'  # override on systems where tesseract is in a custom location

# Google Gemini API Key
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')  # Set in .env file