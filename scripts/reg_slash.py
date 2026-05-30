import re
import json
import argparse
import os

def clean_and_validate_jsonl(file_path):
    if not os.path.exists(file_path):
        print(f"❌ Lỗi: File '{file_path}' không tồn tại.")
        return

    # Biểu thức Regex của bạn để tìm \" bên trong chuỗi
    # Cần dùng r'(?<!^)\\"(?!$)' để Python hiểu đúng chuỗi raw regex
    pattern = re.compile(r'(?<!^)\\"(?!$)')
    
    cleaned_lines = []
    is_broken = False
    
    print(f"🔄 Đang xử lý file: {file_path}...")

    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue  # Bỏ qua dòng trống
            
            try:
                # Bước 1: Thử parse dòng hiện tại thành object JSON trước
                data = json.loads(line)
                
                # Bước 2: Dò các object 'input' và 'output' để xử lý
                # Thay thế bằng rỗng '' theo đúng yêu cầu của bạn (hoặc '"' nếu bạn muốn giữ lại dấu ngoặc đơn thuần)
                if "input" in data and isinstance(data["input"], str):
                    data["input"] = pattern.sub('', data["input"])
                
                if "output" in data and isinstance(data["output"], str):
                    data["output"] = pattern.sub('', data["output"])
                
                # Chuyển ngược lại thành chuỗi JSON một dòng để ghi vào file JSONL
                cleaned_lines.append(json.dumps(data, ensure_ascii=False))
                
            except json.JSONDecodeError as e:
                # Nếu ngay từ đầu dòng này đã lỗi cấu trúc JSON
                print(f"⚠️ Dòng {line_num} lỗi cấu trúc JSON gốc: {e}")
                is_broken = True
                cleaned_lines.append(line) # Giữ nguyên dòng lỗi để xử lý sau

    # Bước 3: Ghi đè lại file cũ (hoặc bạn có thể đổi tên thành file mới nếu muốn an toàn)
    with open(file_path, 'w', encoding='utf-8') as f:
        for line in cleaned_lines:
            f.write(line + '\n')
            
    print("ℹ️ Đang kiểm tra lại cấu trúc JSONL sau khi sạch...")
    
    # Bước 4: Kiểm tra lại toàn bộ file sau khi sửa
    final_check_passed = True
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                json.loads(line)
            except json.JSONDecodeError:
                print(f"❌ Phát hiện lỗi Broken JSON tại dòng {line_num} sau khi replace!")
                final_check_passed = False
                
    if final_check_passed and not is_broken:
        print("✅ Thành công! Dataset đã được làm sạch và cấu trúc JSONL hoàn toàn hợp lệ.")
    else:
        print("🛑 Cảnh báo: File đã được xử lý nhưng vẫn còn lỗi cấu trúc. Hãy kiểm tra lại các dòng báo lỗi ở trên.")

if __name__ == "__main__":
    # Thiết lập bộ bắt tham số chuẩn của argparse
    parser = argparse.ArgumentParser(description="Script xử lý ký tự escape và check cấu trúc JSONL dataset.")
    
    # Định nghĩa tham số đầu vào là tên file
    parser.add_argument('filename', type=str, help='Tên hoặc đường dẫn đến file JSONL cần xử lý')
    
    # Parse các tham số truyền vào
    args = parser.parse_args()
    
    # Chạy hàm xử lý với tham số đã nhận
    clean_and_validate_jsonl(args.filename)