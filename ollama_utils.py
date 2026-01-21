"""
Ollama API統合用のユーティリティモジュール
"""
import requests
import base64
import io
from PIL import Image

# --- 設定エリア ---
OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = 'llama3.2-vision'  # Ollamaのビジョンモデル


def image_to_base64(image):
    """画像をBase64エンコードする"""
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str


def call_ollama_vision(prompt, image):
    """Ollama APIを呼び出してビジョンモデルに画像解析を依頼"""
    img_base64 = image_to_base64(image)
    
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "images": [img_base64],
        "stream": False
    }
    
    try:
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        return result.get("response", "")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Ollama API呼び出しエラー: {e}")
