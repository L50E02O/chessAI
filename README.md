# ♟️ ChessVision AI  
### _Real-time Chess Analysis Assistant_

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python)
![Google Gemini](https://img.shields.io/badge/Google%20Gemini-2.5-orange?style=for-the-badge&logo=google)
![Stockfish](https://img.shields.io/badge/Stockfish-Engine-red?style=for-the-badge&logo=chess)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active-green?style=for-the-badge)

</div>

> **ChessVision AI** combina la visión artificial de **Google Gemini 2.5** con la potencia del motor **Stockfish** para analizar posiciones de ajedrez en tiempo real desde tu pantalla.  
> Captura, analiza y obtén la mejor jugada con un solo atajo de teclado.

---

## 📚 Tabla de Contenidos
- [🚀 Descripción General](#-descripción-general)
- [✨ Características](#-características)
- [🧠 Cómo Funciona](#-cómo-funciona)
- [🛠 Instalación](#-instalación)
- [⚙️ Configuración](#️-configuración)
- [🎮 Uso](#-uso)
- [🏗 Arquitectura](#-arquitectura)
- [🐛 Solución de Problemas](#-solución-de-problemas)
- [🗺 Roadmap](#-roadmap)
- [🤝 Contribuir](#-contribuir)
- [📄 Licencia](#-licencia)

---

## 🚀 Descripción General

**ChessVision AI** es una aplicación de escritorio que te permite analizar posiciones de ajedrez directamente desde cualquier tablero visible en tu pantalla.  
Solo presiona **Ctrl + Q** y la IA:
1. Captura la pantalla
2. Detecta el tablero
3. Extrae la posición (FEN)
4. Analiza con **Stockfish**
5. Muestra la mejor jugada 💡

Perfecto para:
- 🎓 Estudiar aperturas y mejorar tu nivel
- 🔍 Analizar partidas online en tiempo real
- ⚡ Obtener sugerencias instantáneas
- 🎯 Compatible con Chess.com, Lichess y más

---

## ✨ Características Principales

| Tipo | Descripción |
|------|--------------|
| 🖼️ **Reconocimiento Inteligente** | Detecta automáticamente el tablero y las piezas desde capturas de pantalla. |
| 🤖 **Visión por IA** | Utiliza **Google Gemini 2.5 Flash** para reconocer la posición con precisión. |
| 🧠 **Motor Stockfish** | Análisis profesional con profundidad configurable. |
| ⚡ **Rendimiento en Tiempo Real** | Resultados en solo segundos. |
| ⌨️ **Atajo Global (`Ctrl+Q`)** | Captura inmediata desde cualquier ventana. |
| 🔄 **Fallback OpenCV** | Usa visión clásica si la IA falla. |
| 🆓 **Gratis** | Compatible con el plan gratuito de la API de Google Gemini. |

---

## 🛠 Instalación

### 🔧 Requisitos
- **Python** 3.8 o superior  
- **Windows 10/11** (soporte principal)  
- **Conexión a Internet** (para la API de Google Gemini)  
- **Stockfish** instalado en tu sistema  

### 1️⃣ Clonar el repositorio
```bash
git clone https://github.com/L50E02O/chessAI.git
cd chessAI
```

### 2️⃣ Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3️⃣ Obtener tu API Key de Gemini
1. Ve a [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Inicia sesión con tu cuenta de Google
3. Crea una nueva API key
4. Copia la clave

### 4️⃣ Configurar el entorno
Copia el archivo de ejemplo y agrega tu clave:
```bash
copy .env.example .env
```
Edita `.env`:
```ini
GEMINI_API_KEY=tu_api_key_aqui
```

### 5️⃣ Configurar Stockfish
Edita la ruta del ejecutable en:
```python
# src/utils/config.py
STOCKFISH_PATH = r"C:\ruta\a\stockfish.exe"
```

---

## 🎮 Uso

Ejecuta la aplicación:
```bash
python src\main.py
```

**Controles:**
| Atajo | Acción |
|--------|--------|
| `Ctrl + Q` | Captura pantalla y analiza |
| `ESC` | Salir de la aplicación |

Verás algo como:
```
🚀 ChessVision iniciado
⌨️ Escuchando atajo <Ctrl+Q>...
```

---

## ⚙️ Configuración Avanzada

Puedes modificar parámetros en `src/utils/config.py`:

```python
HOTKEY = '<ctrl>+q'   # Cambia el atajo
DEPTH = 15             # Profundidad de Stockfish
```

### 🌐 Variables opcionales (Supabase)
```ini
SUPABASE_URL=tu_url
SUPABASE_ANON_KEY=tu_key
SUPABASE_BUCKET=boards
```

> 🧹 El sistema mantiene solo las últimas **10 capturas** en Supabase, eliminando las más antiguas automáticamente.

---

## 🏗 Arquitectura del Proyecto

```
chessAI/
├── src/
│   ├── main.py                 # Punto de entrada
│   ├── desktop_capture.py      # Captura de pantalla
│   ├── ocr/
│   │   ├── gemini_vision.py    # Integración con Gemini Vision
│   │   ├── board_detection.py  # Fallback OpenCV
│   │   └── fen_generator.py    # Generador FEN
│   ├── engine/
│   │   └── stockfish_engine.py # Comunicación con Stockfish
│   └── utils/
│       ├── config.py           # Configuración general
│       ├── helpers.py          # Funciones auxiliares
│       └── supabase_client.py  # Cliente Supabase
├── requirements.txt
├── .env.example
├── install.bat
├── run.bat
└── README.md
```

---

## 🐛 Solución de Problemas

| Error | Solución |
|-------|-----------|
| ❌ `GEMINI_API_KEY no configurado` | Verifica tu archivo `.env` y reinicia la app. |
| ⚙️ `Stockfish no responde` | Asegúrate de tener la ruta correcta en `config.py`. |
| ⌨️ `El atajo no funciona` | Ejecuta la terminal como administrador o cambia el atajo. |
| ⚠️ `Gemini devuelve FEN incorrecto` | Asegúrate de que el tablero sea visible y sin ventanas encima. |

---

## 🗺 Roadmap

### ✅ Versión actual (v1.0)
- ✔️ Integración Gemini Vision + Stockfish  
- ✔️ Detección OpenCV de respaldo  
- ✔️ Multimonitor y atajo global  

### 🚧 En desarrollo (v1.1)
- 📈 Validación avanzada de FEN  
- 💾 Historial de análisis  
- 🧩 GUI básica  

### 🔮 Futuro (v2.0+)
- 📱 App móvil (Android/iOS)  
- 💬 Integración con streamings (Twitch/YouTube)  
- 🌍 Modo offline con caché  

---

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! 💪  
Puedes:
- Reportar errores o sugerir mejoras  
- Enviar PRs con nuevas funciones  
- Mejorar la documentación  

```bash
git checkout -b feature/nueva-funcion
git commit -m "Agregada nueva funcionalidad"
git push origin feature/nueva-funcion
```

---

## 📄 Licencia

Este proyecto está bajo la licencia **MIT**.  
Consulta el archivo [LICENSE](LICENSE) para más detalles.

---

<div align="center">
  
**Hecho con ❤️ por [L50E02O](https://github.com/L50E02O)**  
_Analiza. Aprende. Mejora tu ajedrez._ ♟️  

</div>
