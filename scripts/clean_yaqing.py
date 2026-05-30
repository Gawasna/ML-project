import json
import os

file_path = "C:/Users/hungl/Downloads/Temp/labs-ml/labs-ml/translated_the_gioi.jsonl"
cleaned_lines = []
count_fixed = 0

if os.path.exists(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if line.strip():
                try:
                    data = json.loads(line)
                    output_text = data.get("output", "")
                    if "một trong học bốn tập đoàn" in output_text:
                        output_text = output_text.replace("một trong học bốn tập đoàn", "một trong bốn tập đoàn")
                        data["output"] = output_text
                        count_fixed += 1
                        print(f"Fixed Xiao Yaqing typo on line {idx+1}")
                    cleaned_lines.append(data)
                except Exception as e:
                    print(f"Error parsing line {idx+1}: {e}")

    with open(file_path, "w", encoding="utf-8") as f:
        for item in cleaned_lines:
            ordered_item = {
                "topic": item.get("topic", ""),
                "instruction": item.get("instruction", ""),
                "input": item.get("input", ""),
                "output": item.get("output", "")
            }
            f.write(json.dumps(ordered_item, ensure_ascii=False) + "\n")
    print(f"Successfully cleaned Xiao Yaqing typo in {count_fixed} lines.")
else:
    print("File not found")
