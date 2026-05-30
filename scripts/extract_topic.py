import json
import re
import sys
import os
import time

# Reconfigure stdout to use UTF-8 encoding to prevent crash on Windows terminal when printing Vietnamese characters
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def get_unique_topics(file_path):
    """
    Scans the clean dataset using streaming to find all unique topics and record counts.
    """
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.", file=sys.stderr)
        sys.exit(1)
        
    # Regex to detect JSON object boundaries
    start_pat = re.compile(r'^\s*\{\s*$')
    end_pat = re.compile(r'^\s*\},?\s*$')
    
    buffer = []
    in_object = False
    topics_counter = {}
    
    print("Scanning dataset to extract unique topics. Please wait...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
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
                        # Fallback for empty topic
                        topic_normalized = topic.strip() if topic else "[EMPTY]"
                        topics_counter[topic_normalized] = topics_counter.get(topic_normalized, 0) + 1
                    except json.JSONDecodeError:
                        pass
                        
    return topics_counter

def sanitize_filename(name):
    """
    Sanitizes string to generate a safe filename for Windows.
    Removes special marks, replaces spaces/hyphens with underscores, and converts to lowercase.
    """
    # Replace common Vietnamese accented characters to plain English for file names
    vietnamese_map = {
        'á': 'a', 'à': 'a', 'ả': 'a', 'ã': 'a', 'ạ': 'a', 'ă': 'a', 'ắ': 'a', 'ằ': 'a', 'ẳ': 'a', 'ẵ': 'a', 'ặ': 'a', 'â': 'a', 'ấ': 'a', 'ầ': 'a', 'ẩ': 'a', 'ẫ': 'a', 'ậ': 'a',
        'é': 'e', 'è': 'e', 'ẻ': 'e', 'ẽ': 'e', 'ẹ': 'e', 'ê': 'e', 'ế': 'e', 'ề': 'e', 'ể': 'e', 'ễ': 'e', 'ệ': 'e',
        'í': 'i', 'ì': 'i', 'ỉ': 'i', 'ĩ': 'i', 'ị': 'i',
        'ó': 'o', 'ò': 'o', 'ỏ': 'o', 'õ': 'o', 'ọ': 'o', 'ô': 'o', 'ố': 'o', 'ồ': 'o', 'ổ': 'o', 'ỗ': 'o', 'ộ': 'o', 'ơ': 'o', 'ớ': 'o', 'ờ': 'o', 'ở': 'o', 'ỡ': 'o', 'ợ': 'o',
        'ú': 'u', 'ù': 'u', 'ủ': 'u', 'ũ': 'u', 'ụ': 'u', 'ư': 'u', 'ứ': 'u', 'ừ': 'u', 'ử': 'u', 'ữ': 'u', 'ự': 'u',
        'ý': 'y', 'ỳ': 'y', 'ỷ': 'y', 'ỹ': 'y', 'ỵ': 'y',
        'đ': 'd'
    }
    
    name_lower = name.lower()
    for char, replacement in vietnamese_map.items():
        name_lower = name_lower.replace(char, replacement)
        
    name_clean = re.sub(r'[^\w\s-]', '', name_lower).strip()
    name_clean = re.sub(r'[-\s]+', '_', name_clean)
    return name_clean

def extract_records(input_path, output_path, target_topics):
    """
    Filters and extracts records belonging to target_topics from the input file
    and writes them to the output file in JSONL format in a memory-efficient streaming manner.
    """
    start_pat = re.compile(r'^\s*\{\s*$')
    end_pat = re.compile(r'^\s*\},?\s*$')
    
    buffer = []
    in_object = False
    count = 0
    start_time = time.time()
    
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
                        topic_normalized = topic.strip() if topic else "[EMPTY]"
                        
                        # Match against targeted topics list
                        if topic_normalized in target_topics:
                            topic_display = topic.strip() if topic and topic.strip() else "Tin tức"
                            # Standard translation instruction format with 'topic' field at the beginning
                            obj_jsonl = {
                                "topic": topic_display,
                                "instruction": f"Dịch thuật sang Tiếng việt theo chủ đề {topic_display}",
                                "input": "",
                                "output": obj.get("content", "")
                            }
                            # Dump single object as a single-line string into the JSONL file
                            jsonl_str = json.dumps(obj_jsonl, ensure_ascii=False)
                            fout.write(jsonl_str + "\n")
                            count += 1
                            
                    except json.JSONDecodeError:
                        pass
                        
    elapsed = time.time() - start_time
    print(f"\nSuccessfully extracted {count:,} records in {elapsed:.2f} seconds!")
    print(f"Result saved to: {output_path}")

def main():
    input_file = "news_dataset_clean.json"
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} does not exist. Please clean the dataset first.", file=sys.stderr)
        sys.exit(1)
        
    # Step 1: Scan and retrieve list of unique topics
    topics_counter = get_unique_topics(input_file)
    sorted_topics = sorted(topics_counter.items(), key=lambda x: x[1], reverse=True)
    
    print("\n" + "="*60)
    print("AVAILABLE TOPICS MENU")
    print("="*60)
    for idx, (topic, count) in enumerate(sorted_topics, 1):
        print(f"  {idx:>2}. {topic:<35} | {count:>7,} records")
    print("="*60)
    
    # Step 2: Interactive menu prompt
    try:
        selection_input = input("\nEnter topic number(s) to extract (e.g. 2 or 2,3,4): ").strip()
        if not selection_input:
            print("Error: No selection made. Exiting.")
            sys.exit(1)
            
        # Parse inputs, discarding non-integers
        selected_indices = [int(x.strip()) for x in selection_input.split(",") if x.strip().isdigit()]
        
        valid_indices = []
        for idx in selected_indices:
            if 1 <= idx <= len(sorted_topics):
                valid_indices.append(idx)
            else:
                print(f"Warning: Index {idx} is out of range. Skipping.")
                
        if not valid_indices:
            print("Error: No valid topic index selected. Exiting.")
            sys.exit(1)
            
        target_topics = [sorted_topics[idx - 1][0] for idx in valid_indices]
        print(f"\nYou selected: {', '.join(target_topics)}")
        
        # Step 3: Define output path
        if len(target_topics) == 1:
            topic_name_clean = sanitize_filename(target_topics[0])
            output_file = f"extracted_{topic_name_clean}.jsonl"
        else:
            output_file = "extracted_multiple_topics.jsonl"
            
        print(f"Target output file: {output_file}")
        
        # Step 4: Extract records
        extract_records(input_file, output_file, set(target_topics))
        
    except KeyboardInterrupt:
        print("\nProcess interrupted by user. Exiting.")
        sys.exit(0)

if __name__ == "__main__":
    main()
