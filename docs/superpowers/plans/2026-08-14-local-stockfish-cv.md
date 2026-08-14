# Local Stockfish + Classical CV Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Gemini pipeline in `chess-vision-fast` with a fully local pipeline: a classical computer-vision algorithm extracts a FEN from a chess.com screenshot, and a local Stockfish binary returns the best move, score, and principal variation.

**Architecture:** A FastAPI backend runs a pure-OpenCV detector (`cv_detector.py`) that finds the board, warps perspective, segments an 8x8 grid, detects occupancy by color, and classifies pieces by template matching against the bundled chess.com "neo" piece set. A `StockfishEngine` (python-chess `SimpleEngine`) analyzes the position. A `StockfishService` maintains game context (turn, castling, en passant) and generates evaluation text from the score. The React frontend drops the model selector/retrospective and shows evaluation data + move history.

**Tech Stack:** Python 3.12+, FastAPI, OpenCV (`cv2` 4.x), Pillow, NumPy, python-chess (`chess.engine`), React 18 + Vite + Tailwind.

## Global Constraints

- All backend checks run with pytest from `chess-vision-fast/backend`: `python -m pytest tests/ -q` (tests append `chess-vision-fast` to `sys.path` and import as `backend.app.*` — follow the pattern in `tests/test_fen.py`).
- Test imports use `from backend.app...` after the `sys.path.append` boilerplate shown in Task 1.
- Use the existing settings pattern in `backend/app/utils.py` (pydantic-settings `BaseSettings`).
- No LLM anywhere: no `google-generativeai`, no `GEMINI_API_KEY`, no Gemini model names.
- Windows-first for the auto-download path; keep path detection cross-platform.
- FEN piece letters: `P N B R Q K` white, lowercase black (python-chess convention).
- The default chess.com "neo" piece set is the classification reference.
- Do NOT add code comments beyond module docstrings and short inline notes where the existing code style has them.

## Plan Corrections (implemented during Tasks 3-4)

The following deviations from the original Task 3/4 code were validated on the synthetic renders (START, MIDGAME, START-flip; 32/32 pieces correct in each) and are now the reference implementation:

1. **Board detection** (`find_board`): detects the playable interior via green-frame segmentation (`_interior_quad`), snap-to-480 and `INTER_NEAREST` warp; the outer-contour approach is the fallback (`_find_board_contours`). `_verify_board` is applied only to the fallback path and tolerates up to 8 vertical-luminance violations (full piece sets break the old <=4 alternation check).
2. **`square_state`**: occupancy uses the cell **median** as background (the empty square dominates >50% of the cell); occupied when `|cell - square_color| > 25` covers `>= 5%` of the cell; piece color = luminance of the **piece pixels only** vs the mid of light/dark luminance.
3. **`_extract_piece`**: background estimated from the cell **median** (not corners); background pixels inside the piece bbox are zeroed before classification.
4. **`_template_piece`**: template's transparent background pixels (`alpha <= 30`) are zeroed so residual RGB under the alpha channel does not corrupt matching (black-piece bug).
5. **`empty_colors`**: deterministic — `cv2.setRNGSeed(42)` before k-means, 10 attempts.
6. **Renderer `white_top`**: the synthetic renderer flips the board with a true 180° rotation (`chess.square(7 - c, r)`), matching the `matrix_to_fen(orientation='w-top')` semantics (`[row[::-1] for row in reversed(matrix)]`). Using `chess.square_mirror` (vertical mirror) produced a physically impossible view and swapped K/Q in the flipped detection.

`find_board` still returns `(480, 480, 3)` BGR boards or `None`; the other public interfaces are unchanged.

7. **Task 7 `test_compute_castling` FEN fixed** (verified empirically): the original `'r1bqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR'` retains all 4 rooks + both kings, so `compute_castling` returns `'KQkq'`, not `'Qq'`. The `'Qq'` expectation requires only a/h rooks: `'r3k3/8/8/8/8/8/8/R3K3'`.

---

### Task 1: FEN matrix orientation support

**Files:**
- Modify: `chess-vision-fast/backend/app/fen.py`
- Test: `chess-vision-fast/backend/tests/test_fen.py` (append)

**Interfaces:**
- Consumes: nothing.
- Produces: `matrix_to_fen(matrix, active_color='w', castling='KQkq', en_passant='-', halfmove_clock=0, fullmove_number=1, orientation='w-bottom') -> str`. `matrix` is 8x8 in **image order** (`matrix[0]` = top row of the image). `orientation='w-bottom'` = white at the bottom (standard chess.com view); `'w-top'` = board flipped 180° (white at the top). Always returns a FEN whose first row is rank 8.

- [ ] **Step 1: Write the failing test**

Append to `chess-vision-fast/backend/tests/test_fen.py`:

```python
def test_matrix_to_fen_w_top_orientation():
    matrix = [['' for _ in range(8)] for _ in range(8)]
    matrix[0][0] = 'P'   # image top-left corner
    matrix[7][7] = 'p'   # image bottom-right corner
    fen = matrix_to_fen(matrix, orientation='w-top')
    ranks = fen.split()[0].split('/')
    assert ranks[0] == 'p7', f'rank 8 must start at a8 with the black piece, got {ranks[0]}'
    assert ranks[7] == '7P', f'rank 1 must end at h1 with the white piece, got {ranks[7]}'


def test_matrix_to_fen_w_bottom_default():
    matrix = [['' for _ in range(8)] for _ in range(8)]
    matrix[0][0] = 'k'   # image top-left corner (a8)
    matrix[7][7] = 'K'   # image bottom-right corner (h1)
    fen = matrix_to_fen(matrix)
    ranks = fen.split()[0].split('/')
    assert ranks[0] == 'k7', ranks[0]
    assert ranks[7] == '7K', ranks[7]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_fen.py -q`
Expected: FAIL — `TypeError: matrix_to_fen() got an unexpected keyword argument 'orientation'`

- [ ] **Step 3: Implement orientation support**

Edit `chess-vision-fast/backend/app/fen.py` — change the `matrix_to_fen` signature and add the orientation mapping at the top of the function:

```python
def matrix_to_fen(matrix: list[list[str]], active_color: str = 'w', castling: str = 'KQkq', en_passant: str = '-', halfmove_clock: int = 0, fullmove_number: int = 1, orientation: str = 'w-bottom') -> str:
    if orientation == 'w-top':
        matrix = [row[::-1] for row in reversed(matrix)]
    rows = []
    for row in matrix:
        empties = 0
        row_parts = []
        for cell in row:
            if not cell:
                empties += 1
                continue
            if empties:
                row_parts.append(str(empties))
                empties = 0
            row_parts.append(cell)
        if empties:
            row_parts.append(str(empties))
        rows.append(''.join(row_parts) or '8')
    return '/'.join(rows) + f' {active_color} {castling} {en_passant} {halfmove_clock} {fullmove_number}'
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_fen.py -q`
Expected: PASS (all 4 tests)

- [ ] **Step 5: Commit**

```bash
git add chess-vision-fast/backend/app/fen.py chess-vision-fast/backend/tests/test_fen.py
git commit -m "feat: add board orientation support to FEN matrix builder"
```

---

### Task 2: Piece template assets + download script

**Files:**
- Create: `chess-vision-fast/backend/scripts/download_pieces.py`
- Create: `chess-vision-fast/backend/app/assets/pieces/README.md`
- Run once to create: `chess-vision-fast/backend/app/assets/pieces/wP.png`, `wN.png`, `wB.png`, `wR.png`, `wQ.png`, `wK.png`, `bP.png`, `bN.png`, `bB.png`, `bR.png`, `bQ.png`, `bK.png`

**Interfaces:**
- Consumes: nothing.
- Produces: `chess-vision-fast/backend/app/assets/pieces/{w,b}{P,N,B,R,Q,K}.png` — the chess.com "neo" piece set, 150px PNGs with transparency. File naming maps directly to FEN letters (`w`/`b` = color, uppercase letter = type).

- [ ] **Step 1: Write the download script**

Create `chess-vision-fast/backend/scripts/download_pieces.py`:

```python
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
        url = BASE_URL + piece + '.png'
        print(f'Downloading {url}')
        urllib.request.urlretrieve(url, dest)


if __name__ == '__main__':
    main()
```

- [ ] **Step 2: Run the script**

Run: `python chess-vision-fast/backend/scripts/download_pieces.py`
Expected: prints `Downloading ...` for each piece and creates the 12 PNGs in `chess-vision-fast/backend/app/assets/pieces/`.

- [ ] **Step 3: Add attribution README**

Create `chess-vision-fast/backend/app/assets/pieces/README.md`:

```markdown
# Piece templates

The 12 PNGs in this directory are the chess.com default "neo" piece set
(150px), downloaded from:

    https://images.chesscomfiles.com/chess-themes/pieces/neo/150/

Used as template-matching references to classify pieces detected in
chess.com screenshots. FEN mapping: `w` = white, `b` = black; the letter
is the piece type (`P N B R Q K`).

License: chess.com piece images are provided for chess UI purposes. Re-run
`backend/scripts/download_pieces.py` to regenerate.
```

- [ ] **Step 4: Verify assets exist**

Run: `Get-ChildItem chess-vision-fast/backend/app/assets/pieces/*.png | Measure-Object`
Expected: Count = 12

- [ ] **Step 5: Commit**

```bash
git add chess-vision-fast/backend/scripts/download_pieces.py chess-vision-fast/backend/app/assets/pieces
git commit -m "feat: add chess.com piece templates and download script"
```

---

### Task 3: CV board detection (BoardFinder)

**Files:**
- Create: `chess-vision-fast/backend/app/cv_detector.py`
- Create: `chess-vision-fast/backend/tests/helpers/__init__.py`
- Create: `chess-vision-fast/backend/tests/helpers/board_renderer.py`
- Create: `chess-vision-fast/backend/tests/test_cv_board.py`

**Interfaces:**
- Consumes: `chess-vision-fast/backend/app/assets/pieces/*.png` (Task 2), Pillow, cv2.
- Produces: `find_board(image: np.ndarray) -> Optional[np.ndarray]` — returns a perspective-corrected, frame-cropped 480x480 board (BGR) or `None`. Internal helpers `_order_points`, `_verify_board`, `_inner_cell`, `_luminance`, `_interior_quad`, `_warp_board`, `_find_board_contours` (see Plan Corrections).

