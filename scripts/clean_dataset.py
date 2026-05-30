import json
import re
import sys
import time
from collections import Counter
import os

# Reconfigure stdout to use UTF-8 encoding to prevent crash on Windows terminal when printing Vietnamese characters
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def clean_text_content(content):
    """
    Safely cleans a record's content by removing specific boilerplate footers,
    signatures, code injections (JS), and designated noise strings.
    """
    if not content:
        return ""
        
    # 1. Specific noise style formatting strings requested by the user
    user_noise_strings = [
        "Đôi bạn 'nắm tay nhau đi khắp Việt Nam', vừa du lịch vừa kiếm tiền siêu giỏi",
        '"Không cho tôi hát, tôi không biết làm gì"',
        "'Không cho tôi hát, tôi không biết làm gì'",
        "Không cho tôi hát, tôi không biết làm gì"
    ]
    for ns in user_noise_strings:
        content = content.replace(ns, "")
        
    # 2. Boilerplate signatures and footers at the end of the text (Case-insensitive)
    footer_patterns = [
        r'(?i)trang thông tin điện tử docbao\.vn.*$',
        r'(?i)công ty cổ phần quang minh việt nam.*$',
        r'(?i)giấy phép thiết lập trang thông tin điện tử.*$',
        r'(?i)chính sách bảo mật rss.*$',
        r'(?i)đọc báo trực tuyến hiện tại chỉ sử dụng tên miền duy nhất là docbao\.vn.*$',
        r'(?i)báo điện tử thể thao & văn hóa.*$',
        r'(?i)all rights reserved ® thể thao & văn hóa.*$',
        r'(?i)\* mời quý độc giả theo dõi các chương trình đã phát sóng.*$'
    ]
    for pat in footer_patterns:
        content = re.sub(pat, "", content)
        
    # 3. Code injections and system warning banners channelling HTML/JS blocks
    js_patterns = [
        r'(?i)//<!\[cdata\[.*?//\]\]>',
        r'(?i),\s*margins:\s*\d+,\s*captions:\s*(?:true|false).*?window\[.*?\]\s*;?',
        r'(?i)24h-banner-in-image-close',
        r'(?i)trình duyệt của bạn không hỗ trợ\.'
    ]
    for pat in js_patterns:
        content = re.sub(pat, "", content)
        
    # 4. Standard URL source links (Rule 3.4)
    url_pat = re.compile(r'(?i)(?:nguồn|source|theo)?\s*[:\-]?\s*https?://[^\s"\'()\[\]{}<>]+')
    content = url_pat.sub("", content)
    
    # 5. Clean excess whitespace and trim boundaries
    content_cleaned = re.sub(r'\s+', ' ', content).strip()
    return content_cleaned

