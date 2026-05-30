import os
import json
import hashlib

def deduplicate_and_prepare():
    input_path = r"C:\Users\hungl\Documents\trae_projects\ML-project\temp\labs-ml\translated_thoi_su.jsonl"
    output_dir = r"C:\Users\hungl\Documents\trae_projects\ML-project\data\train\prepared"
    output_path = os.path.join(output_dir, "prepared_translated_thoi_su.jsonl")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    total_lines = 0
    valid_lines = 0
    
    # Tracking sets for deduplication
    seen_inputs = set()
    seen_pairs = set()
    
    duplicate_inputs_count = 0
    duplicate_pairs_count = 0
    
    unique_records = []

    print("Starting deep content deduplication audit...")

    with open(input_path, "r", encoding="utf-8") as infile:
        for line_num, line in enumerate(infile, 1):
            total_lines += 1
            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Standardize checking strings (strip whitespace and lower case to avoid format anomalies)
            eng_text = str(data.get("input", "")).strip()
            vi_text = str(data.get("output", "")).strip()
            instruction = str(data.get("instruction", "")).strip()

            if not eng_text or not vi_text:
                continue

            # Generate hashes for lookup
            input_hash = hashlib.md5(eng_text.encode('utf-8')).hexdigest()
            pair_hash = hashlib.md5(f"{eng_text}|||{vi_text}".encode('utf-8')).hexdigest()

            is_duplicate = False

            # Check exact English input duplicate
            if input_hash in seen_inputs:
                duplicate_inputs_count += 1
                is_duplicate = True
            else:
                seen_inputs.add(input_hash)

            # Check exact pair duplicate
            if pair_hash in seen_pairs:
                duplicate_pairs_count += 1
                is_duplicate = True
            else:
                seen_pairs.add(pair_hash)

            # If not duplicated in input, we keep it
            if not is_duplicate:
                processed_data = {
                    "instruction": instruction if instruction else "Dịch thuật sang Tiếng việt theo chủ đề thời sự",
                    "input": eng_text,
                    "output": vi_text
                }
                unique_records.append(processed_data)
                valid_lines += 1

            if line_num % 10000 == 0:
                print(f"Audited {line_num} lines for duplicate content...")

    # Write unique records to output file
    with open(output_path, "w", encoding="utf-8") as outfile:
        for record in unique_records:
            outfile.write(json.dumps(record, ensure_ascii=False) + "\n")

    # Summary Report
    print("\n=== DATASET DEDUPLICATION AUDIT REPORT ===")
    print(f"Total Lines Scanned:          {total_lines}")
    print(f"Duplicate 'input' (English):  {duplicate_inputs_count}")
    print(f"Duplicate 'input-output' pairs: {duplicate_pairs_count}")
    print(f"Total Unique Records Kept:    {valid_lines} ({(valid_lines/total_lines)*100:.2f}%)")
    print(f"Clean processed dataset saved to: {output_path}")
    print(f"File size before:             {os.path.getsize(input_path) / (1024*1024):.2f} MB")
    print(f"File size after:              {os.path.getsize(output_path) / (1024*1024):.2f} MB")

if __name__ == "__main__":
    deduplicate_and_prepare()