- [ ] **Step 1: Create test helpers (synthetic board renderer)**

Create `chess-vision-fast/backend/tests/helpers/__init__.py` (empty file).

Create `chess-vision-fast/backend/tests/helpers/board_renderer.py`:

```python
"""Renders a chess.com-style board image from a FEN, for CV pipeline tests."""
from pathlib import Path

import chess
import numpy as np
from PIL import Image, ImageDraw

LIGHT = (240, 217, 181)
DARK = (181, 136, 99)
FRAME = (81, 105, 81)
PIECES_DIR = Path(__file__).resolve().parents[2] / 'backend' / 'app' / 'assets' / 'pieces'
PIECES = {
    key: Image.open(PIECES_DIR / f'{key}.png').convert('RGBA')
    for key in ['wP', 'wN', 'wB', 'wR', 'wQ', 'wK', 'bP', 'bN', 'bB', 'bR', 'bQ', 'bK']
}


def render_board(fen: str, square: int = 60, frame: int = 16, page_margin: int = 40, white_top: bool = False) -> Image.Image:
    board = chess.Board(fen)
    inner = square * 8
    img = Image.new('RGB', (inner + frame * 2 + page_margin * 2, inner + frame * 2 + page_margin * 2), (250, 250, 250))
    draw = ImageDraw.Draw(img)
    frame_x = page_margin
    frame_y = page_margin
    draw.rectangle([frame_x, frame_y, frame_x + inner + frame * 2, frame_y + inner + frame * 2], fill=FRAME)
    ox, oy = page_margin + frame, page_margin + frame
    for r in range(8):
        for c in range(8):
            color = LIGHT if (r + c) % 2 == 0 else DARK
            x0, y0 = ox + c * square, oy + r * square
            draw.rectangle([x0, y0, x0 + square, y0 + square], fill=color)
    for r in range(8):
        for c in range(8):
            if white_top:
                sq = chess.square(7 - c, r)
            else:
                sq = chess.square(c, 7 - r)
            piece = board.piece_at(sq)
            if piece is None:
                continue
            key = ('w' if piece.color == chess.WHITE else 'b') + piece.symbol().upper()
            pimg = PIECES[key].resize((square, square), Image.Resampling.LANCZOS)
            img.paste(pimg, (ox + c * square, oy + r * square), pimg)
    return img
```

- [ ] **Step 2: Write the failing test**

Create `chess-vision-fast/backend/tests/test_cv_board.py`:

```python
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import numpy as np

from backend.app.cv_detector import find_board
from tests.helpers.board_renderer import render_board


def test_find_board_on_synthetic_start_position():
    img = render_board('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1')
    board = find_board(np.array(img.convert('RGB'))[:, :, ::-1])
    assert board is not None
    assert board.shape == (480, 480, 3)
```

- [ ] **Step 3: Run test to verify it fails**

Run: `python -m pytest tests/test_cv_board.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'backend.app.cv_detector'`

- [ ] **Step 4: Implement find_board**

Create `chess-vision-fast/backend/app/cv_detector.py`:

```python
"""Classical computer-vision chess board detection for chess.com screenshots."""
import logging
from typing import Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)

TARGET_SIZE = 480
CELL = TARGET_SIZE // 8


def _order_points(pts: np.ndarray) -> np.ndarray:
    rect = np.zeros((4, 2), dtype=np.float32)
    s = pts.sum(axis=1)
    d = np.diff(pts, axis=1).ravel()
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    rect[1] = pts[np.argmin(d)]
    rect[3] = pts[np.argmax(d)]
    return rect


def _luminance(bgr) -> float:
    return 0.114 * float(bgr[0]) + 0.587 * float(bgr[1]) + 0.299 * float(bgr[2])


def _inner_cell(board: np.ndarray, r: int, c: int, ratio: float = 0.6) -> np.ndarray:
    side = int(CELL * ratio)
    x = int(c * CELL + (CELL - side) / 2)
    y = int(r * CELL + (CELL - side) / 2)
    return board[y:y + side, x:x + side]


def _verify_board(board: np.ndarray) -> bool:
    cells = np.empty((8, 8), dtype=float)
    for r in range(8):
        for c in range(8):
            cells[r, c] = _luminance(np.mean(_inner_cell(board, r, c), axis=(0, 1)))
    violations = 0
    for r in range(7):
        for c in range(8):
            if abs(cells[r, c] - cells[r + 1, c]) < 15:
                violations += 1
    return violations <= 8


def _interior_quad(image: np.ndarray) -> Optional[np.ndarray]:
    """Detect the board interior square (the playable 8x8 area) via its non-green
    extent and return its four corners, snapped to an exact TARGET_SIZE square."""
    b = image[:, :, 0].astype(np.int32)
    g = image[:, :, 1].astype(np.int32)
    r = image[:, :, 2].astype(np.int32)
    is_green = (g > r + 12) & (g > b + 12)
    non_green = (~is_green).astype(np.uint8)
    non_green = cv2.erode(non_green, np.ones((3, 3), np.uint8), iterations=2)
    n, labels, stats, cents = cv2.connectedComponentsWithStats(non_green, 8)
    if n <= 1:
        return None
    big = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    x0 = int(stats[big, cv2.CC_STAT_LEFT])
    y0 = int(stats[big, cv2.CC_STAT_TOP])
    x1 = x0 + int(stats[big, cv2.CC_STAT_WIDTH])
    y1 = y0 + int(stats[big, cv2.CC_STAT_HEIGHT])
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    half = TARGET_SIZE / 2
    x0, x1 = int(round(cx - half)), int(round(cx + half))
    y0, y1 = int(round(cy - half)), int(round(cy + half))
    if x0 < 0 or y0 < 0 or x1 > image.shape[1] or y1 > image.shape[0]:
        return None
    return np.float32([[x0, y0], [x1, y0], [x1, y1], [x0, y1]])


def _warp_board(image: np.ndarray, quad: np.ndarray) -> np.ndarray:
    dst = np.float32([[0, 0], [TARGET_SIZE, 0], [TARGET_SIZE, TARGET_SIZE], [0, TARGET_SIZE]])
    matrix = cv2.getPerspectiveTransform(quad, dst)
    return cv2.warpPerspective(image, matrix, (TARGET_SIZE, TARGET_SIZE), flags=cv2.INTER_NEAREST)


def _find_board_contours(image: np.ndarray) -> Optional[np.ndarray]:
    """Fallback board detection based on the outer 4-corner contour."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY_INV, 11, 2)
    thresh = cv2.dilate(thresh, np.ones((5, 5), np.uint8), iterations=1)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    best = None
    best_area = 0
    for contour in contours:
        peri = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
        if len(approx) != 4:
            continue
        pts = approx.reshape(4, 2).astype(np.float32)
        pts = _order_points(pts)
        side1 = float(np.linalg.norm(pts[1] - pts[0]))
        side2 = float(np.linalg.norm(pts[2] - pts[1]))
        if side1 == 0 or side2 == 0:
            continue
        aspect = max(side1, side2) / min(side1, side2)
        area = cv2.contourArea(approx)
        if 0.8 <= aspect <= 1.25 and area > best_area:
            best_area = area
            best = pts

    if best is None:
        return None
    return _warp_board(image, best)


def find_board(image: np.ndarray) -> Optional[np.ndarray]:
    quad = _interior_quad(image)
    if quad is None:
        board = _find_board_contours(image)
        if board is None:
            return None
        if not _verify_board(board):
            return None
        return board
    return _warp_board(image, quad)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_cv_board.py -q`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add chess-vision-fast/backend/app/cv_detector.py chess-vision-fast/backend/tests/helpers chess-vision-fast/backend/tests/test_cv_board.py
git commit -m "feat: add CV board detection with perspective warp and verification"
```

---

### Task 4: Square occupancy and piece classification

**Files:**
- Modify: `chess-vision-fast/backend/app/cv_detector.py`
- Create: `chess-vision-fast/backend/tests/test_cv_squares.py`

**Interfaces:**
- Consumes: `find_board` + `_inner_cell`/`_luminance` (Task 3).
- Produces:
  - `empty_colors(board: np.ndarray) -> Tuple[np.ndarray, np.ndarray]` — (light, dark) BGR square colors.
  - `square_state(cell: np.ndarray, light, dark) -> Tuple[bool, Optional[str]]` — `(occupied, piece_color)` where `piece_color` is `'w'` or `'b'`.
  - `classify_piece(cell: np.ndarray, piece_color: str) -> Optional[Tuple[str, float]]` — `(letter, score)` or `None`.

- [ ] **Step 1: Write the failing tests**

Create `chess-vision-fast/backend/tests/test_cv_squares.py`:

```python
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import numpy as np

from backend.app.cv_detector import classify_piece, empty_colors, square_state
from tests.helpers.board_renderer import render_board, LIGHT, DARK


def _empty_cell(color):
    cell = np.zeros((60, 60, 3), dtype=np.uint8)
    cell[:] = color
    return cell


def test_empty_colors_on_synthetic_board():
    img = np.array(render_board('4k3/8/8/8/8/8/8/4K3 w - - 0 1').convert('RGB'))[:, :, ::-1]
    light, dark = empty_colors(img)
    assert light.shape == (3,)
    assert dark.shape == (3,)


def test_square_state_empty():
    light = np.array(LIGHT, dtype=np.float32)
    dark = np.array(DARK, dtype=np.float32)
    occupied, color = square_state(_empty_cell(LIGHT), light, dark)
    assert occupied is False
    assert color is None


def test_square_state_occupied():
    light = np.array(LIGHT, dtype=np.float32)
    dark = np.array(DARK, dtype=np.float32)
    cell = _empty_cell(LIGHT)
    cell[10:50, 10:50] = (30, 30, 30)
    occupied, color = square_state(cell, light, dark)
    assert occupied is True
    assert color == 'b'


def test_classify_piece_white_queen():
    img = np.array(render_board('8/8/8/8/8/8/8/3QK3 w - - 0 1').convert('RGB'))[:, :, ::-1]
    # d1 square: renderer offsets board interior by (frame + page_margin) = 56, so cell rows 476:536, cols 236:296
    cell = img[476:536, 236:296]
    letter, score = classify_piece(cell, 'w')
    assert letter == 'Q'
    assert score > 0.5
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_cv_squares.py -q`
Expected: FAIL with `ImportError: cannot import name 'empty_colors'`

- [ ] **Step 3: Implement occupancy + classification**

Append to `chess-vision-fast/backend/app/cv_detector.py`:

```python
from pathlib import Path

