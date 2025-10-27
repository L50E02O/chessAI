# ♟️ ChessVision-AI  
### “Analiza tu tablero de ajedrez desde una captura de pantalla con IA y Stockfish”  

---

## 🧩 Descripción del proyecto  

**ChessVision-AI** es una aplicación multiplataforma (**Windows y Android**) que combina **reconocimiento visual**, **OCR** y **Stockfish**, permitiendo analizar cualquier posición de ajedrez detectada desde una simple **captura de pantalla o foto del tablero**.  

El programa procesa la imagen, identifica las piezas y sus ubicaciones, genera una posición **FEN**, y utiliza el motor **Stockfish** para calcular el mejor movimiento posible en tiempo real.  

---

## ⚙️ Características principales  

### 📸 Captura automática de pantalla o cámara  
El sistema detecta el tablero en pantalla (por ejemplo, de **Chess.com** o **Lichess**) y extrae solo el área relevante.  

### 🧠 Reconocimiento visual del tablero  
Mediante **OpenCV** y **Tesseract-OCR**, se analizan las coordenadas, casillas y símbolos de las piezas.  

### ♟️ Integración con Stockfish  
Usa el motor **Stockfish** para calcular la mejor jugada y mostrarla en notación algebraica.  

### 🖥️ Ejecutable (.exe) para Windows  
El proyecto se empaqueta con **PyInstaller**, permitiendo ejecutar el análisis sin entorno Python.  

### 📱 Versión móvil (Android)  
La aplicación puede adaptarse a Android usando **Kivy / BeeWare / Flutter** con API interna, para capturar fotos con la cámara y procesarlas en local o en un backend.  

---

## 🧬 Arquitectura general  

ChessVision-AI/
│
├── src/
│ ├── capture/
│ │ ├── screen_capture.py # Captura de pantalla en Windows
│ │ ├── camera_capture.py # Captura desde cámara (para móvil)
│ │
│ ├── ocr/
│ │ ├── board_detection.py # Localiza el tablero con OpenCV
│ │ ├── piece_recognition.py # Identifica piezas usando Tesseract
│ │ ├── fen_generator.py # Convierte posiciones detectadas a FEN
│ │
│ ├── engine/
│ │ ├── stockfish_engine.py # Interfaz con Stockfish (mejor jugada)
│ │
│ ├── ui/
│ │ ├── main_app.py # Interfaz de usuario / consola o GUI
│ │ ├── result_display.py # Muestra mejor jugada o resalta movimiento
│ │
│ ├── utils/
│ │ ├── config.py # Configuraciones globales
│ │ ├── helpers.py # Funciones auxiliares
│ │
│ └── main.py # Punto de entrada del programa
│
├── assets/
│ ├── icons/ # Íconos y recursos visuales
│ ├── samples/ # Imágenes de prueba
│
├── stockfish/ # Binarios del motor Stockfish
│ └── stockfish.exe
│
├── requirements.txt # Dependencias de Python
├── README.md # Este archivo
└── setup.spec # Configuración de PyInstaller

---

## 📦 Dependencias principales  

| Librería | Propósito |
|-----------|------------|
| `opencv-python` | Procesamiento de imagen (detección del tablero) |
| `pytesseract` | OCR para reconocer las piezas |
| `stockfish` | Interfaz Python con el motor de ajedrez |
| `python-chess` | Generar y validar posiciones FEN |
| `pyautogui` | Captura de pantalla (Windows) |
| `pyinstaller` | Crear ejecutables (.exe) |
| `kivy` o `beeware` | (opcional) interfaz móvil multiplataforma |

