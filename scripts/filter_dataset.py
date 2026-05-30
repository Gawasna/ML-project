import json
import re
import sys
import time
import os

def filter_news_dataset(input_path, output_path):
    """
    Highly memory-efficient JSON array streaming filter.
    Reads a large JSON array of objects line-by-line, parses each object,
    filters the keys to retain only 'content' and 'topic', and writes to output.
    """
    keys_to_keep = {"content", "topic"}
    
    # Regex to detect line boundaries of individual JSON objects in the array
    # Matches starting line containing only '{'
    start_pat = re.compile(r'^\s*\{\s*$')
    # Matches ending line containing '}' or '},'
    end_pat = re.compile(r'^\s*\},?\s*$')
    
    buffer = []
    in_object = False
    count = 0
    start_time = time.time()
    
    # Estimate total size for progress reporting
    total_bytes = os.path.getsize(input_path)
    bytes_processed = 0
    
    print(f"Starting filtration: {input_path} -> {output_path}")
    print(f"Target keys to keep: {keys_to_keep}")
    
    with open(input_path, 'r', encoding='utf-8') as fin, open(output_path, 'w', encoding='utf-8') as fout:
        # Write opening bracket for the new JSON array
        fout.write("[\n")
        
        first = True
        for line in fin:
            bytes_processed += len(line.encode('utf-8'))
            
            # Detect start of a new JSON object
            if start_pat.match(line):
                in_object = True
                buffer = [line]
                continue
            
            # Accumulate lines within the current JSON object
            if in_object:
                buffer.append(line)
                
                # Detect end of the current JSON object
                if end_pat.match(line):
                    in_object = False
                    obj_str = "".join(buffer)
                    
                    # Strip trailing comma if present to allow valid json parsing
                    obj_str_stripped = obj_str.rstrip()
                    if obj_str_stripped.endswith(","):
                        obj_str = obj_str_stripped[:-1]
                    
                    try:
                        # Load single JSON object into memory
                        obj = json.loads(obj_str)
                        
                        # Retain only content and topic
                        filtered_obj = {k: v for k, v in obj.items() if k in keys_to_keep}
                        
                        # Prepend comma if not the first object
                        if not first:
                            fout.write(",\n")
                        else:
                            first = False
                        
                        # Serialize directly with indent matching the original style
                        fout.write("\t{\n")
                        content_val = filtered_obj.get("content", "")
                        topic_val = filtered_obj.get("topic", "")
                        
                        # Safely serialize using json.dumps to escape string quotes properly
                        content_escaped = json.dumps(content_val, ensure_ascii=False)
                        topic_escaped = json.dumps(topic_val, ensure_ascii=False)
                        
                        fout.write(f'\t\t"content" : {content_escaped},\n')
                        fout.write(f'\t\t"topic" : {topic_escaped}\n')
                        fout.write("\t}")
                        
                        count += 1
                        if count % 20000 == 0:
                            elapsed = time.time() - start_time
                            percent = (bytes_processed / total_bytes) * 100
                            speed = count / elapsed if elapsed > 0 else 0
                            print(f"Processed {count} items | Progress: {percent:.1f}% | Speed: {speed:.1f} items/sec", flush=True)
                            
                    except json.JSONDecodeError as err:
                        print(f"Warning: Failed to parse object {count} - Error: {err}", file=sys.stderr)
        
        # Write closing bracket for the JSON array
        fout.write("\n]\n")
        
    total_elapsed = time.time() - start_time
    print(f"Success! Filtered {count} items in {total_elapsed:.2f} seconds.")
    print(f"Output saved to {output_path}")

if __name__ == "__main__":
    input_file = "news_dataset.json"
    output_file = "news_dataset_filtered.json"
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.", file=sys.stderr)
        sys.exit(1)
        
    filter_news_dataset(input_file, output_file)
