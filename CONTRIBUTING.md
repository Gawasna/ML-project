# Hướng dẫn đóng góp (Workflow & Dataset)

## 0. Quy trình thu thập dữ liệu thô (Video/Audio)
Nếu task của bạn là khai thác và chuẩn bị dữ liệu raw từ nền tảng VTV (VietNamToday), hãy tuân thủ quy trình bảo vệ trùng lặp sau:
1. **Lấy định danh ID & URL CDN**: Khởi chạy `python entry.py`, tuỳ chọn danh tính người dùng đóng góp cá nhân (hung, quang, hoang). Cung cấp các URL bài báo để script tự động phân tích lấy luồng dữ liệu chuẩn (thường là CDN dạng master.m3u8). Hành động này kết thúc tự động chặn/huỷ bỏ bằng cách kiểm tra ID trong `targets.txt`.
2. **Kéo file đa phương tiện cục bộ**: Khởi chạy `python process.py`. Tool tự động đọc định danh danh tính của bạn, tiến hành check trùng lặp chéo giữa các workspace (Cross-workspace Duplicate Validation). Nếu an toàn, `yt-dlp` sẽ tải luồng `mp4` gốc về thư mục `data/raw/video/` và dùng công cụ `ffmpeg` mã hoá PCM WAV để tách âm thanh chuyển về `data/raw/audio/`. Ở bất kì trường hợp phát sinh cảnh báo danh tính trùng từ script này, hãy huỷ bỏ và giải quyết report tay cho Lead.
3. **Chuẩn bị dữ liệu**: Đem các file raw audio , sử dụng bất kỳ công cụ transcribe để chuyển chúng thành các file text. Các file text này sẽ tiếp tục được chuyển do `lora-dataset-architect/` để tạo  dữ liệu chuẩn `.jsonl` phục vụ cho quá trình Training. Nếu không muốn setup `lora-dataset-architect/` và gắn API thủ công, có thể trực tiếp truy cập đường link được cung cấp trong `studio.url.html` để sử dụng.

[Lưu ý quan trọng]: Tuyệt đối chú ý cách hành văn từ dữ liệu do AI tạo ra. Các đặc điểm sẽ làm nhiễu dataset:
- Sử dụng "", - để đánh dấu câu trả lời, thay vì viết tự nhiên. 
- Sử dụng () để đánh dấu phần giải thích , giải thích lại thuật ngữ bằng tiếng anh, thay vì viết tự nhiên.
- Sử dụng Output tiếng việt kèm tiếng anh trong cùng một câu trả lời, thay vì viết tiếng Việt thuần túy. 

Hành vi của STT Engine(Speech to Text) không bao giờ nhận diện được những đặc điểm này, dẫn đến việc mô hình sẽ học theo cách viết không tự nhiên, gây nhiễu và giảm chất lượng tổng thể của dataset. Hãy đảm bảo rằng các câu trả lời được viết một cách tự nhiên, không có dấu hiệu của việc tạo ra bởi AI, để đảm bảo chất lượng và tính đa dạng của dữ liệu huấn luyện.
---

## Cấu trúc chuẩn bị Dataset 4 bước

### 1. Nhận task
Lead tạo Issue với label `dataset` và assign cho bạn.  
Đọc kỹ yêu cầu: chủ đề, số lượng, ví dụ mẫu, deadline.

### 2. Tạo branch và viết data

```bash
git checkout master && git pull
git checkout -b data/<tên>-<chủ-đề>
# ví dụ: git checkout -b data/hungl-python-qa
```

Tạo file tại `data/train/<tên>_<chủ_đề>.jsonl`:

```jsonl
{"instruction": "Dịch thuật sang tiếng Việt", "input": "Today is a beautiful day.", "output": "Hôm nay là một ngày đẹp trời."}
{"instruction": "Dịch đoạn sau sang tiếng Việt", "input": "Hello", "output": "Xin chào"}
```

**Quy tắc bắt buộc:**
- Mỗi dòng = 1 JSON object hợp lệ
- Phải có `instruction` và `output`, `input` có thể để rỗng `""`
- Không copy nguyên văn từ Wikipedia hay nguồn có bản quyền
- Tiếng Việt rõ ràng, tự nhiên

### 3. Validate local trước khi push

```bash
python scripts/validate_dataset.py --file data/train/<file_của_bạn>.jsonl
```

Không có dòng `[ERROR]` mới được push.

### 4. Tạo Pull Request

```bash
git add data/train/<file_của_bạn>.jsonl
git commit -m "data: add <số> <chủ đề> pairs [<tên>]"
git push origin data/<tên>-<chủ-đề>
```

Vào GitHub → tạo PR vào `master` → điền PR template → đề cập `Closes #<số issue>`.

---

## Cấu trúc thư mục

```
data/
├── train/          ← file .jsonl đã được review và merge
│   └── <tên>_<chủ_đề>.jsonl
└── raw/            ← bản nháp (không được dùng để train)
```

## Lỗi thường gặp

| Lỗi | Nguyên nhân | Fix |
|-----|------------|-----|
| `JSON không hợp lệ` | Dấu ngoặc kép sai, dấu phẩy thừa | Dùng [jsonlint.com](https://jsonlint.com) check từng dòng |
| `TRÙNG CHÍNH XÁC` | instruction giống hệt record khác | Xóa hoặc viết lại |
| `instruction rỗng` | Field bị bỏ trống | Điền nội dung |
