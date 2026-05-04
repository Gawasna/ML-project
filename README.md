# Máy Học & Dataset Khai Thác Tiếng Việt (ML-Project)

Dự án này là một tổ hợp các công cụ phục vụ cho toàn bộ vòng đời (pipeline) của học máy: từ việc thu thập dữ liệu thô (raw data) trên VTV, xử lý âm thanh, kiểm duyệt tập dữ liệu, tinh chỉnh mô hình LoRA, cho đến việc ứng dụng hiển thị thời gian thực vào các lớp phủ (overlay) trên màn hình Windows.

## Cấu Trúc Dự Án

* **`entry.py`**: Công cụ trích xuất CDN luồng M3U8 từ các URL bài viết VTV (VietNamToday). Phân tích, lựa chọn danh tính đóng góp (hung, quang, hoang) và ghi log chặn trùng lặp qua hệ thống tệp lưu `targets.txt`.
* **`process.py`**: Công cụ xử lý hậu kỳ hàng loạt. Đọc logs của người dùng cục bộ, tự động kéo video thông qua `yt-dlp` và tách lấy dữ liệu âm thanh qua `ffmpeg`. Bao gồm cả tính năng kiểm tra tự động chéo "Cross-workspace duplicate" giữa những file danh tính khác nhau để cảnh báo xung đột nếu có.
* **`data/`**: Nơi chứa dữ liệu tài nguyên:
  * `raw/video/` và `raw/audio/`: Thành phẩm xuất ra của `process.py`.
  * `train/`: Tập dữ liệu chuẩn `.jsonl` phục vụ quá trình Training.
* **`lora-dataset-architect/`**: Web App React / Vite dùng cho việc thu thập thông số, thiết lập format và xuất trực tiếp log dữ liệu dựa trên Gemini API.
* **`lora-training/`**: Chứa Jupyter Notebook `.ipynb` thực thi mô hình Qwen, tinh chỉnh các tham số LoRA qua framework thư viện Unsloth và HuggingFace TRL.
* **`overlay/`**: Ứng dụng Desktop Windows được viết bằng C# (Avalonia UI), dùng làm lớp giao diện trong suốt trên cùng phục vụ chức năng dịch Live Captions từ audio qua text.
* **`extractor/`**: Module native C++ chứa HookCore và tiến trình Loader phục vụ kết xuất thông tin cấp độ hệ thống trên môi trường Windows.

## Hướng Dẫn Cài Đặt (Prerequisites)

Quá trình cài đặt đã được tự động hóa hoàn toàn thông qua script `init.ps1`. Chỉ cần chạy script này, hệ thống sẽ:
1. Tạo và kích hoạt môi trường ảo (virtual environment).
2. Cài đặt các phụ thuộc Python (`requirements.txt`).
3. Tự động tải về và thiết lập các tệp nhị phân (`yt-dlp.exe`, `ffmpeg.exe`) vào thư mục `bin/`.

**Khởi chạy cấu hình nhanh trên PowerShell:**
```powershell
.\init.ps1
```
*(Yêu cầu: Python 3.x và PowerShell 3.0 trở lên)*

## Hợp Học - Đóng Góp Dự Án
Đọc chi tiết quy trình thu thập dữ liệu và đóng góp dataset tại [CONTRIBUTING.md](CONTRIBUTING.md).