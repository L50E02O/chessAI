"""
Region selector to capture only the chess board.
"""
import cv2
import numpy as np
import mss
import json
import os

CONFIG_FILE = os.path.join(os.path.dirname(__file__), '..', 'board_region.json')

def select_region():
    """
    Allows the user to select a rectangular region on the screen.
    Returns coordinates (x, y, width, height)
    """
    print("📸 Capturing full screen for selection...")
    
    # Capture full screen
    with mss.mss() as sct:
        # Take screenshot of all monitors
        monitor = sct.monitors[0]  # Monitor 0 = all monitors combined
        screenshot = sct.grab(monitor)
        img = np.array(screenshot)
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    
    # Variables for selection
    clone = img.copy()
    ref_point = []
    selecting = False
    
    def click_and_crop(event, x, y, flags, param):
        nonlocal ref_point, selecting, clone
        
        # If left click, register initial point
        if event == cv2.EVENT_LBUTTONDOWN:
            ref_point = [(x, y)]
            selecting = True
        
        # If mouse moves while selecting, draw rectangle
        elif event == cv2.EVENT_MOUSEMOVE and selecting:
            clone = img.copy()
            cv2.rectangle(clone, ref_point[0], (x, y), (0, 255, 0), 2)
        
        # If button is released, register final point
        elif event == cv2.EVENT_LBUTTONUP:
            ref_point.append((x, y))
            selecting = False
            cv2.rectangle(clone, ref_point[0], ref_point[1], (0, 255, 0), 2)
    
    # Create window and set callback
    window_name = "Select the chess board - Drag and drop, then press ENTER"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(window_name, click_and_crop)
    
    # Resize window to fit on screen
    screen_height, screen_width = img.shape[:2]
    display_width = min(1280, screen_width)
    display_height = int(screen_height * (display_width / screen_width))
    cv2.resizeWindow(window_name, display_width, display_height)
    
    print("🖱️ Instructions:")
    print("   1. Drag the mouse over the chess board")
    print("   2. Press ENTER to confirm")
    print("   3. Press ESC to cancel")
    
    # Wait for user to select and press ENTER
    while True:
        cv2.imshow(window_name, clone)
        key = cv2.waitKey(1) & 0xFF
        
        # If ENTER is pressed and 2 points are selected
        if key == 13 and len(ref_point) == 2:  # 13 = ENTER
            break
        
        # If ESC is pressed, cancel
        elif key == 27:  # 27 = ESC
            cv2.destroyAllWindows()
            return None
    
    cv2.destroyAllWindows()
    
    if len(ref_point) == 2:
        # Calculate coordinates and dimensions
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
        
        # Save region to file
        save_region(region)
        
        print(f"✅ Region saved: {width}x{height} at ({x}, {y})")
        return region
    
    return None

def save_region(region):
    """Saves the selected region to a JSON file"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(region, f, indent=2)

def load_region():
    """Loads the saved region from the JSON file"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return None

def capture_region(region=None):
    """
    Captures only the specified region of the screen.
    If no region is provided, uses the saved one.
    """
    if region is None:
        region = load_region()
    
    if region is None:
        raise ValueError("No saved region. Run select_region() first.")
    
    with mss.mss() as sct:
        # Capture the specific region
        screenshot = sct.grab(region)
        img = np.array(screenshot)
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    
    return img

def has_saved_region():
    """Checks if a saved region exists"""
    return os.path.exists(CONFIG_FILE)

if __name__ == '__main__':
    # Test: select region
    print("🎯 Test mode - Region selection")
    region = select_region()
    if region:
        print(f"✅ Region selected: {region}")
        print("📸 Capturing selected region...")
        img = capture_region(region)
        print(f"✅ Capture completed: {img.shape}")
        
        # Show result
        cv2.imshow("Captured region", img)
        print("Press any key to close...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
