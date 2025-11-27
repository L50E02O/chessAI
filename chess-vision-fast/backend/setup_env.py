import os
import urllib.request
import zipfile

# 1. Create .env
env_content = """DETECTION_BACKEND=lichess
YOLO_MODEL_PATH=./models/yolov8-chess.pt
STOCKFISH_PATH=./stockfish/stockfish-16-windows-x86-64-avx2/stockfish-windows-x86-64-avx2.exe
MAX_UPLOAD_SIZE=5242880
ALLOWED_ORIGINS=["http://localhost:5173"]
"""
# We write to .env even if it exists, or maybe check?
# For now, overwrite to ensure correct config.
with open(".env", "w") as f:
    f.write(env_content)
print("Created .env")

# 2. Download Stockfish
if not os.path.exists("stockfish"):
    os.makedirs("stockfish")

stockfish_url = "https://github.com/official-stockfish/Stockfish/releases/download/sf_16/stockfish-16-windows-x86-64-avx2.zip"
zip_path = "stockfish/stockfish.zip"
extract_path = "stockfish"

if not os.path.exists(zip_path):
    print(f"Downloading Stockfish from {stockfish_url}...")
    try:
        urllib.request.urlretrieve(stockfish_url, zip_path)
        print("Downloaded Stockfish.")
        
        print("Extracting Stockfish...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        print("Extracted Stockfish.")
    except Exception as e:
        print(f"Failed to download Stockfish: {e}")
else:
    print("Stockfish zip already exists.")
