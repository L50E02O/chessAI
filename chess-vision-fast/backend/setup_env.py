import os

# 1. Create .env
env_content = """STOCKFISH_PATH=
STOCKFISH_DEPTH=15
STOCKFISH_AUTO_DOWNLOAD=true
MAX_UPLOAD_SIZE=5242880
ALLOWED_ORIGINS=["http://localhost:5173"]
"""
# We write to .env even if it exists, or maybe check?
# For now, overwrite to ensure correct config.
with open(".env", "w") as f:
    f.write(env_content)
print("Created .env")
print("IMPORTANTE: Stockfish se auto-descarga en el primer analisis (Windows) o usa STOCKFISH_PATH si apunta a un binario existente.")
