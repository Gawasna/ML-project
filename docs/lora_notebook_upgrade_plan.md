# KẾ HOẠCH NÂNG CẤP NOTEBOOK HUẤN LUYỆN CORE (CORE NOTEBOOK UPGRADE PLAN)
## Tích Hợp Thuật Toán Học Máy Kinh Điển Vào Tiến Trình Huấn Luyện LoRA

Tài liệu này vạch ra kế hoạch chi tiết để nâng cấp tệp notebook cốt lõi [lora-training/LoRA_Training.ipynb](file:///C:/Users/hungl/Documents/trae_projects/ML-project/lora-training/LoRA_Training.ipynb). Mục tiêu của việc nâng cấp này là chuyển đổi mô hình mục tiêu sang **`Qwen2.5-1.5B (Base Model)`** (điểm ngọt tối ưu) và nhúng trực tiếp các cấu phần Học máy thuần túy (TF-IDF, PCA, K-Means tự viết, và GMM Anomaly Detection) vào luồng thực thi của notebook Colab để tạo nên một bài báo cáo thực hành học thuật hoàn chỉnh, đáp ứng 100% yêu cầu của Giảng viên.

---

## 1. MỤC TIÊU THAY ĐỔI CỐT LÕI (CORE UPGRADE OBJECTIVES)

1. **Chuyển đổi Mô hình đích**: Đổi từ `Qwen/Qwen2.5-3B-Instruct` sang **`Qwen/Qwen2.5-1.5B (Base Model)`** để tối ưu hóa hiệu năng, giảm thời gian huấn luyện trên GPU T4 của Google Colab và tiết kiệm VRAM biên khi chạy thực tế (<1 GB VRAM).
2. **Nhúng Pipeline Tiền xử lý Học máy**: Thực hiện tiền xử lý dữ liệu (Denoising, Tokenization, Outlier Filter) trực tiếp bằng Numpy và Pandas trước khi đẩy vào SFT Trainer.
3. **Nhúng Trực quan hóa dữ liệu cao chiều (PCA + t-SNE + K-Means tự viết)**: Tiến hành phân cụm và trực quan hóa các bài báo trong tập dữ liệu huấn luyện ngay trong notebook Colab để làm minh chứng cho báo cáo kỹ thuật.
4. **Nhúng Mô hình Xác suất Phát hiện Dị thường (GMM Anomaly)**: Huấn luyện bộ GMM trên tập dữ liệu dịch thuật để tính ngưỡng log-likelihood an toàn trước khi lưu trữ mô hình.

---

## 2. CHI TIẾT CÁC BƯỚC NÂNG CẤP TRONG NOTEBOOK (STEP-BY-STEP UPGRADE FLOW)

```
[BƯỚC 1: Setup & Vá lỗi Unsloth] 
       │
       ▼
[BƯỚC 2: Tải Mô hình Qwen2.5-1.5B (Base Model) & Thiết lập LoRA]
       │
       ▼
[BƯỚC 3: Nạp Dữ liệu & Tiền xử lý (Denoising, Outlier Length Removal)]
       │
       ▼
[BƯỚC 4: Trực quan hóa Học máy (TF-IDF + PCA + t-SNE + K-Means tự code)] <--- TÍCH HỢP ML scope
       │
       ▼
[BƯỚC 5: Huấn luyện Hệ thống Fallback (GMM Anomaly Detection)]        <--- TÍCH HỢP ML scope
       │
       ▼
[BƯỚC 6: Huấn luyện LoRA Adapter (AdamW Optimizer + Cross-Entropy Loss)]
       │
       ▼
[BƯỚC 7: Lưu trữ Mô hình & Xuất tệp Adapter]
```

---

### BƯỚC 1 & 2: KHỞI TẠO MÔ HÌNH VỚI QWEN 2.5 1.5B
- **Thay đổi**: Cấu hình lại tham số tải mô hình trong Unsloth để trỏ đến `Qwen/Qwen2.5-1.5B (Base Model)`.
- **Mã nguồn nâng cấp**:
```python
# Cấu hình tải mô hình nén hạng thấp tối ưu
model_name = "Qwen/Qwen2.5-1.5B"
max_seq_length = 2048
dtype = None # Auto detection
load_in_4bit = True # Tiết kiệm VRAM tối đa cho Google Colab T4

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = model_name,
    max_seq_length = max_seq_length,
    dtype = dtype,
    load_in_4bit = load_in_4bit,
)
```

---

### BƯỚC 4: GIẢI NÉN & NẠP DATASET KHÔNG OOM RAM (Z-SCORE $3\sigma$ - LAB 1)
- **Thay đổi**: Thay thế hoàn toàn thư viện Pandas bằng **Hugging Face `load_dataset` (PyArrow)** để load và xử lý 2.87 triệu câu song ngữ trực tiếp từ tệp nén `prepared.rar` giải nén mà không bị OOM RAM (tiêu thụ <150 MB RAM). Áp dụng Z-Score $3\sigma$ lọc outliers thông qua bộ lọc đĩa `dataset.filter`.
- **Mã nguồn nâng cấp**:
```python
from datasets import load_dataset
import numpy as np

# Nạp siêu tốc và tiết kiệm RAM tối đa bằng Hugging Face load_dataset (PyArrow)
# Chỉ nạp các file train (chống rò rỉ dữ liệu)
raw_dataset = load_dataset("json", data_files=["extracted_dataset/train_*.jsonl"], split="train")

# Trích xuất đặc trưng độ dài câu bằng map
def compute_lengths(example):
    example['eng_len'] = len(str(example.get('input', '')).split())
    example['vi_len'] = len(str(example.get('output', '')).split())
    return example

dataset_with_len = raw_dataset.map(compute_lengths, num_proc=2)

# Lọc Outliers bằng phương pháp thống kê Z-Score (LAB 1a, 1b)
eng_lengths = np.array(dataset_with_len['eng_len'])
mean_eng = eng_lengths.mean()
std_eng = eng_lengths.std()

limit_upper = mean_eng + 3 * std_eng
limit_lower = max(0, mean_eng - 3 * std_eng)

df_clean_dataset = dataset_with_len.filter(
    lambda x: limit_lower <= x['eng_len'] <= limit_upper,
    num_proc=2
)
print(f"Đã lọc xong outliers. Mẫu sạch còn lại: {len(df_clean_dataset)}")
```

---

### BƯỚC 5: TRỰC QUAN HÓA PHÂN CỤM TRÊN TẬP MẪU TRÁNH OOM (TF-IDF + PCA + t-SNE + K-MEANS TỰ CODE)
- **Thay đổi**: Lấy một tập mẫu con ngẫu nhiên (ví dụ 1000 mẫu) đại diện cho tập sạch để chạy thuật toán giảm chiều **PCA + t-SNE** và vẽ đồ thị phân cụm **K-Means numpy tự code** (tránh độ phức tạp tính toán phi tuyến $O(N^2)$ của t-SNE gây OOM RAM và chạy mất nhiều ngày khi nạp hàng triệu dòng).
- **Mã nguồn nâng cấp**:
```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
import pandas as pd
import matplotlib.pyplot as plt

# 1. Trích xuất ngẫu nhiên tập con 1000 mẫu đại diện
sample_size = min(1000, len(df_clean_dataset))
sampled_data = df_clean_dataset.shuffle(seed=42).select(range(sample_size))
df_sample = pd.DataFrame(sampled_data)

# 2. Trích xuất đặc trưng TF-IDF (LAB 1a)
vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
tfidf_matrix = vectorizer.fit_transform(df_sample['input'])

# 3. PCA Giảm chiều khử nhiễu xuống 20 chiều (LAB 2a)
pca = PCA(n_components=min(20, tfidf_matrix.shape[0]), random_state=42)
X_pca = pca.fit_transform(tfidf_matrix.toarray())

# 4. t-SNE Giảm chiều trực quan hóa xuống 2D (LAB 2b)
tsne = TSNE(n_components=2, perplexity=min(30, len(X_pca)-1), random_state=42)
X_2d = tsne.fit_transform(X_pca)

# 5. Thuật toán K-Means thủ công bằng Numpy (LAB 6a - Bắt buộc tự code)
class ColabKMeans:
    def __init__(self, k=3, max_iters=30):
        self.k = k
        self.max_iters = max_iters
        self.centroids = None
    def fit(self, X):
        np.random.seed(42)
        idx = np.random.choice(X.shape[0], self.k, replace=False)
        self.centroids = X[idx]
        for _ in range(self.max_iters):
            distances = np.sqrt(((X[:, np.newaxis] - self.centroids) ** 2).sum(axis=2))
            labels = np.argmin(distances, axis=1)
            new_centroids = np.array([X[labels == i].mean(axis=0) if len(X[labels == i]) > 0 
                                      else self.centroids[i] for i in range(self.k)])
            if np.allclose(self.centroids, new_centroids): break
            self.centroids = new_centroids
        return labels

kmeans = ColabKMeans(k=3)
cluster_labels = kmeans.fit(X_2d)

# 6. Vẽ đồ thị trực quan hóa (LAB 1a)
plt.figure(figsize=(8, 6))
plt.scatter(X_2d[:, 0], X_2d[:, 1], c=cluster_labels, cmap='rainbow', alpha=0.7)
plt.title("Visualizing Training Data Clusters in Colab (PCA + t-SNE + K-Means numpy)")
plt.xlabel("t-SNE Dim 1")
plt.ylabel("t-SNE Dim 2")
plt.show()
```

---

### BƯỚC 6: TÍCH HỢP HUẤN LUYỆN GMM ANOMALY DETECTOR
- **Thay đổi**: Lấy một tập mẫu con lớn (ví dụ 50,000 dòng) từ tập sạch để huấn luyện mô hình xác suất **GMM (Gaussian Mixture Model)** trên đặc trưng `[eng_len, vi_len]` siêu nhanh (trong 1 giây) mà không bị tràn RAM. Ngưỡng log-likelihood phân vị 5% được lưu làm chốt chặn an toàn phát hiện dị thường khi suy luận.
- **Mã nguồn nâng cấp**:
```python
from sklearn.mixture import GaussianMixture
import pickle

# Lấy một mẫu con lớn để huấn luyện GMM nhanh chóng
gmm_sample_size = min(50000, len(df_clean_dataset))
sampled_gmm = df_clean_dataset.shuffle(seed=42).select(range(gmm_sample_size))
X_gmm = np.column_stack((sampled_gmm['eng_len'], sampled_gmm['vi_len']))

gmm = GaussianMixture(n_components=2, covariance_type='full', random_state=42)
gmm.fit(X_gmm)

# Tính toán ngưỡng log-probability cho phân vị 5%
scores = gmm.score_samples(X_gmm)
gmm_threshold = np.percentile(scores, 5)

print(f"Huấn luyện GMM hoàn tất. Ngưỡng phát hiện dị thường (Threshold): {gmm_threshold:.4f}")

# Lưu trữ model GMM làm cấu phần Anomaly Detection cho Gateway
with open("gmm_anomaly_detector.pkl", "wb") as f:
    pickle.dump({"model": gmm, "threshold": gmm_threshold}, f)
```

---

### BƯỚC 6: HUẤN LUYỆN LORA VỚI WANDB LOGGING NÂNG CAO
- **Thay đổi**: Cấu hình Wandb để giám sát quá trình tối ưu hóa Cross-Entropy Loss bằng AdamW Optimizer của LoRA Adapter.
- **Mã nguồn nâng cấp**:
```python
# Tải và cấu hình huấn luyện LoRA Adapter
model = FastLanguageModel.get_peft_model(
    model,
    r = 16, # Rank nén thấp
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                      "gate_proj", "up_proj", "down_proj"],
    lora_alpha = 16,
    lora_dropout = 0,
    bias = "none",
    use_gradient_checkpointing = "unsloth",
    random_state = 3407,
)

trainer = SFTTrainer(
    model = model,
    tokenizer = tokenizer,
    train_dataset = formatted_dataset,
    dataset_text_field = "text",
    max_seq_length = max_seq_length,
    dataset_num_proc = 2,
    packing = False,
    args = SFTConfig(
        per_device_train_batch_size = 2,
        gradient_accumulation_steps = 4,
        warmup_steps = 5,
        max_steps = 60, # Tối ưu hóa số bước chạy nhanh trong 10-15 phút trên Colab
        learning_rate = 2e-4,
        fp16 = not torch.cuda.is_bf16_supported(),
        bf16 = torch.cuda.is_bf16_supported(),
        logging_steps = 1,
        optim = "adamw_8bit", # Cực tiểu hóa Loss bằng AdamW
        weight_decay = 0.01, # L2 Regularization (LAB 3a)
        seed = 3407,
        output_dir = "outputs",
        report_to = "wandb" # Giám sát trực quan hóa học thuật bằng Wandb
    ),
)
trainer.train()
```

---

### BƯỚC 7: XUẤT MÔ HÌNH GGUF TRỰC TIẾP LÊN LOCAL HOẶC GOOGLE DRIVE
- **Thay đổi**: Thêm tùy chọn và mã nguồn cho phép merge trực tiếp LoRA weights vào Base Model và xuất ra tệp định dạng **`GGUF`** (lượng hóa tối ưu `q4_k_m` hoặc `q8_0`). Cung cấp 2 lựa chọn: (1) Lưu local tại Colab `/content/` giúp tải trực tiếp qua trình duyệt với tốc độ cao, (2) Lưu Drive làm bản dự phòng lâu dài.
- **Mã nguồn nâng cấp**:
```python
# =================================================================
# 7. LƯU TRỮ VÀ XUẤT BẢN MÔ HÌNH GGUF
# =================================================================
# Cấu hình lưu trữ adapter thông thường
model.save_pretrained("lora_model")
tokenizer.save_pretrained("lora_model")

# Tùy chọn xuất trực tiếp mô hình GGUF lượng hóa
export_gguf = True
quantization_method = "q4_k_m" # Phương pháp lượng hóa cân bằng chất lượng/dung lượng tốt nhất

if export_gguf:
    print(f"⏳ Đang tiến hành merge weights và xuất mô hình GGUF ({quantization_method})...")
    
    # Lựa chọn 1: Lưu local trên Colab (/content/) để tải xuống trực tiếp cực nhanh bằng trình duyệt
    local_gguf_path = "/content/Qwen2.5-1.5B-ThoiSu-GGUF"
    model.save_pretrained_gguf(
        local_gguf_path,
        tokenizer,
        quantization_method = quantization_method,
    )
    print(f"✅ Đã xuất mô hình GGUF local thành công tại: {local_gguf_path}")
    print("💡 Bạn có thể click chuột phải vào file trong tab Files của Colab để tải xuống trực tiếp với tốc độ cao!")
    
    # Lựa chọn 2: Lưu vào Google Drive đã mount ở Bước 2 để lưu trữ lâu dài (tùy chọn)
    # drive_gguf_path = "/content/drive/MyDrive/Qwen2.5-1.5B-ThoiSu-GGUF"
    # model.save_pretrained_gguf(drive_gguf_path, tokenizer, quantization_method = quantization_method)
```

---

## 3. TIÊU CHÍ NGHIỆM THU (ACCEPTANCE CRITERIA FOR THE NOTEBOOK)

- [ ] Chạy thành công 100% không báo lỗi cú pháp trên môi trường Google Colab T4 GPU.
- [ ] Điểm Loss giảm đều và ổn định qua các bước (giám sát trực tiếp trên biểu đồ Wandb).
- [ ] Xuất ra ảnh trực quan hóa phân cụm tin tức 2D ngay trên notebook để chụp ảnh minh chứng cho báo cáo Word.
- [ ] Tạo và lưu trữ thành công tệp `gmm_anomaly_detector.pkl` chứa mô hình Anomaly Detection hợp lệ của LAB 6b.
- [ ] Xuất bản thành công mô hình đã merge dưới dạng định dạng **GGUF (q4_k_m)** trực tiếp lên Google Drive.
- [ ] Xuất bản thư mục adapter LoRA dự phòng.
