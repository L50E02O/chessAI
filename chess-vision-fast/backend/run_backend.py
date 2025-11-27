import subprocess
import sys

print("Starting backend...")
try:
    with open("backend.log", "w") as f:
        subprocess.run([sys.executable, "-m", "uvicorn", "app.main:app", "--reload"], stdout=f, stderr=f)
except Exception as e:
    print(f"Error: {e}")
