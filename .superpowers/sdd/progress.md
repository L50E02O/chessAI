# SDD Progress Ledger - local-stockfish-cv
## Task 1: FEN matrix orientation support
- Status: DONE, reviewed and APPROVED
- Commits: 500bbb4 feat: add board orientation support to FEN matrix builder
- BASE 1b34c9f HEAD 500bbb4; tests 4/4; no findings

## Task 2: Piece template assets + download script
- Status: DONE, reviewed and APPROVED (approved deviation: lowercase URL)
- Commits: ea6a196 feat: add chess.com piece templates and download script
- BASE 500bbb4 HEAD ea6a196; 12 PNGs committed; no findings

## Task 3: CV board detection (BoardFinder)
- Status: DONE, reviewed APPROVED-with-concerns
- Commits: 87be76d feat: add CV board detection with perspective warp and verification
- BASE ea6a196 HEAD 87be76d; tests 5/5
- Deviations verified OK: tests/__init__.py (ultralytics shadow), PIECES_DIR fix, force-add test
- FOLLOW-UP tracked: _crop_frame is a no-op (dilation overshoot -> 15px green frame band remains); MUST be absorbed in Tasks 4/5

- PLAN FIX 47c1c58 docs: fix d1 cell coordinates in Task 4 classify test (verified empirically: d1 = img[476:536, 236:296])

## Task 4: Square occupancy and piece classification
- Status: DONE, reviewed APPROVED-with-concerns (both deviations verified sound)
- Commits: c31d8a4 feat: add square occupancy and piece classification (BASE 87be76d)
- Deviations: ratio 0.6 center sampling in square_state; black-mask in _extract_piece; tests unchanged
- Minor carried: template backdrop asymmetry (_template_piece), empty_colors only shape-asserted, coverage gaps (dark pieces, real-board robustness)

## Pipeline correction (pre-Task 5)
- Commits: 8a35d2b fix: correct CV pipeline for reliable detection on synthetic renders (BASE c31d8a4)
- find_board: green-frame interior segmentation (snap-to-480, INTER_NEAREST), contour = fallback + _verify_board (<=8 violations)
- square_state/_extract_piece: median background + piece-pixel color; _template_piece zeroes transparent bg; empty_colors deterministic (setRNGSeed)
- board_renderer white_top: true 180° rotation (chess.square(7-c, r)) matching matrix_to_fen w-top semantics
- VERIFIED: 9/9 tests; full pipeline 32/32 on START, MIDGAME, START-flip; confidence_from_squares = 0.809 > 0.8
- Plan updated with "Plan Corrections" section + Task 3/4 reference code synced

## Task 5: CVBoardDetector orchestrator + settings + factory
- Status: DONE, reviewed APPROVED-WITH-CONCERNS (no blocking findings)
- Commits: f7256c5 feat: add CV board detector orchestrator with orientation detection
- BASE 8a35d2b HEAD f7256c5; tests 13/13; scope exact (4 files, cv_detector.py purely appended)
- Reviewer verified end-to-end: START 0.809>0.8/32 squares, MIDGAME exact, flipped K/Q intact, bboxes 480x480 coords, error path sets error/fen=''/conf 0.0; routes import clean; gemini fields retained (still referenced until Task 8)
- FOLLOW-UP for Task 8: blank/solid screenshots can yield success-with-confidence-0.0 + empty FEN; API must treat confidence < threshold as failure
- Minor: confidence margin 0.809 vs >0.8 is tight; orientation heuristic ties default to w-bottom

## Task 6: Stockfish engine (discovery, download, analysis)
- Status: DONE, reviewed APPROVED (no findings; 2 deviations verified necessary)
- Commits: e845c02 feat: add Stockfish engine with binary discovery and UCI analysis
- BASE f7256c5 HEAD e845c02; tests 15/15; scope exact (3 new files, +175)
- Deviations (required for python-chess 1.11.2): drop multipv from analyse (list vs dict); SAN computed before push
- Reviewer verified: real subprocess UCI round-trip, find_stockfish no-download, bin/ not created, no new deps
- Minor: unused subprocess import; error msg says STOCKFISH_PATH but setting is AppSettings.stockfish_path; download sync (Task 8 risk); walk of ~/Downloads can be slow

