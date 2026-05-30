import json
import hashlib

input_file = "extracted_the_gioi.jsonl"
output_file = "translated_the_gioi.jsonl"
result_file = "scratch/debug_result.txt"

with open(output_file, "r", encoding="utf-8") as f:
    lines = [line.strip() for line in f if line.strip()]
last_5_lines = lines[-5:]

with open(result_file, "w", encoding="utf-8") as out_f:
    out_f.write("--- LAST 5 TRANSLATED LINES ---\n")
    for idx, line in enumerate(last_5_lines, 1):
        data = json.loads(line)
        vi = data.get("output", "")
        h = hashlib.md5(vi.strip().encode('utf-8')).hexdigest()
        out_f.write(f"Index {idx} (Translated):\n")
        out_f.write(f"  Length: {len(vi)}\n")
        out_f.write(f"  MD5: {h}\n")
        out_f.write(f"  Snippet: {vi[:50]}...\n")
        
        # Try to find matching text in source file
        found = False
        with open(input_file, "r", encoding="utf-8") as inf:
            for line_num, src_line in enumerate(inf, 1):
                if src_line.strip():
                    src_data = json.loads(src_line)
                    src_vi = src_data.get("output", "")
                    src_h = hashlib.md5(src_vi.strip().encode('utf-8')).hexdigest()
                    
                    # Check by text snippet or hash
                    if src_h == h:
                        out_f.write(f"  -> Match found in source at line {line_num} (by exact hash!)\n")
                        found = True
                        break
                    elif vi[:30] in src_vi:
                        out_f.write(f"  -> Partial match in source at line {line_num} (but hash differs!)\n")
                        out_f.write(f"     Source length: {len(src_vi)}\n")
                        out_f.write(f"     Source MD5: {src_h}\n")
                        # Print first character diff
                        min_len = min(len(vi), len(src_vi))
                        for i in range(min_len):
                            if vi[i] != src_vi[i]:
                                out_f.write(f"     First diff at index {i}: repr(trans)={repr(vi[i-5:i+10])} vs repr(src)={repr(src_vi[i-5:i+10])}\n")
                                break
                        else:
                            out_f.write(f"     Lengths differ: trans={len(vi)} vs src={len(src_vi)}\n")
                        found = True
                        break
        if not found:
            out_f.write("  -> NO MATCH FOUND AT ALL IN SOURCE\n")
