import sys
import hashlib
import json
import os

sys.stdout.reconfigure(encoding='utf-8')

def get_md5(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()

input_file = "C:/Users/hungl/Downloads/Temp/labs-ml/labs-ml/extracted_the_gioi.jsonl"
output_file = "C:/Users/hungl/Downloads/Temp/labs-ml/labs-ml/translated_the_gioi.jsonl"

processed_hashes = set()
if os.path.exists(output_file):
    with open(output_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    data = json.loads(line)
                    vi_content = data.get("output", "")
                    en_content = data.get("input", "")
                    if vi_content and en_content and en_content != "[TRANSLATION FAILED]":
                        h = get_md5(vi_content.strip())
                        processed_hashes.add(h)
                except Exception as e:
                    print(f"Err output line: {e}")

print(f"Total processed hashes: {len(processed_hashes)}")

# Print all MD5s of Orlan-10 records in translated file
print("\nOrlan-10 records in translated file after cleanup:")
if os.path.exists(output_file):
    with open(output_file, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if "Một sĩ quan thông tin" in line:
                try:
                    data = json.loads(line)
                    vi_content = data.get("output", "")
                    h = get_md5(vi_content.strip())
                    is_in_processed = h in processed_hashes
                    print(f"Line {idx+1}: MD5={h} | In processed_hashes: {is_in_processed}")
                except Exception as e:
                    print(f"Line {idx+1} Error: {e}")

# Investigate Cyprus, Gas Saving, and Summary records status
prefixes = ["Việc EU cấp tập", "Tiết kiệm cho một mùa đông", "Trong một lá thư, bác sĩ"]
found_records = []
if os.path.exists(input_file):
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    data = json.loads(line)
                    vi_content = data.get("output", "")
                    if vi_content:
                        h = get_md5(vi_content.strip())
                        is_processed = h in processed_hashes
                        for p in prefixes:
                            if p in vi_content:
                                found_records.append((p, h, is_processed, vi_content[:50]))
                except Exception as e:
                    print(f"Err input line: {e}")

print("Investigating records in source file:")
for p, h, is_p, txt in found_records:
    print(f"Prefix: {p} | MD5: {h} | Processed: {is_p} | Text: {txt}")

# Check translated file for these
print("\nInvestigating in translated file:")
if os.path.exists(output_file):
    with open(output_file, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            for p in prefixes:
                if p in line:
                    try:
                        data = json.loads(line)
                        vi_content = data.get("output", "")
                        h = get_md5(vi_content.strip())
                        print(f"Line {idx+1}: Prefix: {p} | MD5 in translated: {h}")
                    except Exception as e:
                        print(f"Line {idx+1} Error: {e}")



# Let's compare Cyprus, Gas Saving, and Summary records
def find_diff(label, src, tr):
    if src and tr:
        print(f"\n--- {label} ---")
        print(f"Source MD5: {get_md5(src.strip())} | Len: {len(src)}")
        print(f"Translated MD5: {get_md5(tr.strip())} | Len: {len(tr)}")
        for i, (c1, c2) in enumerate(zip(src, tr)):
            if c1 != c2:
                print(f"Mismatch at index {i}: source={repr(src[i:i+30])} vs translated={repr(tr[i:i+30])}")
                break

src_cyprus = None
tr_cyprus = None
if os.path.exists(input_file):
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            if "Việc EU cấp tập" in line:
                src_cyprus = json.loads(line).get("output", "")
                break
if os.path.exists(output_file):
    with open(output_file, "r", encoding="utf-8") as f:
        for line in f:
            if "Việc EU cấp tập" in line:
                tr_cyprus = json.loads(line).get("output", "")
                break

find_diff("CYPRUS", src_cyprus, tr_cyprus)

src_gas = None
tr_gas = None
if os.path.exists(input_file):
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            if "Tiết kiệm cho một mùa đông" in line:
                src_gas = json.loads(line).get("output", "")
                break
if os.path.exists(output_file):
    with open(output_file, "r", encoding="utf-8") as f:
        for line in f:
            if "Tiết kiệm cho một mùa đông" in line:
                tr_gas = json.loads(line).get("output", "")
                break

find_diff("GAS SAVING", src_gas, tr_gas)

src_sum = None
tr_sum = None
if os.path.exists(input_file):
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            if "Trong một lá thư, bác sĩ" in line:
                src_sum = json.loads(line).get("output", "")
                break
if os.path.exists(output_file):
    with open(output_file, "r", encoding="utf-8") as f:
        for line in f:
            if "Trong một lá thư, bác sĩ" in line:
                tr_sum = json.loads(line).get("output", "")
                break

find_diff("SUMMARY", src_sum, tr_sum)



# End of script

