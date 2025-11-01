"""
Selector de región para capturar solo el tablero de ajedrez.
"""
import cv2
import numpy as np
import mss
import json
import os

CONFIG_FILE = os.path.join(os.path.dirname(__file__), '..', 'board_region.json')

def select_region():
    """
    Permite al usuario seleccionar una región rectangular en la pantalla.
    Retorna las coordenadas (x, y, width, height)
    """
    print("📸 Capturando pantalla completa para selección...")
    
    # Capturar pantalla completa
    with mss.mss() as sct:
        # Tomar screenshot de todos los monitores
        monitor = sct.monitors[0]  # Monitor 0 = todos los monitores combinados
        screenshot = sct.grab(monitor)
        img = np.array(screenshot)
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    
    # Variables para la selección
    clone = img.copy()
    ref_point = []
    selecting = False
    
    def click_and_crop(event, x, y, flags, param):
        nonlocal ref_point, selecting, clone
        
        # Si se hace clic izquierdo, registrar el punto inicial
        if event == cv2.EVENT_LBUTTONDOWN:
            ref_point = [(x, y)]
            selecting = True
        
        # Si se mueve el mouse mientras se selecciona, dibujar rectángulo
        elif event == cv2.EVENT_MOUSEMOVE and selecting:
            clone = img.copy()
            cv2.rectangle(clone, ref_point[0], (x, y), (0, 255, 0), 2)
        
        # Si se suelta el botón, registrar el punto final
        elif event == cv2.EVENT_LBUTTONUP:
            ref_point.append((x, y))
            selecting = False
            cv2.rectangle(clone, ref_point[0], ref_point[1], (0, 255, 0), 2)
    
    # Crear ventana y establecer callback
    window_name = "Selecciona el tablero de ajedrez - Arrastra y suelta, luego presiona ENTER"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(window_name, click_and_crop)
    
    # Redimensionar ventana para que quepa en pantalla
    screen_height, screen_width = img.shape[:2]
    display_width = min(1280, screen_width)
    display_height = int(screen_height * (display_width / screen_width))
    cv2.resizeWindow(window_name, display_width, display_height)
    
    print("🖱️ Instrucciones:")
    print("   1. Arrastra el mouse sobre el tablero de ajedrez")
    print("   2. Presiona ENTER para confirmar")
    print("   3. Presiona ESC para cancelar")
    
    # Esperar a que el usuario seleccione y presione ENTER
    while True:
        cv2.imshow(window_name, clone)
        key = cv2.waitKey(1) & 0xFF
        
        # Si se presiona ENTER y hay 2 puntos seleccionados
        if key == 13 and len(ref_point) == 2:  # 13 = ENTER
            break
        
        # Si se presiona ESC, cancelar
        elif key == 27:  # 27 = ESC
            cv2.destroyAllWindows()
            return None
    
    cv2.destroyAllWindows()
    
    if len(ref_point) == 2:
        # Calcular coordenadas y dimensiones
        x1, y1 = ref_point[0]
        x2, y2 = ref_point[1]
        
        x = min(x1, x2)
        y = min(y1, y2)
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        
        region = {
            "left": x,
            "top": y,
            "width": width,
            "height": height
        }
        
        # Guardar la región en archivo
        save_region(region)
        
        print(f"✅ Región guardada: {width}x{height} en ({x}, {y})")
        return region
    
    return None

def save_region(region):
    """Guarda la región seleccionada en un archivo JSON"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(region, f, indent=2)

def load_region():
    """Carga la región guardada desde el archivo JSON"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return None

def capture_region(region=None):
    """
    Captura solo la región especificada de la pantalla.
    Si no se proporciona región, usa la guardada.
    """
    if region is None:
        region = load_region()
    
    if region is None:
        raise ValueError("No hay región guardada. Ejecuta select_region() primero.")
    
    with mss.mss() as sct:
        # Capturar la región específica
        screenshot = sct.grab(region)
        img = np.array(screenshot)
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    
    return img

def has_saved_region():
    """Verifica si existe una región guardada"""
    return os.path.exists(CONFIG_FILE)

if __name__ == '__main__':
    # Test: seleccionar región
    print("🎯 Modo de prueba - Selección de región")
    region = select_region()
    if region:
        print(f"✅ Región seleccionada: {region}")
        print("📸 Capturando región seleccionada...")
        img = capture_region(region)
        print(f"✅ Captura completada: {img.shape}")
        
        # Mostrar resultado
        cv2.imshow("Región capturada", img)
        print("Presiona cualquier tecla para cerrar...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
