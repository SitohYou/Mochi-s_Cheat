# check_models.py - Ollama モデル確認スクリプト
import requests

OLLAMA_API_URL = "http://localhost:11434/api/tags"

print("🔍 Ollamaで利用可能なモデルを確認しています...")
try:
    response = requests.get(OLLAMA_API_URL, timeout=5)
    response.raise_for_status()
    
    models = response.json().get("models", [])
    
    if models:
        print("\n✅ 利用可能なモデル:")
        for model in models:
            print(f"  - {model['name']}")
        
        # llama3.2-visionが含まれているか確認
        vision_models = [m for m in models if 'vision' in m['name'].lower() or 'llama3.2' in m['name'].lower()]
        if vision_models:
            print("\n✅ ビジョンモデルが見つかりました！")
        else:
            print("\n⚠️  ビジョンモデルが見つかりません。")
            print("   以下のコマンドでインストールしてください:")
            print("   ollama pull llama3.2-vision")
    else:
        print("⚠️  インストール済みのモデルがありません。")
        print("   以下のコマンドでモデルをインストールしてください:")
        print("   ollama pull llama3.2-vision")
        
except requests.exceptions.ConnectionError:
    print("❌ Ollamaサーバーに接続できません。")
    print("   以下のコマンドでOllamaサーバーを起動してください:")
    print("   ollama serve")
except Exception as e:
    print(f"❌ エラー: {e}")
