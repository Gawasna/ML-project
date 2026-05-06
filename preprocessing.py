import os
import re
import argparse
from pathlib import Path

STT_AI_REG_PATTERN = "^\[Speaker \d+\]\s?"

def clean_text(text: str) -> str:
    """
    Loại bỏ timestamp và tên speaker từ AI generated transcript.
    """
    cleaned_lines = []
    
    # Mẫu regex cho timestamp: [00:00:00], [00:00], 00:00:00, (00:00)...
    timestamp_pattern = re.compile(r'^\[?\d{1,2}:\d{2}(:\d{2})?(\.\d{1,3})?\]?\s*')
    
    # Mẫu regex cho speaker: [Speaker 1]:, Speaker:, [Người nói 1]: ...
    # speaker_pattern = re.compile(r'^\[?(Speaker|Người nói)\s*[^\]:]*\]?:\s*', re.IGNORECASE)
    
    speaker_pattern_alt = re.compile(STT_AI_REG_PATTERN, re.IGNORECASE)

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
            
        # Loại bỏ timestamp ở đầu dòng
        line = timestamp_pattern.sub('', line).strip()
        
        # Loại bỏ speaker name ở đầu dòng
        line = speaker_pattern.sub('', line).strip()
        line = speaker_pattern_alt.sub('', line).strip()
        
        # Chạy lại xóa timestamp đề phòng trường hợp thứ tự [Speaker] [Timestamp] bị đảo ngược
        line = timestamp_pattern.sub('', line).strip()
        
        if line:
            cleaned_lines.append(line)
            
    # Gộp các dòng đã clean lại thành đoạn văn bản hoàn chỉnh
    return ' '.join(cleaned_lines)

def process_file(input_file: str):
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
    cleaned_content = clean_text(content)
    
    with open(input_file, 'w', encoding='utf-8') as f:
        f.write(cleaned_content)
    print(f"Đã xử lý và ghi đè: {input_file}")

def process_directory(input_dir: str):
    for filename in os.listdir(input_dir):
        if filename.endswith(".txt"):
            input_path = os.path.join(input_dir, filename)
            process_file(input_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script tiền xử lý file transcript AI, xóa Speaker và Timestamp (ghi đè trực tiếp).")
    parser.add_argument("-i", "--input", type=str, help="Đường dẫn đến file hoặc thư mục chứa file txt đầu vào", required=True)
    
    args = parser.parse_args()
    
    if os.path.isdir(args.input):
        process_directory(args.input)
    elif os.path.isfile(args.input):
        process_file(args.input)
    else:
        print("Đường dẫn đầu vào không hợp lệ!")
