import json
import re
from collections import Counter
import sys

# Reconfigure stdout to UTF-8 to prevent terminal crash
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')


def find_frequent_sentences(file_path, min_len=15, min_count=20):
    start_pat = re.compile(r'^\s*\{\s*$')
    end_pat = re.compile(r'^\s*\},?\s*$')
    
    buffer = []
    in_object = False
    
    # Counter for candidate phrases
    phrase_counter = Counter()
    
    print(f"Scanning {file_path} for duplicate text boilerplate...")
    
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
                    if obj_str.rstrip().endswith(","):
                        obj_str = obj_str.rstrip()[:-1]
                    try:
                        obj = json.loads(obj_str)
                        content = obj.get("content", "")
                        if content:
                            # Split by common sentence delimiters or quotes
                            # We want to catch block quotes, title lines, or isolated sentences
                            # Split by '.' or '\n' or quotes
                            parts = re.split(r'(?<=\. )|(?<=\? )|(?<=\! )|\n|(?<=\")|(?=\")', content)
                            for part in parts:
                                part_stripped = part.strip().strip('"\'')
                                if len(part_stripped) >= min_len:
                                    phrase_counter[part_stripped] += 1
                    except json.JSONDecodeError:
                        pass

    # Print top frequent boilerplate strings
    print("\nTOP FREQUENT BOILERPLATE PHRASES:")
    print("="*80)
    sorted_phrases = sorted(phrase_counter.items(), key=lambda x: x[1], reverse=True)
    count = 0
    for phrase, freq in sorted_phrases:
        if freq >= min_count:
            print(f"Frequency: {freq:>5} | Text: {phrase[:100]}")
            count += 1
            if count >= 30:
                break
    print("="*80)
    print(f"Total frequent boilerplate phrases detected: {count}")

if __name__ == "__main__":
    find_frequent_sentences("news_dataset_clean.json")
