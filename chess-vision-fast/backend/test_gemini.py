"""Test del detector Gemini"""
from app.gemini_detector import GeminiDetector
from PIL import Image, ImageDraw

# Crear imagen simple de prueba (tablero con algunas piezas)
img = Image.new('RGB', (400, 400), 'white')
draw = ImageDraw.Draw(img)

# Dibujar cuadricula
for i in range(8):
    for j in range(8):
        if (i + j) % 2 == 1:
            x1, y1 = j * 50, i * 50
            draw.rectangle([x1, y1, x1 + 50, y1 + 50], fill='gray')

# Agregar texto simulando piezas
draw.text((25, 375), "K", fill='black')  # Rey blanco
draw.text((225, 375), "k", fill='black')  # Rey negro

img.save('test_board.png')
print("Imagen creada: test_board.png")

# Probar detector
d = GeminiDetector('AIzaSyAm0RiAEh5L5cbUC3q5i3WfH9MvmdeA8yc', 'gemini-2.0-flash')
fen = d.detect_fen(img)
print(f"FEN detectado: {fen}")
