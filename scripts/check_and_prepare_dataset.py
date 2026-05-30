import os
import json

def check_and_prepare_dataset():
    input_path = r"C:\Users\hungl\Documents\trae_projects\ML-project\temp\labs-ml\translated_thoi_su.jsonl"
    output_dir = r"C:\Users\hungl\Documents\trae_projects\ML-project\prepared"
    output_path = os.path.join(output_dir, "prepared_translated_thoi_su.jsonl")

    # Create target directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")

    total_lines = 0
    valid_lines = 0
    corrupted_lines = 0
    missing_fields_lines = 0
    empty_values_lines = 0

    print("Starting dataset stability audit...")

    with open(input_path, "r", encoding="utf-8") as infile, \
         open(output_path, "w", encoding="utf-8") as outfile:
        
        for line_num, line in enumerate(infile, 1):
            total_lines += 1
            line = line.strip()
            if not line:
                continue

            # 1. Check if line is a valid JSON
            try:
                data = json.loads(line)
            except json.JSONDecodeError as e:
                corrupted_lines += 1
                print(f"Line {line_num} is corrupted: {e}")
                continue

            # 2. Check if required fields exist
            required_fields = ["instruction", "input", "output"]
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                missing_fields_lines += 1
                print(f"Line {line_num} is missing fields: {missing_fields}")
                continue

            # 3. Check for empty values in required fields
            empty_val = False
            for field in required_fields:
                if not str(data[field]).strip():
                    empty_val = True
                    break
            if empty_val:
                empty_values_lines += 1
                print(f"Line {line_num} has empty values in required fields")
                continue

            # 4. Process copy: remove the 'topic' field if it exists
            processed_data = {
                "instruction": data["instruction"],
                "input": data["input"],
                "output": data["output"]
            }

            # Write to output file
            outfile.write(json.dumps(processed_data, ensure_ascii=False) + "\n")
            valid_lines += 1

            if line_num % 10000 == 0:
                print(f"Audited {line_num} lines...")

    # Summary Report
    print("\n=== DATASET AUDIT AND PREPARATION REPORT ===")
    print(f"Total Lines Processed: {total_lines}")
    print(f"Valid Lines Saved:     {valid_lines} ({(valid_lines/total_lines)*100:.2f}%)")
    print(f"Corrupted JSON Lines:  {corrupted_lines}")
    print(f"Missing Fields Lines:  {missing_fields_lines}")
    print(f"Empty Values Lines:    {empty_values_lines}")
    print(f"Processed dataset saved to: {output_path}")

    is_stable = (corrupted_lines == 0 and missing_fields_lines == 0 and empty_values_lines == 0)
    print(f"Dataset Stability:     {'PASS' if is_stable else 'WARNING'}")

if __name__ == "__main__":
    check_and_prepare_dataset()
