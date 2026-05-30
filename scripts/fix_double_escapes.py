import json
import os

file_path = "translated_the_gioi.jsonl"
if os.path.exists(file_path):
    cleaned_lines = []
    count_fixed = 0
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    data = json.loads(line)
                    output_text = data.get("output", "")
                    input_text = data.get("input", "")
                    
                    # Check if there is double escaped backslashes or literal \" in decoded string
                    if '\\"' in line or '\\\\' in line:
                        output_text = output_text.replace('\\"', '"').replace('\\\\', '\\')
                        input_text = input_text.replace('\\"', '"').replace('\\\\', '\\')
                        data["output"] = output_text
                        data["input"] = input_text
                        count_fixed += 1
                        
                    cleaned_lines.append(data)
                except Exception as e:
                    print(f"Error parsing line: {e}")
                    
    with open(file_path, "w", encoding="utf-8") as f:
        for item in cleaned_lines:
            ordered_item = {
                "topic": item.get("topic", ""),
                "instruction": item.get("instruction", ""),
                "input": item.get("input", ""),
                "output": item.get("output", "")
            }
            f.write(json.dumps(ordered_item, ensure_ascii=False) + "\n")
    print(f"Successfully cleaned double escapes in {count_fixed} lines of translated_the_gioi.jsonl")
else:
    print("File not found")
