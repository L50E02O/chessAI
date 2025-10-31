# ♟️ ChessVision-AI + Google Gemini + Stockfish

Sistema inteligente de análisis de partidas de ajedrez que usa **Google Gemini Vision API** para extraer posiciones FEN desde capturas de pantalla y **Stockfish** para sugerir las mejores jugadas.

---

## ✨ ¿Qué hace?

1. **Captura**: Presiona `Ctrl+A` para capturar la pantalla completa
2. **Análisis con IA**: Envía la imagen a Google Gemini Vision para extraer el FEN automáticamente
3. **Fallback inteligente**: Si Gemini falla, usa detección de tablero con OpenCV como respaldo
4. **Motor de ajedrez**: Analiza la posición con Stockfish y sugiere la mejor jugada
5. **Historial en Supabase**: (Opcional) Mantiene un histórico de capturas en Supabase Storage

---

## 🚀 Novedades

### 🤖 Integración con Google Gemini
- Usa el modelo `gemini-1.5-flash` para análisis visual del tablero
- Extrae automáticamente el FEN sin necesidad de detección de bordes tradicional
- Funciona con tableros en cualquier perspectiva (blancas o negras abajo)
- Reintentos automáticos en caso de error

### ⚡ Flujo completo
```
Captura de pantalla → Gemini Vision → FEN → Stockfish → Mejor jugada
```

---

## 🧭 Estructura del proyecto

```text
src/
	main.py                    # Punto de entrada con atajo Ctrl+A
	desktop_capture.py         # Captura de pantalla full
	ocr/
		gemini_vision.py         # ⭐ NUEVO: Integración con Google Gemini
		board_detection.py       # Método tradicional (fallback)
		fen_generator.py
	engine/
		stockfish_engine.py      # Análisis con motor Stockfish
	utils/
		supabase_client.py       # Cliente Supabase (opcional)
		config.py                # Configuración y API keys
		helpers.py
```

---

## 🔑 Configuración

### 1. Crea el archivo `.env`

Copia `.env.example` a `.env` y configura tus credenciales:

```bat
copy .env.example .env
```

Edita `.env` y agrega tu API key de Google Gemini:

```ini
# Google Gemini API Key (OBLIGATORIO)
GEMINI_API_KEY=tu_api_key_aqui

# Supabase (opcional, para historial de capturas)
SUPABASE_URL=tu_url_de_supabase
SUPABASE_ANON_KEY=tu_anon_key
SUPABASE_BUCKET=boards
```

### 2. Obtén tu API Key de Google Gemini

1. Ve a [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Inicia sesión con tu cuenta de Google
3. Haz clic en "Create API Key"
4. Copia la clave y pégala en tu archivo `.env`

### 3. Configura Stockfish (si no lo has hecho)

Edita `src/utils/config.py` y actualiza la ruta a tu ejecutable de Stockfish:

```python
STOCKFISH_PATH = r"C:\ruta\a\tu\stockfish.exe"
```

Puedes descargar Stockfish desde: https://stockfishchess.org/download/

---

## 🛠 Instalación

### Requisitos
- Python 3.8+
- pip
- Stockfish instalado en tu sistema

### Instalar dependencias

```bat
pip install -r requirements.txt
```

**Nota Windows**: `pynput` puede requerir permisos de administrador para escuchar atajos globales. Ejecuta la terminal como administrador si tienes problemas.

---

## ▶️ Uso

### 1. Inicia la aplicación

```bat
python src\main.py
```

Verás en consola:
```
🚀 ChessAI iniciado
⌨️ Escuchando atajo <ctrl>+a. Presiona ESC o Ctrl+C para salir.
```

### 2. Analiza una partida

1. Abre tu sitio de ajedrez favorito (Chess.com, Lichess, etc.)
2. Asegúrate de que el tablero esté visible en pantalla
3. Presiona `Ctrl+A`
4. Espera unos segundos mientras:
   - 📸 Se captura la pantalla
   - 🤖 Gemini analiza la imagen
   - ♟️ Se extrae el FEN
   - 🧠 Stockfish calcula la mejor jugada

### 3. Ejemplo de salida

```
============================================================
🎯 Capturando pantalla...
✅ Captura completada: (1920, 1080, 3)
🤖 Enviando imagen a Google Gemini para análisis...
✅ FEN extraído por Gemini: rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1
♟️ FEN detectado: rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1
🧠 Analizando posición con Stockfish...
✨ Mejor jugada sugerida: e7e5
============================================================
```

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

## � Configuración avanzada

### Cambiar el atajo de teclado

Edita `src/main.py` y modifica la variable `HOTKEY`:

```python
HOTKEY = '<ctrl>+a'  # Cambia a '<ctrl>+<shift>+c' u otro atajo
```

### Ajustar profundidad de análisis de Stockfish

En `src/engine/stockfish_engine.py`, ajusta el parámetro `depth`:

```python
def get_best_move_for_fen(fen: str, depth: int = 20):  # Aumenta para análisis más profundo
```

### Usar Supabase para historial (opcional)

Si configuras las variables de Supabase en `.env`, las capturas se subirán automáticamente y se mantendrá un histórico de las últimas 10 imágenes.

---

## 🐛 Solución de problemas

### "GEMINI_API_KEY no configurado"
- Asegúrate de tener un archivo `.env` en la raíz del proyecto
- Verifica que la API key esté correctamente copiada (sin espacios)

### "No se pudo obtener una jugada de Stockfish"
- Verifica que la ruta en `config.py` apunte al ejecutable correcto
- Prueba ejecutar Stockfish manualmente: `stockfish.exe`

### El atajo no funciona
- Ejecuta la terminal como administrador
- Verifica que no haya otro programa usando el mismo atajo

### Gemini devuelve un FEN incorrecto
- Asegúrate de que el tablero sea claramente visible
- Evita capturas con elementos superpuestos
- El sistema usará el método tradicional como fallback

---

## 📊 Limitaciones y costos

### Google Gemini API
- **Gratis**: 15 solicitudes por minuto con `gemini-1.5-flash`
- **Costo**: Después del límite gratuito, revisa los [precios de Gemini](https://ai.google.dev/pricing)

### Stockfish
- Completamente gratuito y open source
- No requiere conexión a internet

---

## ✅ Roadmap

- [ ] Interfaz gráfica con historial de análisis
- [ ] Soporte para múltiples motores de ajedrez
- [ ] Análisis de variantes y líneas principales
- [ ] Exportar partidas a PGN
- [ ] Detección automática del lado del tablero
- [ ] Modo streaming para análisis en tiempo real

---

## 👤 Autor

Leo Holguin – Proyecto personal de IA y visión aplicada al ajedrez.


