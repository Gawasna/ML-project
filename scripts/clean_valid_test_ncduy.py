import os
import json
import re
import time

def clean_dataset_file(file_path):
    temp_output_path = file_path + ".tmp"
    start_time = time.time()

    total_lines = 0
    clean_lines = 0
    removed_cjk = 0
    removed_other_non_latin = 0
    lrm_removed_count = 0
    modified_lrm_lines = 0
    corrupted_lines = 0

    # Compile regex patterns
    cjk_pattern = re.compile(r"[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af]")
    other_non_latin_pattern = re.compile(r"[\u0400-\u04ff\u0600-\u06ff]")
    lrm_char = "\u200e"

    with open(file_path, "r", encoding="utf-8", errors="ignore") as infile, \
         open(temp_output_path, "w", encoding="utf-8") as outfile:
        
        for line in infile:
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

            # 1. Filter out CJK and non-Latin noisy lines
            if CJK_found := (cjk_pattern.search(eng_text) or cjk_pattern.search(vi_text)):
                removed_cjk += 1
                continue

            if other_non_latin_found := (other_non_latin_pattern.search(eng_text) or other_non_latin_pattern.search(vi_text)):
                removed_other_non_latin += 1
                continue

            # 2. Eradicate U+200E LRM control characters
            lrm_in_eng = eng_text.count(lrm_char)
            lrm_in_vi = vi_text.count(lrm_char)

            if lrm_in_eng > 0 or lrm_in_vi > 0:
                data["input"] = eng_text.replace(lrm_char, "")
                data["output"] = vi_text.replace(lrm_char, "")
                modified_lrm_lines += 1
                lrm_removed_count += (lrm_in_eng + lrm_in_vi)

            outfile.write(json.dumps(data, ensure_ascii=False) + "\n")
            clean_lines += 1

    # Safe file replacement
    if os.path.exists(temp_output_path):
        size_before = os.path.getsize(file_path)
        size_after = os.path.getsize(temp_output_path)
        os.replace(temp_output_path, file_path)
        
        duration = time.time() - start_time
        print(f"\n=========================================")
        print(f"REPORT FOR: {os.path.basename(file_path)}")
        print(f"=========================================")
        print(f"Total Rows Scanned:            {total_lines}")
        print(f"Clean Rows Saved:              {clean_lines} ({(clean_lines/total_lines)*100:.2f}%)")
        print(f"Removed CJK (Chinese/Jap/Kor): {removed_cjk}")
        print(f"Removed Cyrillic/Arabic:       {removed_other_non_latin}")
        print(f"Rows with U+200E Cleaned:      {modified_lrm_lines}")
        print(f"Total U+200E Chars Eradicated: {lrm_removed_count}")
        print(f"Time Elapsed:                  {duration:.2f} seconds")
        print(f"File Size before:              {size_before / (1024*1024):.2f} MB")
        print(f"File Size after:               {size_after / (1024*1024):.2f} MB")
    else:
        print(f"Error: Temporary file for {os.path.basename(file_path)} not created.")

def clean_valid_and_test():
    prepared_dir = r"C:\Users\hungl\Documents\trae_projects\ML-project\data\train\prepared"
    
    if not os.path.exists(prepared_dir):
        print(f"Error: Prepared directory not found at {prepared_dir}")
        return

    # Dynamically find test and valid files (resilient to renaming hooks)
    test_files = [os.path.join(prepared_dir, f) for f in os.listdir(prepared_dir) 
                  if f.endswith(".jsonl") and "ncduy_test" in f]
                  
    valid_files = [os.path.join(prepared_dir, f) for f in os.listdir(prepared_dir) 
                   if f.endswith(".jsonl") and "ncduy_valid" in f]

    if not test_files:
        print("Error: ncduy_test file not found in prepared directory.")
    else:
        clean_dataset_file(test_files[0])

    if not valid_files:
        print("Error: ncduy_valid file not found in prepared directory.")
    else:
        clean_dataset_file(valid_files[0])

if __name__ == "__main__":
    clean_valid_and_test()
