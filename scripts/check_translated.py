import json
import hashlib
import collections

output_file = "translated_the_gioi.jsonl"
report_file = "duplicate_report.txt"
hashes = collections.defaultdict(list)

with open(output_file, "r", encoding="utf-8") as f:
    for idx, line in enumerate(f, 1):
        if line.strip():
            try:
                data = json.loads(line)
                vi = data.get("output", "")
                md5 = hashlib.md5(vi.strip().encode('utf-8')).hexdigest()
                hashes[md5].append((idx, vi[:100]))
            except Exception as e:
                with open(report_file, "a", encoding="utf-8") as rf:
                    rf.write(f"Error at line {idx}: {e}\n")

duplicates = {k: v for k, v in hashes.items() if len(v) > 1}
with open(report_file, "w", encoding="utf-8") as rf:
    if duplicates:
        rf.write(f"Found {len(duplicates)} duplicates:\n")
        for md5, items in duplicates.items():
            rf.write(f"Hash {md5}:\n")
            for idx, short in items:
                rf.write(f"  Line {idx}: {short}...\n")
    else:
        rf.write("No duplicates found!\n")
