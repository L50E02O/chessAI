import os
from dotenv import load_dotenv

load_dotenv()

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
STOCKFISH_PATH=r"C:\Users\leoan\Downloads\stockfish-windows-x86-64-avx2\stockfish\stockfish-windows-x86-64-avx2.exe"
TESSERACT_CMD = 'tesseract'  # override on systems where tesseract is in a custom location

# Google Gemini API Key
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')  # Set in .env file