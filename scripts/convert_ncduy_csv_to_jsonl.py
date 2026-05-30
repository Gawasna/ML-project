import os
import csv
import json
import hashlib
import time

def convert_csv_to_jsonl():
    raws_dir = r"C:\Users\hungl\Documents\trae_projects\ML-project\temp\labs-ml\raws\ncduy"
    output_dir = r"C:\Users\hungl\Documents\trae_projects\ML-project\data\train\prepared"
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    csv_files = ["test.csv", "valid.csv", "train.csv"] # Process smaller files first for safety

    print("Starting high-efficiency memory-safe CSV to JSONL conversion...")

    for csv_file in csv_files:
        csv_path = os.path.join(raws_dir, csv_file)
        if not os.path.exists(csv_path):
            print(f"Warning: File {csv_file} not found. Skipping.")
            continue

        jsonl_filename = f"prepared_ncduy_{os.path.splitext(csv_file)[0]}.jsonl"
        jsonl_path = os.path.join(output_dir, jsonl_filename)

        print(f"\nProcessing: {csv_file} -> {jsonl_filename}")
        start_time = time.time()

        total_rows = 0
        valid_rows = 0
        duplicate_count = 0
        
        # Use a set of MD5 hashes to keep VRAM/RAM footprint minimal for train.csv (597MB)
        seen_hashes = set()

        # Increase CSV field size limit just in case of very large text cells
        csv.field_size_limit(10000000)

        with open(csv_path, "r", encoding="utf-8") as infile, \
             open(jsonl_path, "w", encoding="utf-8") as outfile:
            
            # Using csv.reader to avoid memory overhead of Pandas
            reader = csv.reader(infile)
            
            # Read header
            try:
                header = next(reader)
                # Find columns index mapping
                en_idx = header.index("en")
                vi_idx = header.index("vi")
            except (StopIteration, ValueError) as e:
                print(f"Error reading header of {csv_file}: {e}")
                continue

            for row in reader:
                total_rows += 1
                if not row or len(row) <= max(en_idx, vi_idx):
                    continue

                en_text = row[en_idx].strip()
                vi_text = row[vi_idx].strip()

                if not en_text or not vi_text:
                    continue

                # Deduplicate based on English input hash
                input_hash = hashlib.md5(en_text.encode('utf-8')).hexdigest()
                if input_hash in seen_hashes:
                    duplicate_count += 1
                    continue
                else:
                    seen_hashes.add(input_hash)

                # Structure output JSON
                record = {
                    "instruction": "Dịch thuật sang Tiếng việt theo chủ đề Thời sự",
                    "input": en_text,
                    "output": vi_text
                }

                # Write directly to JSONL to keep memory O(1) space
                outfile.write(json.dumps(record, ensure_ascii=False) + "\n")
                valid_rows += 1

                if total_rows % 100000 == 0:
                    print(f"  Processed {total_rows} rows...")

        duration = time.time() - start_time
        print(f"--> SUCCESS: Processed {csv_file}")
        print(f"    Total Rows Read:      {total_rows}")
        print(f"    Unique Rows Saved:    {valid_rows} ({(valid_rows/total_rows)*100:.2f}%)")
        print(f"    Duplicates Removed:   {duplicate_count}")
        print(f"    Time Elapsed:         {duration:.2f} seconds")
        print(f"    File Size before:     {os.path.getsize(csv_path) / (1024*1024):.2f} MB")
        print(f"    File Size after:      {os.path.getsize(jsonl_path) / (1024*1024):.2f} MB")

if __name__ == "__main__":
    convert_csv_to_jsonl()
