"""Entry point for the mobile Kivy app.

This file is runnable both as a script (python src/main_kivy.py) and as a module
(python -m src.main_kivy). When executed as a script Python puts `src/` on
sys.path which prevents importing the top-level `src` package; we add the
project root to sys.path so `import src...` works either way.
"""
import os
import sys

# Ensure project root is on sys.path so `import src...` works when running
# `python src/main_kivy.py` from the repository root.
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.ui.mobile_app import MobileApp


def main():
    MobileApp().run()


if __name__ == '__main__':
    main()
