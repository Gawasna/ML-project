import os
import json
import re
import hashlib
import time

def merge_and_clean_thoi_su_batches():
    temp_dir = r"C:\Users\hungl\Documents\trae_projects\ML-project\temp\labs-ml"
    output_dir = r"C:\Users\hungl\Documents\trae_projects\ML-project\data\train\prepared"
    output_path = os.path.join(output_dir, "prepared_translated_thoi_su_N0002_N1000.jsonl")

    if not os.path.exists(temp_dir):
        print(f"Error: Temp directory not found at {temp_dir}")
        return

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print("Scanning and collecting all batch files (translated_thoi_su_N*.jsonl)...")
    
    # Locate all batch files matching the pattern translated_thoi_su_N*.jsonl
    batch_files = [os.path.join(temp_dir, f) for f in os.listdir(temp_dir) 
                   if f.startswith("translated_thoi_su_N") and f.endswith(".jsonl")]
    
    # Sort files naturally for ordered processing
    batch_files.sort()

    if not batch_files:
        print("Error: No batch files matching 'translated_thoi_su_N*.jsonl' found.")
        return

    print(f"Found {len(batch_files)} batch files to merge and clean.")
    start_time = time.time()

    # Regex patterns for cleaning
    cjk_pattern = re.compile(r"[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af]")
    other_non_latin_pattern = re.compile(r"[\u0400-\u04ff\u0600-\u06ff]")
    lrm_char = "\u200e"

    total_scanned_lines = 0
    valid_saved_lines = 0
    duplicate_count = 0
    removed_cjk_count = 0
    removed_other_non_latin_count = 0
    lrm_removed_chars_count = 0
    lrm_modified_lines_count = 0
    corrupted_lines_count = 0

    seen_hashes = set()

    with open(output_path, "w", encoding="utf-8") as outfile:
        for batch_file in batch_files:
            file_basename = os.path.basename(batch_file)
            print(f"Processing batch: {file_basename}")
            
            with open(batch_file, "r", encoding="utf-8", errors="ignore") as infile:
                for line in infile:
                    line = line.strip()
                    if not line:
                        continue
                    
                    total_scanned_lines += 1
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        corrupted_lines_count += 1
                        continue

                    eng_text = data.get("input", "")
                    vi_text = data.get("output", "")

                    if not eng_text or not vi_text:
                        continue

                    eng_text = str(eng_text).strip()
                    vi_text = str(vi_text).strip()

                    # A. Filter out CJK and non-Latin noisy lines
                    if cjk_pattern.search(eng_text) or cjk_pattern.search(vi_text):
                        removed_cjk_count += 1
                        continue

                    if other_non_latin_pattern.search(eng_text) or other_non_latin_pattern.search(vi_text):
                        removed_other_non_latin_count += 1
                        continue

                    # B. Deduplicate based on English input hash
                    input_hash = hashlib.md5(eng_text.encode('utf-8')).hexdigest()
                    if input_hash in seen_hashes:
                        duplicate_count += 1
                        continue
                    else:
                        seen_hashes.add(input_hash)

                    # C. Eradicate U+200E LRM control characters
                    lrm_in_eng = eng_text.count(lrm_char)
                    lrm_in_vi = vi_text.count(lrm_char)

                    if lrm_in_eng > 0 or lrm_in_vi > 0:
                        eng_text = eng_text.replace(lrm_char, "")
                        vi_text = vi_text.replace(lrm_char, "")
                        lrm_modified_lines_count += 1
                        lrm_removed_chars_count += (lrm_in_eng + lrm_in_vi)

                    # D. Structure record: strip topic and id, enforce 'Thời sự' instruction
                    record = {
                        "instruction": "Dịch thuật sang Tiếng việt theo chủ đề Thời sự",
                        "input": eng_text,
                        "output": vi_text
                    }

                    # Write clean record to unified output
                    outfile.write(json.dumps(record, ensure_ascii=False) + "\n")
                    valid_saved_lines += 1

    duration = time.time() - start_time
    print("\n=== BATCH MERGE AND DEEP CLEANING REPORT ===")
    print(f"Total Batch Files Processed:  {len(batch_files)}")
    print(f"Total Lines Scanned:          {total_scanned_lines}")
    print(f"Unique Clean Lines Saved:     {valid_saved_lines} ({(valid_saved_lines/total_scanned_lines)*100:.2f}%)")
    print(f"Duplicates Removed:           {duplicate_count}")
    print(f"Removed CJK (Chinese/Jap/Kor): {removed_cjk_count}")
    print(f"Removed Cyrillic/Arabic:       {removed_other_non_latin_count}")
    print(f"Lines with U+200E Cleaned:    {lrm_modified_lines_count}")
    print(f"Total U+200E Chars Eradicated: {lrm_removed_chars_count}")
    print(f"Corrupted Lines Skipped:       {corrupted_lines_count}")
    print(f"Time Elapsed:                 {duration:.2f} seconds")
    print(f"Output File Saved at:         {output_path}")
    print(f"Output File Size:             {os.path.getsize(output_path) / (1024*1024):.2f} MB")

if __name__ == "__main__":
    merge_and_clean_thoi_su_batches()
