# Fix Wave Report — Final Whole-Branch Review

Worktree: `C:\Users\leoan\Desktop\chessAI\.worktrees\local-stockfish-cv` (branch `feature/local-stockfish-cv`)
Commit: `896036f` — "fix: honor FEN side-to-move, wire orientation to detector, reject invalid en-passant FENs"

## Per-Fix Summary

### Fix 1 — Turn: default to the FEN's own side when no `turn` is given
Added module-level pure helper `resolve_active_color(fen, turn=None)` in
`backend/app/services/stockfish_service.py` and replaced the hardcoded
`active = turn if turn in ('w','b') else 'w'` in `analyze_position` (line 48) with
`active = resolve_active_color(fen, turn)`. Everything else (parts[1] overwrite, castling, ep, etc.)
unchanged. No engine-backed black-to-move test added, per the brief's warning (mock always plays e2e4).

### Fix 2 — Orientation: wire the query through to the detector
- `backend/app/api/routes.py`: `/api/detect` and `/api/detect_and_move` now call
  `detector.detect(image, orientation)`.
- `backend/app/cv_detector.py`: `detect(self, image, orientation=None)` resolves the final
  orientation (`front`→`w-bottom`, `back`→`w-top`, else `_detect_orientation(squares)`). For
  `w-top` it remaps each `SquareDetection.square` to `_square_at(7-r, 7-c)` where `r,c` are derived
  from the bbox (`int(s.bbox[1] // CELL)`, `int(s.bbox[0] // CELL)`). `final_orientation` is passed
  to `matrix_to_fen` (no pre-flip of the matrix) and set on the returned `DetectionResult`. Docstring
  documents `orientation: 'auto' | 'front' | 'back' | None`. Classification loop left exactly as-is.

### Fix 3 — UNRECOVERABLE_MASK: add STATUS_INVALID_EP_SQUARE
`backend/app/fen_sanitizer.py`: added `| chess.STATUS_INVALID_EP_SQUARE` to `UNRECOVERABLE_MASK`.
Empirically confirmed with python-chess 1.11.2: `'... w KQkq e3 0 1'` → status 512, valid
`'... w KQkq d6 0 3'` → status 0.

### Fix 4 — Success-path fen_warnings test
Added `test_detect_returns_fen_warnings_on_castling_prune` to `tests/test_api.py`. **Notable: this
test PASSED on pre-fix code** — the success path already surfaced real warnings (detector emits
`KQkq`, sanitizer prunes `K` with the h1 rook missing). The test now pins that behavior rather than
fixing a defect.

### Fix 5 — Frontend White/Black Turn toggle
Added a "Turn" control (White / Black buttons) to the Engine Settings section of
`frontend/src/App.jsx`, next to Depth and Board, wired to `setTurn('w')`/`setTurn('b')` with the
same styling pattern as the Depth buttons.

## TDD / Test Evidence

RED phase (new tests added, implementations absent):
```
$ python -m pytest tests/test_stockfish_service.py tests/test_cv_detector.py tests/test_fen_sanitizer.py tests/test_api.py -q
- ImportError: cannot import name 'resolve_active_color' ...   (Fix 1)
- FAILED tests/test_cv_detector.py::test_detect_starting_position_back_orientation_w_top
- FAILED tests/test_cv_detector.py::test_detect_starting_position_front_orientation_w_bottom
  TypeError: CVBoardDetector.detect() got an unexpected keyword argument 'orientation'   (Fix 2)
- FAILED tests/test_fen_sanitizer.py::test_invalid_en_passant_square_unrecoverable
  AssertionError: assert True is False (FenSanitizeResult valid=True)   (Fix 3)
3 failed, 24 passed; test_api's new test (Fix 4) passed immediately.
```

GREEN phase (all fixes implemented):
```
$ python -m pytest tests/ -q
52 passed, 2 warnings in 6.40s
```
(43 pre-existing + 9 new: 4 resolve_active_color + 2 orientation + 2 en-passant + 1 fen_warnings)

Frontend:
```
$ npm run build
✓ 34 modules transformed.  ✓ built in 2.32s   (SUCCESS)
```

Note: an initial build failed due to an extra `</div>` my first edit introduced in App.jsx (Turn div
was nested inside the Board container's parent prematurely); fixed by removing the stray closing tag,
verified structure, rebuild SUCCESS.

## Files Changed
- `chess-vision-fast/backend/app/services/stockfish_service.py` — resolve_active_color helper + use
- `chess-vision-fast/backend/app/api/routes.py` — orientation passed to detector (2 routes)
- `chess-vision-fast/backend/app/cv_detector.py` — orientation param, final_orientation resolution, w-top square remap
- `chess-vision-fast/backend/app/fen_sanitizer.py` — UNRECOVERABLE_MASK + STATUS_INVALID_EP_SQUARE
- `chess-vision-fast/frontend/src/App.jsx` — Turn toggle
- `chess-vision-fast/backend/tests/test_stockfish_service.py` — 4 pure helper tests
- `chess-vision-fast/backend/tests/test_cv_detector.py` — 2 orientation tests
- `chess-vision-fast/backend/tests/test_fen_sanitizer.py` — 2 en-passant tests
- `chess-vision-fast/backend/tests/test_api.py` — success-path fen_warnings test
- `.superpowers/sdd/progress.md` — `## FINAL REVIEW FIX WAVE` section

Test files were already tracked (no `git add -f` needed).

## Deviations from the Brief
- Fix 4's test passed on pre-fix code; the brief expected it to demonstrate the success path, which
  it does — but there was no actual defect to fix there. Implemented exactly as written.
- Single commit (not split per fix); message as suggested in the brief.

## Concerns
- Fix 4 passed without any code change: if the reviewer intended it to exercise a currently-broken
  path, it does not (the success path already worked). The test is still valuable as a pin.
- Frontend build emits pre-existing caniuse-lite / baseline-browser-mapping staleness warnings (not
  from this change).
