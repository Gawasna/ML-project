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
                    
                    fixed = False
                    # Fix Cyprus record typo
                    if "Việc EU cấp tập" in output_text and "giếng nữa vào cuối năm" in output_text:
                        output_text = output_text.replace("giếng nữa vào cuối năm", "giếng nữa và vào cuối năm")
                        fixed = True
                        
                    # Fix Gas Saving record typo
                    if "Tiết kiệm cho một mùa đông" in output_text and "mùa đông an sau" in output_text:
                        output_text = output_text.replace("mùa đông an sau", "mùa đông an toàn")
                        fixed = True
                        
                    # Fix Summary record typo
                    if "Trong một lá thư" in output_text and "mối threat cụ thể" in output_text:
                        output_text = output_text.replace("mối threat cụ thể", "mối đe dọa cụ thể")
                        fixed = True
                        
                    if fixed:
                        data["output"] = output_text
                        count_fixed += 1
                        print(f"Fixed typo on line {idx+1}")
                        
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
    print(f"Successfully cleaned typos in {count_fixed} lines.")
else:
    print("File not found")
