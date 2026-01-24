import requests
import json

# 貼上你的 API Key
API_KEY = "AIzaSyCUmsAZ52fpN44LegDnhHo-0Sf6cQOltes"

def list_my_models():
    print("正在查詢你的可用模型清單...\n")
    
    # 這是向 Google 詢問「我有什麼模型可用？」的網址
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
    
    try:
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            models = data.get('models', [])
            
            print("=== 🎉 你的帳號可用模型如下 ===")
            found_any = False
            for m in models:
                # 我們只列出可以產生文字的模型 (generateContent)
                if 'generateContent' in m.get('supportedGenerationMethods', []):
                    # 只顯示 gemini 系列
                    if 'gemini' in m['name']:
                        print(f"👉 {m['name']}")
                        found_any = True
            
            if not found_any:
                print("❌ 沒看到任何 Gemini 模型，可能是地區限制或帳號設定問題。")
                
        else:
            print(f"❌ 查詢失敗 (Error {response.status_code})")
            print(f"原因: {response.text}")
            
    except Exception as e:
        print(f"❌ 連線發生錯誤: {e}")

if __name__ == "__main__":
    list_my_models()