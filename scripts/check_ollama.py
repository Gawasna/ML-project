import urllib.request
import json
import sys

# Reconfigure stdout to use UTF-8 encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def check_ollama():
    print("Checking connection to Ollama server at http://localhost:11434...")
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags")
        with urllib.request.urlopen(req, timeout=5) as response:
            res_data = response.read().decode('utf-8')
            models = json.loads(res_data).get("models", [])
            available_models = [m.get("name") for m in models]
            print(f"Ollama connected successfully!")
            print(f"Available models in library: {available_models}")
            
            target_model = "aya:8b"
            has_model = False
            for m in available_models:
                if target_model in m or m.startswith(target_model):
                    has_model = True
                    break
                    
            if has_model:
                print(f"SUCCESS: Model '{target_model}' is available and ready for testing!")
                sys.exit(0)
            else:
                print(f"WARNING: Model '{target_model}' is NOT found in your local library.")
                print(f"Please run 'ollama pull {target_model}' to download the model first.")
                sys.exit(2)
    except urllib.error.URLError as e:
        print(f"ERROR: Cannot connect to Ollama server. Please ensure Ollama is running. Error details: {e}")
        sys.exit(1)

if __name__ == "__main__":
    check_ollama()