PIECES_DIR = Path(__file__).resolve().parent / 'assets' / 'pieces'
TEMPLATE_SIZE = 128
PIECE_LETTERS = ['P', 'N', 'B', 'R', 'Q', 'K']
_TEMPLATES = {}


def _load_templates() -> dict:
    global _TEMPLATES
    if _TEMPLATES:
        return _TEMPLATES
    for letter in PIECE_LETTERS:
        for color in ('w', 'b'):
            path = PIECES_DIR / f'{color}{letter}.png'
            img = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
            if img is not None:
                _TEMPLATES.setdefault(letter, {})[color] = img
    return _TEMPLATES


def empty_colors(board: np.ndarray, k: int = 4) -> Tuple[np.ndarray, np.ndarray]:
    pixels = board.reshape(-1, 3).astype(np.float32)[::4]
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    cv2.setRNGSeed(42)
    _, labels, centers = cv2.kmeans(pixels, k, None, criteria, 10, cv2.KMEANS_PP_CENTERS)
    counts = np.bincount(labels.ravel(), minlength=k)
    order = np.argsort(-counts)
    colors = [centers[order[0]], centers[order[1]]]
    if _luminance(colors[0]) < _luminance(colors[1]):
        colors.reverse()
    return colors[0], colors[1]


def square_state(cell: np.ndarray, light, dark) -> Tuple[bool, Optional[str]]:
    bg = np.median(cell.reshape(-1, 3), axis=0)
    sq = light if np.linalg.norm(bg - light) < np.linalg.norm(bg - dark) else dark
    mask = np.linalg.norm(cell.astype(np.float32) - sq, axis=2) > 25
    if mask.mean() < 0.05:
        return False, None
    mean = np.mean(cell[mask], axis=0)
    mid = (_luminance(light) + _luminance(dark)) / 2
    return True, ('w' if _luminance(mean) > mid else 'b')


def _extract_piece(cell: np.ndarray, margin: int = 3) -> Optional[np.ndarray]:
    h, w = cell.shape[:2]
    bg = np.median(cell.reshape(-1, 3), axis=0)
    mask = np.linalg.norm(cell.astype(np.float32) - bg, axis=2) > 25
    ys, xs = np.where(mask)
    if len(ys) < 20:
        return None
    y0, y1 = max(0, ys.min() - margin), min(h, ys.max() + margin + 1)
    x0, x1 = max(0, xs.min() - margin), min(w, xs.max() + margin + 1)
    piece = cell[y0:y1, x0:x1].copy()
    piece[~mask[y0:y1, x0:x1]] = 0
    return piece


def _template_piece(img: np.ndarray) -> Optional[np.ndarray]:
    if img.shape[2] == 4:
        alpha = img[:, :, 3]
        ys, xs = np.where(alpha > 30)
        if len(ys) == 0:
            return None
        crop = img[ys.min():ys.max() + 1, xs.min():xs.max() + 1].copy()
        transparent = alpha[ys.min():ys.max() + 1, xs.min():xs.max() + 1] <= 30
        crop[transparent] = 0
        return crop
    return img


def classify_piece(cell: np.ndarray, piece_color: str) -> Optional[Tuple[str, float]]:
    extracted = _extract_piece(cell)
    if extracted is None:
        return None
    extracted = cv2.resize(extracted, (TEMPLATE_SIZE, TEMPLATE_SIZE))
    extracted_gray = cv2.cvtColor(extracted, cv2.COLOR_BGR2GRAY)
    best_letter = None
    best_score = -1.0
    for letter, by_color in _load_templates().items():
        tpl = by_color.get(piece_color)
        if tpl is None:
            continue
        tpiece = _template_piece(tpl)
        if tpiece is None:
            continue
        tpiece = cv2.resize(tpiece, (TEMPLATE_SIZE, TEMPLATE_SIZE))
        tpiece_gray = cv2.cvtColor(tpiece, cv2.COLOR_BGR2GRAY)
        score = float(cv2.matchTemplate(extracted_gray, tpiece_gray, cv2.TM_CCOEFF_NORMED)[0][0])
        if score > best_score:
            best_score = score
            best_letter = letter
    if best_letter is None or best_score < 0.5:
        return None
    return best_letter, best_score
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_cv_squares.py -q`
Expected: PASS (4 tests). If `test_square_state_occupied` fails, verify `square_state` receives a 60x60 cell and adjust the occupancy threshold inside `square_state` (keep it between 40 and 60).

- [ ] **Step 5: Commit**

```bash
git add chess-vision-fast/backend/app/cv_detector.py chess-vision-fast/backend/tests/test_cv_squares.py
git commit -m "feat: add square occupancy and piece classification"
```

---

### Task 5: CVBoardDetector orchestrator + settings + factory

**Files:**
- Modify: `chess-vision-fast/backend/app/cv_detector.py`
- Modify: `chess-vision-fast/backend/app/detector.py`
- Modify: `chess-vision-fast/backend/app/utils.py`
- Create: `chess-vision-fast/backend/tests/test_cv_detector.py`

**Interfaces:**
- Consumes: `find_board`, `empty_colors`, `square_state`, `classify_piece`; `BaseDetector`, `SquareDetection`, `DetectionResult` from `detector.py`; `matrix_to_fen` from `fen.py`.
- Produces:
  - `CVBoardDetector(BaseDetector)` with `detect(image: PIL.Image) -> DetectionResult`. `squares` bboxes are in warped 480x480 coordinates; `board_image` (PIL) is the warped board; `fen` uses `active_color='w'` and the detected `orientation` in `('w-bottom', 'w-top')`.
  - `utils.AppSettings` gains `stockfish_path: str = ''`, `stockfish_depth: int = 15`, `stockfish_auto_download: bool = True`.
  - `DetectorFactory.create()` returns a `CVBoardDetector`.

- [ ] **Step 1: Write the failing tests**

Create `chess-vision-fast/backend/tests/test_cv_detector.py`:

```python
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import numpy as np

from backend.app.cv_detector import CVBoardDetector
from tests.helpers.board_renderer import render_board

START = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
MIDGAME = 'r1bq1rk1/ppp2ppp/2np1n2/2b1p3/2B1P3/2NP1N2/PPP2PPP/R1BQ1RK1 w - - 0 1'


def _detect(fen, white_top=False):
    detector = CVBoardDetector(None)
    img = render_board(fen, white_top=white_top)
    return detector.detect(img)


def test_detect_starting_position():
    result = _detect(START)
    assert result.fen.startswith('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR')
    assert result.confidence > 0.8
    assert len(result.squares) == 32


def test_detect_midgame():
    result = _detect(MIDGAME)
    board_part = result.fen.split()[0]
    assert board_part == 'r1bq1rk1/ppp2ppp/2np1n2/2b1p3/2B1P3/2NP1N2/PPP2PPP/R1BQ1RK1'


def test_detect_flipped_board():
    result = _detect(START, white_top=True)
    board_part = result.fen.split()[0]
    assert board_part == 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR'


def test_detect_returns_warped_board_image():
    result = _detect(START)
    assert result.board_image is not None
    assert result.board_image.size == (480, 480)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_cv_detector.py -q`
Expected: FAIL with `ImportError: cannot import name 'CVBoardDetector'`

- [ ] **Step 3: Update settings**

Edit `chess-vision-fast/backend/app/utils.py` — replace the Gemini fields block:

```python
class AppSettings(BaseSettings):
    # Stockfish engine
    stockfish_path: str = ''
    stockfish_depth: int = 15
    stockfish_auto_download: bool = True

    # General
    allowed_origins: List[str] = ['*']
    max_upload_size: int = 5 * 1024 * 1024
    detection_confidence_threshold: float = 0.45
    frame_throttle_ms: int = 500

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )
```

- [ ] **Step 4: Implement CVBoardDetector**

Append to `chess-vision-fast/backend/app/cv_detector.py`:

```python
import chess
from PIL import Image

from .detector import BaseDetector, DetectionResult, SquareDetection
from .fen import confidence_from_squares, matrix_to_fen


def _square_at(r: int, c: int) -> str:
    file = chr(ord('a') + c)
    rank = 8 - r
    return f'{file}{rank}'


def _detect_orientation(squares: list) -> str:
    top_white = sum(1 for s in squares if s.piece and s.piece.isupper() and s.bbox[1] < 4 * CELL)
    bot_white = sum(1 for s in squares if s.piece and s.piece.isupper() and s.bbox[1] >= 4 * CELL)
    if top_white > bot_white:
        return 'w-top'
    return 'w-bottom'


class CVBoardDetector(BaseDetector):
    def detect(self, image: Image.Image) -> DetectionResult:
        img = cv2.cvtColor(np.array(image.convert('RGB')), cv2.COLOR_RGB2BGR)
        board = find_board(img)
        if board is None:
            return self._error_result(
                image,
                'Could not detect the chess board. Make sure the screenshot shows the full board facing forward.',
            )
        colors = empty_colors(board)
        if colors is None:
            return self._error_result(image, 'Could not determine board colors.')
        light, dark = colors

        squares = []
        matrix = [['' for _ in range(8)] for _ in range(8)]
        unknown = []
        for r in range(8):
            for c in range(8):
                cell = board[r * CELL:(r + 1) * CELL, c * CELL:(c + 1) * CELL]
                occupied, piece_color = square_state(cell, light, dark)
                if not occupied:
                    continue
                classified = classify_piece(cell, piece_color)
                if classified is None:
                    unknown.append(_square_at(r, c))
                    continue
                letter, conf = classified
                fen_letter = letter if piece_color == 'w' else letter.lower()
                squares.append(SquareDetection(square=_square_at(r, c), bbox=(c * CELL, r * CELL, CELL, CELL), piece=fen_letter, confidence=conf))
                matrix[r][c] = fen_letter

        if unknown:
            return self._error_result(
                image,
                f'Could not classify pieces on squares: {", ".join(unknown)}. Try flipping the board or using a cleaner screenshot.',
            )

        orientation = _detect_orientation(squares)
        fen = matrix_to_fen(matrix, active_color='w', orientation=orientation)
        try:
            chess.Board(fen)
        except ValueError:
            return self._error_result(image, f'Invalid position detected: {fen}. Please try again.')

        board_pil = Image.fromarray(cv2.cvtColor(board, cv2.COLOR_BGR2RGB))
        return DetectionResult(
            fen=fen,
            board_image_base64=self._image_to_base64(board_pil),
            squares=squares,
            confidence=confidence_from_squares(squares),
            board_image=board_pil,
        )

    def _error_result(self, image: Image.Image, message: str) -> DetectionResult:
        return DetectionResult(
            fen='',
            board_image_base64=self._image_to_base64(image),
            squares=[],
            confidence=0.0,
            error=message,
        )
