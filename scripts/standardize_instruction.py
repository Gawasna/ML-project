import os
import json
import re

def standardize_instructions_regex():
    prepared_dir = r"C:\Users\hungl\Documents\trae_projects\ML-project\data\train\prepared"
    
    if not os.path.exists(prepared_dir):
        print(f"Error: Prepared directory not found at {prepared_dir}")
        return

    print("Starting smart regex instruction standardization across all prepared datasets...")
    
    # Compile case-insensitive regex for 'thế giới'
    pattern = re.compile(r"thế giới", re.IGNORECASE)
    
    # Scan all .jsonl files in the prepared directory
    jsonl_files = [os.path.join(prepared_dir, f) for f in os.listdir(prepared_dir) if f.endswith(".jsonl")]
    
    total_files_updated = 0

    for file_path in jsonl_files:
        print(f"Auditing file: {os.path.basename(file_path)}")
        modified_records = []
        replacement_count = 0
        total_lines = 0
        file_needs_rewrite = False

        with open(file_path, "r", encoding="utf-8") as infile:
            for line in infile:
                line = line.strip()
                if not line:
                    continue
                
                total_lines += 1
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    modified_records.append(line)
                    continue

                instruction = data.get("instruction", "")
                
                # Apply regex replacement if pattern is found
                if pattern.search(instruction):
                    new_instruction = pattern.sub("Thời sự", instruction)
                    data["instruction"] = new_instruction
                    replacement_count += 1
                    file_needs_rewrite = True
                
                modified_records.append(data)

        # Overwrite file if changes were made
        if file_needs_rewrite:
            with open(file_path, "w", encoding="utf-8") as outfile:
                for record in modified_records:
                    outfile.write(json.dumps(record, ensure_ascii=False) + "\n")
            print(f"--> SUCCESS: Standardized {replacement_count} lines in {os.path.basename(file_path)}")
            total_files_updated += 1
        else:
            print(f"--> No 'The gioi' instruction pattern found in {os.path.basename(file_path)}.")

    print("\n=== REGEX STANDARDIZATION OVERVIEW ===")
    print(f"Total Prepared Files Audited: {len(jsonl_files)}")
    print(f"Total Files Upgraded:         {total_files_updated}")

if __name__ == "__main__":
    standardize_instructions_regex()
