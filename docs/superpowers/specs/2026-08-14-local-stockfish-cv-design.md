# Local Stockfish + Classical CV Design

Date: 2026-08-14
Status: Approved design (pending implementation)

## Goal

Replace the Gemini AI pipeline in `chess-vision-fast` with a fully local one:

1. **Board detection**: a classical computer-vision algorithm (no LLM) that extracts a FEN from a chess.com screenshot.
2. **Best move**: Stockfish running locally (no LLM), returning best move, score, and principal variation.
3. Remove all Gemini code, config, and UI.

**Target input**: clean chess.com screenshots (board facing forward, flat colors, default piece set). The default chess.com piece set is the classification reference.

## Architecture

```
chess.com screenshot
      │
      ▼
┌─────────────────────────┐   ┌──────────────────────────┐
│ app/cv_detector.py      │   │ app/stockfish_engine.py  │
│  BoardFinder            │   │  _find/download binary   │
│  SquareGrid (8x8)       │   │  analyze_position(fen)   │
│  OccupancyDetector      │   │   → bestmove, score, PV  │
│  PieceClassifier (tpl)  │   └────────────┬─────────────┘
└────────────┬────────────┘                │
             │ FEN                         │
             ▼                             ▼
┌──────────────────────────────────────────────────────┐
│ app/services/stockfish_service.py                     │
│  maintains context (turn, move history, castling)     │
│  validates FEN with python-chess                      │
│  generates evaluation text from score                 │
└──────────────────────────────────────────────────────┘
             │  JSON (move, score, PV, text)
             ▼
       React frontend
```

### Modules

**New**
- `backend/app/cv_detector.py` — classical CV pipeline → FEN.
- `backend/app/stockfish_engine.py` — binary discovery + UCI via `chess.engine.SimpleEngine`.
- `backend/app/services/stockfish_service.py` — replaces `gemini_chess_service.py`.
- `backend/app/assets/pieces/` — 12 reference PNG templates (6 white + 6 black) from the default chess.com piece set, with an attribution note.

**Removed**
- `backend/app/gemini_detector.py`
- `backend/app/services/gemini_chess_service.py`
- Routes `/api/change_model`, `/api/current_model`
- `GEMINI_API_KEY` / `GEMINI_MODEL` settings; `google-generativeai` dependency.

**Adjusted**
- `backend/app/utils.py` — settings: add `STOCKFISH_PATH`, `STOCKFISH_DEPTH`, `STOCKFISH_AUTO_DOWNLOAD`; remove Gemini settings.
- `backend/app/detector.py` — `DetectorFactory` only creates the CV detector; `fen_from_squares` gains orientation support.
- `backend/app/api/routes.py` — endpoint contracts below.
- `backend/requirements.txt` — drop `google-generativeai` (OpenCV, Pillow, numpy, python-chess, fastapi stay).
- Frontend — remove model selector and retrospective; add flip toggle, depth selector, evaluation bar, generated text, move history.

## CV Detection Pipeline

### A. Board detection (`BoardFinder`)
1. Grayscale → blur → adaptive threshold → `findContours`.
2. Find the largest quadrilateral with aspect ratio ≈ 1:1 (`approxPolyDP`). This filters out non-board page elements when the screenshot includes the full chess.com page.
3. `getPerspectiveTransform` → warp to 480×480.
4. **Verify**: sample the 8×8 grid centers and check that colors alternate light/dark (board pattern). On failure → error "board not detected".

### B. Grid and occupancy (`SquareGrid` + `OccupancyDetector`)
- Each square = 60×60; use the central ~60% of each square to avoid piece bleed across boundaries.
- Empty-square colors are derived **from the board itself** (two dominant colors via light k-means), not hardcoded — supports light/dark themes.
- A square is **occupied** if its central color deviates from both empty colors. Piece is **white** if luminance is higher than the background, **black** if lower.

### C. Piece classification (`PieceClassifier`)
- Crop the piece → scale to template size → `cv2.matchTemplate` with normalized cross-correlation against the 12 templates.
- Best match above a threshold; below threshold → "unknown" square → invalid FEN with a clear error naming the square.

### D. Orientation, turn, castling, en passant
- **Orientation**: auto heuristic (compare luminance of the two back-rank corner pieces; brighter side = white) + manual "flip" toggle in the UI as override.
- **Turn**: maintained by the service across moves (alternates after each analysis). The API accepts an explicit `turn` (`w`/`b`) for the first analysis; UI toggle as backup.
- **Castling**: `KQkq` only if the corresponding king and rooks are on their original squares; otherwise `-`.
- **En passant**: `-` by default; inferred from context if a pawn advances two squares.

### E. Stockfish engine (`stockfish_engine.py`)
- Binary discovery: `STOCKFISH_PATH` (env) → common paths (Program Files, Downloads, Desktop) → auto-download the official GitHub release (Windows x86-64 avx2) to `backend/bin/`.
- `chess.engine.SimpleEngine.popen_uci()`; `analyze_position(fen, depth=15)` → `bestmove`, `score` (cp or mate), `pv` (principal variation, first 6 moves in SAN).
- `StockfishService` builds the complete FEN (turn/castling/EP), validates with `chess.Board`, and generates evaluation text from the score (e.g., "Mate in 3 for White", "+1.2 White advantage").

## API Contract

| Endpoint | Change |
|---|---|
| `POST /api/detect` | No `model`. Returns `fen`, `squares` (per-square piece), `confidence`, `orientation` |
| `POST /api/detect_and_move` | Body: image + `orientation` (auto/front/back) + optional `turn` (w/b). Returns FEN, overlay, move, score, PV, text |
| `POST /api/best_move` | Body: `fen` + optional `turn`. Returns `uci`, `san`, `score {cp, mate}`, `pv[]`, `evaluation_text`, `source: stockfish` |
| `POST /api/clear_context` | Kept |
| `GET /api/context` | **New**: move history (replaces retrospective, which requires an LLM) |
| `POST /api/change_model` / `GET /api/current_model` | **Removed** |

## Frontend Changes

- **Remove**: Gemini model selector, Retrospective button.
- **Add**: "Flip board" toggle (sends `orientation`), engine depth selector (10/15/20), horizontal evaluation bar (green/white split), evaluation text, move history.
- **Keep**: image upload (drag & drop / paste), overlay with the best-move arrow, download button.

## Error Handling

- Board not found / invalid FEN → specific message ("Make sure the screenshot shows the full board facing forward").
- Unknown square during classification → error naming the square; suggest flipping or retaking the screenshot.
- Stockfish not found and download failed → manual install instructions.
- Turn ambiguity: if context turn differs from user's, show a non-blocking notice.

## Testing (pytest, backend)

- **Synthetic render**: generate an 8×8 board from a FEN with PIL (chess.com colors + pieces) and test the full round-trip detection → FEN → move. Cases: starting position, mid-game, empty squares, flipped board.
- **Stockfish mock**: fake UCI engine to test `analyze_position` without a real binary.
- **Evaluation text**: table-driven tests for cp/mate → text.
- **`fen_from_squares`**: front/back orientation.

## Out of Scope

- Physical board photos (perspective/lighting/3D pieces) — detection is tuned for clean chess.com screenshots.
- Custom chess.com piece sets (classification uses the default set reference templates).
- LLM-based retrospective/strategic explanations.
