import json
import hashlib
import sys

# Đảm bảo stdout ghi dưới dạng utf-8 để không bị lỗi mã hóa trên console Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

src_file = "extracted_the_gioi.jsonl"
tgt_file = "translated_the_gioi.jsonl"

# Đọc toàn bộ extracted (nguồn)
src_lines = []
with open(src_file, "r", encoding="utf-8") as f:
    for idx, line in enumerate(f, 1):
        if line.strip():
            data = json.loads(line)
            src_lines.append((idx, data.get("output", "")))

# Đọc toàn bộ translated (đích)
tgt_lines = []
with open(tgt_file, "r", encoding="utf-8") as f:
    for idx, line in enumerate(f, 1):
        if line.strip():
            data = json.loads(line)
            tgt_lines.append((idx, data))

# Tạo map MD5 -> line_number của extracted (strip khoảng trắng ở cả hai đầu)
src_md5_map = {}
for idx, vi_text in src_lines:
    h = hashlib.md5(vi_text.strip().encode("utf-8")).hexdigest()
    src_md5_map[h] = idx

print(f"Tổng số dòng nguồn (extracted): {len(src_lines)}")
print(f"Tổng số dòng đích (translated): {len(tgt_lines)}")

# Kiểm tra xem mỗi dòng đích khớp với dòng nguồn nào
unmatched = []
matched_count = 0
for idx, data in tgt_lines:
    vi_text = data.get("output", "")
    h = hashlib.md5(vi_text.strip().encode("utf-8")).hexdigest()
    if h in src_md5_map:
        src_idx = src_md5_map[h]
        matched_count += 1
        # In 10 dòng cuối để kiểm tra tiến trình gần đây
        if idx > len(tgt_lines) - 10:
            print(f"Dòng đích {idx} khớp với dòng nguồn {src_idx} (MD5: {h})")
    else:
        unmatched.append((idx, vi_text))

print(f"\nSố dòng khớp MD5: {matched_count}")
print(f"Số dòng không khớp MD5: {len(unmatched)}")
if unmatched:
    print("Danh sách 20 dòng không khớp đầu tiên:")
    for idx, vi_text in unmatched[:20]:
        print(f"  - Dòng đích {idx}: {vi_text[:100]}...")
