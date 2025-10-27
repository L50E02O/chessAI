# ♟️ ChessVision-AI (modo escritorio con atajo y Supabase)

Ahora el flujo principal funciona en Windows con un atajo global de teclado: presiona Ctrl+X para capturar la pantalla, detectar y recortar automáticamente el tablero de ajedrez, subir la imagen recortada a Supabase Storage y mantener un histórico en forma de pila limitado a 10 imágenes (se eliminan las más antiguas).

---

## ✨ ¿Qué hace?

- Escucha el atajo global Ctrl+X.
- Captura la pantalla completa.
- Detecta el tablero (OpenCV) y recorta a un cuadrado del tablero; si no lo encuentra, hace un recorte central como respaldo.
- Sube la imagen a Supabase Storage y devuelve una URL firmada de acceso temporal.
- Mantiene solo las últimas 10 imágenes en el bucket (las antiguas se eliminan automáticamente).

> Nota: La parte móvil con Kivy quedó deshabilitada como flujo principal. Los archivos siguen en `src/ui/` y `src/main_kivy.py`, pero el punto de entrada por defecto ahora es `src/main.py`.

---

## 🧭 Estructura relevante

```text
src/
	main.py                    # Punto de entrada con el atajo Ctrl+X
	desktop_capture.py         # Captura, detección/corte de tablero y subida a Supabase
	ocr/
		board_detection.py       # (stub antiguo) – ahora usamos una detección CV simple en desktop_capture
	engine/
		stockfish_engine.py      # (sin cambios en este flujo)
	utils/
		supabase_client.py       # Inicializa cliente Supabase desde .env
		config.py, helpers.py
captures/                    # Carpeta local temporal de capturas (se crea al vuelo)
```

---

## 🔑 Configuración de entorno (.env)

Crea un archivo `.env` en la raíz del proyecto con:

```ini
SUPABASE_URL=tu_url_de_supabase
SUPABASE_ANON_KEY=tu_anon_key
SUPABASE_BUCKET=boards
```

- Asegúrate de crear el bucket en Supabase Storage (por ejemplo `boards`). Puede ser público o se pueden usar URLs firmadas (este proyecto usa URLs firmadas de 24h).

---

## 🛠 Instalación

```bat
pip install -r requirements.txt
```

En Windows, puede que `pynput` pida permisos para escuchar teclas globales. Ejecutar la terminal con permisos suficientes ayuda en algunos entornos.

---

## ▶️ Ejecutar

```bat
python src\main.py
```

- Verás en consola: “Escuchando atajo Ctrl+X. Presiona ESC para salir.”
- Abre tu sitio de ajedrez (Chess.com, Lichess, etc.), coloca el tablero visible y presiona Ctrl+X.
- El programa intentará detectar y recortar el tablero, subirá la imagen a Supabase y te mostrará una URL firmada.

Las capturas locales se guardan en `captures/` con nombres `board_YYYYMMDD_HHMMSS.png`.

---

## 🧪 Notas técnicas de detección

La detección en `src/desktop_capture.py` usa un método heurístico con OpenCV:

- Convierte a escala de grises, suaviza y detecta bordes (Canny).
- Busca contornos con 4 lados y selecciona el que maximiza área y “cuadratura”.
- Recorta un cuadrado a partir del bounding box; si falla, recorta la zona central como respaldo.

Esto es suficiente para tableros bien visibles con contraste razonable. Se puede mejorar con:

- Warp por homografía para enderezar el plano.
- Clasificador/CNN o plantillas para cuadrícula.
- Umbral adaptativo y morfología para bordes más robustos.

---

## 🧹 Política de retención en Storage

Tras cada subida, se listan los objetos en `SUPABASE_BUCKET/prefix` (por defecto `boards/`) y se eliminan los más antiguos dejando solo los últimos 10. El orden se determina por el nombre (`board_YYYYMMDD_HHMMSS.png`), por lo que se conserva en orden cronológico.

---

## 🚧 Qué no hace aún

- No descarga automáticamente la última imagen desde Supabase; el flujo devuelve una URL firmada para acceso directo.
- No integra (todavía) la evaluación con Stockfish a partir de esa imagen; esto puede añadirse como siguiente paso.

---

## ✅ Siguientes pasos sugeridos

1. Añadir descarga de la última imagen desde Supabase para reenviar el recorte a módulos OCR/FEN.
2. Integrar `python-chess` + `stockfish_engine.py` para completar el pipeline hasta “mejor jugada”.
3. Permitir definir región de pantalla o multi-monitor.
4. Ajustar el atajo por variable de entorno (por ejemplo `HOTKEY=ctrl+x`).

---

## 👤 Autor

Leo Holguin – Proyecto personal de IA y visión aplicada al ajedrez.


