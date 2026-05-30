import os
import json
import time

def remove_lrm_control_chars():
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

    print(f"Starting deep eradication of invisible U+200E (LRM) chars in: {os.path.basename(input_path)}...")
    start_time = time.time()

    total_lines = 0
    modified_lines_count = 0
    total_lrm_removed = 0
    corrupted_lines = 0

    # LRM char representation in unicode
    lrm_char = "\u200e"

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

            # Count occurrences of U+200E in the strings
            lrm_in_eng = eng_text.count(lrm_char)
            lrm_in_vi = vi_text.count(lrm_char)

            if lrm_in_eng > 0 or lrm_in_vi > 0:
                # Remove U+200E chars
                data["input"] = eng_text.replace(lrm_char, "")
                data["output"] = vi_text.replace(lrm_char, "")
                
                modified_lines_count += 1
                total_lrm_removed += (lrm_in_eng + lrm_in_vi)

            # Write clean data back
            outfile.write(json.dumps(data, ensure_ascii=False) + "\n")

            if line_num % 500000 == 0:
                print(f"  Scanned {line_num} rows...")

    # Safe file replacement
    if os.path.exists(temp_output_path):
        size_before = os.path.getsize(input_path)
        size_after = os.path.getsize(temp_output_path)
        
        os.replace(temp_output_path, input_path)
        
        duration = time.time() - start_time
        print("\n=== LRM (U+200E) ERADICATION REPORT ===")
        print(f"Total Rows Scanned:          {total_lines}")
        print(f"Rows Containing U+200E:      {modified_lines_count}")
        print(f"Total U+200E Chars Eradicated: {total_lrm_removed}")
        print(f"Corrupted Lines Skipped:     {corrupted_lines}")
        print(f"Time Elapsed:                {duration:.2f} seconds")
        print(f"File Size before:            {size_before / (1024*1024):.2f} MB")
        print(f"File Size after:             {size_after / (1024*1024):.2f} MB")
        print(f"Eradicated dataset saved at: {input_path}")
    else:
        print("Error: Temporary output file was not created successfully.")

if __name__ == "__main__":
    remove_lrm_control_chars()
