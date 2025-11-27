# Chess Vision Fast - Análisis con Gemini AI

Solución full-stack para detectar el estado de un tablero físico y obtener análisis de ajedrez usando Google Gemini AI como Gran Maestro virtual. Está diseñada para funcionar en Windows/macOS/Linux y ofrece modos foto y webcam con análisis contextual de partidas.

## Características

- **Detección de tablero**: Usa Google Gemini Vision para detectar la posición del tablero desde imágenes
- **Análisis de GM**: Gemini actúa como Gran Maestro, proporcionando análisis estratégico y táctico
- **Contexto de partida**: Mantiene el historial de movimientos y contexto durante toda la partida
- **Retrospectiva**: Genera análisis retrospectivo de la partida completa
- **Interfaz moderna y amigable**: React 18 + Vite + Tailwind con diseño intuitivo
- **Múltiples formas de subir**: Arrastra y suelta, busca archivo, o pega con Ctrl+V
- **Sin dependencias locales**: No requiere modelos locales, solo la API de Gemini

## Estructura

```
chess-vision-fast/
├── backend/          # FastAPI + Google Gemini API
│   ├── app/         # Aplicación principal
│   │   ├── api/     # Rutas y WebSocket
│   │   ├── services/# Servicio de análisis de ajedrez
│   │   └── ...      # Detector, overlay, etc.
│   └── tests/       # Tests unitarios
├── frontend/        # React 18 + Vite + Tailwind
│   └── src/         # Componentes y servicios
└── examples/        # Imágenes de ejemplo
```

## Requisitos

1. **Python 3.12+** y `pip install -r chess-vision-fast/backend/requirements.txt`
2. **Node 18+** (para frontend: `npm install` dentro de `chess-vision-fast/frontend`)
3. **API Key de Google Gemini** (obtener en https://aistudio.google.com/apikey)

## Configuración

### Backend

1. Navega a la carpeta del backend:
```bash
cd chess-vision-fast/backend
```

2. Crea un archivo `.env`:
```env
GEMINI_API_KEY=tu_api_key_aqui
GEMINI_MODEL=gemini-2.0-flash
MAX_UPLOAD_SIZE=5242880
ALLOWED_ORIGINS=["http://localhost:5173"]
```

3. Instala las dependencias:
```bash
pip install -r requirements.txt
```

4. Arranca el backend:
```bash
python -m uvicorn app.main:app --reload --port 8000
```

O usa el script de Python:
```bash
python run_backend.py
```

### Frontend

1. Navega a la carpeta del frontend:
```bash
cd chess-vision-fast/frontend
```

2. Instala las dependencias:
```bash
npm install
```

3. Arranca el frontend:
```bash
npm run dev
```

O usa el script de Python:
```bash
python run_frontend.py
```

## Endpoints de la API

- `POST /api/detect`: Detecta la posición del tablero y retorna el FEN
- `POST /api/best_move`: Obtiene la mejor jugada con análisis completo de Gemini
- `POST /api/detect_and_move`: Combina detección y análisis en una sola llamada
- `POST /api/clear_context`: Limpia el contexto de la partida actual
- `GET /api/retrospective`: Obtiene retrospectiva de la partida completa

## Uso

1. Inicia backend y frontend en terminales separadas
2. Abre la UI en el navegador (por defecto http://localhost:5173)
3. Sube una imagen del tablero (arrastra y suelta, busca archivo, o pega con Ctrl+V)
4. El sistema detectará la posición y Gemini analizará la mejor jugada automáticamente
5. Usa **"Analizar Posición"** para re-analizar la posición actual
6. Usa **"Ver retrospectiva"** para obtener análisis completo de la partida
7. Usa **"Limpiar contexto"** para empezar una nueva partida

## Características del Análisis

El análisis de Gemini incluye:
- **Mejor jugada**: En formato UCI (ej: e2e4) y notación algebraica estándar (SAN, ej: e4)
- **Explicación**: Por qué es la mejor jugada
- **Análisis de posición**: Evaluación de la posición actual
- **Notas estratégicas**: Consideraciones tácticas y estratégicas
- **Contexto**: Mantiene el historial de movimientos durante la partida

## Tecnologías

### Backend
- FastAPI - Framework web moderno y rápido
- Google Gemini AI - Detección y análisis de ajedrez
- Python Chess - Validación y manipulación de posiciones

### Frontend
- React 18 - Biblioteca UI
- Vite - Build tool rápido
- Tailwind CSS - Estilos modernos
- WebSocket API - Comunicación en tiempo real

## Docker (Opcional)

Para usar Docker:

```bash
cd chess-vision-fast/backend
docker-compose up --build
```

La app expone:
- Frontend: http://localhost:5173
- Backend API/WS: http://localhost:8000

## Tests

Desde `chess-vision-fast/backend/` ejecuta:

```bash
python -m pytest tests/
```

## Cambios Recientes

- ✅ Eliminado Stockfish - Ahora usa solo Gemini AI
- ✅ Eliminado YOLO - Solo detección con Gemini Vision
- ✅ Eliminado Roboflow - Simplificado a solo Gemini
- ✅ Agregado contexto de partida - Mantiene historial de movimientos
- ✅ Agregada retrospectiva - Análisis completo de la partida
- ✅ Simplificado código - Arquitectura más limpia y mantenible

## Licencia

MIT (ver LICENSE).

## Autor

Leo Holguin - 2025
