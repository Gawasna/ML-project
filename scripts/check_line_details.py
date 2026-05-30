import json
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

src_file = "extracted_the_gioi.jsonl"
with open(src_file, "r", encoding="utf-8") as f:
    for idx, line in enumerate(f, 1):
        if idx in range(536, 543):
            src_data = json.loads(line)
            print(f"Line {idx}: {src_data.get('output', '')[:100]}...")