```

- [ ] **Step 5: Add `board_image` and `error` fields to DetectionResult**

Edit `chess-vision-fast/backend/app/detector.py`:

```python
@dataclass
class DetectionResult:
    fen: str
    board_image_base64: str
    squares: List[SquareDetection]
    confidence: float
    board_image: Optional[Image.Image] = None
    error: Optional[str] = None
```

Add the import at the top of `detector.py` (it already imports `from PIL import Image, ImageDraw, ImageFont`).

- [ ] **Step 6: Point the factory at the CV detector**

Edit `chess-vision-fast/backend/app/detector.py` — replace the `DetectorFactory.create` body:

```python
class DetectorFactory:
    """Detector factory. Uses the local CV pipeline for board detection."""

    def __init__(self, settings: AppSettings, override_backend: Optional[str] = None) -> None:
        self.settings = settings

    def create(self) -> BaseDetector:
        from .cv_detector import CVBoardDetector
        return CVBoardDetector(self.settings)
```

- [ ] **Step 7: Run test to verify it passes**

Run: `python -m pytest tests/test_cv_detector.py -q`
Expected: PASS (4 tests)

- [ ] **Step 8: Commit**

```bash
git add chess-vision-fast/backend/app/cv_detector.py chess-vision-fast/backend/app/detector.py chess-vision-fast/backend/app/utils.py chess-vision-fast/backend/tests/test_cv_detector.py
git commit -m "feat: add CV board detector orchestrator with orientation detection"
```

---

### Task 6: Stockfish engine (discovery, download, analysis)

**Files:**
- Create: `chess-vision-fast/backend/app/stockfish_engine.py`
- Create: `chess-vision-fast/backend/tests/mock_uci_engine.py`
- Create: `chess-vision-fast/backend/tests/test_stockfish_engine.py`

**Interfaces:**
- Consumes: `AppSettings` (Task 5).
- Produces:
  - `find_stockfish(configured_path=None, auto_download=True) -> Optional[str]`
  - `download_and_extract_stockfish() -> Optional[str]`
  - `StockfishEngine(path=None, depth=15, auto_download=True, command=None)`. `command` is a test-only override (list of argv). `analyze_position(fen, depth=None) -> dict` with keys `uci`, `score_cp`, `score_mate`, `pv` (list of SAN), `depth`, `source: 'stockfish'`.

- [ ] **Step 1: Create the mock UCI engine**

Create `chess-vision-fast/backend/tests/mock_uci_engine.py`:

```python
"""Minimal UCI engine for tests. Always replies with e2e4 (cp 57)."""


def main() -> None:
    for line in iter(sys.stdin.readline, ''):
        line = line.strip()
        if line == 'uci':
            print('id name MockEngine 1.0')
            print('id author test')
            print('uciok', flush=True)
        elif line == 'isready':
            print('readyok', flush=True)
        elif line.startswith('go'):
            print('info depth 15 score cp 57 pv e2e4 e7e5', flush=True)
            print('bestmove e2e4', flush=True)
        elif line == 'quit':
            break


if __name__ == '__main__':
    import sys
    main()
```

- [ ] **Step 2: Write the failing tests**

Create `chess-vision-fast/backend/tests/test_stockfish_engine.py`:

```python
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.app.stockfish_engine import StockfishEngine

MOCK = [sys.executable, str(Path(__file__).resolve().parent / 'mock_uci_engine.py')]


def test_analyze_position_with_mock_engine():
    engine = StockfishEngine(command=MOCK)
    result = engine.analyze_position('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1')
    assert result['uci'] == 'e2e4'
    assert result['score_cp'] == 57
    assert result['score_mate'] is None
    assert result['pv'] == ['e4', 'e5']
    assert result['source'] == 'stockfish'


def test_find_stockfish_with_configured_path_missing_returns_none():
    from backend.app.stockfish_engine import find_stockfish
    assert find_stockfish(configured_path=str(Path(__file__).resolve().parent / 'does_not_exist.exe'), auto_download=False) is None
```

- [ ] **Step 3: Run test to verify it fails**

Run: `python -m pytest tests/test_stockfish_engine.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'backend.app.stockfish_engine'`

- [ ] **Step 4: Implement the engine**

Create `chess-vision-fast/backend/app/stockfish_engine.py`:

```python
"""Stockfish binary discovery, download, and UCI analysis."""
import logging
import os
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path
from typing import Optional

import chess
import chess.engine

logger = logging.getLogger(__name__)

STOCKFISH_DOWNLOAD_URL = 'https://github.com/official-stockfish/Stockfish/releases/latest/download/stockfish-windows-x86-64-avx2.zip'
BIN_DIR = Path(__file__).resolve().parent / 'bin'

COMMON_PATHS = [
    r'C:\Program Files\Stockfish\stockfish.exe',
    r'C:\Program Files (x86)\Stockfish\stockfish.exe',
    os.path.expanduser(r'~\Desktop\stockfish.exe'),
    r'C:\stockfish\stockfish.exe',
]


def find_stockfish(configured_path: Optional[str] = None, auto_download: bool = True) -> Optional[str]:
    candidates = []
    if configured_path and os.path.exists(configured_path):
        candidates.append(configured_path)
    local = BIN_DIR / 'stockfish.exe'
    if local.exists():
        candidates.append(str(local))
    for path in COMMON_PATHS:
        if os.path.exists(path):
            candidates.append(path)
    downloads = os.path.expanduser('~/Downloads')
    if os.path.isdir(downloads):
        for root, dirs, files in os.walk(downloads):
            if root[len(downloads):].count(os.sep) > 2:
                dirs[:] = []
            for file in files:
                if file.lower().startswith('stockfish') and file.lower().endswith('.exe'):
                    candidates.append(os.path.join(root, file))
    if candidates:
        return candidates[0]
    if auto_download and sys.platform == 'win32':
        return download_and_extract_stockfish()
    return None


def download_and_extract_stockfish() -> Optional[str]:
    exe = BIN_DIR / 'stockfish.exe'
    if exe.exists():
        return str(exe)
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = BIN_DIR / 'stockfish.zip'
    try:
        logger.info('Downloading Stockfish for Windows...')
        urllib.request.urlretrieve(STOCKFISH_DOWNLOAD_URL, zip_path)
        with zipfile.ZipFile(zip_path) as zf:
            for member in zf.namelist():
                if member.lower().endswith('.exe'):
                    with zf.open(member) as src, open(exe, 'wb') as dst:
                        dst.write(src.read())
                    return str(exe)
        return None
    except Exception as e:
        logger.error(f'Stockfish download failed: {e}')
        return None
    finally:
        try:
            zip_path.unlink()
        except OSError:
            pass


class StockfishEngine:
    def __init__(self, path: Optional[str] = None, depth: int = 15,
                 auto_download: bool = True, command: Optional[list] = None) -> None:
        self.path = path
        self.depth = depth
        self.auto_download = auto_download
        self._command = command

    def ensure_available(self) -> str:
        if self._command is not None:
            return ''
        if self.path and os.path.exists(self.path):
            return self.path
        found = find_stockfish(self.path, self.auto_download)
        if not found:
            raise RuntimeError(
                'Stockfish not found. Install it or set STOCKFISH_PATH. '
                'Download: https://stockfishchess.org/download/'
            )
        self.path = found
        return found

    def _command_list(self) -> list:
        if self._command is not None:
            return self._command
        return [self.ensure_available()]

    def analyze_position(self, fen: str, depth: Optional[int] = None) -> dict:
        board = chess.Board(fen)
        engine = chess.engine.SimpleEngine.popen_uci(self._command_list())
        try:
            limit = chess.engine.Limit(depth=depth or self.depth)
            info = engine.analyse(board, limit=limit, multipv=1)
            white_score = info['score'].white()
            if white_score.is_mate():
                score_cp, score_mate = None, white_score.mate()
            else:
                score_cp, score_mate = white_score.cp, None
            pv = []
            walk = chess.Board(fen)
            for move in info.get('pv', [])[:6]:
                walk.push(move)
                pv.append(walk.san(move))
            return {
                'uci': info['pv'][0].uci() if info.get('pv') else None,
                'score_cp': score_cp,
                'score_mate': score_mate,
                'pv': pv,
                'depth': depth or self.depth,
                'source': 'stockfish',
            }
        finally:
            engine.quit()
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_stockfish_engine.py -q`
Expected: PASS (2 tests)

- [ ] **Step 6: Commit**

```bash
git add chess-vision-fast/backend/app/stockfish_engine.py chess-vision-fast/backend/tests/mock_uci_engine.py chess-vision-fast/backend/tests/test_stockfish_engine.py
git commit -m "feat: add Stockfish engine with binary discovery and UCI analysis"
```

---

### Task 7: StockfishService (context + evaluation text)

**Files:**
- Create: `chess-vision-fast/backend/app/services/stockfish_service.py`
- Modify: `chess-vision-fast/backend/app/services/__init__.py`
- Create: `chess-vision-fast/backend/tests/test_stockfish_service.py`

**Interfaces:**
- Consumes: `StockfishEngine` (Task 6).
- Produces:
  - `compute_castling(board_part: str) -> str`
  - `en_passant_from_history(move_history_uci: list) -> str`
  - `evaluation_text(score_cp, score_mate) -> str`
  - `StockfishService(engine)` with `analyze_position(fen, turn=None, depth=None) -> dict` (keys `uci`, `san`, `score {cp, mate}`, `pv`, `evaluation_text`, `turn`, `depth`, `source`), `get_context() -> dict`, `clear_context()`.

- [ ] **Step 1: Write the failing tests**

Create `chess-vision-fast/backend/tests/test_stockfish_service.py`:

```python
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.app.services.stockfish_service import (
    StockfishService,
    compute_castling,
    en_passant_from_history,
    evaluation_text,
)
from backend.app.stockfish_engine import StockfishEngine

