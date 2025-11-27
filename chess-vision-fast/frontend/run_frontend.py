import subprocess
import sys

print("Starting frontend...")
try:
    with open("frontend.log", "w") as f:
        # Use shell=True to find npm in path
        subprocess.run(["npm", "run", "dev"], stdout=f, stderr=f, shell=True)
except Exception as e:
    print(f"Error: {e}")
