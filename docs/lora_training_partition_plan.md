# KẾ HOẠCH PHÂN CHIA DỮ LIỆU HUẤN LUYỆN LORA (TRAIN / VALID / TEST)
## Tối ưu hóa chu kỳ 1,400 - 1,800 steps trên hạ tầng GPU T4 Google Colab

Tài liệu này ghi nhận kế hoạch phân chia dữ liệu thực tế và các con số toán học chính xác nhằm chuyển dịch từ giai đoạn kiểm thử đường dẫn (sanity check 60 steps) sang chu kỳ huấn luyện hội tụ thực tế (1,400 - 1,800 steps) trên hạ tầng giới hạn của Google Colab, đáp ứng các tiêu chuẩn học thuật cao của báo cáo đồ án Học máy.

---

## 1. TÓM TẮT TOÁN HỌC: STEPS VÀ SAMPLES SEEN

Với cấu hình phần cứng GPU T4 16GB trên Google Colab, kích thước lô hiệu dụng (Effective Batch Size) được thiết lập tối ưu để bảo vệ bộ nhớ VRAM khỏi lỗi OOM là:

$$\text{Effective Batch Size} = \text{per\_device\_train\_batch\_size} \times \text{gradient\_accumulation\_steps} = 2 \times 4 = 8 \text{ samples/step}$$

Dựa trên cấu hình này, số lượng mẫu dữ liệu song ngữ thực tế mô hình được nạp vào GPU qua các lượt lan truyền xuôi/ngược và cập nhật trọng số là:

*   **Tại mốc 1,400 steps**:
    $$\text{Samples Seen} = 1,400 \text{ steps} \times 8 \text{ samples/step} = 11,200 \text{ samples}$$
*   **Tại mốc 1,800 steps (Tối ưu ràng buộc 4 giờ T4)**:
    $$\text{Samples Seen} = 1,800 \text{ steps} \times 8 \text{ samples/step} = 14,400 \text{ samples}$$

Như vậy, mô hình sẽ tiếp cận và học hỏi trực tiếp trên **11,200 đến 14,400 mẫu song ngữ độc lập**.

---

## 2. KẾ HOẠCH PHÂN CHIA TẬP DỮ LIỆU SẠCH (DATA PARTITION PLAN)

Để đảm bảo tính ngẫu nhiên, đa dạng ngữ nghĩa và ngăn chặn hiện tượng quá khớp (overfitting) hoặc rò rỉ dữ liệu (data leakage) giữa các tập, tổng số lượng mẫu song ngữ sạch được trích xuất từ Working Dataset tinh lọc (Z-Score + GMM) là **24,000 samples**. 

Tập dữ liệu này được phân chia theo tỷ lệ vàng học thuật $83.3\% - 8.3\% - 8.3\%$ tương ứng bộ ba: **20,000 / 2,000 / 2,000**:

```
Tổng số mẫu sạch trích xuất: 24,000
│
├── Train Set (Tập huấn luyện): 20,000 samples (83.3%)
│   └── Mô hình học 11,200 - 14,400 mẫu ngẫu nhiên qua 1,400 - 1,800 steps (~72% Epoch 1)
│
├── Validation Set (Tập kiểm định): 2,000 samples (8.3%)
│   └── Tính toán loss và perplexity kiểm định độc lập định kỳ sau mỗi 200 steps
│
└── Test Set (Tập kiểm thử): 2,000 samples (8.3%)
    └── Đánh giá độc lập cuối cùng (Tính điểm BLEU/ROUGE so với mô hình Baseline)
```

### Chi tiết phân vai trò các tập dữ liệu:

1.  **Tập huấn luyện (Train Set) - 20,000 samples**:
    *   Lấy ngẫu nhiên 20,000 mẫu sạch từ tập dữ liệu đã qua lọc outliers Z-score 3-sigma và GMM.
    *   Với chu kỳ 1,800 steps (thấy 14,400 mẫu), mô hình sẽ học được khoảng **72% tập dữ liệu huấn luyện**. Việc không chạy hết 1 epoch đầy đủ giúp mô hình duy trì tính tổng quát hóa cao, ngăn ngừa hiện tượng quá khớp vào các cấu trúc câu lặp đi lặp lại.
2.  **Tập kiểm định (Validation Set) - 2,000 samples**:
    *   Trích xuất 2,000 mẫu sạch tiếp theo (không trùng lặp với tập Train).
    *   Tập này được nạp vào `SFTTrainer` thông qua tham số `eval_dataset`. Cấu hình `evaluation_strategy = "steps"` và `eval_steps = 200` để theo dõi sự hội tụ của hàm loss kiểm định độc lập, đảm bảo loss kiểm định giảm song song với loss huấn luyện.
