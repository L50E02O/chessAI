# Modelos locales

Este proyecto detecta piezas mediante dos backends opcionales:

1. **Lichess Chessboard Image Detector** (recomendado para fotos cenitales bien iluminadas)
2. **YOLOv8 personalizado** (para modelos entrenados con tus propias piezas)

## Paso 1: descargar el detector de Lichess

`ash
cd models
git clone https://github.com/lichess-org/chessboard-image-detector lichess-detector
` 

El módulo python chessboard_image_detector quedará disponible si instalas esa carpeta en tu entorno (por ejemplo ejecutando pip install -e models/lichess-detector).

## Paso 2: descargar pesos YOLOv8 (opcional)

1. Visita: https://huggingface.co/ y busca yolov8-chess o usa el release oficial compartido para detección de piezas.
2. Descarga el archivo yolov8-chess.pt y colócalo en models/yolov8-chess.pt.
3. Actualiza ackend/app/utils.py o el .env con YOLO_MODEL_PATH=./models/yolov8-chess.pt.

## Alternativa: script local

Puedes copiar el siguiente comando para bajar un modelo de ejemplo (modifica la URL con la que elijas):

`ash
cd chess-vision-fast/models
curl -L -o yolov8-chess.pt https://huggingface.co/tu_usuario/yolov8-chess/resolve/main/yolov8-chess.pt
`

## Recomendaciones

- Mantén el archivo models/yolov8-chess.pt dentro del repo (o enlázalo como volumen) para usar YOLO en el contenedor.
- Usa pip install -e models/lichess-detector para que FastAPI pueda importar el detector sin copiar el código.
