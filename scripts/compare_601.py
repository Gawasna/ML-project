import json
import hashlib
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

src_file = "extracted_the_gioi.jsonl"
tgt_file = "translated_the_gioi.jsonl"

src_val = None
with open(src_file, "r", encoding="utf-8") as f:
    for idx, line in enumerate(f, 1):
        if idx == 540:
            src_val = json.loads(line).get("output", "")
            break

tgt_val = None
with open(tgt_file, "r", encoding="utf-8") as f:
    for idx, line in enumerate(f, 1):
        if idx == 601:
            tgt_val = json.loads(line).get("output", "")
            break

print("Source 540:")
print(repr(src_val))
print("MD5:", hashlib.md5(src_val.strip().encode("utf-8")).hexdigest())

print("Target 601:")
print(repr(tgt_val))
print("MD5:", hashlib.md5(tgt_val.strip().encode("utf-8")).hexdigest())