def clean_filtered_dataset(input_path, output_path):
    """
    Cleans the filtered dataset by:
    1. Removing records where both 'content' and 'topic' are empty/whitespace.
    2. Removing records of topics that appear in less than 0.50% of the entire dataset.
    Uses two-pass streaming to process large files with extremely low memory consumption.
    """
    if not os.path.exists(input_path):
        print(f"Error: File {input_path} does not exist.", file=sys.stderr)
        return
        
    start_time = time.time()
    
    # Regex to detect JSON object boundaries
    start_pat = re.compile(r'^\s*\{\s*$')
    end_pat = re.compile(r'^\s*\},?\s*$')
    
    # ----------------------------------------------------
    # PASS 1: Count topics and total records to calculate the 0.50% threshold
    # ----------------------------------------------------
    print("Pass 1: Analyzing topics and calculating frequency threshold...")
    
    buffer = []
    in_object = False
    total_records = 0
    topics_counter = Counter()
    
    with open(input_path, 'r', encoding='utf-8') as f:
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
                        total_records += 1
                        topic = obj.get("topic", "")
                        # Only count non-empty topics for the frequency check
                        if topic and topic.strip():
                            topics_counter[topic.strip()] += 1
                    except json.JSONDecodeError:
                        pass
                        
    print(f"  - Total records before cleaning: {total_records}")
    threshold = total_records * 0.005
    print(f"  - Minimum occurrences threshold for a topic (0.50%): {threshold:.2f} records")
    
    # Identify blacklisted topics (under 0.50% threshold)
    blacklisted_topics = set()
    kept_topics_info = []
    
    for topic, count in topics_counter.items():
        if count < threshold:
            blacklisted_topics.add(topic)
        else:
            kept_topics_info.append((topic, count))
            
    print(f"  - Unique topics to be REMOVED (frequency < 0.50%): {len(blacklisted_topics)}")
    
    # ----------------------------------------------------
    # PASS 2: Filter and write the clean JSON array
    # ----------------------------------------------------
    print("\nPass 2: Filtering and writing cleaned dataset...")
    
    buffer = []
    in_object = False
    written_count = 0
    removed_empty_content = 0
    removed_too_short = 0
    removed_under_threshold = 0
    
    with open(input_path, 'r', encoding='utf-8') as fin, open(output_path, 'w', encoding='utf-8') as fout:
        # Write opening bracket for JSON array
        fout.write("[\n")
        
        first = True
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
                        content = obj.get("content", "")
                        topic = obj.get("topic", "")
                        
                        # Rule 3.5: Comprehensive content cleaning (boilterplate, footers, JS, URLs)
                        content_clean = clean_text_content(content)
                        
                        is_content_empty = not content_clean or not content_clean.strip()
                        is_topic_empty = not topic or not topic.strip()
                        
                        # Rule 3.2: Remove records with empty content (after cleaning)
                        if is_content_empty:
                            removed_empty_content += 1
                            continue
                            
                        # Rule 3.6: Remove records with content length under 50 characters
                        if len(content_clean) < 50:
                            removed_too_short += 1
                            continue
                            
                        # Rule 3.1: Remove records where topic is under 0.50% frequency
                        if not is_topic_empty and topic.strip() in blacklisted_topics:
                            removed_under_threshold += 1
                            continue
                            
                        # Keep the record and write
                        if not first:
                            fout.write(",\n")
                        else:
                            first = False
                            
                        fout.write("\t{\n")
                        content_escaped = json.dumps(content_clean, ensure_ascii=False)
                        topic_escaped = json.dumps(topic, ensure_ascii=False)
                        
                        fout.write(f'\t\t"content" : {content_escaped},\n')
                        fout.write(f'\t\t"topic" : {topic_escaped}\n')
                        fout.write("\t}")
                        
                        written_count += 1
                        if written_count % 20000 == 0:
                            print(f"  - Written {written_count} cleaned records...", flush=True)
                            
                    except json.JSONDecodeError:
                        pass
                        
        # Write closing bracket for JSON array
        fout.write("\n]\n")
        
    elapsed = time.time() - start_time
    print("\n" + "="*60)
    print("DATASET CLEANING SUMMARY")
    print("="*60)
    print(f"  - Total records before         : {total_records:,}")
    print(f"  - Total records after          : {written_count:,}")
    print(f"  - Removed (empty content)      : {removed_empty_content:,} ({ (removed_empty_content/total_records)*100 if total_records else 0:.2f}%)")
    print(f"  - Removed (content < 50 chars) : {removed_too_short:,} ({ (removed_too_short/total_records)*100 if total_records else 0:.2f}%)")
    print(f"  - Removed (under 0.50% topic) : {removed_under_threshold:,} ({ (removed_under_threshold/total_records)*100 if total_records else 0:.2f}%)")
    print(f"  - Total removed records        : {total_records - written_count:,} ({ ((total_records - written_count)/total_records)*100 if total_records else 0:.2f}%)")
    print(f"  - Time taken                  : {elapsed:.2f} seconds")
    print(f"  - Output file saved to        : {output_path}")
    print("="*60)

if __name__ == "__main__":
    input_file = "news_dataset_filtered.json"
    output_file = "news_dataset_clean.json"
    
    clean_filtered_dataset(input_file, output_file)
