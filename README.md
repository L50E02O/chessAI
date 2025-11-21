# Chess Vision Fast

Solución full-stack para detectar el estado de un tablero físico y consultar Stockfish local sin depender de servicios en la nube. Está diseñada para funcionar en Windows/macOS/Linux y ofrece modos foto y webcam con overlay de jugadas.

## Estructura

- ackend/: FastAPI + Stockfish + detectores locales.
- rontend/: React 18 + Vite + Tailwind para UX responsiva.
- models/: instrucciones para bajar pesos y código del detector de Lichess o YOLO.
- examples/: imágenes demo (oard.jpg, con_movimiento.jpg).

## Requisitos

1. Python 3.12+ y pip install -r backend/requirements.txt.
2. Node 18+ (para frontend: 
pm install dentro de rontend).
3. Stockfish local (puedes usar el binario del sistema o seguir las instrucciones abajo).
4. Modelos opcionales en models/ (ver sección Modelos).

## Backend

1. Define variables opcionales en .env dentro de ackend/:
   `env
   DETECTION_BACKEND=lichess
   YOLO_MODEL_PATH=./models/yolov8-chess.pt
   STOCKFISH_PATH=/usr/bin/stockfish
   MAX_UPLOAD_SIZE=5242880
   `
2. Arranca con uvicorn app.main:app --reload desde ackend.
3. Endpoints principales:
   - POST /api/detect: recibe multipart/form-data con ile, retorna FEN, bounding boxes, timestamp y nivel de confianza.
   - POST /api/best_move: envía { fen, options?:{depth,time_ms} } y recibe UCI/SAN/score.
   - POST /api/detect_and_move: combina detección y cálculo (regresa overlay base64).
   - WS /ws/stream: recibe { frame: base64, backend?: 'lichess'|'yolo' }, devuelve JSON con en, est_move, squares y overlay_coords.

## Frontend

1. Desde rontend/ instala dependencias (
pm install) y arranca 
pm run dev.
2. Componentes:
   - CameraCapture controla la webcam y envía frames via websocket.
   - UploadImage envía la foto al backend.
   - BoardPreview muestra el overlay y la mejor jugada.
   - Controls permite elegir detector, profundidad y tiempo.
3. Los estados en pantalla presentan el FEN, la mejor jugada y la confianza de la detección.

## Modelos

Sigue los pasos en models/README.md. Para usar el detector de Lichess:

`ash
cd models
git clone https://github.com/lichess-org/chessboard-image-detector lichess-detector
pip install -e lichess-detector
`

Para YOLOv8, descarga el .pt y colocarlo en models/yolov8-chess.pt, luego ajusta YOLO_MODEL_PATH.

## Stockfish local

### Linux/macOS
`ash
sudo apt install stockfish  # Debian/Ubuntu
# o descarga binario oficial y añade a PATH
`

### Windows
Descarga el binario desde https://stockfishchess.org/download/ y agrega la ruta al STOCKFISH_PATH en .env.

## Docker

- Construye backend y frontend con docker compose -f backend/docker-compose.yml up --build.
- La app expone http://localhost:5173 (frontend) y http://localhost:8000 (API/WS).

## Tests

Desde ackend/ ejecuta:

`ash
python -m pytest tests/test_fen.py tests/test_stockfish_engine.py
`

El frontend incluye pruebas mínimas con 
pm run test (si se amplía con storyshots o React Testing Library).

## Ejemplos y troubleshooting

- Usa examples/board.jpg para pruebas de demo; con_movimiento.jpg incluye overlay de referencia.
- Para fotos físicas, evita sombras y procura ángulo lo más cenital posible.
- Si la confianza es baja (confianza < 0.4) en la UI, el sistema mostrará una advertencia verde/amarilla.

## Flujo recomendado

1. Inicia backend (uvicorn) y frontend (
pm run dev).
2. Descarga modelos necesarios según el detector elegido.
3. Abre la UI, selecciona detector y profundidad.
4. Usa la cámara o sube una imagen; la UI mostrará la mejor jugada y un overlay.

## Licencia

MIT (ver LICENSE).
