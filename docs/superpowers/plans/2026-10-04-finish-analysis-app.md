# Finish Chess Vision Fast Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finish Chess Vision Fast as a tested analysis/study tool (screenshot, FEN, PGN) with a local Stockfish.

**Architecture:** FastAPI backend (CV detector + Stockfish via python-chess) unchanged in shape; add multipv test coverage and `/api/engine`. React frontend moves pure chess logic into `src/lib/chess.js` and gains a Vitest suite.

**Tech Stack:** Python 3.13, FastAPI, python-chess 1.11, pytest; React 18, Vite 5, chess.js 1.4, Vitest, @testing-library/react, jsdom.

**Spec:** `docs/superpowers/specs/2026-10-04-finish-analysis-app-design.md`

## Global Constraints
- Run backend tests from `chess-vision-fast/backend`: `python -m pytest tests -q`.
- On this Windows machine use `npm.cmd` (PowerShell blocks `npm.ps1`).
- No fake data in the UI: every number shown comes from the engine or is hidden.
- No live-game / auto screen-capture features.

---

### Task 1: Clean `.agents`
**Files:** delete `.agents/plugins/`, and skills `dispatching-parallel-agents`, `finishing-a-development-branch`,
`receiving-code-review`, `requesting-code-review`, `subagent-driven-development`, `using-git-worktrees`, `writing-skills`.
- [ ] Delete with `Remove-Item -Recurse -Force`.
- [ ] Verify `Get-ChildItem .agents\skills` lists exactly the 7 kept skills.

### Task 2: Backend — repair suite, cover multipv, `/api/engine`
**Files:**
- Modify: `backend/tests/mock_uci_engine.py` (advertise `MultiPV`, emit 3 lines for `position startpos`, also handle `setoption`)
- Modify: `backend/tests/test_stockfish_engine.py` (isolate `find_stockfish` test with monkeypatch; multipv + nps + engine_name tests)
- Modify: `backend/tests/test_stockfish_service.py` (`format_score`, `format_pv_line`, `lines` tests)
- Modify: `backend/tests/test_api.py` (`lines`/`score_text` on best_move, `/api/engine`)
- Modify: `backend/app/stockfish_engine.py` (`nps` → `None` when absent; `engine_name()`; drop unused `subprocess`)
- Modify: `backend/app/api/routes.py` (`GET /api/engine`; error branch of detect_and_move returns `lines`, `score_text`)
- Create: `backend/requirements-dev.txt`

**Interfaces produced:**
- `StockfishEngine.engine_name() -> Optional[str]`
- `GET /api/engine -> {"name": str|None, "depth": int}` (+ `"error"` on failure)
- line dict: `{rank, move, uci, score_text, depth, nps: str|None, continuation, pv, score}`

- [ ] Write failing tests:
```python
def test_analyze_position_returns_multipv_lines():
    engine = StockfishEngine(command=MOCK)
    result = engine.analyze_position(START_FEN, multipv=3)
    assert [l['uci'] for l in result['lines']] == ['e2e4', 'd2d4', 'g1f3']
    assert result['lines'][0]['score_cp'] == 57

def test_analyze_position_nps_none_when_engine_omits_it():
    result = StockfishEngine(command=MOCK).analyze_position(START_FEN)
    assert result['lines'][0]['nps'] is None

def test_engine_name_reads_uci_id():
    assert StockfishEngine(command=MOCK).engine_name() == 'MockEngine 1.0'

def test_format_score():
    assert format_score(57, None) == '+0.57'
    assert format_score(-120, None) == '-1.20'
    assert format_score(None, 3) == 'M+3'
    assert format_score(None, None) == '0.00'

def test_format_pv_line_numbers_moves_from_fen():
    assert format_pv_line(START_FEN, ['e4', 'e5', 'Nf3']) == '1... e5 2. Nf3'
    assert format_pv_line(START_FEN, ['e4']) == ''

def test_engine_endpoint():
    routes._chess_service = StockfishService(StockfishEngine(command=MOCK))
    data = client.get('/api/engine').json()
    assert data['name'] == 'MockEngine 1.0'
```
- [ ] Run → FAIL (MultiPV unsupported / missing functions).
- [ ] Implement; run full suite → all PASS.
- [ ] Commit `feat(backend): multipv analysis lines, engine endpoint and tests`.