MOCK = [sys.executable, str(Path(__file__).resolve().parent / 'mock_uci_engine.py')]


def test_evaluation_text_mate():
    assert evaluation_text(None, 3) == 'Checkmate in 3 move(s) for White.'
    assert evaluation_text(None, -2) == 'Checkmate in 2 move(s) for Black.'


def test_evaluation_text_cp():
    assert 'decisive advantage' in evaluation_text(450, None)
    assert 'better' in evaluation_text(-150, None)
    assert 'Balanced' in evaluation_text(50, None)


def test_compute_castling():
    assert compute_castling('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR') == 'KQkq'
    assert compute_castling('r3k3/8/8/8/8/8/8/R3K3') == 'Qq'
    assert compute_castling('4k3/8/8/8/8/8/8/4K3') == '-'


def test_en_passant_from_history():
    assert en_passant_from_history([]) == '-'
    assert en_passant_from_history(['e2e4']) == 'e3'
    assert en_passant_from_history(['e7e5']) == 'e6'
    assert en_passant_from_history(['g1f3']) == '-'


def test_service_analyze_position_builds_context():
    engine = StockfishEngine(command=MOCK)
    service = StockfishService(engine)
    result = service.analyze_position('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR')
    assert result['uci'] == 'e2e4'
    assert result['san'] == 'e4'
    assert result['score'] == {'cp': 57, 'mate': None}
    assert result['evaluation_text'] == 'Balanced position (+0.6).'
    assert result['source'] == 'stockfish'
    assert service.get_context()['total_moves'] == 1


def test_service_clear_context():
    engine = StockfishEngine(command=MOCK)
    service = StockfishService(engine)
    service.analyze_position('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR')
    service.clear_context()
    assert service.get_context()['total_moves'] == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_stockfish_service.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'backend.app.services.stockfish_service'`

- [ ] **Step 3: Implement the service**

Create `chess-vision-fast/backend/app/services/stockfish_service.py`:

```python
"""Chess analysis service using local Stockfish. Maintains game context."""
import logging
from typing import Optional

import chess

from ..stockfish_engine import StockfishEngine

logger = logging.getLogger(__name__)


def compute_castling(board_part: str) -> str:
    board = chess.Board(board_part)
    rights = []
    if board.piece_at(chess.parse_square('e1')) == chess.Piece(chess.KING, chess.WHITE):
        if board.piece_at(chess.parse_square('h1')) == chess.Piece(chess.ROOK, chess.WHITE):
            rights.append('K')
        if board.piece_at(chess.parse_square('a1')) == chess.Piece(chess.ROOK, chess.WHITE):
            rights.append('Q')
    if board.piece_at(chess.parse_square('e8')) == chess.Piece(chess.KING, chess.BLACK):
        if board.piece_at(chess.parse_square('h8')) == chess.Piece(chess.ROOK, chess.BLACK):
            rights.append('k')
        if board.piece_at(chess.parse_square('a8')) == chess.Piece(chess.ROOK, chess.BLACK):
            rights.append('q')
    return ''.join(rights) or '-'


