# FEN Sanitizer & Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a validation + sanitization layer that repairs recoverable FEN issues (illegal castling rights, back-rank pawns) before any Stockfish analysis and returns a clear, exact error message for unrecoverable FENs.

**Architecture:** New pure-function module `backend/app/fen_sanitizer.py` (no CV/engine deps) exposing `sanitize_fen(fen) -> FenSanitizeResult` and `compute_castling`. The three routes (`/api/detect`, `/api/detect_and_move`, `/api/best_move`) call `sanitize_fen` before analysis and add a `fen_warnings` list to their responses. The frontend renders the warnings. `StockfishService` re-uses `compute_castling` from the new module (single source of truth).

**Tech Stack:** Python 3.12, python-chess 1.11.x, FastAPI, React 18 + Vite.

## Global Constraints

- Backend validation uses `python-chess` (no chess.js).
- Exact UI error message (single source, defined in `fen_sanitizer.py`):
  `Invalid FEN generated from board image. Please check piece placement or re-upload.`
- No new dependencies.
- All existing 31 tests must keep passing.
- `python-chess` flags (1.11.x): `STATUS_NO_WHITE_KING=1`, `STATUS_NO_BLACK_KING=2`,
  `STATUS_TOO_MANY_KINGS=4`, `STATUS_TOO_MANY_WHITE_PAWNS=8`, `STATUS_TOO_MANY_BLACK_PAWNS=16`,
  `STATUS_PAWNS_ON_BACKRANK=32`, `STATUS_TOO_MANY_WHITE_PIECES=64`, `STATUS_TOO_MANY_BLACK_PIECES=128`,
  `STATUS_BAD_CASTLING_RIGHTS=256`. These names/values are asserted by the tests — use the constants, not magic numbers.
- Test files live in `backend/tests/` and are gitignored (`test_*.py`) → commit them with `git add -f`.
- Run tests from `chess-vision-fast/backend` with `python -m pytest tests/ -q`.
- Back-rank pawn fix must run BEFORE the castling fix (restoring a piece can change castling eligibility).
- Sanitizer may only REMOVE invalid castling rights, never invent rights from `-`.

---

### Task 1: Move `compute_castling` to `fen_sanitizer.py`

**Files:**
- Create: `chess-vision-fast/backend/app/fen_sanitizer.py`
- Create: `chess-vision-fast/backend/tests/test_fen_sanitizer.py`
- Modify: `chess-vision-fast/backend/app/services/stockfish_service.py:12-25` (remove local `compute_castling`, import from new module)

**Interfaces:**
- Consumes: nothing.
- Produces: `compute_castling(board_part: str) -> str` — returns the castling field (e.g. `'KQkq'`, `'Qq'`, `'-'`) that the piece placement on `board_part` supports (white king on e1 + rook h1/a1 → K/Q; black king e8 + rook h8/a8 → k/q). Later tasks rely on this name.

- [ ] **Step 1: Write the failing test**

Create `chess-vision-fast/backend/tests/test_fen_sanitizer.py`:

```python
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.app.fen_sanitizer import compute_castling


def test_compute_castling():
    assert compute_castling('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR') == 'KQkq'
    assert compute_castling('r3k3/8/8/8/8/8/8/R3K3') == 'Qq'
    assert compute_castling('4k3/8/8/8/8/8/8/4K3') == '-'
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_fen_sanitizer.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'backend.app.fen_sanitizer'`

- [ ] **Step 3: Create the module with `compute_castling`**

Create `chess-vision-fast/backend/app/fen_sanitizer.py`:

```python
"""FEN sanitization and validation for the analysis pipeline."""
from dataclasses import dataclass, field
from typing import List, Optional

import chess

INVALID_FEN_MESSAGE = (
    'Invalid FEN generated from board image. '
    'Please check piece placement or re-upload.'
)

INITIAL_COUNTS = {'R': 2, 'N': 2, 'B': 2, 'Q': 1, 'K': 1}
FILE_PIECE = {'a': 'R', 'b': 'N', 'c': 'B', 'd': 'Q', 'e': 'K', 'f': 'B', 'g': 'N', 'h': 'R'}
FIX_PRIORITY = ['R', 'N', 'B', 'Q']


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
```

- [ ] **Step 4: Update `stockfish_service.py` to use the moved function**

