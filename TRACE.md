# TRACE

## Nhiệm vụ hiện tại
- Chuẩn bị môi trường và mã nguồn huấn luyện LoRA cho mô hình đích tối ưu **`qwen2.5:1.5b`** (điểm ngọt/sweet spot) bằng các bộ dữ liệu siêu sạch khổng lồ đã chuẩn bị tại thư mục `data/train/prepared/`.
- Khởi chạy demo ứng dụng Playground SPA (`.\run-demo.ps1`) để kiểm thử kết nối API Gateway.

## Tiến độ
- [x] Thiết lập lịch biểu check tự động 5 phút/lần (`task-669`) để duy trì tiến trình và bảo toàn token quota.
- [x] Hoàn thành đo lường baseline cực đoan 500 mẫu và xuất báo cáo tại [models_baseline_extreme_report.md](file:///C:/Users/hungl/Documents/trae_projects/ML-project/docs/models_baseline_extreme_report.md).
- [x] Thiết lập Khung học thuật ML (ML Academic Framework) tại [ml_academic_framework.md](file:///C:/Users/hungl/Documents/trae_projects/ML-project/docs/ml_academic_framework.md) để phục vụ báo cáo đồ án, tránh lỗi Out of Scope.
- [x] Ánh xạ chi tiết đồ án với 12 bài LAB thực hành của giảng viên tại [academic_mapping_report.md](file:///C:/Users/hungl/Documents/trae_projects/ML-project/docs/LECTURER_REQ/academic_mapping_report.md) theo đúng cấu trúc mẫu báo cáo `REPORT_TEMPLATE_WORD.md`.
- [x] Soạn thảo và cấu trúc Hướng dẫn triển khai thuật toán ML thuần tại [native_ml_implementation.md](file:///C:/Users/hungl/Documents/trae_projects/ML-project/docs/LECTURER_REQ/native_ml_implementation.md) (gồm TF-IDF Classifier, PCA+t-SNE K-Means, GMM Anomaly Detection) để đảm bảo 100% nằm trong scope môn học.
- [x] Thiết lập Kế hoạch nâng cấp notebook huấn luyện core LoRA tại [lora_notebook_upgrade_plan.md](file:///C:/Users/hungl/Documents/trae_projects/ML-project/docs/lora_notebook_upgrade_plan.md) để nhúng trực tiếp mã nguồn ML thuần túy vào môi trường Colab.
- [x] Kiểm tra độ ổn định & thực hiện lọc trùng sâu nội dung trên `temp\labs-ml\translated_thoi_su.jsonl` (phát hiện và loại bỏ 2,270 mẫu trùng lặp), loại bỏ trường `topic`, di chuyển và lưu trữ **43,038 mẫu duy nhất** tại thư mục chuẩn bị sẵn [data/train/prepared/prepared_translated_thoi_su.jsonl](file:///C:/Users/hungl/Documents/trae_projects/ML-project/data/train/prepared/prepared_translated_thoi_su.jsonl).
- [x] Thực hiện đối chiếu chéo (0 trùng lặp) và lọc trùng nội bộ (63 trùng lặp) trên `temp\labs-ml\translated_the_gioi.jsonl`, loại bỏ trường `topic`, lưu trữ **937 mẫu Thế giới duy nhất** tại thư mục chuẩn bị sẵn [data/train/prepared/data_937_thoisu_4.jsonl](file:///C:/Users/hungl/Documents/trae_projects/ML-project/data/train/prepared/data_937_thoisu_4.jsonl).
- [x] Thực hiện đồng bộ hóa nhãn chỉ dẫn (instruction) bằng biểu thức chính quy (Regex), thay thế toàn bộ cụm từ `"thế giới"` thành `"Thời sự"` trên cả **937 dòng** của tập dữ liệu Thế giới để tối ưu hóa attention weights khi train LoRA.
- [x] Chuyển đổi siêu tốc bộ dữ liệu khổng lồ **2,906,992 dòng** từ 3 file CSV của `ncduy/` (train, test, valid) thành dạng JSONL sạch, loại bỏ trường `source`, thêm instruction chuẩn hóa `"Thời sự"`, lưu tại thư mục [data/train/prepared/](file:///C:/Users/hungl/Documents/trae_projects/ML-project/data/train/prepared/).
- [x] Lọc sạch triệt để ký tự non-Latinh, CJK (loại bỏ tổng cộng 8,510 dòng chữ Trung/Nhật/Hàn) và Cyrillic/Arabic (loại bỏ 3,850 dòng) song song với triệt tiêu 1,018 ký tự điều khiển rác ẩn **U+200E** trên cả 3 bộ dữ liệu (train, test, valid) của ncduy, bảo đảm độ tinh khiết dữ liệu tối đa.
- [x] Thực hiện gộp và làm sạch đồng bộ **36 lô tệp tin thời sự lẻ** từ N0002 đến N1000, loại bỏ 2,270 bản ghi trùng lặp nội bộ, lược bỏ các trường `id` và `topic`, chuẩn hóa chỉ dẫn thành `"Thời sự"`, lưu trữ thành công **42,987 mẫu duy nhất** tại [prepared_translated_thoi_su_N0002_N1000.jsonl](file:///C:/Users/hungl/Documents/trae_projects/ML-project/data/train/prepared/prepared_translated_thoi_su_N0002_N1000.jsonl).
- [ ] Xây dựng mã nguồn huấn luyện LoRA cho mô hình `qwen2.5:1.5b` dựa trên file Colab gốc.
- [ ] Thực hiện so sánh điểm BLEU sau huấn luyện để đo đạc delta cải thiện.

## Kế hoạch hành động tiếp theo
1. Cấu hình kịch bản huấn luyện LoRA chi tiết cho `qwen2.5:1.5b` (Unsloth/HuggingFace) sử dụng các tham số toán học đã ánh xạ.
2. Khởi chạy demo web để kiểm tra và tối ưu hóa trải nghiệm Bento UI.
