import json
import os

notebook_path = r"C:\Users\hungl\Documents\trae_projects\ML-project\train\LoRA_Training.ipynb"

if not os.path.exists(notebook_path):
    print(f"Error: Notebook not found at {notebook_path}")
    exit(1)

with open(notebook_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

modified = False

for cell in nb.get("cells", []):
    if cell.get("cell_type") == "code":
        source = cell.get("source", [])
        source_str = "".join(source)
        
        # Look for the dataset loading line in Step 4
        if 'raw_dataset = load_dataset("json", data_files="/content/prepared/train_*.jsonl", split="train")' in source_str:
            print("Found dataset loading cell. Updating glob pattern dynamically...")
            new_source = []
            for line in source:
                if 'raw_dataset = load_dataset("json", data_files="/content/prepared/train_*.jsonl", split="train")' in line:
                    new_source.append("    \"import glob\\n\",\n")
                    new_source.append("    \"print(\\\"⏳ Đang quét danh sách tệp tin huấn luyện...\\\")\\n\",\n")
                    new_source.append("    \"all_files = glob.glob(\\\"/content/prepared/*.jsonl\\\")\\n\",\n")
                    new_source.append("    \"train_files = [f for f in all_files if \\\"_test_\\\" not in f and \\\"_valid_\\\" not in f]\\n\",\n")
                    new_source.append("    \"print(f\\\"✅ Tìm thấy {len(train_files)} tệp tin huấn luyện\\\")\\n\",\n")
                    new_source.append("    \"raw_dataset = load_dataset(\\\"json\\\", data_files=train_files, split=\\\"train\\\")\\n\"\n")
                else:
                    new_source.append(line)
            cell["source"] = new_source
            modified = True
            break

if modified:
    with open(notebook_path, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)
    print("Notebook glob patterns successfully updated dynamically!")
else:
    print("No changes made to the notebook.")
