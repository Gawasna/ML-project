import json

output_file = "translated_the_gioi.jsonl"
lines = {}

with open(output_file, "r", encoding="utf-8") as f:
    for idx, line in enumerate(f, 1):
        if line.strip():
            data = json.loads(line)
            vi = data.get("output", "")
            if "Nữ sinh năm hai đại học ở Uy Hải" in vi:
                lines[idx] = vi

with open("hash_diff_report.txt", "w", encoding="utf-8") as rf:
    line_nums = list(lines.keys())
    rf.write(f"Found lines at numbers: {line_nums}\n")
    for i in range(len(line_nums)):
        for j in range(i + 1, len(line_nums)):
            idx1, idx2 = line_nums[i], line_nums[j]
            s1, s2 = lines[idx1], lines[idx2]
            rf.write(f"\n--- Comparing Line {idx1} and Line {idx2} ---\n")
            if s1 == s2:
                rf.write("Strings are exactly identical!\n")
            else:
                rf.write(f"Strings differ! Lengths: {len(s1)} vs {len(s2)}\n")
                # find first difference
                min_len = min(len(s1), len(s2))
                diff_found = False
                for k in range(min_len):
                    if s1[k] != s2[k]:
                        rf.write(f"First diff at char {k}:\n")
                        rf.write(f"  Line {idx1}[{max(0, k-10)}:{k+10}]: {repr(s1[max(0, k-10):k+10])}\n")
                        rf.write(f"  Line {idx2}[{max(0, k-10)}:{k+10}]: {repr(s2[max(0, k-10):k+10])}\n")
                        diff_found = True
                        break
                if not diff_found:
                    rf.write("No difference in first min_len chars. One is longer.\n")
                    rf.write(f"  Line {idx1} length: {len(s1)}, extra: {repr(s1[min_len:])}\n")
                    rf.write(f"  Line {idx2} length: {len(s2)}, extra: {repr(s2[min_len:])}\n")
