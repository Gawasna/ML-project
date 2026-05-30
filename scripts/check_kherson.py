import json
import hashlib

src_file = "extracted_the_gioi.jsonl"
tgt_file = "translated_the_gioi.jsonl"
report_file = "scratch/kherson_report.txt"

with open(report_file, "w", encoding="utf-8") as rf:
    rf.write("--- SOURCE OCCURRENCES OF KHERSON ---\n")
    with open(src_file, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            if line.strip():
                data = json.loads(line)
                vi = data.get("output", "")
                if "Kherson" in vi:
                    h = hashlib.md5(vi.strip().encode('utf-8')).hexdigest()
                    rf.write(f"Line {line_num} in Source: Length={len(vi)}, MD5={h}, Snippet={vi[:60]}...\n")

    rf.write("\n--- TARGET OCCURRENCES OF KHERSON ---\n")
    with open(tgt_file, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            if line.strip():
                data = json.loads(line)
                vi = data.get("output", "")
                if "Kherson" in vi:
                    h = hashlib.md5(vi.strip().encode('utf-8')).hexdigest()
                    rf.write(f"Line {line_num} in Target: Length={len(vi)}, MD5={h}, Snippet={vi[:60]}...\n")
