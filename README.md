# Chess Vision Fast - Análisis con Gemini AI

Solución full-stack para detectar el estado de un tablero físico y obtener análisis de ajedrez usando Google Gemini AI como Gran Maestro virtual. Está diseñada para funcionar en Windows/macOS/Linux y ofrece modos foto y webcam con análisis contextual de partidas.

## Características

- **Detección de tablero**: Usa Google Gemini Vision para detectar la posición del tablero desde imágenes
- **Análisis de GM**: Gemini actúa como Gran Maestro, proporcionando análisis estratégico y táctico
- **Contexto de partida**: Mantiene el historial de movimientos y contexto durante toda la partida
- **Retrospectiva**: Genera análisis retrospectivo de la partida completa
- **Interfaz moderna**: React 18 + Vite + Tailwind para UX responsiva

## Estructura

- `backend/`: FastAPI + Google Gemini API para detección y análisis
- `frontend/`: React 18 + Vite + Tailwind para UX responsiva
- `models/`: Instrucciones opcionales para configuración adicional

## Requisitos

1. Python 3.12+ y `pip install -r backend/requirements.txt`
2. Node 18+ (para frontend: `npm install` dentro de `frontend`)
3. **API Key de Google Gemini** (obtener en https://aistudio.google.com/apikey)

## Configuración

### Backend

1. Crea un archivo `.env` dentro de `backend/`:
```env
GEMINI_API_KEY=tu_api_key_aqui
GEMINI_MODEL=gemini-1.5-flash
DETECTION_BACKEND=gemini
MAX_UPLOAD_SIZE=5242880
```

2. Arranca el backend:
```bash
cd backend
uvicorn app.main:app --reload
```

### Frontend

1. Desde `frontend/` instala dependencias:
```bash
npm install
```

2. Arranca el frontend:
```bash
npm run dev
```

## Endpoints de la API

- `POST /api/detect`: Detecta la posición del tablero y retorna FEN
- `POST /api/best_move`: Obtiene la mejor jugada con análisis de Gemini
- `POST /api/detect_and_move`: Combina detección y análisis en una llamada
- `POST /api/clear_context`: Limpia el contexto de la partida actual
- `GET /api/retrospective`: Obtiene retrospectiva de la partida
- `WS /ws/stream`: WebSocket para análisis en tiempo real con cámara

## Uso

1. Inicia backend y frontend
2. Abre la UI en el navegador (por defecto http://localhost:5173)
3. Sube una foto o usa la cámara para detectar el tablero
4. El sistema detectará la posición y Gemini analizará la mejor jugada
5. Usa "Limpiar contexto" para empezar una nueva partida
6. Usa "Ver retrospectiva" para obtener análisis de la partida completa

## Características del Análisis

El análisis de Gemini incluye:
- **Mejor jugada**: En formato UCI y notación algebraica estándar (SAN)
- **Explicación**: Por qué es la mejor jugada
- **Análisis de posición**: Evaluación de la posición actual
- **Notas estratégicas**: Consideraciones tácticas y estratégicas
- **Contexto**: Mantiene el historial de movimientos durante la partida

## Docker (Opcional)

Para usar Docker:

```bash
cd backend
docker-compose up --build
```

La app expone http://localhost:5173 (frontend) y http://localhost:8000 (API/WS).

## Tests

Desde `backend/` ejecuta:

```bash
python -m pytest tests/
```

## Licencia

MIT (ver LICENSE).