def en_passant_from_history(move_history_uci: list) -> str:
    if not move_history_uci:
        return '-'
    fr, to = move_history_uci[-1][:2], move_history_uci[-1][2:4]
    if fr[0] == to[0] and abs(int(fr[1]) - int(to[1])) == 2:
        return to[0] + str((int(fr[1]) + int(to[1])) // 2)
    return '-'


def evaluation_text(score_cp, score_mate) -> str:
    if score_mate is not None:
        side = 'White' if score_mate > 0 else 'Black'
        return f'Checkmate in {abs(score_mate)} move(s) for {side}.'
    if score_cp is None:
        return 'No evaluation available.'
    if score_cp > 300:
        return f'White has a decisive advantage (+{score_cp / 100:.1f}).'
    if score_cp > 100:
        return f'White is better (+{score_cp / 100:.1f}).'
    if score_cp > -100:
        return f'Balanced position ({score_cp / 100:+.1f}).'
    if score_cp > -300:
        return f'Black is better ({score_cp / 100:+.1f}).'
    return f'Black has a decisive advantage ({score_cp / 100:+.1f}).'


class StockfishService:
    def __init__(self, engine: StockfishEngine) -> None:
        self.engine = engine
        self.move_history_uci: list = []
        self.move_history_san: list = []
        self.current_fen: Optional[str] = None

    def analyze_position(self, fen: str, turn: Optional[str] = None, depth: Optional[int] = None) -> dict:
        board = chess.Board(fen.split()[0])
        active = turn if turn in ('w', 'b') else 'w'
        castling = compute_castling(fen.split()[0])
        ep = en_passant_from_history(self.move_history_uci)
        parts = board.fen().split()
        parts[1] = active
        parts[2] = castling
        parts[3] = ep
        complete = ' '.join(parts)

        result = self.engine.analyze_position(complete, depth=depth)

        b = chess.Board(complete)
        move = chess.Move.from_uci(result['uci'])
        san = b.san(move)
        self.move_history_uci.append(result['uci'])
        self.move_history_san.append(san)
        self.current_fen = complete

        return {
            'uci': result['uci'],
            'san': san,
            'score': {'cp': result['score_cp'], 'mate': result['score_mate']},
            'pv': result['pv'],
            'evaluation_text': evaluation_text(result['score_cp'], result['score_mate']),
            'turn': active,
            'depth': result['depth'],
            'source': 'stockfish',
        }

    def get_context(self) -> dict:
        return {
            'move_history': self.move_history_san,
            'total_moves': len(self.move_history_san),
            'current_fen': self.current_fen,
        }

    def clear_context(self) -> None:
        self.move_history_uci = []
        self.move_history_san = []
        self.current_fen = None
```

Replace the contents of `chess-vision-fast/backend/app/services/__init__.py`:

```python
from .stockfish_service import StockfishService

__all__ = ['StockfishService']
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_stockfish_service.py -q`
Expected: PASS (6 tests). If `test_service_analyze_position_builds_context` fails on `evaluation_text`, confirm `score_cp` is `57` (white-relative) from the mock.

- [ ] **Step 5: Commit**

```bash
git add chess-vision-fast/backend/app/services/stockfish_service.py chess-vision-fast/backend/app/services/__init__.py chess-vision-fast/backend/tests/test_stockfish_service.py
git commit -m "feat: add Stockfish service with game context and evaluation text"
```

---

### Task 8: Rewrite API routes + remove Gemini

**Files:**
- Modify: `chess-vision-fast/backend/app/api/routes.py`
- Delete: `chess-vision-fast/backend/app/gemini_detector.py`
- Delete: `chess-vision-fast/backend/app/services/gemini_chess_service.py`
- Modify: `chess-vision-fast/backend/requirements.txt`
- Create: `chess-vision-fast/backend/tests/test_api.py`

**Interfaces:**
- Consumes: `DetectorFactory`, `StockfishService`, `StockfishEngine`, `draw_overlay`, `AppSettings` (Tasks 5-7).
- Produces:
  - `POST /api/detect` (multipart `file`, query `orientation` in `auto|front|back`) → `{fen, board_image_base64, squares, confidence, orientation, error?}`
  - `POST /api/detect_and_move` (multipart `file`, query `orientation`, `turn` (`w|b`), `depth`) → detection + `overlay_image_base64`, `overlay_coords`, analysis fields, `source`
  - `POST /api/best_move` (JSON `{fen, turn?, depth?}`) → `{uci, san, score {cp, mate}, pv, evaluation_text, turn, depth, source, error?}`
  - `POST /api/clear_context`, `GET /api/context`

- [ ] **Step 1: Write the failing tests**

Create `chess-vision-fast/backend/tests/test_api.py`:

```python
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import io

import numpy as np
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.stockfish_service import StockfishService
from backend.app.stockfish_engine import StockfishEngine
from backend.app.api import routes
from tests.helpers.board_renderer import render_board

MOCK = [sys.executable, str(Path(__file__).resolve().parent / 'mock_uci_engine.py')]
client = TestClient(app)


def _png_bytes(fen):
    img = render_board(fen)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf


def test_detect_endpoint():
    routes._chess_service = StockfishService(StockfishEngine(command=MOCK))
    files = {'file': ('board.png', _png_bytes('4k3/8/8/8/8/8/8/4K3 w - - 0 1'), 'image/png')}
    response = client.post('/api/detect', files=files)
    assert response.status_code == 200
    data = response.json()
    assert '4k3/8/8/8/8/8/8/4K3' in data['fen']
    assert data['orientation'] in ('w-bottom', 'w-top')


def test_best_move_endpoint():
    routes._chess_service = StockfishService(StockfishEngine(command=MOCK))
    response = client.post('/api/best_move', json={'fen': 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'})
    assert response.status_code == 200
    data = response.json()
    assert data['uci'] == 'e2e4'
    assert data['san'] == 'e4'
    assert data['source'] == 'stockfish'


def test_detect_and_move_endpoint():
    routes._chess_service = StockfishService(StockfishEngine(command=MOCK))
    files = {'file': ('board.png', _png_bytes('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'), 'image/png')}
    response = client.post('/api/detect_and_move', files=files)
    assert response.status_code == 200
    data = response.json()
    assert data['fen'].startswith('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR')
    assert data['best_move'] == 'e2e4'
    assert data['overlay_image_base64']
    assert data['squares']


def test_context_endpoint():
    routes._chess_service = StockfishService(StockfishEngine(command=MOCK))
    client.post('/api/clear_context')
    response = client.get('/api/context')
    assert response.status_code == 200
    assert response.json()['total_moves'] == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_api.py -q`
Expected: FAIL — `/api/detect` etc. still return Gemini-shaped responses (or 500). Confirm failures before editing.

- [ ] **Step 3: Rewrite routes.py**

Replace the entire contents of `chess-vision-fast/backend/app/api/routes.py`:

```python
"""
API routes for chess detection and analysis using local CV + Stockfish.
"""
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, List, Optional

import chess
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from PIL import Image
from pydantic import BaseModel

from ..detector import DetectorFactory, SquareDetection
from ..overlay import draw_overlay
from ..services import StockfishService
from ..stockfish_engine import StockfishEngine
from ..utils import AppSettings, get_settings

router = APIRouter()

_chess_service: Optional[StockfishService] = None


def get_chess_service(settings: AppSettings) -> StockfishService:
    global _chess_service
    if _chess_service is None:
        engine = StockfishEngine(
            path=settings.stockfish_path,
            depth=settings.stockfish_depth,
            auto_download=settings.stockfish_auto_download,
        )
        _chess_service = StockfishService(engine)
    return _chess_service


class BestMoveRequest(BaseModel):
    fen: str
    turn: Optional[str] = None
    depth: Optional[int] = None


def _validate_file(file: UploadFile, settings: AppSettings) -> bytes:
    contents = file.file.read()
    if len(contents) > settings.max_upload_size:
        raise HTTPException(status_code=413, detail='File too large')
    return contents


def _open_image(payload: bytes) -> Image.Image:
    try:
        return Image.open(BytesIO(payload)).convert('RGB')
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f'Could not read image: {exc}')


def _squares_to_response(squares: List[SquareDetection]) -> List[Dict[str, Any]]:
    return [
        {
            'square': square.square,
            'bbox': [square.bbox[0], square.bbox[1], square.bbox[2], square.bbox[3]],
            'piece': square.piece,
            'confidence': square.confidence,
        }
        for square in squares
    ]


@router.post('/api/detect')
def detect(
    file: UploadFile = File(...),
    orientation: Optional[str] = Query(None),
    settings: AppSettings = Depends(get_settings),
) -> Dict[str, Any]:
    detector = DetectorFactory(settings).create()
    result = detector.detect(_open_image(_validate_file(file, settings)))
    return {
        'fen': result.fen,
        'board_image_base64': result.board_image_base64,
        'squares': _squares_to_response(result.squares),
        'confidence': result.confidence,
        'orientation': result.orientation if hasattr(result, 'orientation') else 'w-bottom',
        'error': result.error,
    }


@router.post('/api/best_move')
def best_move(
    payload: BestMoveRequest,
    settings: AppSettings = Depends(get_settings),
) -> Dict[str, Any]:
    try:
        service = get_chess_service(settings)
        result = service.analyze_position(payload.fen, turn=payload.turn, depth=payload.depth)
        return {
            'uci': result['uci'],
            'san': result['san'],
            'score': result['score'],
            'pv': result['pv'],
            'evaluation_text': result['evaluation_text'],
            'turn': result['turn'],
            'depth': result['depth'],
            'source': result['source'],
        }
    except Exception as e:
        return {
            'uci': None, 'san': None,
            'score': {'cp': None, 'mate': None},
            'pv': [], 'evaluation_text': None,
            'turn': None, 'depth': None, 'source': 'stockfish',
            'error': f'Error in analysis: {str(e)}',
        }


@router.post('/api/detect_and_move')
def detect_and_move(
    file: UploadFile = File(...),
    orientation: Optional[str] = Query(None),
    turn: Optional[str] = Query(None),
    depth: Optional[int] = Query(None),
    settings: AppSettings = Depends(get_settings),
) -> Dict[str, Any]:
    detector = DetectorFactory(settings).create()
    detection = detector.detect(_open_image(_validate_file(file, settings)))
    squares = _squares_to_response(detection.squares)
    overlay_image_base64 = detection.board_image_base64
    overlay_coords: List[float] = []

    if not detection.fen:
        return {
            'fen': '', 'best_move': None, 'uci': None, 'san': None,
            'score': {'cp': None, 'mate': None}, 'pv': [],
            'evaluation_text': None, 'overlay_image_base64': overlay_image_base64,
            'squares': squares, 'confidence': detection.confidence,
            'error': detection.error or 'Could not detect the board.',
        }

    try:
        service = get_chess_service(settings)
        result = service.analyze_position(detection.fen, turn=turn, depth=depth)
        if detection.board_image is not None:
            overlay_png, overlay_coords = draw_overlay(detection.board_image, squares, result['uci'])
            overlay_image_base64 = overlay_png
        return {
            'fen': detection.fen,
            'best_move': result['uci'],
            'uci': result['uci'],
            'san': result['san'],
            'score': result['score'],
            'pv': result['pv'],
            'evaluation_text': result['evaluation_text'],
            'overlay_image_base64': overlay_image_base64,
            'overlay_coords': overlay_coords,
            'squares': squares,
            'confidence': detection.confidence,
            'orientation': detection.orientation if hasattr(detection, 'orientation') else 'w-bottom',
            'source': 'stockfish',
            'timestamp': datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {
            'fen': detection.fen, 'best_move': None, 'uci': None, 'san': None,
            'score': {'cp': None, 'mate': None}, 'pv': [],
            'evaluation_text': None, 'overlay_image_base64': overlay_image_base64,
            'squares': squares, 'confidence': detection.confidence,
            'error': f'Error in analysis: {str(e)}',
        }


@router.post('/api/clear_context')
def clear_context(settings: AppSettings = Depends(get_settings)) -> Dict[str, Any]:
    try:
        get_chess_service(settings).clear_context()
        return {'status': 'success', 'message': 'Game context cleared'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error clearing context: {str(e)}')


@router.get('/api/context')
def get_context(settings: AppSettings = Depends(get_settings)) -> Dict[str, Any]:
    try:
        return get_chess_service(settings).get_context()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error getting context: {str(e)}')
```

- [ ] **Step 4: Add `orientation` to DetectionResult and set it in CVBoardDetector**

Edit `chess-vision-fast/backend/app/detector.py` — add field:

```python
    board_image: Optional[Image.Image] = None
    orientation: Optional[str] = None
    error: Optional[str] = None
```

Edit `chess-vision-fast/backend/app/cv_detector.py` — in the successful `DetectionResult(...)`, add `orientation=orientation`:

```python
        return DetectionResult(
            fen=fen,
            board_image_base64=self._image_to_base64(board_pil),
            squares=squares,
            confidence=confidence_from_squares(squares),
            board_image=board_pil,
            orientation=orientation,
        )
```

- [ ] **Step 5: Remove Gemini files and dependency**

Delete `chess-vision-fast/backend/app/gemini_detector.py` and `chess-vision-fast/backend/app/services/gemini_chess_service.py`.

Edit `chess-vision-fast/backend/requirements.txt` — remove the last line `google-generativeai`.

- [ ] **Step 6: Run the full backend test suite**

Run: `python -m pytest tests/ -q`
Expected: PASS — all tests including `test_fen.py`, `test_cv_board.py`, `test_cv_squares.py`, `test_cv_detector.py`, `test_stockfish_engine.py`, `test_stockfish_service.py`, `test_api.py`.

- [ ] **Step 7: Verify backend starts**

Run: `python -c "from backend.app.main import app; print(app.title)"`
Expected: prints `Chess Vision Fast` without Gemini import errors.

- [ ] **Step 8: Commit**

```bash
git add chess-vision-fast/backend/app/api/routes.py chess-vision-fast/backend/app/detector.py chess-vision-fast/backend/app/cv_detector.py chess-vision-fast/backend/app/services chess-vision-fast/backend/app/gemini_detector.py chess-vision-fast/backend/requirements.txt chess-vision-fast/backend/tests/test_api.py
git commit -m "feat: rewrite API for CV + Stockfish and remove Gemini"
```

---

### Task 9: Update frontend API client

**Files:**
- Modify: `chess-vision-fast/frontend/src/services/api.js`

**Interfaces:**
- Consumes: backend routes (Task 8).
- Produces: `detectImage(file, signal, orientation)`, `detectAndMove(file, signal, orientation, turn, depth)`, `bestMove(fen, signal, turn, depth)`, `clearContext(signal)`, `getContext(signal)`.

- [ ] **Step 1: Rewrite api.js**

Replace the contents of `chess-vision-fast/frontend/src/services/api.js`:

```js
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

async function _jsonResponse(response) {
  if (!response.ok) {
    const message = await response.text()
    throw new Error(message || 'Error en la API')
  }
  return response.json()
}

function _query(url, params) {
  const u = new URL(url)
  for (const [key, value] of Object.entries(params)) {
    if (value !== null && value !== undefined && value !== '') {
      u.searchParams.set(key, value)
    }
  }
  return u.toString()
}

export function detectImage(file, signal, orientation) {
  const form = new FormData()
  form.set('file', file)
  return fetch(_query(`${API_BASE}/api/detect`, { orientation }), {
    method: 'POST',
    body: form,
    signal,
  }).then(_jsonResponse)
}

export function detectAndMove(file, signal, orientation, turn, depth) {
  const form = new FormData()
  form.set('file', file)
  return fetch(_query(`${API_BASE}/api/detect_and_move`, { orientation, turn, depth }), {
    method: 'POST',
    body: form,
    signal,
  }).then(_jsonResponse)
}

export function bestMove(fen, signal, turn, depth) {
  return fetch(`${API_BASE}/api/best_move`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ fen, turn, depth }),
    signal,
  }).then(_jsonResponse)
}

export function clearContext(signal) {
  return fetch(`${API_BASE}/api/clear_context`, {
    method: 'POST',
    signal,
  }).then(_jsonResponse)
}

export function getContext(signal) {
  return fetch(`${API_BASE}/api/context`, {
    method: 'GET',
    signal,
  }).then(_jsonResponse)
}
```

- [ ] **Step 2: Verify no stale imports**

Run: `rg "changeModel|getCurrentModel" chess-vision-fast/frontend/src/services`
Expected: no matches.

> NOTE: `App.jsx` still imports `getRetrospective`/`changeModel`/`getCurrentModel` until Task 10 rewrites it, so the `rg` check is scoped to `src/services` here. Tasks 9+10 must be delivered back-to-back (two commits) so the frontend build is only verified green at the end of Task 10.

- [ ] **Step 3: Commit**

```bash
git add chess-vision-fast/frontend/src/services/api.js
git commit -m "feat: update frontend API client for stockfish endpoints"
```

---

### Task 10: Update frontend UI

**Files:**
- Modify: `chess-vision-fast/frontend/src/App.jsx`
- Modify: `chess-vision-fast/frontend/src/components/UploadImage.jsx`
- Modify: `chess-vision-fast/frontend/src/components/BoardPreview.jsx`

**Interfaces:**
- Consumes: `api.js` (Task 9).
- Produces: a UI without the Gemini model selector/retrospective, with a flip toggle, depth selector, evaluation bar, evaluation text, and move history.

- [ ] **Step 1: Rewrite UploadImage.jsx**

Replace the contents of `chess-vision-fast/frontend/src/components/UploadImage.jsx`:

```jsx
import React, { useRef, useState, useEffect } from 'react'
import { detectAndMove } from '../services/api'

export default function UploadImage({ onResult, setStatus, setIsLoading, abortControllerRef, orientation, turn, depth }) {
  const input = useRef(null)
  const dropZoneRef = useRef(null)
  const [isDragging, setIsDragging] = useState(false)

  async function processFile(file) {
    if (!file || !file.type.startsWith('image/')) {
      setStatus('File is not a valid image')
      return
    }

    if (abortControllerRef?.current) {
      abortControllerRef.current.abort()
    }

    abortControllerRef.current = new AbortController()

    if (setIsLoading) setIsLoading(true)
    setStatus('Analyzing image with Stockfish...')

    try {
      const data = await detectAndMove(file, abortControllerRef.current.signal, orientation, turn, depth)
      onResult(data)
      if (!data.error) {
        setStatus('Analysis completed')
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        setStatus('Analysis cancelled')
      } else {
        console.error(error)
        const errorMsg = error.message || 'Error processing image'
        setStatus(`Error: ${errorMsg}`)
        onResult({ error: errorMsg })
      }
    } finally {
      if (setIsLoading) setIsLoading(false)
      abortControllerRef.current = null
    }
  }

  function handleUpload(event) {
    const file = event.target.files?.[0]
    if (!file) return
    processFile(file)
    if (input.current) input.current.value = ''
  }

  function handleDragOver(e) {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(true)
  }

  function handleDragLeave(e) {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }

  async function handleDrop(e) {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
    const file = e.dataTransfer.files?.[0]
    if (file) await processFile(file)
  }

  useEffect(() => {
    async function handlePaste(e) {
      const items = e.clipboardData?.items
      if (!items) return
      for (const item of items) {
        if (item.type.startsWith('image/')) {
          e.preventDefault()
          const file = item.getAsFile()
          if (file) await processFile(file)
          break
        }
      }
    }
    document.addEventListener('paste', handlePaste)
    return () => document.removeEventListener('paste', handlePaste)
  }, [orientation, turn, depth])

  return (
    <div
      ref={dropZoneRef}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={`rounded border-2 border-dashed p-3 text-center transition-colors ${
        isDragging
          ? 'border-emerald-500 bg-emerald-500/10'
          : 'border-slate-700 bg-slate-900 hover:border-slate-600'
      }`}
    >
      <div className="space-y-2">
        <div className="text-slate-400">
          <svg
            className="mx-auto h-8 w-8"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
            />
          </svg>
        </div>
        <div>
          <p className="text-xs font-medium text-slate-300">
            Drag an image here or{' '}
            <label className="cursor-pointer text-emerald-400 hover:text-emerald-300">
              browse your device
              <input
                ref={input}
                type="file"
                accept="image/png,image/jpeg,image/webp"
                onChange={handleUpload}
                className="hidden"
              />
            </label>
          </p>
          <p className="mt-0.5 text-xs text-slate-500">
            You can also paste with Ctrl+V
          </p>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Rewrite BoardPreview.jsx**

Replace the contents of `chess-vision-fast/frontend/src/components/BoardPreview.jsx`:

```jsx
import React from 'react'

function winPercent(cp, mate) {
  if (mate != null) return mate > 0 ? 100 : 0
  if (cp == null) return 50
  return Math.round(100 / (1 + Math.pow(10, -cp / 400)))
}

export default function BoardPreview({
  fen,
  bestMove,
  confidence,
  evaluationText,
  score,
  pv,
  error,
}) {
  const whitePct = score ? winPercent(score.cp, score.mate) : null
  return (
    <div className="space-y-2">
      {error && (
        <div className="rounded border border-red-500/30 bg-red-500/10 p-2">
          <p className="text-xs font-semibold text-red-400 mb-1">Error</p>
          <p className="text-xs text-red-300">{error}</p>
        </div>
      )}

      {score && (
        <div className="rounded border border-slate-700 bg-slate-900/50 p-2">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
            Evaluation
          </p>
          <div className="flex h-3 w-full overflow-hidden rounded bg-slate-700">
            <div
              className="bg-emerald-500"
              style={{ width: `${whitePct}%` }}
            ></div>
          </div>
          <p className="mt-1 text-xs text-slate-200">
            {score.mate != null
              ? `Mate in ${Math.abs(score.mate)}`
              : `${score.cp == null ? 'n/a' : (score.cp / 100).toFixed(1)}`}
            {evaluationText && <span className="text-slate-400"> — {evaluationText}</span>}
          </p>
        </div>
      )}

      {fen && (
        <div className="rounded border border-slate-700 bg-slate-900/50 p-2">
          <div className="flex items-center justify-between mb-1">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">FEN</p>
            {confidence !== null && (
              <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/20 px-1.5 py-0.5 text-xs font-semibold text-emerald-400">
                <div className="h-1 w-1 rounded-full bg-emerald-400"></div>
                {confidence?.toFixed(2) ?? 'n/a'}
              </span>
            )}
          </div>
          <p className="text-xs font-mono text-slate-200 break-all">{fen}</p>
        </div>
      )}

      {bestMove && (
        <div className="space-y-2 rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-2 backdrop-blur-sm">
          <div className="flex items-center gap-1.5">
            <svg className="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <p className="text-xs font-semibold text-emerald-400">Best Move</p>
          </div>
          <p className="text-base font-bold text-white">{bestMove}</p>

          {pv && pv.length > 0 && (
            <div className="rounded border border-slate-700/50 bg-slate-900/30 p-2">
              <p className="text-xs font-semibold text-slate-400 mb-0.5">Line</p>
              <p className="text-xs text-slate-200">{pv.join(' ')}</p>
            </div>
          )}
        </div>
      )}

      {!bestMove && fen && !error && (
        <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-2 text-center">
          <p className="text-xs text-amber-400">
            Click "Analyze" to get the best move
          </p>
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 3: Rewrite App.jsx**

Replace the contents of `chess-vision-fast/frontend/src/App.jsx`:

```jsx
import React, { useState, useRef, useEffect } from 'react'
import UploadImage from './components/UploadImage'
import BoardPreview from './components/BoardPreview'
import { bestMove, clearContext, getContext } from './services/api'

const DEPTHS = [10, 15, 20]

export default function App() {
  const [status, setStatus] = useState('Ready to analyze')
  const [overlayImage, setOverlayImage] = useState(null)
  const [fen, setFen] = useState('')
  const [bestMoveText, setBestMoveText] = useState('')
  const [evaluationText, setEvaluationText] = useState('')
  const [score, setScore] = useState(null)
  const [pv, setPv] = useState([])
  const [confidence, setConfidence] = useState(null)
  const [moveHistory, setMoveHistory] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [orientation, setOrientation] = useState('auto')
  const [turn, setTurn] = useState('w')
  const [depth, setDepth] = useState(15)
  const abortControllerRef = useRef(null)

  useEffect(() => {
    getContext()
      .then(data => {
        if (data && Array.isArray(data.move_history)) {
          setMoveHistory(data.move_history)
        }
      })
      .catch(() => {})
  }, [])

  const cancelOperation = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
    }
    setIsLoading(false)
    setStatus('Operation cancelled')
    setError(null)
  }

  const handleResult = (data) => {
    setFen(data.fen || '')
    setOverlayImage(data.overlay_image_base64 || data.board_image_base64 || null)
    setBestMoveText(data.best_move || data.uci || '')
    setEvaluationText(data.evaluation_text || '')
    setScore(data.score || null)
    setPv(data.pv || [])
    setConfidence(data.confidence)
    if (data.orientation && data.orientation !== 'w-bottom') {
      setOrientation(data.orientation === 'w-top' ? 'back' : 'auto')
    }
    if (data.error) {
      setError(data.error)
      setStatus(`Error: ${data.error}`)
    } else {
      setError(null)
      setStatus('Analysis completed')
    }
    setIsLoading(false)
  }

  const handleManualBestMove = async () => {
    if (!fen) {
      setStatus('First upload a board image')
      setError('No FEN available')
      return
    }
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    abortControllerRef.current = new AbortController()
    setIsLoading(true)
    setError(null)
    setStatus(`Analyzing with Stockfish (depth ${depth})...`)
    try {
      const response = await bestMove(fen, abortControllerRef.current.signal, turn, depth)
      setBestMoveText(response.uci || '')
      setEvaluationText(response.evaluation_text || '')
      setScore(response.score || null)
      setPv(response.pv || [])
      if (response.error) {
        setError(response.error)
        setStatus(`Error: ${response.error}`)
      } else {
        setError(null)
        setStatus('Analysis completed')
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        setStatus('Analysis cancelled')
        setError(null)
      } else {
        console.error(error)
        const errorMsg = error.message || 'Error analyzing position'
        setError(errorMsg)
        setStatus(`Error: ${errorMsg}`)
      }
    } finally {
      setIsLoading(false)
      abortControllerRef.current = null
    }
  }

  const handleClearContext = async () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    abortControllerRef.current = new AbortController()
    setIsLoading(true)
    setError(null)
    setStatus('Clearing context...')
    try {
      await clearContext(abortControllerRef.current.signal)
      setFen('')
      setBestMoveText('')
      setEvaluationText('')
      setScore(null)
      setPv([])
      setOverlayImage(null)
      setMoveHistory([])
      setError(null)
      setStatus('Context cleared - Ready for new game')
    } catch (error) {
      if (error.name === 'AbortError') {
        setStatus('Operation cancelled')
        setError(null)
      } else {
        console.error(error)
        setError(error.message || 'Error clearing context')
        setStatus('Error clearing context')
      }
    } finally {
      setIsLoading(false)
      abortControllerRef.current = null
    }
  }

  const downloadOverlay = () => {
    if (!overlayImage) return
    const link = document.createElement('a')
    link.href = `data:image/png;base64,${overlayImage}`
    link.download = 'analyzed-board.png'
    link.click()
  }

  const toggleOrientation = (value) => {
    setOrientation(value)
    setStatus(value === 'auto' ? 'Orientation: auto' : `Orientation: ${value}`)
  }

  return (
    <div className="h-screen overflow-hidden bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex flex-col">
      <header className="flex-shrink-0 px-4 py-2 text-center border-b border-slate-700/50">
        <div className="flex items-center justify-center gap-3 flex-wrap">
          <div className="inline-block rounded-full bg-emerald-500/20 px-2 py-1">
            <p className="text-xs font-semibold uppercase tracking-wider text-emerald-400">Chess Vision Fast</p>
          </div>
          <h1 className="text-lg sm:text-xl font-bold text-white">
            Analysis with{' '}
            <span className="bg-gradient-to-r from-emerald-400 to-blue-400 bg-clip-text text-transparent">
              Stockfish
            </span>
          </h1>
          <div className="flex items-center gap-1.5 text-xs text-slate-400">
            <div className={`h-1.5 w-1.5 rounded-full ${isLoading ? 'bg-yellow-500 animate-pulse' : error ? 'bg-red-500' : 'bg-emerald-500'}`}></div>
            <span className="hidden sm:inline">{status}</span>
          </div>
          {isLoading && (
            <button
              onClick={cancelOperation}
              className="ml-2 rounded bg-red-500/20 hover:bg-red-500/30 px-2 py-1 text-xs font-semibold text-red-400 transition-all flex items-center gap-1"
            >
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
              Cancel
            </button>
          )}
        </div>
        {error && (
          <div className="mt-1 text-xs text-red-400 bg-red-500/10 rounded px-2 py-1 inline-block">
            {error}
          </div>
        )}
      </header>

      <main className="flex-1 overflow-hidden px-4 py-2">
        <div className="h-full flex flex-col gap-2 max-w-7xl mx-auto">
          <section className="flex-shrink-0 rounded-lg border border-slate-700 bg-slate-800/50 backdrop-blur-sm p-2 shadow-xl">
            <div className="flex items-center justify-between gap-2 flex-wrap">
              <div className="flex items-center gap-2">
                <svg className="w-4 h-4 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                <span className="text-xs font-semibold text-white">Engine Settings</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-1.5">
                  <span className="text-xs text-slate-400">Depth</span>
                  {DEPTHS.map((d) => (
                    <button
                      key={d}
                      onClick={() => setDepth(d)}
                      disabled={isLoading}
                      className={`px-2 py-1 text-xs font-semibold rounded transition-all ${
                        depth === d ? 'bg-emerald-500 text-white' : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                      } disabled:opacity-50 disabled:cursor-not-allowed`}
                    >
                      {d}
                    </button>
                  ))}
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="text-xs text-slate-400">Board</span>
                  {[
                    { value: 'auto', label: 'Auto' },
                    { value: 'front', label: 'Front' },
                    { value: 'back', label: 'Back' },
                  ].map((opt) => (
                    <button
                      key={opt.value}
                      onClick={() => toggleOrientation(opt.value)}
                      disabled={isLoading}
                      className={`px-2 py-1 text-xs font-semibold rounded transition-all ${
                        orientation === opt.value ? 'bg-emerald-500 text-white' : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                      } disabled:opacity-50 disabled:cursor-not-allowed`}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </section>

          <section className="flex-shrink-0 rounded-lg border border-slate-700 bg-slate-800/50 backdrop-blur-sm p-3 shadow-xl">
            <div className="flex items-center gap-2 mb-2">
              <svg className="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <h2 className="text-sm font-semibold text-white">Upload Image</h2>
            </div>
            <UploadImage
              onResult={handleResult}
              setStatus={setStatus}
              setIsLoading={setIsLoading}
              abortControllerRef={abortControllerRef}
              orientation={orientation}
              turn={turn}
              depth={depth}
            />
          </section>

          {(overlayImage || fen) ? (
            <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-2 min-h-0">
              {overlayImage && (
                <section className="rounded-lg border border-slate-700 bg-slate-800/50 backdrop-blur-sm p-3 shadow-xl flex flex-col min-h-0">
                  <div className="flex items-center gap-2 mb-2 flex-shrink-0">
                    <svg className="w-4 h-4 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <h2 className="text-sm font-semibold text-white">Board</h2>
                  </div>
                  <div className="flex-1 rounded overflow-hidden border border-slate-700 bg-black min-h-0 flex items-center justify-center">
                    <img
                      src={`data:image/png;base64,${overlayImage}`}
                      alt="Analyzed board"
                      className="max-w-full max-h-full object-contain"
                    />
                  </div>
                </section>
              )}

              <section className="rounded-lg border border-slate-700 bg-slate-800/50 backdrop-blur-sm p-3 shadow-xl overflow-y-auto min-h-0">
                <BoardPreview
                  fen={fen}
                  bestMove={bestMoveText}
                  confidence={confidence}
                  evaluationText={evaluationText}
                  score={score}
                  pv={pv}
                  error={error}
                />
              </section>
            </div>
          ) : (
            <div className="flex-1"></div>
          )}

          <section className="flex-shrink-0 rounded-lg border border-slate-700 bg-slate-800/50 backdrop-blur-sm p-3 shadow-xl">
            <div className="flex items-center gap-2 mb-2">
              <svg className="w-4 h-4 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
              </svg>
              <h2 className="text-sm font-semibold text-white">Controls</h2>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              <button
                onClick={handleManualBestMove}
                disabled={isLoading || !fen}
                className="col-span-2 sm:col-span-1 rounded-lg bg-gradient-to-r from-emerald-500 to-emerald-600 px-2 py-2 text-xs font-semibold text-white shadow-lg hover:from-emerald-600 hover:to-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-1.5"
              >
                <span>Analyze</span>
              </button>

              <button
                onClick={downloadOverlay}
                disabled={!overlayImage}
                className="rounded-lg bg-slate-700 px-2 py-2 text-xs font-semibold text-white hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-1.5"
              >
                <span>Download</span>
              </button>

              <div className="rounded-lg bg-slate-700/50 px-2 py-2 text-xs font-semibold text-white overflow-y-auto max-h-20">
                <span className="text-slate-400 block mb-1">Moves</span>
                <span className="text-slate-200">
                  {moveHistory.length ? moveHistory.join(' ') : 'No moves yet'}
                </span>
              </div>

              <button
                onClick={handleClearContext}
                disabled={isLoading}
                className="rounded-lg bg-gradient-to-r from-red-500 to-red-600 px-2 py-2 text-xs font-semibold text-white shadow-lg hover:from-red-600 hover:to-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-1.5"
              >
                <span>Clear</span>
              </button>
            </div>
          </section>
        </div>
      </main>
    </div>
  )
}
```

- [ ] **Step 4: Refresh move history after each analysis**

Edit `chess-vision-fast/frontend/src/App.jsx` — in `handleResult`, after `setIsLoading(false)`, refresh the context:

```jsx
    setIsLoading(false)
    getContext().then(ctx => {
      if (ctx && Array.isArray(ctx.move_history)) setMoveHistory(ctx.move_history)
    }).catch(() => {})
```

- [ ] **Step 5: Build the frontend**

Run: `npm run build` (from `chess-vision-fast/frontend`)
Expected: build succeeds with no errors.

- [ ] **Step 6: Commit**

```bash
git add chess-vision-fast/frontend/src/App.jsx chess-vision-fast/frontend/src/components/UploadImage.jsx chess-vision-fast/frontend/src/components/BoardPreview.jsx
git commit -m "feat: update UI for local stockfish analysis"
```

---

### Task 11: README + final verification

**Files:**
- Modify: `chess-vision-fast/README.md`
- Modify: `chess-vision-fast/backend/tests/test_fen.py` (only if a stale import breaks — see note)

**Interfaces:**
- Consumes: everything above.
- Produces: an accurate README and a green full test run.

- [ ] **Step 1: Update README**

Edit `chess-vision-fast/README.md`:
- Title/subtitle: `# Chess Vision Fast - Local Analysis with Stockfish` and description "detects a chess.com board from a screenshot using classical computer vision and analyzes the best move with a local Stockfish engine."
- Replace the Features list: Board Detection (OpenCV classical CV), Best Move (Stockfish), Score + Principal Variation, Game Context / move history, modern UI, drag&drop/paste, 100% local (no API keys).
- Requirements: Python 3.12+, Node 18+; remove the Gemini API key bullet; note Stockfish is auto-downloaded on first analysis (Windows) or detected at common paths / `STOCKFISH_PATH`.
- `.env` example block → remove `GEMINI_API_KEY`/`GEMINI_MODEL`, add `STOCKFISH_PATH=`, `STOCKFISH_DEPTH=15`, `STOCKFISH_AUTO_DOWNLOAD=true`.
- API endpoints table → the new set from Task 8.
- "Usage" section → remove model selector and retrospective steps; add "Use the Board Auto/Front/Back toggle when the screenshot is flipped" and "depth selector".
- "Analysis Features" → best move (UCI + SAN), score (cp/mate), principal variation, evaluation text.
- Technologies → drop Google Gemini; add OpenCV.
- "Recent Changes" → replace the Gemini-era bullets with: added local CV board detection, added Stockfish analysis, removed Gemini.
- Docker section → the Dockerfile still installs `stockfish`; keep it.

- [ ] **Step 2: Run the full backend test suite**

Run: `python -m pytest tests/ -q` (from `chess-vision-fast`)
Expected: PASS (all tests)

- [ ] **Step 3: Verify the frontend dev build**

Run: `npm run build` (from `chess-vision-fast/frontend`)
Expected: succeeds.

- [ ] **Step 4: Commit**

```bash
git add chess-vision-fast/README.md
git commit -m "docs: update README for local CV + Stockfish pipeline"
```

---

## Self-Review Notes

- **Spec coverage:** board detection (Tasks 3-5), template classification (Tasks 2+4), orientation/turn/castling/EP (Tasks 1, 5, 7), Stockfish discovery/download/analysis (Task 6), API contract (Task 8), frontend changes (Tasks 9-10), error handling (built into `CVBoardDetector._error_result` and route try/except), testing incl. synthetic renderer + mock engine (each task), Gemini removal (Tasks 5, 8, 9-11).
- **Placeholders:** none — every code step has full code.
- **Type consistency:** `DetectionResult` gains `board_image`/`orientation`/`error` (Tasks 5/8); `StockfishEngine.analyze_position` returns `uci/score_cp/score_mate/pv/depth/source` (Task 6) and `StockfishService` wraps it as `uci/san/score/pv/evaluation_text/turn/depth/source` (Task 7); routes consume exactly those keys (Task 8). `matrix_to_fen(..., orientation=...)` used by `CVBoardDetector` (Task 5).
