"""
OCR/board detection stub.
In a full implementation this module would use OpenCV to detect the board, segment squares
and use CNN to identify pieces.
run detection on-device with a lightweight model or call a backend.

This stub attempts to import OpenCV and falls back to a mock FEN.
"""
import os

MOCK_FEN = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'


def detect_board_from_image(image_path: str) -> str:
    """Try to detect a board and return a FEN string.
    Returns None or mock FEN if detection isn't possible.
    """
    try:
        import cv2
    except Exception as e:
    # Not available – return mock FEN.
        print('OpenCV not available, returning mock FEN:', e)
        return MOCK_FEN

    # Minimal example: this is only a placeholder. Real detection is more involved.
    try:
        img = cv2.imread(image_path)
        if img is None:
            print('Could not read image, returning mock FEN')
            return MOCK_FEN
        # For now return mock; place detection pipeline here later.
        return MOCK_FEN
    except Exception as ex:
        print('Error during detection, returning mock FEN:', ex)
        return MOCK_FEN