## Task 7: StockfishService (context + evaluation text)
- Status: DONE, reviewed APPROVED
- Commits: 600723a feat: add Stockfish service with game context and evaluation text (amended to include force-added test)
- BASE e845c02 HEAD 600723a; tests 21/21; scope exact (3 files)
- PLAN FIX d32e29e docs: compute_castling test FEN -> r3k3 (r1bqkbnr returns KQkq, not Qq)
- Reviewer verified: pure funcs boundaries, service integration (fen fields to engine confirmed), no blockers
- NOTE: services/__init__.py dropped GeminiChessService -> routes.py/main.py import broken until Task 8 (expected, no test imports routes)
- Minor: from_uci(None) unguarded; castling is positional heuristic; ep from suggested move

## Task 8: Rewrite API routes + remove Gemini
- Status: DONE, reviewed APPROVED
- Commits: 33c1d85 feat: rewrite API for CV + Stockfish and remove Gemini
- BASE 600723a HEAD 33c1d85; tests 25/25; app imports clean (root = chess-vision-fast); scope exact (7 files, -1 dep)
- Deviation: confidence guard added (implemented Task 5 reviewer follow-up): fen='' + error when confidence < 0.45; verified for blank/solid images in both routes
- Reviewer verified: overlay really draws (pixel diffs), overlay_coords normalized for legal capture, context endpoints work
- Minor: orientation query parsed but not forwarded to detector (inert, matches brief); vestigial GeminiVisionDetector + gemini settings fields (dead, acceptable); datetime.utcnow() deprecation; FRONTEND still calls removed endpoints (retrospective/change_model/current_model) -> resolved by Tasks 9-11

## Task 9: Update frontend API client
- Status: DONE, reviewed APPROVED
- Commits: f8846f0 feat: update frontend API client for stockfish endpoints
- BASE 33c1d85; brief task-9-brief.md (92 lines)
- PLAN FIX (doc) 6fd01e7: Step 2 rg check scoped to src/services only; App.jsx stale imports are fixed by Task 10
- NOTE: Tasks 9+10 dispatched together (single implementer, two commits) because Task 9 alone breaks the frontend build (App.jsx imports removed exports); build verified only at end of Task 10
- Reviewer: api.js programmatically IDENTICAL to plan; exports exactly the 5 functions; no stale refs anywhere in src

## Task 10: Update frontend UI
- Status: DONE, reviewed APPROVED
- Commits: fd68408 feat: update UI for local stockfish analysis
- BASE 33c1d85; brief task-10-brief.md (624 lines)
- Implementation: npm install needed (no node_modules); npm run build SUCCESS (34 modules)
- Reviewer: App/UploadImage/BoardPreview byte-identical to plan + Step 4 context refresh present; backend contract verified (/api/best_move {fen,turn,depth}, /api/context move_history); orientation mapping sound; em-dash U+2014
- Minor (non-blocking): turn state never wired to UI (always 'w', matches plan); confidence chip renders 'n/a' if undefined; detectImage exported but unused

