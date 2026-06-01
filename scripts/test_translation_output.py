import json
import urllib.request
import time

def test_and_save(model_name, text, filepath):
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
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            res_data = response.read().decode('utf-8')
            res_obj = json.loads(res_data)
            translation = res_obj.get("message", {}).get("content", "").strip()
            
            with open(filepath, "a", encoding="utf-8") as f:
                f.write(f"=== MODEL: {model_name} ===\n")
                f.write(f"English: {text}\n")
                f.write(f"Vietnamese: {translation}\n")
                f.write(f"Length: {len(translation.split())} words\n")
                f.write("-" * 50 + "\n\n")
            print(f"Success saving output for {model_name}")
    except Exception as e:
        print(f"Error for {model_name}: {e}")

test_text = "Reality suggests that leaving a mark in a once underdeveloped region can sometimes be easier than charting a breakthrough path for a mega-city that has already grown large and prosperous."

filepath = "diagnostics_output.txt"
# Clear file first
with open(filepath, "w", encoding="utf-8") as f:
    f.write("=== DIAGNOSTIC TRANSLATION OUTPUT ===\n\n")

test_and_save("qwen2.5:1.5b", test_text, filepath)
test_and_save("qwen2.5-vi", test_text, filepath)
