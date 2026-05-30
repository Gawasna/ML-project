import json
import re
import sys
import os

# Reconfigure stdout to use UTF-8 encoding to prevent crash on Windows terminal
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')


def prepare_1000_records(input_path, output_path, target_topic="Thế giới", limit=1000):
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found.", file=sys.stderr)
        sys.exit(1)
        
    start_pat = re.compile(r'^\s*\{\s*$')
    end_pat = re.compile(r'^\s*\},?\s*$')
    
    buffer = []
    in_object = False
    count = 0
    
    print(f"Extracting {limit} records for topic '{target_topic}' to prepare test dataset...")
    
    with open(input_path, 'r', encoding='utf-8') as fin, open(output_path, 'w', encoding='utf-8') as fout:
        for line in fin:
            if start_pat.match(line):
                in_object = True
                buffer = [line]
                continue
                
            if in_object:
                buffer.append(line)
                if end_pat.match(line):
                    in_object = False
                    obj_str = "".join(buffer)
                    
                    obj_str_stripped = obj_str.rstrip()
                    if obj_str_stripped.endswith(","):
                        obj_str = obj_str_stripped[:-1]
                        
                    try:
                        obj = json.loads(obj_str)
                        topic = obj.get("topic", "")
                        
                        if topic and topic.strip() == target_topic:
                            obj_jsonl = {
                                "topic": target_topic,
                                "instruction": f"Dịch thuật sang Tiếng việt theo chủ đề {target_topic}",
                                "input": "",
                                "output": obj.get("content", "")
                            }
                            jsonl_str = json.dumps(obj_jsonl, ensure_ascii=False)
                            fout.write(jsonl_str + "\n")
                            count += 1
                            
                            if count >= limit:
                                break
                    except json.JSONDecodeError:
                        pass
                        
    print(f"Successfully prepared test data: {count} records written to {output_path}")

if __name__ == "__main__":
    prepare_1000_records("news_dataset_clean.json", "extracted_the_gioi.jsonl")
