import json
import urllib.request
import time
import sys

def test_model(model_name, text):
    url = "http://127.0.0.1:11434/api/chat"
    payload = {
        "model": model_name,
        "messages": [
            {
                "role": "system",
                "content": "Dịch đoạn văn tiếng Anh sau đây sang tiếng Việt một cách tự nhiên và chuyên nghiệp theo chủ đề Thời sự. Chỉ cung cấp duy nhất bản dịch, không thêm lời mở đầu, giải thích hay đặt trong dấu ngoặc kép."
            },
            {
                "role": "user",
                "content": text
            }
        ],
        "stream": False,
        "options": {
            "temperature": 0.3,
            "num_ctx": 4096
        }
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=data,
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"\nTesting model: {model_name}")
    print(f"Input English: '{text}'")
    start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=40) as response:
            res_data = response.read().decode('utf-8')
            res_obj = json.loads(res_data)
            translation = res_obj.get("message", {}).get("content", "").strip()
            elapsed = time.time() - start
            print(f"Status: SUCCESS")
            print(f"Elapsed Time: {elapsed:.3f} seconds")
            print(f"Translation Output:\n{translation}")
            print(f"Output Length: {len(translation)} chars, {len(translation.split())} words")
            return translation, elapsed, True
    except Exception as e:
        elapsed = time.time() - start
        print(f"Status: FAILED")
        print(f"Elapsed Time: {elapsed:.3f} seconds")
        print(f"Error: {e}")
        return "", elapsed, False

test_text = "Reality suggests that leaving a mark in a once underdeveloped region can sometimes be easier than charting a breakthrough path for a mega-city that has already grown large and prosperous."

print("=== DIAGNOSTIC OLLAMA TEST ===")
test_model("qwen2.5:1.5b", test_text)
test_model("qwen2.5-vi", test_text)