### Task 3: Frontend — test infra + `src/lib/chess.js`
**Files:** Modify `frontend/package.json`, `frontend/vite.config.js`; Create `frontend/src/test/setup.js`,
`frontend/src/lib/chess.js`, `frontend/src/lib/chess.test.js`.

**Interfaces produced (`src/lib/chess.js`):**
- `START_FEN: string`
- `parseImport(text) -> { fens: string[], moves: string[] }` — FEN → `{fens:[fen], moves:[]}`; PGN → one FEN per ply (`fens.length === moves.length + 1`); throws `Error` with readable message on invalid input/empty.
- `setFenTurn(fen, color) -> string` — sets side to move, clears en passant; throws if resulting position is invalid.
- `formatScore(score) -> string` — `{cp:142}` → `'+1.42'`, `{mate:-2}` → `'-M2'`, null → `'0.00'`.
- `evalToWhitePercent(score) -> number` — 50 for null, 100/0 for mate, clamped 5..95 using `50 + 50*(2/(1+e^(-cp/400))-1)`.

- [ ] Install: `npm.cmd i -D vitest@^2 @testing-library/react@^16 @testing-library/jest-dom@^6 @testing-library/user-event@^14 jsdom@^25`.
- [ ] Add `"test": "vitest run"` script; `test: { environment: 'jsdom', setupFiles: './src/test/setup.js', globals: true }` in vite config.
- [ ] Write failing tests for each function (see chess.test.js), run → FAIL, implement, run → PASS.
- [ ] Commit `test(frontend): add vitest and pure chess helpers`.

### Task 4: Frontend — API client
**Files:** Modify `frontend/src/services/api.js`; Create `frontend/src/services/api.test.js`.
- Add `getEngine(signal)` → `GET /api/engine`.
- Tests mock `global.fetch`: best_move posts JSON body `{fen, turn, depth}`; detectAndMove builds query `orientation/turn/depth` skipping empty; non-OK response rejects with body text.
- [ ] Red → green → commit `test(frontend): cover api client`.

### Task 5: Frontend — ImportModal + EvalBar
**Files:** Modify `ImportModal.jsx` (validate with `parseImport`; on success call `onImport(parsed)` and close; on error show message, stay open; presets = start, Sicilian, QGD), `EvalBar.jsx` (use `formatScore`/`evalToWhitePercent`). Tests: `ImportModal.test.jsx`, `EvalBar.test.jsx`.
- [ ] Red → green → commit `feat(frontend): validated import modal and eval bar helpers`.

### Task 6: Frontend — App fixes + smoke test
**Files:** Modify `App.jsx`, `UploadImage.jsx`; Delete `BoardPreview.jsx`, `Controls.jsx`; Create `App.test.jsx`.
- Start at `START_FEN`, no `DEFAULT_LINES`, lines `[]`, status `Ready`.
- `flipped` state + "Flip board" button → `ChessBoard orientation={flipped ? 'back' : 'front'}`.
- Detector orientation = `boardOrientation` (`auto|front|back`) passed to UploadImage.
- Turn buttons call `setFenTurn`; error on throw.
- `handleImport({fens, moves})` sets full history, index = last.
- OCR result sets `evalScore` and history.
- Engine name from `getEngine()` on mount shown in header; nps/depth only rendered when present.
- Tests (api mocked with `vi.mock('./services/api')`): renders start position + engine name; importing a PGN enables "Previous move"; clicking Analyze shows returned best move.
- [ ] Red → green → build → commit `feat(frontend): finish analysis UI and add app tests`.

### Task 7: Verification
- [ ] `python -m pytest tests -q`, `npm.cmd test`, `npm.cmd run build` all green.
- [ ] Start both servers; browser check: start position analysis returns real Stockfish line; PGN import + navigation; screenshot upload of `examples/board.jpg`.

### Task 8: Docs
- [ ] Update README (setup, tests, `/api/engine`, fair-play note). Commit `docs: update README`.