## Task 11: README + final verification
- Status: DONE, reviewed APPROVED
- Commits: 7f59daa docs: update README for local CV + Stockfish pipeline
- BASE fd68408; brief task-11-brief.md (48 lines)
- Deviations (documented): README lives at repo ROOT (plan said chess-vision-fast/README.md which does not exist); pytest run from chess-vision-fast/backend (plan said chess-vision-fast)
- Reviewer: commit scope only root README.md; all Step 1 content verified; no stale Gemini refs; env var names + endpoints contract-checked vs routes.py/utils.py; 25/25 tests + frontend build green
- FOLLOW-UP FIX a8c1a43: setup_env.py still generated GEMINI_API_KEY/GEMINI_MODEL .env (Task 11 reviewer finding #2) -> now generates STOCKFISH_PATH/STOCKFISH_DEPTH=15/STOCKFISH_AUTO_DOWNLOAD=true
- Minor (non-blocking): endpoints in bullet list not Markdown table (cosmetic)

## PLAN COMPLETE
- All 11 tasks implemented and reviewed. Branch feature/local-stockfish-cv at a8c1a43.
- Full verification: 25/25 backend tests, frontend build green, pipeline 32/32 synthetic renders, end-to-end reviewed per task.
- Known acceptable vestigial code: GeminiVisionDetector (detector.py, unreachable), gemini_api_key/model settings fields (utils.py), both explicitly approved in Task 8 review.
- Pending: finishing decision (merge/PR/cleanup) via finishing-a-development-branch.

## POST-PLAN BUGFIX: board detection for arbitrary cell sizes (user report)
- Status: FIXED, verified; commit cd4c6ca "fix: align board detection for boards with any cell size"
- Root cause: `_interior_quad` always returned the CENTERED 480px window of the non-green component, so any board whose interior is not exactly 480px (e.g. a 640x640 chess.com screenshot with 80px cells, with or without a green frame) produced a misaligned warp -> all 64 squares unclassified ("Could not classify pieces on squares: a8...h1"). The synthetic renderer (60px cells, 480px interior) masked the bug; the edge-to-edge examples/board.jpg + con_movimiento.jpg and the user's real screenshot reproduced it.
- Fix (cv_detector.py):
  - `_interior_quad` now returns the TRUE detected square extent (erode -> component -> dilate back -> intersect original non-green), not a fixed 480 window.
  - New `_largest_square_quad` fallback for tight edge-to-edge boards with no green frame.
  - `find_board` now tries candidates (interior, largest-square, contour) and returns the first that passes `_verify_board`.
  - `_verify_board` samples the four CORNERS of each cell (pieces occupy cell centers and broke the old center sampling even on correct warps); checks horizontal+vertical alternation.
  - `_extract_piece` erodes the foreground mask 1px to tolerate ~1px residual grid misalignment (template matching was sub-pixel sensitive).
- TDD: 3 new tests (test_find_board_edge_to_edge_large_board, test_find_board_framed_large_board, test_detect_starting_position_framed_large_cells) failed before the fix (RED), pass now (GREEN).
- Verification: 28/28 tests (25 + 3 new); examples: board.jpg now detects as an empty board (was misaligned error), con_movimiento.jpg classifies e3=P 0.656 and e2=P 0.594 (e2 previously wrong R 0.523); synthetic START/MIDGAME/flip still 32/32.
- Known residual: con_movimiento.jpg e4 is a low-res borderline pawn (best match 0.462 < 0.5) -> API still errors on that one square; not the reported bug (previously 64/64 unknown).
- Pending: user re-test with their real screenshot; PR creation still outstanding.

## POST-PLAN BUGFIX 2: green-theme boards + last-move highlight (user report, imagen-prueba.png)
- Status: FIXED, verified; commit 51cc022 "fix: detect green-theme boards and ignore last-move highlight"
- Root cause (two separate defects found on the user's real chess.com screenshot examples/imagen-prueba.png, 1073x524 full-page, green theme where dark squares are green, board x/y [5,508], 63px cells):
  1. Board not detected at all: the chess.com green theme has no green FRAME; `is_green` (g > r+12 & g > b+12) matches the green DARK squares, so `_interior_quad`'s erode disconnected the checkerboard into ~32 components and found nothing. (The synthetic renderer's dark=(181,136,99) is not green, which is why this never showed in tests.)
  2. h8 unclassified: chess.com tints the last-move/check squares with a cyan highlight (BGR ~[67,202,185]); that square no longer matches either `empty_colors` light/dark, so `square_state` mask>25 reported it occupied, but `_extract_piece` found no piece (mask vs cell median ~0.001) -> "Could not classify pieces on squares: h8".
- Fix (cv_detector.py):
  - New `_green_board_quad`: largest 8-connected green component WITHOUT erosion (erosion splits the checkerboard into isolated cells); bbox is the board extent; fill-ratio guard <0.3 rejects green frames / incidental page green; inserted in find_board after _interior_quad. Verified: user image -> (5,5)-(509,509) verified; None on board.jpg/con_movimiento/synthetic.
  - `square_state` now also requires the cell to differ from its OWN median (`non_uniform` mask): `if mask.mean() < 0.05 or non_uniform.mean() < 0.05: return (False, None)`; piece color computed from `non_uniform` pixels. Empty highlighted squares now read as empty.
- TDD: 3 new tests (test_detect_green_theme_board_with_highlighted_empty_square, test_green_theme_board_detection, test_square_state_highlighted_empty_square_is_empty) + new render helper render_green_theme_board (dark=(67,202,185), no frame, optional highlight tint).
- Verification: 31/31 tests (28 + 3). User screenshot: fen 'pnbqkbn1/ppp2pp1/4p3/3pP2r/5P2/8/PPPP2PP/PNB1KBNR w KQkq - 0 1', 30 squares, confidence 0.755 (no error). board.jpg empty board, synthetic START/MIDGAME 32/32, green-theme test 18/18.
- Known residual (unchanged): con_movimiento.jpg e4 borderline pawn 0.462 < 0.5 still errors on that single square.
- Pending: user re-test of their real screenshot; PR creation still outstanding.

## PLAN: FEN sanitizer & validation (plan 2026-08-14-fen-sanitizer.md)
- Plan commit 85c51b6; spec 2026-08-14-fen-sanitizer-design.md (bf0306a + 74f3c41). Execution mode: Subagent-Driven (6 tasks).

## FEN Task 1: Move compute_castling to fen_sanitizer.py
- Status: DONE, reviewed APPROVED
- Commits: ea42963 feat: add FEN sanitizer module with compute_castling
- BASE 85c51b6 HEAD ea42963; 32/32 tests green; scope exact (3 files, +43/-16)
- Controller fix 2c35485 chore: ignore auto-downloaded stockfish binary dir — untracked 114MB app/bin/stockfish.exe (auto-download scratch) broke test_find_stockfish_with_configured_path_missing_returns_none; deleted + gitignored; suite restored to green
- Reviewer: verbatim move, re-export load-bearing (test_stockfish_service imports from service module), minor-only (plan-mandated dead constants for later tasks)

## FEN Task 2: sanitize_fen parse/normalize/castling fix
- Status: DONE, reviewed APPROVED
- Commits: a71aef6 feat: sanitize FEN parse, normalization and castling rights
- BASE ea42963 HEAD a71aef6; 36/36 tests green; zero drift from brief
- Reviewer traced: empty/6+ field rejection, padding to 6 fields, no-castling-field -> '-' silent, prune-only never invents, fresh chess.Board post-castling-fix (stale-rights trap avoided), compute_castling intact
- Minor (noted): dead `board` var (per-brief); UNRECOVERABLE_MASK excludes STATUS_INVALID_EP_SQUARE (512)/check flags -> check in Task 4; no castling-string canonicalization (KQKq passes through); second import block in test file (per-brief)

## FEN Task 3: back-rank pawn repair + unrecoverable hardening
- Status: DONE, reviewed APPROVED
- Commits: f6cb5b4 feat: repair back-rank pawns and harden FEN validation
- BASE a71aef6 HEAD f6cb5b4; 41/41 tests green; verbatim per brief
- Reviewer traced: deficit heuristic correct (a1 pawn->R + castling prune to Q, h8->r, e1 full-material -> unrecoverable False, a1+h1 one rook consumes deficit then False), counts recomputed per pawn, pawn-skip guard present, pawn-fix-before-castling-fix ordering with board re-sync
- Minor (noted): king-restoration branches untested (e-file pawn w/o king, expected!=K && K in deficits), FILE_PIECE knight/bishop paths uncovered; display duplicates lowercase logic

## FEN Task 4: wire sanitizer into API routes
- Status: DONE, reviewed APPROVED
- Commits: 915d9b1 -> amended d355c9a feat: validate and sanitize FEN across all API routes
- BASE f6cb5b4 HEAD d355c9a; 43/43 tests green
- DEVIATION (app-approved): plan's kings-only test FEN -> '4k3/8/8/8/8/8/4P3/4K3 w - - 0 1' (mock bestmove e2e4 illegal on kings-only -> EngineError infinite hang)
- CONTROLLER FOLLOW-UP: fen_warnings added to best_move except branch (spec: every response includes the field)
- Reviewer: all 10 response paths across 3 routes carry fen_warnings; sanitize after confidence gate / top of best_move try; engine skipped on invalid; sanitized FEN returned; no raw FEN leaks
- Minor (noted for Task 6): warnings test exercises catch-all error branch not success path; no success-path/non-empty warning test; FenSanitizeResult import unused (per-brief)

## FEN Task 5: surface FEN corrections in the frontend
- Status: DONE, reviewed APPROVED
- Commits: caa2747 feat: surface FEN corrections in the UI
- BASE d355c9a HEAD caa2747; npm run build SUCCESS (34 modules, 3.00s); scope exact (2 files, +15)
- Reviewer: all 5 anchors present and placed per brief (state after confidence, handleResult after setConfidence, handleManualBestMove after setPv, handleClearContext reset, prop after error); amber block byte-for-byte spec, immediately after error block; no missed handler (cancelOperation pattern consistent); no new deps

## FEN Task 6: final verification
- Status: DONE (controller)
- Full backend suite: 43/43 passed (31 pre-existing + 10 sanitizer + 2 API)
- Manual check: sanitize_fen('rnbqkbnr/.../RNBQKBN1 w KQkq - 0 1') -> valid=True, '...RNBQKBN1 w Qkq - 0 1', warnings=['Removed invalid castling rights (KQkq -> Qkq).'] — matches plan expectation exactly
- Frontend build SUCCESS (final gate)
- Ledger committed

## POST-PLAN FEATURE: FEN sanitizer & validation
- Status: COMPLETE. Plan 2026-08-14-fen-sanitizer.md executed via Subagent-Driven (6 tasks), all reviewed APPROVED.
- Module `backend/app/fen_sanitizer.py`: FenSanitizeResult(fen, valid, warnings, error), sanitize_fen (normalize to 6 fields -> back-rank pawn repair via initial-arrangement heuristic -> prune-only castling fix -> fresh-board final validation with UNRECOVERABLE_MASK), compute_castling moved from stockfish_service (re-exported), INVALID_FEN_MESSAGE exact per spec.
- Commits: ea42963 (T1 compute_castling move), a71aef6 (T2 sanitize_fen core), f6cb5b4 (T3 back-rank pawns), d355c9a (T4 routes wiring, amended), caa2747 (T5 UI warnings), ledger commit (T6).
- Routes: /api/detect, /api/detect_and_move, /api/best_move all return fen_warnings on every path; unrecoverable -> fen='' + INVALID_FEN_MESSAGE + engine skipped; detect/detect_and_move return SANITIZED FEN. Frontend: amber "FEN corrected" warnings block.
- Final counts: 43/43 backend tests, frontend build green.
- Plan deviations (all controller-approved): T1 controller cleanup 2c35485 (.gitignore bin/ + delete untracked 114MB stockfish.exe that broke find_stockfish test); T4 test FEN kings-only -> '4k3/8/8/8/8/8/4P3/4K3' (mock bestmove e2e4 illegal -> EngineError hang); T4 fen_warnings added to best_move except branch (spec: every response carries the field).
- Known follow-ups (Minor, not blocking): no API test asserting success-path fen_warnings or non-empty warnings; king-restoration + FILE_PIECE knight/bishop branches of back-rank heuristic untested; UNRECOVERABLE_MASK excludes STATUS_INVALID_EP_SQUARE/check flags (plan-mandated).
