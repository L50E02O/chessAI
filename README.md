# Chess Vision Fast - Local Analysis with Stockfish

Full-stack solution that detects a chess.com board from a screenshot using classical computer vision and analyzes the best move with a local Stockfish engine. Designed to work on Windows/macOS/Linux.

## Features

- **Board Detection**: Classical OpenCV computer vision detects the board and classifies the pieces
- **Best Move**: Local Stockfish engine computes the best move
- **Score + Principal Variation**: Centipawn/mate score with the suggested line
- **Game Context**: Maintains move history and context throughout the game
- **Modern and Friendly Interface**: React 18 + Vite + Tailwind with intuitive design
- **Multiple Upload Methods**: Drag and drop, file browser, or paste with Ctrl+V
- **100% Local**: No API keys and no cloud dependencies

> **Fair Play Notice:** Chess Vision Fast is designed purely as an analysis and study tool for offline positions, PGNs of finished games, and static captures. Any form of automatic screen capture or live reading of ongoing games on platforms like chess.com is out of scope and explicitly against fair play / anti-cheating policies. Please respect fair play guidelines.

## Structure

```
chess-vision-fast/
├── backend/          # FastAPI + OpenCV + Stockfish
│   ├── app/         # Main application
│   │   ├── api/     # Routes and WebSocket
│   │   ├── services/# Chess analysis service
│   │   └── ...      # Detector, overlay, etc.
│   └── tests/       # Unit tests
├── frontend/        # React 18 + Vite + Tailwind
│   └── src/         # Components and services
└── examples/        # Example images
```

## Requirements

1. **Python 3.12+** and `pip install -r chess-vision-fast/backend/requirements.txt`
2. **Node 18+** (for frontend: `npm install` inside `chess-vision-fast/frontend`)
3. **Stockfish**: auto-downloaded on first analysis (Windows) or detected at common paths / via `STOCKFISH_PATH`

## Setup

### Backend

1. Navigate to the backend folder:
```bash
cd chess-vision-fast/backend
```

2. Create a `.env` file:
```env
STOCKFISH_PATH=
STOCKFISH_DEPTH=15
STOCKFISH_AUTO_DOWNLOAD=true
MAX_UPLOAD_SIZE=5242880
ALLOWED_ORIGINS=["http://localhost:5173"]
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Start the backend:
```bash
python -m uvicorn app.main:app --reload --port 8000
```

Or use the Python script:
```bash
python run_backend.py
```

### Frontend

1. Navigate to the frontend folder:
```bash
cd chess-vision-fast/frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the frontend:
```bash
npm run dev
```

Or use the Python script:
```bash
python run_frontend.py
```

## API Endpoints

- `GET /api/engine`: Returns information about the running engine (e.g., `{"name": "Stockfish 16.1", "depth": 15}`)
- `POST /api/detect`: Detects the board position from an image and returns a FEN
- `POST /api/detect_and_move`: Detects the board and returns analysis in a single call (returns `lines` and `score_text`)
- `POST /api/best_move`: Returns the best move for a given FEN
- `POST /api/clear_context`: Clears the context of the current game
- `GET /api/context`: Returns the current game context / move history

## Usage

1. Start backend and frontend in separate terminals
2. Open the UI in your browser (default http://localhost:5173)
3. Upload a board image (drag and drop, file browser, or paste with Ctrl+V)
4. The system will detect the position and Stockfish will analyze the best move automatically
5. Use the Board **Auto/Front/Back** toggle when the screenshot is flipped
6. Use the depth selector to adjust the analysis depth (10, 15, 20)
7. Use **"Analyze"** to re-analyze the current position
8. Use **"Clear"** to start a new game

## Analysis Features

Analysis includes:
- **Best Move**: In UCI format (e.g., e2e4) and standard algebraic notation (SAN, e.g., e4)
- **Score**: Centipawn evaluation or forced mate
- **Principal Variation**: The suggested line after the best move
- **Evaluation Text**: Human-readable assessment of the position
- **Context**: Maintains move history during the game

## Technologies

### Backend
- FastAPI - Modern and fast web framework
- OpenCV - Classical computer vision for board detection
- Python Chess - Position validation and manipulation
- Stockfish - Chess engine for local analysis

### Frontend
- React 18 - UI library
- Vite - Fast build tool
- Tailwind CSS - Modern styles

## Docker (Optional)

To use Docker:

```bash
cd chess-vision-fast/backend
docker-compose up --build
```

The app exposes:
- Frontend: http://localhost:5173
- Backend API/WS: http://localhost:8000

## Tests

**Backend tests:**
From `chess-vision-fast/backend/` run:

```bash
python -m pytest tests/ -q
```

**Frontend tests:**
From `chess-vision-fast/frontend/` run:

```bash
npm run test
```

## Recent Changes

- ✅ Added local CV board detection - Classical OpenCV replaces Gemini Vision
- ✅ Added Stockfish analysis - Best move, score, and principal variation
- ✅ Removed Gemini - No API keys required

## License

MIT (see LICENSE).

## Author

Leo Holguin - 2025
