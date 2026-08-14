"""Downloads the chess.com 'neo' piece set (150px PNGs) into app/assets/pieces.

Only needed once; assets are committed to the repo so the app runs offline.
"""
import urllib.request
from pathlib import Path

PIECES = ['wP', 'wN', 'wB', 'wR', 'wQ', 'wK', 'bP', 'bN', 'bB', 'bR', 'bQ', 'bK']
BASE_URL = 'https://images.chesscomfiles.com/chess-themes/pieces/neo/150/'
OUT = Path(__file__).resolve().parents[1] / 'app' / 'assets' / 'pieces'


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for piece in PIECES:
        dest = OUT / f'{piece}.png'
        if dest.exists() and dest.stat().st_size > 0:
            print(f'Exists: {dest}')
            continue
        url = BASE_URL + piece.lower() + '.png'
        print(f'Downloading {url}')
        urllib.request.urlretrieve(url, dest)


if __name__ == '__main__':
    main()
