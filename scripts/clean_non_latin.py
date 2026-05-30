import os
import json
import re
import time

def clean_non_latin_dataset():
    prepared_dir = r"C:\Users\hungl\Documents\trae_projects\ML-project\data\train\prepared"
    
    if not os.path.exists(prepared_dir):
        print(f"Error: Prepared directory not found at {prepared_dir}")
        return

    # Find the actual train file (resilient to renaming hooks)
    train_files = [os.path.join(prepared_dir, f) for f in os.listdir(prepared_dir) 
                   if f.endswith(".jsonl") and "ncduy_train" in f]
    
    if not train_files:
        print("Error: data_ncduy_train_.jsonl file not found in prepared directory.")
        return
        
    input_path = train_files[0]
    temp_output_path = input_path + ".tmp"

    print("Starting high-speed stream filtering of non-Latin and non-UTF8 noise...")
    start_time = time.time()

    total_lines = 0
    clean_lines = 0
    removed_cjk_lines = 0
    removed_other_non_latin_lines = 0
    corrupted_lines = 0

    # 1. Regex pattern to detect CJK (Chinese, Japanese, Korean) characters
    cjk_pattern = re.compile(r"[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af]")
    
    # 2. Regex pattern to detect Cyrillic and Arabic characters which are non-Latin noise
    other_non_latin_pattern = re.compile(r"[\u0400-\u04ff\u0600-\u06ff]")

    with open(input_path, "r", encoding="utf-8", errors="ignore") as infile, \
         open(temp_output_path, "w", encoding="utf-8") as outfile:
        
        for line_num, line in enumerate(infile, 1):
            total_lines += 1
            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                corrupted_lines += 1
                continue

            eng_text = data.get("input", "")
            vi_text = data.get("output", "")

            # A. Check CJK characters in both fields
            if cjk_pattern.search(eng_text) or cjk_pattern.search(vi_text):
                removed_cjk_lines += 1
                continue

            # B. Check other non-Latin characters (Cyrillic, Arabic)
            if other_non_latin_pattern.search(eng_text) or other_non_latin_pattern.search(vi_text):
                removed_other_non_latin_lines += 1
                continue

            # If clean, write to temporary output
            outfile.write(json.dumps(data, ensure_ascii=False) + "\n")
            clean_lines += 1

            if line_num % 500000 == 0:
                print(f"  Processed {line_num} rows...")

    # Safe swap files
    if os.path.exists(temp_output_path):
        size_before = os.path.getsize(input_path)
        size_after = os.path.getsize(temp_output_path)
        
        os.replace(temp_output_path, input_path)
        
        duration = time.time() - start_time
        print("\n=== DATASET LATIN FILTERING REPORT ===")
        print(f"Total Rows Scanned:            {total_lines}")
        print(f"Clean Rows Saved:              {clean_lines} ({(clean_lines/total_lines)*100:.2f}%)")
        print(f"Removed CJK (Chinese/Jap/Kor): {removed_cjk_lines}")
        print(f"Removed Cyrillic/Arabic:       {removed_other_non_latin_lines}")
        print(f"Corrupted Lines Skipped:       {corrupted_lines}")
        print(f"Time Elapsed:                  {duration:.2f} seconds")
        print(f"File Size before:              {size_before / (1024*1024):.2f} MB")
        print(f"File Size after:               {size_after / (1024*1024):.2f} MB")
        print(f"Cleaned dataset saved at:      {input_path}")
    else:
        print("Error: Temporary output file was not created successfully.")

if __name__ == "__main__":
    clean_non_latin_dataset()
