import json
import hashlib
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

src_file = "extracted_the_gioi.jsonl"

# Đọc tin thứ 3 của Batch 37 trong output.txt
# Nó bắt đầu bằng: "Trong cuộc đối thoại đầu tiên như vậy kể từ khi Nga mở chiến dịch quân sự đặc biệt ở Ukraine ngày 24/2..."
# Hãy băm MD5 của nó
target_text = "Trong cuộc đối thoại đầu tiên như vậy kể từ khi Nga mở chiến dịch quân sự đặc biệt ở Ukraine ngày 24/2, Ngoại trưởng Mỹ Antony Blinken và người đồng cấp Nga Sergei Lavrov đã tìm cách giữ vững lập trường hiện có của họ. Reuters dẫn lời ông Blinken phát biểu tại một cuộc họp báo ở Bộ Ngoại giao Mỹ hôm 29/7: \"Chúng tôi đã có một cuộc trao đổi thẳng thắn và trực tiếp. Tôi đã hối thúc Điện Kremlin chấp nhận đề xuất quan trọng mà chúng tôi đưa ra về việc thả Paul Whelan và Brittney Griner\". Một quan chức Mỹ giấu tên nói, cuộc điện đàm giữa hai nhà ngoại giao hàng đầu của Washington và Moscow kéo dài khoảng 25 phút và \"không mang tính luận chiến\". Động thái diễn ra khi một nguồn thạo tin tiết lộ, Nga đã cố gắng đưa Vadim Krasikov, một nhân vật bị Đức kết án chung thân vì tội giết một cựu tay súng người Chechnya ở Berlin năm 2019, vào danh sách trao đổi tù nhân. Nguồn thạo tin xác nhận thông tin do CNN đăng tải rằng, các quan chức Mỹ không xem trọng ý tưởng này vì nhiều lí do, bao gồm cả việc Krasikov đang bị Đức giam giữ. Mặc dù không nêu chi tiết nhưng Hội đồng An ninh quốc gia Mỹ đã bác bỏ đề xuất của Moscow. \"Dùng hai công dân Mỹ bị bắt giữ trái phép làm con tin cho việc phóng thích một tên sát nhân người Nga đang bị giam giữ ở nước thứ 3 không phải là một lời đề nghị nghiêm túc. Nga không nên có nỗ lực thiếu thiện chí đó để tránh đạt thỏa thuận\", phát ngôn viên của Hội đồng An ninh quốc gia Mỹ Adrienne Watson nhấn mạnh. Theo Tuấn Anh (VietNamNet)"
target_md5 = hashlib.md5(target_text.strip().encode("utf-8")).hexdigest()
print(f"Target MD5: {target_md5}")

with open(src_file, "r", encoding="utf-8") as f:
    for idx, line in enumerate(f, 1):
        if idx in [342, 359]:
            data = json.loads(line)
            content = data.get("output", "")
            h = hashlib.md5(content.strip().encode("utf-8")).hexdigest()
            print(f"Line {idx} MD5: {h}")
            if h == target_md5:
                print(f"MATCH FOUND AT LINE {idx}!")
