import json
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

tgt_file = "translated_the_gioi.jsonl"
with open(tgt_file, "r", encoding="utf-8") as f:
    lines = [json.loads(line) for line in f if line.strip()]

print(f"Total translated lines: {len(lines)}")
for idx in range(-5, 0):
    item = lines[idx]
    actual_idx = len(lines) + idx + 1
    print(f"Line {actual_idx}:")
    print(f"  EN: {item.get('input', '')[:120]}...")
    print(f"  VI: {item.get('output', '')[:120]}...")
