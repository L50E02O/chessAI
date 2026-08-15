# FEN Sanitizer & Validation Module

Date: 2026-08-14
Branch: feature/local-stockfish-cv (worktree .worktrees/local-stockfish-cv)

## Problem

The CV detector generates a FEN that always carries castling rights `KQkq`
(`fen.py` `matrix_to_fen` default), regardless of the actual piece placement, and
can emit impossible positions (e.g. a pawn on rank 1/8 from a misclassified
piece). Today:

- `/api/detect` and `/api/detect_and_move` return that raw FEN to the UI; the
  displayed FEN can claim castling rights that the position does not support.
- `/api/best_move` sends any FEN straight to Stockfish; a syntactically invalid
  FEN surfaces only as a generic `Error in analysis: ...` from the route
  try/except, which does not tell the user the FEN itself is the problem.
- `python-chess` `Board(fen)` only raises on *syntax* errors. Position-level
  problems (pawns on back rank, missing kings, illegal castling rights, piece
  count violations) are silently accepted and only visible via `board.status()`.

Goal: a validation + sanitization layer that runs before any analysis, repairs
what is confidently repairable, and returns a clear, specific error message for
anything unrecoverable.

## Scope

- Backend is Python → validation uses `python-chess` (no chess.js).
- Sanitization applies to all three routes: `/api/detect`, `/api/detect_and_move`,
  `/api/best_move`.
- Repairable issues: illegal castling rights, back-rank pawns (via the
  initial-arrangement piece-count heuristic).
- Unrecoverable issues → the exact UI message:
  `Invalid FEN generated from board image. Please check piece placement or re-upload.`
- Corrections are reported to the UI as visible warnings (`fen_warnings`).

## Section 1 — Module: `backend/app/fen_sanitizer.py`

Pure functions; no dependency on CV code or the engine.

```python
@dataclass
class FenSanitizeResult:
    fen: str            # sanitized FEN (6 fields) or '' if unrecoverable
    valid: bool         # True if the final FEN is analyzable
    warnings: list[str] # human-readable messages describing each fix
    error: str | None   # descriptive message when unrecoverable

def sanitize_fen(fen: str) -> FenSanitizeResult
def compute_castling(board_part: str) -> str   # moved from stockfish_service.py
```

### Order of operations in `sanitize_fen`

Order matters: restoring a piece on a back-rank square can change castling
eligibility, so back-rank pawns are fixed before castling.

1. **Parse.** `chess.Board(fen)` inside try/except. A `ValueError` (bad syntax)
   → unrecoverable. Input FEN is normalized to 6 fields (pad missing fields with
   `w KQkq - 0 1`) so board-only FENs (as the detector/service produce) are
   accepted.
2. **Fix back-rank pawns.** For each pawn on rank 1 or 8: replace with the piece
   type that has a deficit vs. the initial arrangement
   (R=2, N=2, B=2, Q=1, K=1), preferring the column-expected piece
   (a/h→R, b/g→N, c/f→B, d→Q, e→K) when that type has a deficit; otherwise any
   deficit type (order R, N, B, Q; K only if that color's king is missing).
   Each replacement appends a warning. If a back-rank pawn remains with no
   deficit → unrecoverable (impossible position).
3. **Fix castling.** Compare the declared castling field against
   `compute_castling` (king present on e1/e8 + rook on a1/h1/a8/h8). Remove
   invalid rights; warn when something was removed. A declared `-` is left as-is
   even if pieces would allow rights (rights cannot be invented without move
   history).
4. **Final validation.** Rebuild the FEN and re-run `chess.Board`. Unrecoverable
   if: missing king for a side, more than one king of a color, more than 16
   pieces or more than 8 pawns of a color, remaining back-rank pawns, or illegal
   castling rights remaining. Everything else → `valid=True` with the sanitized
   FEN (odd-but-analyzable positions pass; `warnings` may note them).

## Section 2 — Route integration (`backend/app/api/routes.py`)

- `/api/detect` and `/api/detect_and_move`: after the confidence threshold gate,
  call `sanitize_fen(result.fen)`.
  - `not valid` → response with `fen=''` and
    `error='Invalid FEN generated from board image. Please check piece placement or re-upload.'`
  - `valid` → return the sanitized FEN and add `fen_warnings: List[str]` to the
    payload (empty list when nothing was fixed).
- `/api/best_move`: run the incoming FEN through `sanitize_fen` before calling
  the service. Unrecoverable → same error message above. Valid → pass the
  sanitized FEN to the engine. The existing try/except around the engine call is
  retained as the final safety net.

The new `fen_warnings` field is additive and does not break the existing frontend
contract.

## Section 3 — `StockfishService` refactor

- `compute_castling` moves to `fen_sanitizer.py` (single source of truth);
  `backend/app/services/stockfish_service.py` imports it. No behavior change:
  `analyze_position` keeps recomputing castling on every analysis, now via the
  imported function.
- `en_passant_from_history` stays in the service (history-context specific).
- Sanitization lives at the route layer only; the service keeps its current
  responsibilities.

## Section 4 — Frontend

- `App.jsx`: store `fenWarnings` from `data.fen_warnings`.
- `BoardPreview.jsx`: render `fenWarnings` in amber near the FEN box (same visual
  language as the "Click Analyze" hint). The existing error block already shows
  the specific error message; no change to error handling needed.

## Section 5 — Testing (TDD)

New `backend/tests/test_fen_sanitizer.py`:

- Valid FEN → unchanged, `valid=True`, no warnings.
- `KQkq` with h1 rook missing → rights pruned, warning.
- Castling rights without a king → unrecoverable.
- Pawn on a1 → replaced with `R` (deficit heuristic), warning.
- Pawn on h8 → replaced with `r`.
- Pawn on e1 with white king present and no deficit → unrecoverable.
- Two back-rank pawns with a single deficit → one restored, other → invalid.
- Garbage string → unrecoverable + error message.
- Board-only FEN (1 field) → normalized to 6 fields.
- Ordering: back-rank pawn fixed before castling (restored rook → castling right
  recovered).

`backend/tests/test_api.py` additions:

- `/api/best_move` with an invalid FEN returns the exact error message.

All 31 existing tests must keep passing.

## Out of scope

- En-passant normalization (context/history dependent; handled by the service).
- Halfmove clock / fullmove number semantics.
- Detecting illegal-but-analyzable positions (e.g. king in double check) as
  errors; they are allowed through with warnings.
- Any chess.js/frontend-side validation.
