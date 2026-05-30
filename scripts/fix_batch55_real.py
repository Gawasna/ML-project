import json
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

src_file = "extracted_the_gioi.jsonl"
tgt_file = "translated_the_gioi.jsonl"

# Read correct source texts
# Dòng nguồn 430 (index 429), 431 (index 430), 433 (index 432), 434 (index 433), 435 (index 434)
src_indices = [430, 431, 433, 434, 435]
src_lines = {}
with open(src_file, "r", encoding="utf-8") as f:
    for idx, line in enumerate(f, 1):
        if idx in src_indices:
            src_lines[idx] = json.loads(line).get("output", "")

# Read all target lines
tgt_lines = []
with open(tgt_file, "r", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            tgt_lines.append(json.loads(line))

# Overwrite target lines 492-496 (0-indexed: 491-495) with correct source texts
for offset, src_idx in enumerate(src_indices):
    tgt_idx = 492 + offset
    tgt_lines[tgt_idx - 1]["output"] = src_lines[src_idx]
    print(f"Mapping: Target line {tgt_idx} -> Source line {src_idx}")

# Overwrite target file
with open(tgt_file, "w", encoding="utf-8") as f:
    for data in tgt_lines:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")

print("Fixed Batch 55 mapping successfully!")
