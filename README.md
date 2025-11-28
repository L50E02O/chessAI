# Chess Vision Fast - Analysis with Gemini AI

Full-stack solution to detect the state of a physical chess board and get chess analysis using Google Gemini AI as a virtual Grandmaster. Designed to work on Windows/macOS/Linux and offers photo mode with contextual game analysis.

## Features

- **Board Detection**: Uses Google Gemini Vision to detect board position from images
- **GM Analysis**: Gemini acts as a Grandmaster, providing strategic and tactical analysis
- **Game Context**: Maintains move history and context throughout the game
- **Retrospective**: Generates retrospective analysis of the complete game
- **Modern and Friendly Interface**: React 18 + Vite + Tailwind with intuitive design
- **Multiple Upload Methods**: Drag and drop, file browser, or paste with Ctrl+V
- **No Local Dependencies**: No local models required, only Gemini API

## Structure

```
chess-vision-fast/
├── backend/          # FastAPI + Google Gemini API
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
3. **Google Gemini API Key** (get it at https://aistudio.google.com/apikey)

## Setup

### Backend

1. Navigate to the backend folder:
```bash
cd chess-vision-fast/backend
```

2. Create a `.env` file:
```env
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.0-flash
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

- `POST /api/detect`: Detects board position and returns FEN
- `POST /api/best_move`: Gets best move with complete Gemini analysis
- `POST /api/detect_and_move`: Combines detection and analysis in a single call
- `POST /api/clear_context`: Clears context of current game
- `GET /api/retrospective`: Gets retrospective of complete game
- `POST /api/change_model`: Changes the Gemini model to use
- `GET /api/current_model`: Gets the currently active model

## Usage

1. Start backend and frontend in separate terminals
2. Open the UI in your browser (default http://localhost:5173)
3. Upload a board image (drag and drop, file browser, or paste with Ctrl+V)
4. The system will detect the position and Gemini will analyze the best move automatically
5. Use **"Analyze Position"** to re-analyze the current position
6. Use **"Retrospective"** to get complete game analysis
7. Use **"Clear Context"** to start a new game
8. Use the model selector to switch between Gemini 2.0 Flash, 2.5 Flash, and 2.5 Pro

## Analysis Features

Gemini analysis includes:
- **Best Move**: In UCI format (e.g., e2e4) and standard algebraic notation (SAN, e.g., e4)
- **Explanation**: Why it's the best move
- **Position Analysis**: Evaluation of current position
- **Strategic Notes**: Tactical and strategic considerations
- **Context**: Maintains move history during the game

## Technologies

### Backend
- FastAPI - Modern and fast web framework
- Google Gemini AI - Chess detection and analysis
- Python Chess - Position validation and manipulation

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

From `chess-vision-fast/backend/` run:

```bash
python -m pytest tests/
```

## Recent Changes

- ✅ Removed Stockfish - Now uses only Gemini AI
- ✅ Removed YOLO - Only detection with Gemini Vision
- ✅ Removed Roboflow - Simplified to only Gemini
- ✅ Added game context - Maintains move history
- ✅ Added retrospective - Complete game analysis
- ✅ Simplified code - Cleaner and more maintainable architecture
- ✅ Added model selector - Switch between Gemini 2.0 Flash, 2.5 Flash, and 2.5 Pro

## License

MIT (see LICENSE).

## Author

Leo Holguin - 2025
