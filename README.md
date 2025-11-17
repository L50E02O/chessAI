# ♟️ ChessVision AI  
### _Real-time Chess Analysis Assistant_

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python)
![Google Gemini](https://img.shields.io/badge/Google%20Gemini-2.5-orange?style=for-the-badge&logo=google)
![Stockfish](https://img.shields.io/badge/Stockfish-Engine-red?style=for-the-badge&logo=chess)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active-green?style=for-the-badge)

</div>

> **ChessVision AI** combines the artificial vision of **Google Gemini 2.5** with the power of the **Stockfish** engine to analyze chess positions in real-time from your screen.  
> Capture, analyze and get the best move with a single keyboard shortcut.

---

## 📚 Table of Contents
- [🚀 Overview](#-overview)
- [✨ Features](#-features)
- [🧠 How It Works](#-how-it-works)
- [🛠 Installation](#-installation)
- [⚙️ Configuration](#️-configuration)
- [🎮 Usage](#-usage)
- [🏗 Architecture](#-architecture)
- [🐛 Troubleshooting](#-troubleshooting)
- [🗺 Roadmap](#-roadmap)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)

---

## 🚀 Overview

**ChessVision AI** is a desktop application that allows you to analyze chess positions directly from any board visible on your screen.  
Just press **Ctrl + Q** and the AI will:
1. Capture the screen
2. Detect the board
3. Extract the position (FEN)
4. Analyze with **Stockfish**
5. Show the best move 💡

Perfect for:
- 🎓 Studying openings and improving your level
- 🔍 Analyzing online games in real-time
- ⚡ Getting instant suggestions
- 🎯 Compatible with Chess.com, Lichess and more

---

## ✨ Main Features

| Type | Description |
|------|--------------|
| 🖼️ **Smart Recognition** | Automatically detects the board and pieces from screenshots. |
| 🤖 **AI Vision** | Uses **Google Gemini 2.5 Flash** to recognize positions accurately. |
| 🧠 **Stockfish Engine** | Professional analysis with configurable depth. |
| ⚡ **Real-time Performance** | Results in just seconds. |
| ⌨️ **Global Shortcut (`Ctrl+Q`)** | Instant capture from any window. |
| 🔄 **OpenCV Fallback** | Uses classical vision if AI fails. |
| 🆓 **Free** | Compatible with Google Gemini API free plan. |

---

## 🛠 Installation

### 🔧 Requirements
- **Python** 3.8 or higher  
- **Windows 10/11** (main support)  
- **Internet Connection** (for Google Gemini API)  
- **Stockfish** installed on your system  

### 1️⃣ Clone the repository
```bash
git clone https://github.com/L50E02O/chessAI.git
cd chessAI
```

### 2️⃣ Install dependencies
```bash
pip install -r requirements.txt
```

### 3️⃣ Get your Gemini API Key
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Create a new API key
4. Copy the key

### 4️⃣ Configure the environment
Copy the example file and add your key:
```bash
copy .env.example .env
```
Edit `.env`:
```ini
GEMINI_API_KEY=your_api_key_here
```

### 5️⃣ Stockfish (Windows)
Por defecto, el sistema intentará detectar Stockfish. Si no lo encuentra en Windows, hará un **auto-descarga** segura del binario oficial (AVX2) y lo extraerá en `external/stockfish_win/`.

Enlace utilizado para la descarga:  
<https://github.com/official-stockfish/Stockfish/releases/latest/download/stockfish-windows-x86-64-avx2.zip>

Opcionalmente puedes establecer la ruta manualmente si prefieres tu propia instalación:
#
```ini
STOCKFISH_PATH=C:\\ruta\\a\\stockfish.exe
```

---

## 🎮 Usage

Run the application:
```bash
python src\main.py
```

**Controls:**
| Shortcut | Action |
|--------|--------|
| `Ctrl + Q` | Capture screen and analyze |
| `ESC` | Exit the application |

You'll see something like:
```
🚀 ChessVision started
⌨️ Listening for shortcut <Ctrl+Q>...
```

---

## ⚙️ Advanced Configuration

You can modify parameters in `src/utils/config.py`:

```python
# Stockfish is now handled automatically - no path configuration needed!
# The system uses python-stockfish which handles everything automatically
```

### 🌐 Optional variables (Supabase)
```ini
SUPABASE_URL=your_url
SUPABASE_ANON_KEY=your_key
SUPABASE_BUCKET=boards
```

> 🧹 The system keeps only the last **10 captures** in Supabase, automatically deleting older ones.

---

## 🏗 Project Architecture

```
chessAI/
├── src/
│   ├── main.py                 # Entry point
│   ├── desktop_capture.py      # Screen capture
│   ├── ocr/
│   │   ├── gemini_vision.py    # Gemini Vision integration
│   │   ├── board_detection.py  # OpenCV fallback
│   │   └── fen_generator.py    # FEN generator
│   ├── engine/
│   │   └── stockfish_engine.py # Stockfish communication
│   └── utils/
│       ├── config.py           # General configuration
│       ├── helpers.py          # Helper functions
│       └── supabase_client.py  # Supabase client
├── requirements.txt
├── .env.example
├── install.bat
├── run.bat
└── README.md
```

---

## 🐛 Troubleshooting

| Error | Solution |
|-------|-----------|
| ❌ `GEMINI_API_KEY not configured` | Check your `.env` file and restart the app. |
| ⚙️ `Stockfish not responding` | The system will download Stockfish automatically. Make sure you have internet connection. |
| ⌨️ `Shortcut not working` | Run the terminal as administrator or change the shortcut. |
| ⚠️ `Gemini returns incorrect FEN` | Make sure the board is visible and no windows are on top. |
| 📥 `Stockfish download failed` | Check your internet connection. On Windows, Stockfish downloads automatically. |

---

## 🗺 Roadmap

### ✅ Current version (v1.0)
- ✔️ Gemini Vision + Stockfish integration  
- ✔️ OpenCV fallback detection  
- ✔️ Multi-monitor and global shortcut  

### 🚧 In development (v1.1)
- 📈 Advanced FEN validation  
- 💾 Analysis history  
- 🧩 Basic GUI  

### 🔮 Future (v2.0+)
- 📱 Mobile app (Android/iOS)  
- 💬 Streaming integration (Twitch/YouTube)  
- 🌍 Offline mode with cache  

---

## 🤝 Contributing

Contributions are welcome! 💪  
You can:
- Report bugs or suggest improvements  
- Submit PRs with new features  
- Improve documentation  

```bash
git checkout -b feature/new-feature
git commit -m "Added new functionality"
git push origin feature/new-feature
```

---

## 📄 License

This project is licensed under **MIT**.  
See the [LICENSE](LICENSE) file for more details.

---

<div align="center">
  
**Made with ❤️ by [L50E02O](https://github.com/L50E02O)**  
_Analyze. Learn. Improve your chess._ ♟️  

</div>
