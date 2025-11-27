import os

# 1. Create .env
env_content = """GEMINI_API_KEY=tu_api_key_aqui
GEMINI_MODEL=gemini-1.5-flash
MAX_UPLOAD_SIZE=5242880
ALLOWED_ORIGINS=["http://localhost:5173"]
"""
# We write to .env even if it exists, or maybe check?
# For now, overwrite to ensure correct config.
with open(".env", "w") as f:
    f.write(env_content)
print("Created .env")
print("IMPORTANTE: Edita .env y agrega tu GEMINI_API_KEY de https://aistudio.google.com/apikey")
