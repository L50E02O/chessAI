"""Script de prueba para Roboflow API"""
from inference_sdk import InferenceHTTPClient

API_KEY = "X3y287bLrr6Qny0oXKMG"
MODEL_ID = "chess-pieces-mjzgj/1"

client = InferenceHTTPClient(
    api_url="https://detect.roboflow.com",
    api_key=API_KEY
)

print("Cliente creado OK")

# Probar con URL de imagen
test_url = "https://images.chesscomfiles.com/uploads/v1/images_users/tiny_mce/SamCopeland/phpmeXx6V.png"

try:
    result = client.infer(test_url, model_id=MODEL_ID)
    predictions = result.get("predictions", [])
    print(f"Predicciones encontradas: {len(predictions)}")
    for p in predictions[:5]:
        print(f"  - {p.get('class')}: {p.get('confidence'):.2f}")
except Exception as e:
    print(f"Error: {e}")