3.  **Tập kiểm thử (Test Set) - 2,000 samples**:
    *   Trích xuất 2,000 mẫu sạch độc lập hoàn toàn (không nằm trong tập Train và Valid).
    *   Tập này được lưu trữ riêng để chạy đánh giá ngoại tuyến (offline evaluation) sau khi quá trình huấn luyện hoàn tất, tính toán các điểm số học thuật (BLEU, ROUGE) và so sánh trực tiếp với mô hình Baseline ban đầu để minh chứng delta cải tiến cho báo cáo.

---

## 3. THIẾT KẾ MÃ NGUỒN TRÍCH XUẤT PHÂN CHIA DỮ LIỆU TRÊN COLAB

Dưới đây là thiết kế mã nguồn Python (sạch, chuẩn hóa, sử dụng kỹ thuật chỉ mục ngẫu nhiên để tránh OOM) được nhúng trực tiếp vào Bước 8 của notebook để thực hiện phân chia dữ liệu chính xác trước khi khởi tạo Trainer:

```python
# =================================================================
# TRÍCH XUẤT VÀ PHÂN CHIA DỮ LIỆU HỌC THUẬT (TRAIN/VALID/TEST)
# =================================================================
import numpy as np

# 1. Đảm bảo tính nhất quán của phép xáo trộn bằng seed cố định
np.random.seed(42)

# 2. Xác định quy mô các tập dữ liệu
total_clean_samples = len(df_clean_dataset)
train_size = 20000
val_size = 2000
test_size = 2000
required_total = train_size + val_size + test_size

if total_clean_samples < required_total:
    raise ValueError(f"Tập dữ liệu sạch chỉ có {total_clean_samples:,} mẫu, không đủ phân chia {required_total:,} mẫu!")

print(f"Tổng số mẫu sạch khả dụng sau lọc Z-score và GMM: {total_clean_samples:,}")

# 3. Sinh mảng chỉ số ngẫu nhiên không trùng lặp cho toàn bộ 24,000 mẫu
all_indices = np.random.choice(total_clean_samples, required_total, replace=False)

# 4. Phân chia chỉ mục rạch ròi cho từng tập (Ngăn chặn hoàn toàn rò rỉ dữ liệu - Data Leakage)
train_indices = all_indices[:train_size]
val_indices = all_indices[train_size:(train_size + val_size)]
test_indices = all_indices[(train_size + val_size):required_total]

# 5. Khởi tạo các tập dữ liệu con bằng phương pháp load chỉ mục nhanh (.select)
train_dataset = df_clean_dataset.select(train_indices)
val_dataset = df_clean_dataset.select(val_indices)
test_dataset = df_clean_dataset.select(test_indices)

print("Phân chia tập dữ liệu thành công:")
print(f"  - Tập Huấn luyện (Train Set): {len(train_dataset):,} mẫu (Mô hình sẽ học 14,400 mẫu qua 1,800 steps)")
print(f"  - Tập Kiểm định (Val Set)   : {len(val_dataset):,} mẫu")
print(f"  - Tập Kiểm thử (Test Set)   : {len(test_dataset):,} mẫu")

# 6. Áp dụng hàm format ChatML template lên các tập dữ liệu
formatted_train_dataset = train_dataset.map(format_prompts, batched=True)
formatted_val_dataset = val_dataset.map(format_prompts, batched=True)

# 7. Lưu tập test độc lập xuống đĩa để sử dụng đánh giá ngoại tuyến BLEU sau train
test_df = test_dataset.to_pandas()
test_df.to_json("clean_test_dataset.jsonl", orient="records", lines=True, force_ascii=False)
print("Saved clean test dataset to clean_test_dataset.jsonl for post-training evaluation.")
```

---

## 4. TÍNH TOÁN BĂNG THÔNG VÀ KHẢ THI THỜI GIAN TRÊN COLAB T4

Với cấu hình phân chia này, tổng số token mô hình cần xử lý trong 1,800 steps huấn luyện là:

$$\text{Tổng số tokens} = 1,800 \text{ steps} \times 8 \text{ samples/step} \times \text{độ dài trung bình câu (~150 tokens)} \approx 2,160,000 \text{ tokens}$$

Tốc độ tính toán của GPU T4 khi chạy Unsloth QLoRA 4-bit đạt trung bình khoảng **12,000 đến 15,000 tokens/giây**. Do đó:

$$\text{Thời gian huấn luyện thực tế} = \frac{2,160,000 \text{ tokens}}{13,500 \text{ tokens/giây}} \approx 1,600 \text{ giây} \approx 26.6 \text{ phút}$$

Nếu tính thêm thời gian Overhead của thư viện, quá trình lưu checkpoint và chuẩn bị mô hình, chu kỳ 1,800 steps sẽ hoàn thành trong khoảng **35 đến 50 phút** chạy thực tế trên GPU T4. Điều này cực kỳ tối ưu, vượt xa kỳ vọng và đảm bảo an toàn tuyệt đối trước giới hạn 4 giờ của Google Colab, đồng thời đem lại hàm loss hội tụ lý tưởng phục vụ viết báo cáo học thuật.