Edit `chess-vision-fast/backend/app/services/stockfish_service.py`:
- Delete the `def compute_castling(board_part: str) -> str:` block (currently lines 12-25, ending before the `en_passant_from_history` docstring).
- Add the import after `import chess`:

```python
from ..fen_sanitizer import compute_castling
```

(The existing `test_stockfish_service.py::test_compute_castling` keeps importing `compute_castling` from `backend.app.services.stockfish_service` — the import binds it into that module's namespace, so the old import still works.)

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/ -q`
Expected: PASS (31 tests).

- [ ] **Step 6: Commit**

```bash
git add -f chess-vision-fast/backend/app/fen_sanitizer.py chess-vision-fast/backend/tests/test_fen_sanitizer.py chess-vision-fast/backend/app/services/stockfish_service.py
git commit -m "feat: add FEN sanitizer module with compute_castling"
```

---

### Task 2: `sanitize_fen` — parse, normalize, castling fix

**Files:**
- Modify: `chess-vision-fast/backend/app/fen_sanitizer.py`
- Modify: `chess-vision-fast/backend/tests/test_fen_sanitizer.py`

**Interfaces:**
- Consumes: `compute_castling`, `INVALID_FEN_MESSAGE` (Task 1).
- Produces: `@dataclass FenSanitizeResult` with fields `fen: str`, `valid: bool`,
  `warnings: List[str]` (default empty list), `error: Optional[str]` (default `None`);
  and `sanitize_fen(fen: str) -> FenSanitizeResult`. Task 4 (routes) relies on these names.

- [ ] **Step 1: Write the failing tests**

Append to `chess-vision-fast/backend/tests/test_fen_sanitizer.py`:

```python
from backend.app.fen_sanitizer import (
    FenSanitizeResult,
    INVALID_FEN_MESSAGE,
    compute_castling,
    sanitize_fen,
)

START_FEN = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'


def test_valid_fen_passes_unchanged():
    result = sanitize_fen(START_FEN)
    assert result.valid is True
    assert result.fen == START_FEN
    assert result.warnings == []


def test_castling_pruned_when_rook_missing():
    fen = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBN1 w KQkq - 0 1'
    result = sanitize_fen(fen)
    assert result.valid is True
    assert result.fen == 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBN1 w Qkq - 0 1'
    assert any('castling' in w.lower() for w in result.warnings)


def test_castling_without_king_unrecoverable():
    result = sanitize_fen('rnbqbnr1/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1')
    assert result.valid is False
    assert result.fen == ''
    assert result.error == INVALID_FEN_MESSAGE


def test_board_only_fen_normalized():
    result = sanitize_fen('4k3/8/8/8/8/8/8/4K3')
    assert result.valid is True
    assert result.fen == '4k3/8/8/8/8/8/8/4K3 w - - 0 1'
    assert result.warnings == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_fen_sanitizer.py -q`
Expected: FAIL with `ImportError: cannot import name 'sanitize_fen'` (and `FenSanitizeResult`).

- [ ] **Step 3: Implement the result type, helpers, and castling fix**

Append to `chess-vision-fast/backend/app/fen_sanitizer.py`:

```python
@dataclass
class FenSanitizeResult:
    fen: str
    valid: bool
    warnings: List[str] = field(default_factory=list)
    error: Optional[str] = None


DEFAULT_FIELDS = ['w', '-', '-', '0', '1']

UNRECOVERABLE_MASK = (
    chess.STATUS_NO_WHITE_KING
    | chess.STATUS_NO_BLACK_KING
    | chess.STATUS_TOO_MANY_KINGS
    | chess.STATUS_TOO_MANY_WHITE_PAWNS
    | chess.STATUS_TOO_MANY_BLACK_PAWNS
    | chess.STATUS_TOO_MANY_WHITE_PIECES
    | chess.STATUS_TOO_MANY_BLACK_PIECES
    | chess.STATUS_PAWNS_ON_BACKRANK
    | chess.STATUS_BAD_CASTLING_RIGHTS
)


def _fix_castling(parts: list, had_castling: bool, warnings: list) -> None:
    if not had_castling:
        parts[2] = '-'
        return
    declared = parts[2]
    if declared == '-':
        return
    actual = compute_castling(parts[0])
    kept = ''.join(ch for ch in declared if ch in actual)
    if kept != declared:
        parts[2] = kept or '-'
        warnings.append(
            f'Removed invalid castling rights ({declared} -> {parts[2]}).'
        )


def sanitize_fen(fen: str) -> FenSanitizeResult:
    warnings = []
    stripped = fen.strip()
    parts = stripped.split()
    if not stripped or len(parts) > 6:
        return FenSanitizeResult(fen='', valid=False, error=INVALID_FEN_MESSAGE)

    had_castling = len(parts) > 2
    while len(parts) < 6:
        parts.append(DEFAULT_FIELDS[len(parts) - 1])

    try:
        board = chess.Board(' '.join(parts))
    except ValueError:
        return FenSanitizeResult(fen='', valid=False, error=INVALID_FEN_MESSAGE)

    _fix_castling(parts, had_castling, warnings)

    # Rebuild from the updated parts: the castling fix only mutates the parts
    # list, and the board created above still carries the declared (invalid)
    # castling rights, which would wrongly flag STATUS_BAD_CASTLING_RIGHTS.
    if chess.Board(' '.join(parts)).status() & UNRECOVERABLE_MASK:
        return FenSanitizeResult(fen='', valid=False, error=INVALID_FEN_MESSAGE)

    return FenSanitizeResult(fen=' '.join(parts), valid=True, warnings=warnings)
```

Note: `_fix_backrank_pawns` is added in Task 3; for now `sanitize_fen` handles only parse/normalize/castling.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_fen_sanitizer.py -q`
Expected: PASS (5 tests in the file: 1 from Task 1 + 4 new).

Also run full suite: `python -m pytest tests/ -q` — Expected: PASS (31).

- [ ] **Step 5: Commit**

```bash
git add -f chess-vision-fast/backend/app/fen_sanitizer.py chess-vision-fast/backend/tests/test_fen_sanitizer.py
git commit -m "feat: sanitize FEN parse, normalization and castling rights"
```

---

### Task 3: Back-rank pawn heuristic + unrecoverable conditions

**Files:**
- Modify: `chess-vision-fast/backend/app/fen_sanitizer.py`
- Modify: `chess-vision-fast/backend/tests/test_fen_sanitizer.py`

**Interfaces:**
- Consumes: `sanitize_fen`, `INITIAL_COUNTS`, `FILE_PIECE`, `FIX_PRIORITY` (Task 1), `FenSanitizeResult`, `_fix_castling`, `UNRECOVERABLE_MASK` (Task 2).
- Produces: (internal) `_counts_for(board, color) -> dict`, `_backrank_pawns(board) -> List[str]`,
  `_fix_backrank_pawns(board, warnings) -> bool` (returns `False` when a back-rank pawn cannot be resolved). No external consumers.

- [ ] **Step 1: Write the failing tests**

Append to `chess-vision-fast/backend/tests/test_fen_sanitizer.py`:

```python
def test_backrank_pawn_replaced_and_castling_recovered():
    # a1 is a misdetected pawn; the missing rook is restored, which in turn
    # makes the declared castling right Q valid. Proves pawn fix runs first.
    result = sanitize_fen('4k3/8/8/8/8/8/8/P3K3 w KQkq - 0 1')
    assert result.valid is True
    assert result.fen == '4k3/8/8/8/8/8/8/R3K3 w Q - 0 1'
    assert any('a1' in w for w in result.warnings)


def test_backrank_black_pawn_replaced_with_rook():
    result = sanitize_fen('7p/8/8/8/8/8/8/4K2k w - - 0 1')
    assert result.valid is True
    assert result.fen == '7r/8/8/8/8/8/8/4K2k w - - 0 1'
    assert any('h8' in w for w in result.warnings)


def test_backrank_pawn_e1_with_full_material_unrecoverable():
    # e1 pawn while the white king is already on g2 and all other pieces are at
    # their initial counts: no piece type has a deficit, so the pawn is a
    # contradiction -> unrecoverable.
    fen = '4k3/8/8/8/8/8/6K1/RNBQPBNR w - - 0 1'
    result = sanitize_fen(fen)
    assert result.valid is False
    assert result.fen == ''


def test_two_backrank_pawns_single_deficit_unrecoverable():
    # a1 and h1 are pawns but only one rook is missing; the second pawn has no
    # piece type to restore into.
    fen = '4k3/8/8/8/8/8/R7/PNBQKBNP w - - 0 1'
    result = sanitize_fen(fen)
    assert result.valid is False
    assert result.fen == ''


def test_garbage_fen_unrecoverable():
    result = sanitize_fen('not a fen at all')
    assert result.valid is False
    assert result.fen == ''
    assert result.error == INVALID_FEN_MESSAGE
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_fen_sanitizer.py -q`
Expected: FAIL — `test_garbage_fen_unrecoverable` may pass already, but the four pawn tests fail
(`AssertionError` because the pawns are not replaced / status flags the position unrecoverable).

- [ ] **Step 3: Implement the back-rank pawn fix and hook it in**

Append to `chess-vision-fast/backend/app/fen_sanitizer.py`:

```python
def _counts_for(board: chess.Board, color: bool) -> dict:
    counts = {p: 0 for p in 'RNBQK'}
    for piece in board.piece_map().values():
        if piece.color == color and piece.piece_type != chess.PAWN:
            counts[piece.symbol().upper()] += 1
    return counts


def _backrank_pawns(board: chess.Board) -> list:
    return sorted(
        chess.square_name(sq)
        for sq, piece in board.piece_map().items()
        if piece.piece_type == chess.PAWN and chess.square_rank(sq) in (0, 7)
    )


def _fix_backrank_pawns(board: chess.Board, warnings: list) -> bool:
    for sq_name in _backrank_pawns(board):
        sq = chess.parse_square(sq_name)
        color = board.piece_at(sq).color
        counts = _counts_for(board, color)
        deficits = [t for t in 'RNBQK' if counts[t] < INITIAL_COUNTS[t]]
        expected = FILE_PIECE[sq_name[0]]

        candidates = []
        if expected in deficits:
            candidates.append(expected)
        if expected != 'K' and 'K' in deficits and 'K' not in candidates:
            candidates.append('K')
        for t in FIX_PRIORITY:
            if t in deficits and t not in candidates:
                candidates.append(t)

        if not candidates:
            return False

        chosen = candidates[0]
        symbol = chosen.lower() if color == chess.BLACK else chosen
        board.set_piece_at(sq, chess.Piece.from_symbol(symbol))
        display = chosen.lower() if color == chess.BLACK else chosen
        warnings.append(f'Back-rank pawn on {sq_name} replaced with {display}.')
    return True
```

Then update `sanitize_fen` so the pawn fix runs before the castling fix and the board part is
re-synced before castling is computed. Replace the body between the `try/except` parse and the
final return with:

```python
    try:
        board = chess.Board(' '.join(parts))
    except ValueError:
        return FenSanitizeResult(fen='', valid=False, error=INVALID_FEN_MESSAGE)

    if not _fix_backrank_pawns(board, warnings):
        return FenSanitizeResult(fen='', valid=False, error=INVALID_FEN_MESSAGE)
    parts[0] = board.fen().split()[0]

    _fix_castling(parts, had_castling, warnings)

    if chess.Board(' '.join(parts)).status() & UNRECOVERABLE_MASK:
        return FenSanitizeResult(fen='', valid=False, error=INVALID_FEN_MESSAGE)

    return FenSanitizeResult(fen=' '.join(parts), valid=True, warnings=warnings)
```

Heuristic rules implemented by `_fix_backrank_pawns`:
- A back-rank pawn may only become a piece type that is below its initial count (`deficits`).
- The column-expected piece (a/h→R, b/g→N, c/f→B, d→Q, e→K) is preferred when it has a deficit.
- A king (`K`) is only assignable to a NON-`e` file pawn when that color's king is missing.
- If no candidate exists, the FEN is unrecoverable.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/ -q`
Expected: PASS (31 existing + 10 in `test_fen_sanitizer.py`).

- [ ] **Step 5: Commit**

```bash
git add -f chess-vision-fast/backend/app/fen_sanitizer.py chess-vision-fast/backend/tests/test_fen_sanitizer.py
git commit -m "feat: repair back-rank pawns and harden FEN validation"
```

---

### Task 4: Wire the sanitizer into the API routes

**Files:**
- Modify: `chess-vision-fast/backend/app/api/routes.py`
- Modify: `chess-vision-fast/backend/tests/test_api.py`

**Interfaces:**
- Consumes: `sanitize_fen`, `INVALID_FEN_MESSAGE` from `backend.app.fen_sanitizer`.
- Produces: every response from `/api/detect`, `/api/detect_and_move`, `/api/best_move` includes a new
  `fen_warnings: List[str]` field (additive; existing keys unchanged). Unrecoverable FENs return
  `fen=''`, `error=INVALID_FEN_MESSAGE`. `detect`/`detect_and_move` return the SANITIZED FEN (not the raw detected one).

- [ ] **Step 1: Write the failing tests**

Append to `chess-vision-fast/backend/tests/test_api.py`:

```python
from backend.app.fen_sanitizer import INVALID_FEN_MESSAGE


def test_best_move_invalid_fen_returns_clear_error():
    routes._chess_service = StockfishService(StockfishEngine(command=MOCK))
    response = client.post('/api/best_move', json={'fen': 'not a fen at all'})
    assert response.status_code == 200
    data = response.json()
    assert data['uci'] is None
    assert data['error'] == INVALID_FEN_MESSAGE


def test_detect_and_move_includes_fen_warnings():
    routes._chess_service = StockfishService(StockfishEngine(command=MOCK))
    files = {'file': ('board.png', _png_bytes('4k3/8/8/8/8/8/8/4K3 w - - 0 1'), 'image/png')}
    response = client.post('/api/detect_and_move', files=files)
    assert response.status_code == 200
    data = response.json()
    assert 'fen_warnings' in data
    assert isinstance(data['fen_warnings'], list)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_api.py -q`
Expected: FAIL — `test_best_move_invalid_fen_returns_clear_error` returns the generic
`Error in analysis: ...` message; `test_detect_and_move_includes_fen_warnings` fails on the missing key.

- [ ] **Step 3: Modify `routes.py`**

Add the import at the top of `chess-vision-fast/backend/app/api/routes.py`:

```python
from ..fen_sanitizer import FenSanitizeResult, INVALID_FEN_MESSAGE, sanitize_fen
```

**`/api/detect`** — replace the success branch (after the confidence gate) with:

```python
    sanitized = sanitize_fen(result.fen)
    if not sanitized.valid:
        return {
            'fen': '',
            'board_image_base64': result.board_image_base64,
            'squares': [],
            'confidence': result.confidence,
            'orientation': result.orientation if hasattr(result, 'orientation') else 'w-bottom',
            'fen_warnings': [],
            'error': INVALID_FEN_MESSAGE,
        }
    return {
        'fen': sanitized.fen,
        'board_image_base64': result.board_image_base64,
        'squares': _squares_to_response(result.squares),
        'confidence': result.confidence,
        'orientation': result.orientation if hasattr(result, 'orientation') else 'w-bottom',
        'fen_warnings': sanitized.warnings,
        'error': result.error,
    }
```

Also add `'fen_warnings': [],` to the low-confidence return in `detect`.

**`/api/best_move`** — replace the `try` block start with:

```python
    try:
        sanitized = sanitize_fen(payload.fen)
        if not sanitized.valid:
            return {
                'uci': None, 'san': None,
                'score': {'cp': None, 'mate': None},
                'pv': [], 'evaluation_text': None,
                'turn': None, 'depth': None, 'source': 'stockfish',
                'fen_warnings': [],
                'error': INVALID_FEN_MESSAGE,
            }
        service = get_chess_service(settings)
        result = service.analyze_position(sanitized.fen, turn=payload.turn, depth=payload.depth)
        return {
            'uci': result['uci'],
            'san': result['san'],
            'score': result['score'],
            'pv': result['pv'],
            'evaluation_text': result['evaluation_text'],
            'turn': result['turn'],
            'depth': result['depth'],
            'source': result['source'],
            'fen_warnings': sanitized.warnings,
        }
```

**`/api/detect_and_move`** — after the confidence gate, sanitize before analysis. Add
`sanitized = sanitize_fen(detection.fen)` and an unrecoverable branch right after it:

```python
    sanitized = sanitize_fen(detection.fen)
    if not sanitized.valid:
        return {
            'fen': '', 'best_move': None, 'uci': None, 'san': None,
            'score': {'cp': None, 'mate': None}, 'pv': [],
            'evaluation_text': None, 'overlay_image_base64': overlay_image_base64,
            'squares': squares, 'confidence': detection.confidence,
            'fen_warnings': [],
            'error': INVALID_FEN_MESSAGE,
        }
```

In the success branch of `detect_and_move`, call `service.analyze_position(sanitized.fen, ...)`,
use `'fen': sanitized.fen`, and add `'fen_warnings': sanitized.warnings,` to the success and the
catch-all error responses. Add `'fen_warnings': [],` to the low-confidence response of
`detect_and_move` as well.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/ -q`
Expected: PASS (31 + 2 new API tests + 10 sanitizer tests).

- [ ] **Step 5: Commit**

```bash
git add -f chess-vision-fast/backend/app/api/routes.py chess-vision-fast/backend/tests/test_api.py
git commit -m "feat: validate and sanitize FEN across all API routes"
```

---

### Task 5: Show FEN corrections in the frontend

**Files:**
- Modify: `chess-vision-fast/frontend/src/App.jsx`
- Modify: `chess-vision-fast/frontend/src/components/BoardPreview.jsx`

**Interfaces:**
- Consumes: `data.fen_warnings` from `/api/detect`, `/api/detect_and_move`, `/api/best_move` responses.
- Produces: `fenWarnings` state in `App` passed to `BoardPreview` as `fenWarnings: Array<string>`.

- [ ] **Step 1: Add the state and wiring in `App.jsx`**

Edit `chess-vision-fast/frontend/src/App.jsx`:

- Add state next to the other `useState` calls:

```jsx
  const [fenWarnings, setFenWarnings] = useState([])
```

- In `handleResult`, add after `setConfidence(data.confidence)`:

```jsx
    setFenWarnings(data.fen_warnings || [])
```

- In `handleManualBestMove`, add after `setPv(response.pv || [])`:

```jsx
      setFenWarnings(response.fen_warnings || [])
```

- In `handleClearContext`, add after `setPv([])`:

```jsx
      setFenWarnings([])
```

- Pass it to `BoardPreview` (add the prop to the existing `<BoardPreview ... />`):

```jsx
                  fenWarnings={fenWarnings}
```

- [ ] **Step 2: Render the warnings in `BoardPreview.jsx`**

Edit `chess-vision-fast/frontend/src/components/BoardPreview.jsx`:

- Add `fenWarnings` to the destructured props:

```jsx
export default function BoardPreview({
  fen,
  bestMove,
  confidence,
  evaluationText,
  score,
  pv,
  error,
  fenWarnings,
}) {
```

- Insert this block immediately after the existing error block (the `{error && (...)}` section):

```jsx
      {fenWarnings && fenWarnings.length > 0 && (
        <div className="rounded border border-amber-500/30 bg-amber-500/10 p-2">
          <p className="text-xs font-semibold text-amber-400 mb-1">FEN corrected</p>
          {fenWarnings.map((warning, index) => (
            <p key={index} className="text-xs text-amber-300">{warning}</p>
          ))}
        </div>
      )}
```

- [ ] **Step 3: Verify the frontend builds**

Run from `chess-vision-fast/frontend`:
`npm run build`
Expected: SUCCESS (vite build completes without errors; the browserslist/baseline warnings are pre-existing and harmless).

- [ ] **Step 4: Commit**

```bash
git add chess-vision-fast/frontend/src/App.jsx chess-vision-fast/frontend/src/components/BoardPreview.jsx
git commit -m "feat: surface FEN corrections in the UI"
```

---

### Task 6: Final verification

- [ ] **Step 1: Run the full backend suite**

Run from `chess-vision-fast/backend`:
`python -m pytest tests/ -q`
Expected: PASS (31 + 10 sanitizer + 2 API = 43 tests).

- [ ] **Step 2: Manual end-to-end check**

Run from `chess-vision-fast/backend`:

```python
python -c "
import sys
sys.path.insert(0, r'..')
from backend.app.fen_sanitizer import sanitize_fen
r = sanitize_fen('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBN1 w KQkq - 0 1')
print('valid:', r.valid)
print('fen:', r.fen)
print('warnings:', r.warnings)
"
```

Expected: `valid: True`, `fen: ...RNBQKBN1 w Qkq - 0 1`, warnings contain the castling message.

- [ ] **Step 3: Update the SDD ledger**

Append a `## POST-PLAN FEATURE: FEN sanitizer & validation` section to
`.superpowers/sdd/progress.md` summarizing the module, the 6 commits, and the final test count.

- [ ] **Step 4: Commit the ledger**

```bash
git add .superpowers/sdd/progress.md
git commit -m "docs: record FEN sanitizer implementation in SDD ledger"
```
