# ♟️ ChessVision AI - Real-time Chess Analysis Assistant# ♟️ ChessVision AI - Real-time Chess Analysis Assistant



<div align="center"><div align="center">



![Chess AI Banner](https://img.shields.io/badge/Chess-AI%20Assistant-blue?style=for-the-badge&logo=chess.com)![Chess AI Banner](https://img.shields.io/badge/Chess-AI%20Assistant-blue?style=for-the-badge&logo=chess.com)

![Python](https://img.shields.io/badge/Python-3.8+-green?style=for-the-badge&logo=python)![Python](https://img.shields.io/badge/Python-3.8+-green?style=for-the-badge&logo=python)

![Google Gemini](https://img.shields.io/badge/Google-Gemini%202.5-orange?style=for-the-badge&logo=google)![Google Gemini](https://img.shields.io/badge/Google-Gemini%202.5-orange?style=for-the-badge&logo=google)

![Stockfish](https://img.shields.io/badge/Stockfish-Engine-red?style=for-the-badge&logo=chess)![Stockfish](https://img.shields.io/badge/Stockfish-Engine-red?style=for-the-badge&logo=chess)

![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

**AI-powered chess analysis tool using Google Gemini Vision and Stockfish engine**

**AI-powered chess analysis tool using Google Gemini Vision and Stockfish engine**

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [Architecture](#-architecture) • [Roadmap](#-roadmap)

</div>

</div>

---

---

## 📋 Table of Contents

## 📋 Overview

- [Overview](#-overview)

- [Features](#-features)ChessVision AI is an intelligent desktop application that combines **Google Gemini's Vision API** with the **Stockfish chess engine** to provide real-time chess position analysis. Simply press a hotkey while viewing any chess board on your screen, and the AI will instantly analyze the position and suggest the best move.

- [How It Works](#-how-it-works)

- [Installation](#-installation)### ✨ Key Features

- [Usage](#-usage)

- [Architecture](#-architecture)- 🖼️ **Smart Board Recognition**: Automatically detects and analyzes chess positions from screenshots

- [Configuration](#-configuration)- 🤖 **AI-Powered Vision**: Uses Google Gemini 2.5 Flash for accurate piece recognition

- [API Limits](#-api-limits)- 🧠 **Engine Analysis**: Integrates Stockfish for professional-grade move suggestions

- [Troubleshooting](#-troubleshooting)- ⚡ **Real-time Processing**: Fast analysis with results in seconds

- [Roadmap](#-roadmap)- 🎯 **Universal Compatibility**: Works with any chess website (Chess.com, Lichess, etc.)

- [Contributing](#-contributing)- ⌨️ **Global Hotkey**: Convenient `Ctrl+Q` shortcut for instant capture

- [License](#-license)- 🔄 **Intelligent Fallback**: Traditional CV detection if AI fails

- 🆓 **Free to Use**: Leverages free tier of Google Gemini API

---

---

## 📋 Overview

## 🚀 How It Works

ChessVision AI is an intelligent desktop application that combines **Google Gemini's Vision API** with the **Stockfish chess engine** to provide real-time chess position analysis. Simply press a hotkey while viewing any chess board on your screen, and the AI will instantly analyze the position and suggest the best move.

```mermaid

Perfect for:graph LR

- 🎓 Learning and improving your chess skills    A[Press Ctrl+Q] --> B[Capture Screen]

- 📊 Analyzing online games in real-time    B --> C[Google Gemini Vision]

- 🔍 Studying chess positions quickly    C --> D[Extract FEN]

- 💡 Getting instant move suggestions    D --> E[Stockfish Analysis]

    E --> F[Best Move Suggestion]

---    

    C -.Fallback.-> G[OpenCV Detection]

## ✨ Features    G --> D

```

### Current Features

1. **Capture**: Press `Ctrl+Q` to capture your screen

- 🖼️ **Smart Board Recognition** - Automatically detects chess positions from screenshots2. **AI Analysis**: Image is sent to Google Gemini Vision API

- 🤖 **AI-Powered Vision** - Uses Google Gemini 2.5 Flash for accurate piece recognition3. **FEN Extraction**: AI identifies all pieces and generates FEN notation

- 🧠 **Engine Analysis** - Integrates Stockfish for professional-grade move suggestions4. **Engine Evaluation**: Stockfish analyzes the position

- ⚡ **Real-time Processing** - Fast analysis with results in seconds5. **Move Suggestion**: Best move is displayed in algebraic notation

- 🎯 **Universal Compatibility** - Works with any chess website (Chess.com, Lichess, etc.)

- ⌨️ **Global Hotkey** - Convenient `Ctrl+Q` shortcut for instant capture---

- 🔄 **Intelligent Fallback** - OpenCV-based detection if AI fails

- 🆓 **Free to Use** - Leverages free tier of Google Gemini API (1,500 requests/day)## 💻 Requirements



---### System Requirements

- **OS**: Windows 10/11 (primary), Linux/macOS (experimental)

## 🚀 How It Works- **Python**: 3.8 or higher

- **RAM**: 2GB minimum

```- **Internet**: Required for Google Gemini API

┌─────────────────┐

│  Press Ctrl+Q   │### Dependencies

└────────┬────────┘- `google-generativeai` - Google Gemini API client

         │- `python-chess` - Chess logic and validation

         ▼- `stockfish` - Chess engine wrapper

┌─────────────────┐- `opencv-python` - Computer vision (fallback detection)

│ Capture Screen  │- `mss` - Fast screen capture

│    (MSS)        │- `pynput` - Global hotkey listener

└────────┬────────┘- `python-dotenv` - Environment configuration

         │

         ▼See [`requirements.txt`](requirements.txt) for complete list.

┌─────────────────┐

│ Google Gemini   │---

│ Vision API      │

│ (gemini-2.5)    │## 🔑 Configuración

└────────┬────────┘

         │### 1. Crea el archivo `.env`

         ▼

┌─────────────────┐Copia `.env.example` a `.env` y configura tus credenciales:

│  Extract FEN    │

│   Notation      │```bat

└────────┬────────┘copy .env.example .env

         │```

         ▼

┌─────────────────┐Edita `.env` y agrega tu API key de Google Gemini:

│   Stockfish     │

│     Engine      │```ini

│  (depth: 15)    │# Google Gemini API Key (OBLIGATORIO)

└────────┬────────┘GEMINI_API_KEY=tu_api_key_aqui

         │

         ▼# Supabase (opcional, para historial de capturas)

┌─────────────────┐SUPABASE_URL=tu_url_de_supabase

│   Best Move     │SUPABASE_ANON_KEY=tu_anon_key

│   Suggestion    │SUPABASE_BUCKET=boards

└─────────────────┘```

```

### 2. Obtén tu API Key de Google Gemini

### Process Flow

1. Ve a [Google AI Studio](https://aistudio.google.com/app/apikey)

1. **Capture**: Press `Ctrl+Q` to capture your entire screen2. Inicia sesión con tu cuenta de Google

2. **AI Analysis**: Image is sent to Google Gemini Vision API3. Haz clic en "Create API Key"

3. **FEN Extraction**: AI identifies all pieces and board state, generates FEN notation4. Copia la clave y pégala en tu archivo `.env`

4. **Engine Evaluation**: Stockfish analyzes the position at depth 15

5. **Move Suggestion**: Best move is displayed in algebraic notation (e.g., `g1f3`)### 3. Configura Stockfish (si no lo has hecho)



**Example Output:**Edita `src/utils/config.py` y actualiza la ruta a tu ejecutable de Stockfish:

```

============================================================```python

🎯 Capturando pantalla...STOCKFISH_PATH = r"C:\ruta\a\tu\stockfish.exe"

✅ Captura completada: (1920, 1080, 3)```

🤖 Enviando imagen a Google Gemini para análisis...

✅ Usando modelo: models/gemini-2.5-flashPuedes descargar Stockfish desde: https://stockfishchess.org/download/

✅ FEN extraído por Gemini: rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 1

♟️ FEN detectado: rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 1---

🧠 Analizando posición con Stockfish...

✨ Mejor jugada sugerida: g1f3## 🛠 Instalación

============================================================

```### Requisitos

- Python 3.8+

---- pip

- Stockfish instalado en tu sistema

## 🛠 Installation

### Instalar dependencias

### Prerequisites

```bat

- **Python** 3.8 or higherpip install -r requirements.txt

- **Windows** 10/11 (primary support)```

- **Internet connection** for Google Gemini API

- **Stockfish** chess engine**Nota Windows**: `pynput` puede requerir permisos de administrador para escuchar atajos globales. Ejecuta la terminal como administrador si tienes problemas.



### Step 1: Clone the Repository---



```bash## ▶️ Uso

git clone https://github.com/L50E02O/chessAI.git

cd chessAI### 1. Inicia la aplicación

```

```bat

### Step 2: Install Python Dependenciespython src\main.py

```


**Option A: Manual**```

```cmd

pip install -r requirements.txt### 2. Analiza una partida

```

1. Abre tu sitio de ajedrez favorito (Chess.com, Lichess, etc.)

### Step 3: Get Google Gemini API Key2. Asegúrate de que el tablero esté visible en pantalla

3. Presiona `Ctrl+A`

1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)4. Espera unos segundos mientras:

2. Sign in with your Google account   - 📸 Se captura la pantalla

3. Click **"Create API Key"**   - 🤖 Gemini analiza la imagen

4. Copy your API key   - ♟️ Se extrae el FEN

   - 🧠 Stockfish calcula la mejor jugada

### Step 4: Configure Environment


1. Copy the environment template:

   ```cmd```

   copy .env.example .env============================================================

   ```🎯 Capturando pantalla...

✅ Captura completada: (1920, 1080, 3)

2. Edit `.env` and add your API key:🤖 Enviando imagen a Google Gemini para análisis...

   ```ini✅ FEN extraído por Gemini: rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1

   GEMINI_API_KEY=your_actual_api_key_here♟️ FEN detectado: rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1

   ```🧠 Analizando posición con Stockfish...

✨ Mejor jugada sugerida: e7e5

### Step 5: Download Stockfish============================================================

```

1. Download from [stockfishchess.org](https://stockfishchess.org/download/)

2. Extract the executable---

3. Update the path in `src/utils/config.py`:

   ```python## 🧪 Notas técnicas de detección

   STOCKFISH_PATH = r"C:\path\to\stockfish.exe"

   ```La detección en `src/desktop_capture.py` usa un método heurístico con OpenCV:



---- Convierte a escala de grises, suaviza y detecta bordes (Canny).

- Busca contornos con 4 lados y selecciona el que maximiza área y “cuadratura”.

## 🎮 Usage- Recorta un cuadrado a partir del bounding box; si falla, recorta la zona central como respaldo.



### Starting the ApplicationEsto es suficiente para tableros bien visibles con contraste razonable. Se puede mejorar con:





---

**Manual Start:**

```cmd## 🧹 Política de retención en Storage

python src\main.py

```Tras cada subida, se listan los objetos en `SUPABASE_BUCKET/prefix` (por defecto `boards/`) y se eliminan los más antiguos dejando solo los últimos 10. El orden se determina por el nombre (`board_YYYYMMDD_HHMMSS.png`), por lo que se conserva en orden cronológico.



You should see:---

```

🚀 ChessAI iniciado## � Configuración avanzada

⌨️ Escuchando atajo <ctrl>+q. Presiona ESC para salir.

```### Cambiar el atajo de teclado



### Analyzing a PositionEdita `src/main.py` y modifica la variable `HOTKEY`:



1. **Open your chess platform** (Chess.com, Lichess, etc.)```python

2. **Make sure the board is visible** on your screenHOTKEY = '<ctrl>+a'  # Cambia a '<ctrl>+<shift>+c' u otro atajo

3. **Press `Ctrl+Q`** to capture and analyze```

4. **Wait 2-3 seconds** for results

5. **View the suggested move** in the console### Ajustar profundidad de análisis de Stockfish



### Keyboard ShortcutsEn `src/engine/stockfish_engine.py`, ajusta el parámetro `depth`:



| Shortcut | Action |```python

|----------|--------|def get_best_move_for_fen(fen: str, depth: int = 20):  # Aumenta para análisis más profundo

| `Ctrl+Q` | Capture screen and analyze position |```

| `ESC` | Exit application |

### Usar Supabase para historial (opcional)

---

Si configuras las variables de Supabase en `.env`, las capturas se subirán automáticamente y se mantendrá un histórico de las últimas 10 imágenes.

## 🏗 Architecture

---

### Project Structure

## 🐛 Solución de problemas

```

chessAI/### "GEMINI_API_KEY no configurado"

├── src/- Asegúrate de tener un archivo `.env` en la raíz del proyecto

│   ├── main.py                 # Application entry point & hotkey listener- Verifica que la API key esté correctamente copiada (sin espacios)

│   ├── desktop_capture.py      # Screen capture functionality

│   ├── ocr/### "No se pudo obtener una jugada de Stockfish"

│   │   ├── gemini_vision.py    # Google Gemini Vision integration- Verifica que la ruta en `config.py` apunte al ejecutable correcto

│   │   ├── board_detection.py  # OpenCV fallback detection- Prueba ejecutar Stockfish manualmente: `stockfish.exe`

│   │   └── fen_generator.py    # FEN notation utilities

│   ├── engine/### El atajo no funciona

│   │   └── stockfish_engine.py # Stockfish wrapper & move calculation- Ejecuta la terminal como administrador

│   └── utils/- Verifica que no haya otro programa usando el mismo atajo

│       ├── config.py            # Configuration & environment variables

│       ├── helpers.py           # Utility functions & logging### Gemini devuelve un FEN incorrecto

│       └── supabase_client.py  # Optional cloud storage client- Asegúrate de que el tablero sea claramente visible

├── external/- Evita capturas con elementos superpuestos

├── requirements.txt            # Python dependencies

├── .env.example               # Environment configuration template---

└── README.md                  # This file- **Gratis**: 15 solicitudes por minuto con `gemini-1.5-flash`

```- **Costo**: Después del límite gratuito, revisa los [precios de Gemini](https://ai.google.dev/pricing)



### Technology Stack### Stockfish

- Completamente gratuito y open source

| Layer | Technology | Purpose |- No requiere conexión a internet

|-------|-----------|---------|

| **Vision AI** | Google Gemini 2.5 Flash | Board & piece recognition via multimodal AI |---

| **Chess Engine** | Stockfish 16+ | Position evaluation & move calculation |

| **Computer Vision** | OpenCV 4.8+ | Fallback board detection (edge/contour detection) |## ✅ Roadmap

| **Screen Capture** | MSS 9.0+ | Fast multi-monitor screenshot capture |

| **Hotkey Manager** | pynput 1.7+ | Global keyboard shortcut listener |- [ ] Interfaz gráfica con historial de análisis

| **Chess Logic** | python-chess | Move validation & FEN parsing |- [ ] Soporte para múltiples motores de ajedrez

| **Environment** | python-dotenv | Secure API key management |- [ ] Análisis de variantes y líneas principales

- [ ] Exportar partidas a PGN

### Data Flow Diagram- [ ] Detección automática del lado del tablero

- [ ] Modo streaming para análisis en tiempo real

```

┌──────────────────────────────────────────────────────────────┐---

│                      USER INTERACTION                         │

│                       (Ctrl+Q Press)                          │## 👤 Autor

└───────────────────────────┬──────────────────────────────────┘

                            │Leo Holguin – Proyecto personal de IA y visión aplicada al ajedrez.

                            ▼

┌──────────────────────────────────────────────────────────────┐

│                     SCREEN CAPTURE                            │
│  • MSS library captures all monitors                          │
│  • Returns RGB numpy array                                    │
└───────────────────────────┬──────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                   VISION AI PROCESSING                        │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ PRIMARY: Google Gemini 2.5 Flash                        │ │
│  │ • Multimodal AI analysis                                │ │
│  │ • Piece recognition via vision model                    │ │
│  │ • Direct FEN output                                     │ │
│  │ • ~2-3 second latency                                   │ │
│  └─────────────────────────────────────────────────────────┘ │
│                            │                                   │
│                   ┌────────┴────────┐                         │
│                   │   Success?      │                         │
│                   └────────┬────────┘                         │
│                    YES │    │ NO                              │
│                        │    │                                  │
│                        │    ▼                                  │
│                        │  ┌─────────────────────────────────┐ │
│                        │  │ FALLBACK: OpenCV Detection     │ │
│                        │  │ • Canny edge detection         │ │
│                        │  │ • Contour finding              │ │
│                        │  │ • Board cropping               │ │
│                        │  │ • Template matching            │ │
│                        │  └─────────────────────────────────┘ │
│                        │                │                      │
└────────────────────────┼────────────────┼──────────────────────┘
                         │                │
                         └────────┬───────┘
                                  │
                                  ▼
                      ┌────────────────────┐
                      │   FEN STRING       │
                      │  (Position Data)   │
                      └─────────┬──────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────┐
│                   CHESS ENGINE ANALYSIS                       │
│  • Stockfish evaluation                                       │
│  • Position scoring                                           │
│  • Best move calculation (depth 15)                           │
│  • Move notation (algebraic)                                  │
└───────────────────────────┬──────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                      OUTPUT TO USER                           │
│  • Console display with emojis                                │
│  • FEN notation                                               │
│  • Best move suggestion                                       │
│  • Execution time                                             │
└──────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

#### `main.py`
- Global hotkey listener (`Ctrl+Q`)
- Application lifecycle management
- Orchestrates workflow between components

#### `gemini_vision.py`
- Google Gemini API client
- Image to FEN conversion
- Model selection & fallback
- Error handling & retries

#### `stockfish_engine.py`
- Stockfish process management
- UCI protocol communication
- Best move calculation
- Position evaluation

#### `desktop_capture.py`
- Multi-monitor screenshot capture
- Image preprocessing
- Optional Supabase upload

---

## ⚙️ Configuration

### Environment Variables

Edit `.env` file:

```ini
# Google Gemini API Key (REQUIRED)
GEMINI_API_KEY=your_gemini_api_key_here

# Supabase Configuration (OPTIONAL - for cloud storage)
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_BUCKET=boards
```

### Application Settings

Edit `src/utils/config.py`:

```python
# Stockfish Engine Path
STOCKFISH_PATH = r"C:\path\to\stockfish.exe"

# Analysis Depth (higher = slower but more accurate)
ANALYSIS_DEPTH = 15  # Default: 15 (range: 10-25)

# Hotkey Configuration
HOTKEY = '<ctrl>+q'  # Change as needed
```

---

## 📊 API Limits

### Google Gemini Free Tier

| Metric | Limit |
|--------|-------|
| **Requests per Minute (RPM)** | ~15 |
| **Requests per Day (RPD)** | ~1,500 |
| **Tokens per Minute (TPM)** | ~32,000 |
| **Cost** | **FREE** |

**Typical Usage per Analysis:**
- Input tokens: ~1,000-2,000 (image + prompt)
- Output tokens: ~100-200 (FEN notation)
- **Result**: You can analyze 15 positions per minute, 1,500 per day

**Paid Tier Pricing** (if needed):
- Input: $0.30 per 1M tokens
- Output: $2.50 per 1M tokens
- **Estimate**: 1,000 analyses ≈ $0.50-$1.00 USD

---

## 🐛 Troubleshooting

### Common Issues

#### "GEMINI_API_KEY no configurado"
**Solution:**
- Verify `.env` file exists in project root
- Check API key is correct (no extra spaces)
- Restart the application

#### "No se pudo obtener una jugada de Stockfish"
**Solution:**
- Verify Stockfish path in `config.py`
- Test Stockfish manually: run `stockfish.exe`
- Check Stockfish version (requires 14+)

#### Hotkey Not Working
**Solution:**
- Run terminal as Administrator
- Check no other app uses `Ctrl+Q`
- Try changing hotkey in `config.py`

#### Gemini Returns Incorrect FEN
**Solution:**
- Ensure board is clearly visible
- Avoid overlapping windows
- Try zooming in on the board
- System will fallback to OpenCV automatically

### Testing Gemini Connection

Run the test script:
```cmd
python test_gemini.py
```

This will:
- ✅ Verify API key is valid
- ✅ List available models
- ✅ Show your current quota

---

## 🗺 Roadmap

### ✅ Current Version (v1.0)
- [x] Desktop application with global hotkey
- [x] Google Gemini Vision integration
- [x] Stockfish engine integration
- [x] OpenCV fallback detection
- [x] Multi-monitor support
- [x] Windows support

### 🚧 In Development (v1.1)
- [ ] Improved FEN validation
- [ ] Move history tracking
- [ ] Position evaluation display
- [ ] Multiple engine support (Leela, etc.)

### 🔮 Future Features (v2.0+)

#### Mobile Application
- [ ] **Android/iOS app** with background service
- [ ] **Floating overlay button** for one-tap analysis
- [ ] **Notification-based results**
- [ ] **Share functionality** for positions
- [ ] **Offline mode** with cached engine
- [ ] **Cross-platform sync** via cloud

#### Desktop Enhancements
- [ ] **GUI application** (Qt/Tkinter)
- [ ] **Real-time analysis mode** (continuous capture)
- [ ] **Game history & database**
- [ ] **Opening book integration**
- [ ] **PGN export**
- [ ] **Multiple board detection** (streaming multiple games)

#### Advanced Features
- [ ] **Multi-language support**
- [ ] **Custom board themes** recognition
- [ ] **3D board support**
- [ ] **Live tournament analysis**
- [ ] **YouTube/Twitch integration** for streamers

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

### Ways to Contribute

1. **Report Bugs** - Open an issue with details
2. **Suggest Features** - Share your ideas
3. **Submit Pull Requests** - Code improvements
4. **Improve Documentation** - Help others understand
5. **Test on Different Platforms** - Linux/macOS feedback

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

### Third-Party Licenses

- **Stockfish**: GPL-3.0
- **Google Gemini API**: [Google API Terms](https://ai.google.dev/gemini-api/terms)
- **OpenCV**: Apache 2.0

---

## 👤 Author

**Leo Holguin** - [@L50E02O](https://github.com/L50E02O)

Personal project combining AI, computer vision, and chess analysis.

---

## 🙏 Acknowledgments

- **Google Gemini Team** - For the powerful Vision API
- **Stockfish Developers** - For the open-source engine
- **Chess.com / Lichess** - For inspiring this project
- **Open Source Community** - For amazing libraries

---

## 📬 Contact & Support

- **GitHub Issues**: [Report a bug](https://github.com/L50E02O/chessAI/issues)
- **Discussions**: [Ask questions](https://github.com/L50E02O/chessAI/discussions)

---

<div align="center">

**⭐ Star this repo if you find it useful!**

Made with ♟️ and 🤖 by Leo Holguin

</div>
