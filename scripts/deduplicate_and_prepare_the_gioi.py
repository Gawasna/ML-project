import os
import json
import hashlib

def deduplicate_and_prepare_the_gioi():
    thoi_su_path = r"C:\Users\hungl\Documents\trae_projects\ML-project\data\train\prepared\prepared_translated_thoi_su.jsonl"
    the_gioi_path = r"C:\Users\hungl\Documents\trae_projects\ML-project\temp\labs-ml\translated_the_gioi.jsonl"
    output_dir = r"C:\Users\hungl\Documents\trae_projects\ML-project\data\train\prepared"
    output_path = os.path.join(output_dir, "prepared_translated_the_gioi.jsonl")

    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 1. Load already processed Thoi Su inputs to check for cross-dataset duplicates
    thoi_su_inputs = set()
    print("Scanning and loading all Thoi Su dataset files for cross-dataset duplicate auditing...")
    
    if os.path.exists(output_dir):
        thoi_su_files = [os.path.join(output_dir, f) for f in os.listdir(output_dir) 
                         if f.endswith(".jsonl") and "thoisu" in f]
        
        for ts_file_path in thoi_su_files:
            print(f"Loading inputs from: {os.path.basename(ts_file_path)}")
            with open(ts_file_path, "r", encoding="utf-8") as ts_file:
                for line in ts_file:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        eng_text = str(data.get("input", "")).strip()
                        if eng_text:
                            input_hash = hashlib.md5(eng_text.encode('utf-8')).hexdigest()
                            thoi_su_inputs.add(input_hash)
                    except json.JSONDecodeError:
                        continue
        print(f"Loaded a total of {len(thoi_su_inputs)} unique Thoi Su inputs for cross-auditing.")
    else:
        print("Warning: Output directory does not exist. Skipping cross-dataset duplicate check.")

    total_lines = 0
    valid_lines = 0
    cross_duplicates_count = 0
    internal_duplicates_count = 0
    
    # Internal tracking set for The Gioi
    seen_the_gioi_inputs = set()
    unique_records = []

    print("\nStarting deep audit on The Gioi dataset...")

    with open(the_gioi_path, "r", encoding="utf-8") as tg_file:
        for line_num, line in enumerate(infile := tg_file, 1):
            total_lines += 1
            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue

            eng_text = str(data.get("input", "")).strip()
            vi_text = str(data.get("output", "")).strip()
            instruction = str(data.get("instruction", "")).strip()

            if not eng_text or not vi_text:
                continue

            input_hash = hashlib.md5(eng_text.encode('utf-8')).hexdigest()

            # A. Check cross-dataset duplicates with Thoi Su
            if input_hash in thoi_su_inputs:
                cross_duplicates_count += 1
                continue

            # B. Check internal duplicates in The Gioi
            if input_hash in seen_the_gioi_inputs:
                internal_duplicates_count += 1
                continue
            else:
                seen_the_gioi_inputs.add(input_hash)

            # Keep clean record without the 'topic' field
            processed_data = {
                "instruction": instruction if instruction else "Dịch thuật sang Tiếng việt theo chủ đề Thế giới",
                "input": eng_text,
                "output": vi_text
            }
            unique_records.append(processed_data)
            valid_lines += 1

            if line_num % 500 == 0:
                print(f"Audited {line_num} lines of The Gioi dataset...")

    # Write unique records to target prepared path
    with open(output_path, "w", encoding="utf-8") as outfile:
        for record in unique_records:
            outfile.write(json.dumps(record, ensure_ascii=False) + "\n")

    # Summary Report
    print("\n=== THE GIOI DATASET DEDUPLICATION AUDIT REPORT ===")
    print(f"Total Lines Scanned:          {total_lines}")
    print(f"Cross-Duplicates with Thoi Su: {cross_duplicates_count}")
    print(f"Internal Duplicates:          {internal_duplicates_count}")
    print(f"Total Unique Records Kept:    {valid_lines} ({(valid_lines/total_lines)*100:.2f}%)")
    print(f"Clean processed dataset saved to: {output_path}")
    print(f"File size before:             {os.path.getsize(the_gioi_path) / (1024*1024):.2f} MB")
    print(f"File size after:              {os.path.getsize(output_path) / (1024*1024):.2f} MB")

if __name__ == "__main__":
    deduplicate_and_prepare_the_gioi()
