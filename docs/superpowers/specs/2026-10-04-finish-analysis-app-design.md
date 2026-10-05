# Finish Chess Vision Fast (analysis & study tool) — Design

**Date:** 2026-10-04 · **Status:** Approved by user in chat

## Purpose
Ship Chess Vision Fast as a finished, tested **analysis and study tool**: analyze positions
from screenshots, FEN or PGN of finished games with a local Stockfish. Explicitly out of
scope: any automatic screen capture or live reading of chess.com games (fair-play).

## Scope
1. **`.agents` cleanup** — keep `AGENTS.md`, `GEMINI.md` and skills `using-superpowers`,
   `brainstorming`, `writing-plans`, `executing-plans`, `test-driven-development`,
   `systematic-debugging`, `verification-before-completion`. Delete `plugins/` and all other skills.
2. **Backend**
   - Keep the uncommitted multipv work (top-3 lines, `score_text`, `lines`) and cover it with tests.
   - `nps` is `None` when the engine does not report it (no fake `"1.2M nps"`).
   - `StockfishEngine.engine_name()` returns the UCI `id name`; new `GET /api/engine`
     returns `{"name": str | null, "depth": int, "error"?: str}`.
   - `detect_and_move` exception branch also returns `lines: []` and `score_text: None`.
   - `requirements-dev.txt` adds `pytest` and `httpx`.
3. **Frontend**
   - Pure logic in `src/lib/chess.js`: `parseImport`, `buildHistoryFromPgn`, `setFenTurn`,
     `formatScore`, `evalToWhitePercent`, `START_FEN`.
   - App starts at the standard start position, no hardcoded fake lines/status/threads/nps.
   - PGN import builds one FEN per ply so `|< < > >|` navigation works.
   - Display flip (`White/Black at bottom`) is separate from detector orientation (`auto/front/back`).
   - Turn toggle rewrites the FEN side-to-move; illegal result shows an error.
   - `ImportModal` validates via `parseImport`; on error it stays open and shows the message.
   - Screenshot result updates the eval bar; engine name shown from `/api/engine`.
   - Remove unused `BoardPreview.jsx`, `Controls.jsx`.
4. **Frontend tests** — Vitest + @testing-library/react + jsdom: lib, api client, ImportModal,
   EvalBar, App smoke test (API mocked).

## Error handling
Backend never raises for analysis errors; it returns `error` strings (existing contract).
Frontend shows errors in the existing red banner; aborted requests are not errors.

## Testing / verification
`python -m pytest tests` (backend), `npm.cmd test` (Vitest), `npm.cmd run build`,
then a browser run against both dev servers.
