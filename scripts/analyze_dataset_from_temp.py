import json
import re
import sys
import time
from collections import Counter
import os

# Reconfigure stdout to use UTF-8 encoding to prevent crash on Windows terminal when printing Vietnamese characters
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')


def analyze_filtered_dataset(file_path):
    """
    Analyzes the filtered news dataset to list unique topics and calculate ratios
    of empty content, empty topic, and both empty records.
    Processes the file via streaming for high memory efficiency.
    """
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} does not exist.", file=sys.stderr)
        return
        
    start_time = time.time()
    
    # Regex to detect object boundaries of single JSON objects in the array
    start_pat = re.compile(r'^\s*\{\s*$')
    end_pat = re.compile(r'^\s*\},?\s*$')
    
    buffer = []
    in_object = False
    
    total_count = 0
    empty_content_count = 0
    empty_topic_count = 0
    both_empty_count = 0
    
    topics_counter = Counter()
    
    print(f"Analyzing dataset: {file_path}")
    print("Please wait...")
    
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
                    
                    # Remove trailing comma to make it a valid single JSON object
                    obj_str_stripped = obj_str.rstrip()
                    if obj_str_stripped.endswith(","):
                        obj_str = obj_str_stripped[:-1]
                        
                    try:
                        # Load single JSON object into memory
                        obj = json.loads(obj_str)
                        total_count += 1
                        
                        content = obj.get("content", "")
                        topic = obj.get("topic", "")
                        
                        # Normalize content and topic to check if empty/whitespace
                        is_content_empty = not content or not content.strip()
                        is_topic_empty = not topic or not topic.strip()
                        
                        if is_content_empty:
                            empty_content_count += 1
                        if is_topic_empty:
                            empty_topic_count += 1
                        if is_content_empty and is_topic_empty:
                            both_empty_count += 1
                            
                        # Record topic representation
                        if not is_topic_empty:
                            topics_counter[topic.strip()] += 1
                        else:
                            topics_counter["[EMPTY]"] += 1
                            
                    except json.JSONDecodeError as err:
                        print(f"Warning: Failed to parse object {total_count} - Error: {err}", file=sys.stderr)
                        
    elapsed = time.time() - start_time
    
    # Define report path
    docs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")
    os.makedirs(docs_dir, exist_ok=True)
    report_path = os.path.join(docs_dir, "analysis_report.md")
    
    # Sort topics by frequency in descending order
    sorted_topics = sorted(topics_counter.items(), key=lambda x: x[1], reverse=True)
    
    # 1. Print overview to console (limit topics to top 20 to prevent console flood)
    print("\n" + "="*60)
    print("1. UNIQUE TOPICS IN DATASET (Showing Top 20)")
    print("="*60)
    for topic, count in sorted_topics[:20]:
        percentage = (count / total_count) * 100 if total_count > 0 else 0
        print(f"  - {topic:<30} | {count:>7} records | {percentage:>6.2f}%")
    if len(sorted_topics) > 20:
        print(f"  ... and {len(sorted_topics) - 20} more topics. (See full report in docs/analysis_report.md)")
        
    # 2. Report empty stats to console
    print("\n" + "="*60)
    print("2. EMPTY FIELDS REPORT")
    print("="*60)
    print(f"Total processed records: {total_count}")
    
    def print_stat(label, count):
        percentage = (count / total_count) * 100 if total_count > 0 else 0
        print(f"  - {label:<35}: {count:>7} records ({percentage:>6.2f}%)")
        
    print_stat("Empty Content (empty/whitespace)", empty_content_count)
    print_stat("Empty Topic (empty/whitespace)", empty_topic_count)
    print_stat("Both Content and Topic empty", both_empty_count)
    
    print("\n" + "="*60)
    print(f"Analysis completed in {elapsed:.2f} seconds.")
    print("="*60)

    # 3. Export full comprehensive Markdown report to docs/analysis_report.md
    with open(report_path, "w", encoding="utf-8") as rf:
        rf.write("# Dataset Analysis Report\n\n")
        rf.write(f"- **Target File:** `{os.path.basename(file_path)}`\n")
        rf.write(f"- **Total Records:** {total_count:,}\n")
        rf.write(f"- **Execution Time:** {elapsed:.2f} seconds\n\n")
        
        rf.write("## 1. Empty Fields Summary\n\n")
        rf.write("| Metric | Record Count | Percentage |\n")
        rf.write("| :--- | :---: | :---: |\n")
        
        def write_md_row(label, count):
            percentage = (count / total_count) * 100 if total_count > 0 else 0
            rf.write(f"| {label} | {count:,} | {percentage:.2f}% |\n")
            
        write_md_row("Empty Content", empty_content_count)
        write_md_row("Empty Topic", empty_topic_count)
        write_md_row("Both Content and Topic Empty", both_empty_count)
        rf.write("\n")
        
        rf.write("## 2. Topic Distribution\n\n")
        rf.write("| Topic | Record Count | Percentage |\n")
        rf.write("| :--- | :---: | :---: |\n")
        for topic, count in sorted_topics:
            percentage = (count / total_count) * 100 if total_count > 0 else 0
            rf.write(f"| {topic} | {count:,} | {percentage:.2f}% |\n")
            
    print(f"Full comprehensive report written to: {report_path}")


if __name__ == "__main__":
    # Support custom target file from CLI argument, default to news_dataset_clean.json
    target_file = sys.argv[1] if len(sys.argv) > 1 else "news_dataset_clean.json"
    analyze_filtered_dataset(target_file)