### Instalación:
```bash
pip install -r requirements.txt

🧠 Flujo de funcionamiento

Captura o foto del tablero

En Windows: usa pyautogui.screenshot()

En Android: usa la cámara integrada

Detección del tablero y piezas

OpenCV localiza el tablero

Tesseract identifica las piezas mediante símbolos o texto OCR

Generación de FEN

fen_generator.py traduce las coordenadas detectadas a formato FEN estándar

Evaluación con Stockfish

stockfish_engine.py carga el motor y calcula la mejor jugada (get_best_move())

Resultado

Se muestra en consola o interfaz, con movimiento y evaluación

🖥️ Ejemplo de uso (modo consola)
python main.py


Salida esperada:

📸 Capturando tablero...
🧩 Reconociendo piezas...
♟️ Posición FEN: rnbq1bnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq -
🔍 Evaluando con Stockfish...
➡️ Mejor jugada: Nf3 (valor +0.45)

📲 Modo Android (plan futuro)

Para Android, el flujo sería el mismo:

Captura la imagen con la cámara

Procesa localmente o en un servidor Python (API REST)

Muestra el mejor movimiento en pantalla con una interfaz Kivy o Flutter

🔐 Compilación a .exe

Para crear el ejecutable:

pyinstaller --onefile --noconsole src/main.py -n ChessVisionAI


El archivo resultante estará en:

dist/ChessVisionAI.exe

🚀 Mejoras futuras

🔄 Reconocimiento de piezas por red neuronal (CNN) entrenada en tableros reales

📡 API online para análisis remoto

🗣️ Asistente por voz para anunciar la mejor jugada

📷 Detección automática del turno (blancas o negras)

📊 Interfaz visual que muestre la jugada sobre la imagen capturada

🧑‍💻 Autor

Leo Holguin
Proyecto personal de IA y visión computacional aplicados al ajedrez.
Desarrollado con Python, Tesseract y Stockfish.

---

## 📱 Enfoque móvil (implementación ahora)

Se añadirá primero una versión pensada para Android usando **Kivy**. Esta implementación inicial proporciona:

- Una UI mínima en `src/ui/mobile_app.py` y el punto de entrada `src/main_kivy.py`.
- Stubs que funcionan en escritorio y que pueden reemplazarse por implementaciones optimizadas para móvil: `src/ocr/board_detection.py`, `src/ocr/fen_generator.py`, `src/engine/stockfish_engine.py`.

Cómo probar en desarrollo (escritorio):

1. Instala las dependencias en tu entorno de desarrollo:

```bash
pip install -r requirements.txt
python src/main_kivy.py
```

2. La app permite seleccionar una imagen (archivo) y ejecutar un pipeline mínimo que devuelve una FEN de ejemplo y una jugada "mock" cuando faltan dependencias (OpenCV, Tesseract o Stockfish).

Notas sobre Android / empaquetado:

- Recomendado: Buildozer (Kivy) o Briefcase (BeeWare) para generar el APK. El empaquetado móvil requiere adaptar las dependencias nativas (OpenCV, Tesseract, Stockfish) o usar versiones móviles/nativas del motor y modelos.
- Para reducir complejidad, la primera versión móvil puede llamar a un servicio REST (host en un servidor o en la nube) que ejecute la detección y Stockfish, retornando FEN y la mejor jugada.

Bases para mantener el .exe (Windows) y compatibilidad:

- Conserva la carpeta `stockfish/` con los binarios (`stockfish.exe`) para la ejecución local en Windows.
- Mantén `src/engine/stockfish_engine.py` como el punto único de integración con el motor — así puedes cambiar la implementación por una nativa Android o por una llamada a un servicio remoto sin tocar la UI móvil.
- Conserva `setup.spec` y los scripts de `pyinstaller`; sirven para producir el `.exe` en Windows cuando quieras mantener la versión de escritorio.

Siguientes pasos sugeridos (opcional):

1. Integrar detección real con OpenCV + un pequeño modelo CNN para piezas (mejor precisión en móviles).
2. Preparar un buildozer.spec con dependencias mínimas y pruebas en un emulador Android.
3. Evaluar empaquetar Stockfish como una librería nativa (.so) para Android o usar un endpoint remoto para offload.

