import json
import hashlib

input_file = "extracted_the_gioi.jsonl"
output_file = "translated_the_gioi.jsonl"
report_file = "hash_report.txt"

with open(report_file, "w", encoding="utf-8") as rf:
    rf.write("--- FROM INPUT FILE ---\n")
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                vi = data.get("output", "")
                if "Nữ sinh năm hai đại học ở Uy Hải" in vi:
                    h = hashlib.md5(vi.strip().encode('utf-8')).hexdigest()
                    rf.write(f"Text len: {len(vi)}, MD5: {h}\n")
                    rf.write(f"{repr(vi[:100])}\n")
                    break

    rf.write("\n--- FROM OUTPUT FILE ---\n")
    with open(output_file, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f, 1):
            if line.strip():
                data = json.loads(line)
                vi = data.get("output", "")
                if "Nữ sinh năm hai đại học ở Uy Hải" in vi:
                    h = hashlib.md5(vi.strip().encode('utf-8')).hexdigest()
                    rf.write(f"Line {idx} - Text len: {len(vi)}, MD5: {h}\n")
                    rf.write(f"{repr(vi[:100])}\n")
