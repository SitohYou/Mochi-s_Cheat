# check_models.py
import google.generativeai as genai

# さっきのAPIキーを入れてください
API_KEY = "AIzaSyAf6kpnHqSyaVdcQJfI5eYrst_qD1LWc64"

genai.configure(api_key=API_KEY)

print("🔍 利用可能なモデルを探しています...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
except Exception as e:
    print(f"エラー: {e}")