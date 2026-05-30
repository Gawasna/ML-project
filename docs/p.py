import os

def reformat_csv_for_vietnamese_excel(input_path, output_path):
    if not os.path.exists(input_path):
        print(f"Lỗi: Không tìm thấy file {input_path}")
        return

    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    
    # Xử lý dòng tiêu đề (Header) - Chỉ thay thế dấu phẩy thành dấu chấm phẩy
    header = lines[0].strip().split(',')
    new_lines.append(";".join(header))

    # Xử lý các dòng dữ liệu
    for line in lines[1:]:
        if not line.strip():
            continue
            
        # Tách các cột theo dấu phẩy gốc
        parts = line.strip().split(',')
        
        # Đảm bảo dòng có đủ số cột (tránh lỗi dòng trống hoặc log lỗi)
        if len(parts) >= 6:
            model_name = parts[0]
            sample_index = parts[1]
            word_count = parts[2]
            
            # Đổi dấu chấm thập phân thành dấu phẩy cho các cột số
            bleu_score = parts[3].replace('.', ',')
            latency_sec = parts[4].replace('.', ',')
            status = parts[5]
            
            # Gộp lại bằng dấu chấm phẩy
            new_line = f"{model_name};{sample_index};{word_count};{bleu_score};{latency_sec};{status}"
            new_lines.append(new_line)

    # Ghi ra file mới
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(new_lines))
        
    print(f"Đã chuyển đổi định dạng thành công! File lưu tại: {output_path}")

# Đường dẫn file của bạn (thay đổi cho đúng thực tế cấu hình homelab/project)
input_file = "C:/Users/hungl/Documents/trae_projects/ML-project/docs/aaa.csv"
output_file = "C:/Users/hungl/Documents/trae_projects/ML-project/docs/benchmark_excel_fix.csv"

reformat_csv_for_vietnamese_excel(input_file, output_file)