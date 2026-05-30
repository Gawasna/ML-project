import json
import os

def patch_notebook_parameters():
    notebook_path = r"C:\Users\hungl\Documents\trae_projects\ML-project\train\LoRA_Training.ipynb"
    if not os.path.exists(notebook_path):
        print(f"Error: Notebook not found at {notebook_path}")
        return

    with open(notebook_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    patched_setup = False
    patched_train = False

    for cell in data.get("cells", []):
        cell_id = cell.get("metadata", {}).get("id")
        
        # 1. Patch cell 'lora-setup'
        if cell_id == "lora-setup":
            new_setup_source = [
                "# Prompt Template ChatML toi uu cho Qwen Base Model\n",
                "prompt_template = \"\"\"<|im_start|>system\n",
                "{instruction}<|im_end|>\n",
                "<|im_start|>user\n",
                "{input}<|im_end|>\n",
                "<|im_start|>assistant\n",
                "{output}<|im_end|>\"\"\"\n",
                "\n",
                "def format_prompts(batch):\n",
                "    texts = []\n",
                "    for inst, inp, out in zip(batch['instruction'], batch['input'], batch['output']):\n",
                "        text = prompt_template.format(instruction=inst, input=inp, output=out) + tokenizer.eos_token\n",
                "        texts.append(text)\n",
                "    return {\"text\": texts}\n",
                "\n",
                "# Trích xuất và phân chia dữ liệu học thuật Train/Valid/Test song ngữ sạch\n",
                "import numpy as np\n",
                "\n",
                "# 1. Đảm bảo tính nhất quán của phép xáo trộn bằng seed cố định\n",
                "np.random.seed(42)\n",
                "\n",
                "# 2. Xác định quy mô các tập dữ liệu\n",
                "total_clean_samples = len(df_clean_dataset)\n",
                "train_size = min(20000, total_clean_samples)\n",
                "val_size = min(2000, total_clean_samples - train_size)\n",
                "test_size = min(2000, total_clean_samples - train_size - val_size)\n",
                "required_total = train_size + val_size + test_size\n",
                "\n",
                "print(f\"Tổng số mẫu sạch khả dụng sau lọc Z-score và GMM: {total_clean_samples:,}\")\n",
                "\n",
                "# 3. Sinh mảng chỉ số ngẫu nhiên không trùng lặp cho toàn bộ 24,000 mẫu\n",
                "all_indices = np.random.choice(total_clean_samples, required_total, replace=False)\n",
                "\n",
                "# 4. Phân chia chỉ mục rạch ròi cho từng tập (Ngăn chặn hoàn toàn rò rỉ dữ liệu - Data Leakage)\n",
                "train_indices = all_indices[:train_size]\n",
                "val_indices = all_indices[train_size:(train_size + val_size)]\n",
                "test_indices = all_indices[(train_size + val_size):required_total]\n",
                "\n",
                "# 5. Khởi tạo các tập dữ liệu con bằng phương pháp load chỉ mục nhanh (.select)\n",
                "train_dataset = df_clean_dataset.select(train_indices)\n",
                "val_dataset = df_clean_dataset.select(val_indices)\n",
                "test_dataset = df_clean_dataset.select(test_indices)\n",
                "\n",
                "print(\"Phân chia tập dữ liệu thành công:\")\n",
                "print(f\"  - Tập Huấn luyện (Train Set): {len(train_dataset):,} mẫu (Mô hình sẽ học 14,400 mẫu qua 1,800 steps)\")\n",
                "print(f\"  - Tập Kiểm định (Val Set)   : {len(val_dataset):,} mẫu\")\n",
                "print(f\"  - Tập Kiểm thử (Test Set)   : {len(test_dataset):,} mẫu\")\n",
                "\n",
                "# 6. Áp dụng hàm format ChatML template lên các tập dữ liệu SFT\n",
                "formatted_train_dataset = train_dataset.map(format_prompts, batched=True)\n",
                "formatted_val_dataset = val_dataset.map(format_prompts, batched=True)\n",
                "\n",
                "# 7. Lưu tập test độc lập xuống đĩa để sử dụng đánh giá ngoại tuyến BLEU sau train\n",
                "test_df = test_dataset.to_pandas()\n",
                "test_df.to_json(\"clean_test_dataset.jsonl\", orient=\"records\", lines=True, force_ascii=False)\n",
                "print(\"Saved clean test dataset to clean_test_dataset.jsonl for post-training evaluation.\")\n",
                "\n",
                "# Ap dung cau hinh PEFT LoRA\n",
                "model = FastLanguageModel.get_peft_model(\n",
                "    model,\n",
                "    r = 16,\n",
                "    target_modules = [\"q_proj\", \"k_proj\", \"v_proj\", \"o_proj\",\n",
                "                      \"gate_proj\", \"up_proj\", \"down_proj\"],\n",
                "    lora_alpha = 16,\n",
                "    lora_dropout = 0,\n",
                "    bias = \"none\",\n",
                "    use_gradient_checkpointing = \"unsloth\",\n",
                "    random_state = 3407,\n",
                ")\n",
                "\n",
                "print(\"PEFT LoRA configured successfully.\")"
            ]
            cell["source"] = new_setup_source
            patched_setup = True
            print("Cell 'lora-setup' patched successfully.")

        # 2. Patch cell 'train-lora'
        elif cell_id == "train-lora":
            new_train_source = [
                "from trl import SFTTrainer\n",
                "from transformers import TrainingArguments\n",
                "\n",
                "# Cấu hình SFTTrainer với packing = True và Cosine Learning Rate Decay cho chu kỳ 1,800 steps\n",
                "trainer = SFTTrainer(\n",
                "    model = model,\n",
                "    tokenizer = tokenizer,\n",
                "    train_dataset = formatted_train_dataset,\n",
                "    eval_dataset = formatted_val_dataset,\n",
                "    dataset_text_field = \"text\",\n",
                "    max_seq_length = max_seq_length,\n",
                "    packing = True,  # Bật đóng gói ngữ cảnh giúp tăng tốc độ train lên gấp 2-3 lần\n",
                "    args = TrainingArguments(\n",
                "        per_device_train_batch_size = 2,\n",
                "        gradient_accumulation_steps = 4,           # Effective batch size = 8\n",
                "        warmup_steps = 50,                         # ~2.8% tổng số steps\n",
                "        max_steps = 1800,                          # ~3.5h train + 0.5h buffer trên GPU T4\n",
                "        learning_rate = 2e-4,\n",
                "        lr_scheduler_type = \"cosine\",              # Lịch trình cosine decay đảm bảo sự hội tụ sâu\n",
                "        evaluation_strategy = \"steps\",             # Đánh giá định kỳ\n",
                "        eval_steps = 200,                          # Đánh giá loss kiểm định sau mỗi 200 steps\n",
                "        save_steps = 600,                          # Ghi checkpoint mỗi ~1 giờ tránh mất kết nối Colab\n",
                "        save_total_limit = 2,                      # Chỉ giữ 2 checkpoint mới nhất để tiết kiệm đĩa\n",
                "        logging_steps = 10,                        # Tần suất ghi log tối ưu cho WandB\n",
                "        optim = \"adamw_8bit\",                      # Sử dụng AdamW 8-bit tiết kiệm bộ nhớ\n",
                "        weight_decay = 0.01,\n",
                "        seed = 3407,\n",
                "        output_dir = \"outputs\",\n",
                "        report_to = \"wandb\"                        # Báo cáo trực quan trực tiếp lên Weights & Biases\n",
                "    ),\n",
                ")\n",
                "\n",
                "print(\"Starting LoRA Fine-Tuning...\")\n",
                "trainer.train()\n",
                "print(\"LoRA Fine-Tuning completed successfully.\")"
            ]
            cell["source"] = new_train_source
            patched_train = True
            print("Cell 'train-lora' patched successfully.")

    if not patched_setup or not patched_train:
        print(f"Warning: Cell patching incomplete. Setup: {patched_setup}, Train: {patched_train}")
        return

    with open(notebook_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print("Notebook updated successfully with SFT 1,800 steps config.")

if __name__ == "__main__":
    patch_notebook_parameters()
