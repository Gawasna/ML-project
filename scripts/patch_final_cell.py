import json
import os

def patch_notebook():
    notebook_path = r"C:\Users\hungl\Documents\trae_projects\ML-project\train\LoRA_Training.ipynb"
    if not os.path.exists(notebook_path):
        print(f"Error: Notebook not found at {notebook_path}")
        return

    with open(notebook_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    patched = False
    for cell in data.get("cells", []):
        if cell.get("metadata", {}).get("id") == "export-gguf":
            new_source = [
                "# 1. Lưu trữ bản Adapter dự phòng\n",
                "adapter_path = \"lora_adapter\"\n",
                "model.save_pretrained(adapter_path)\n",
                "tokenizer.save_pretrained(adapter_path)\n",
                "print(f\"✅ Đã lưu trữ Adapter dự phòng tại: {adapter_path}\")\n",
                "\n",
                "# 2. Merge model sang 16-bit và lưu Hugging Face format trước (Không bao giờ treo máy, chỉ mất 1 phút)\n",
                "print(\"⏳ Đang tiến hành merge weights sang 16-bit Hugging Face format...\")\n",
                "merged_path = \"/content/merged_model\"\n",
                "model.save_pretrained_merged(merged_path, tokenizer, save_method = \"merged_16bit\")\n",
                "print(f\"✅ Đã merge và lưu mô hình 16-bit thành công tại: {merged_path}\")\n",
                "\n",
                "# 3. Giải phóng bộ nhớ RAM/VRAM triệt để trước khi lượng hóa GGUF\n",
                "import gc\n",
                "import torch\n",
                "\n",
                "try:\n",
                "    del model\n",
                "    del tokenizer\n",
                "    if 'trainer' in globals():\n",
                "        del trainer\n",
                "except Exception:\n",
                "    pass\n",
                "\n",
                "gc.collect()\n",
                "torch.cuda.empty_cache()\n",
                "gc.collect()\n",
                "print(\"✅ Đã giải phóng bộ nhớ RAM/VRAM hệ thống trước khi lượng hóa!\")\n",
                "\n",
                "# 4. Chuyển đổi thủ công sang GGUF bằng llama.cpp trực tiếp (Tránh 100% treo cell của Unsloth)\n",
                "print(\"⏳ Đang cài đặt llama.cpp và các thư viện phụ trợ...\")\n",
                "# Cài đặt các thư viện cần thiết cho việc convert GGUF\n",
                "!pip install gguf sentencepiece numpy\n",
                "\n",
                "# Clone llama.cpp nếu chưa có\n",
                "import os\n",
                "if not os.path.exists(\"llama.cpp\"):\n",
                "    !git clone --recursive https://github.com/ggerganov/llama.cpp\n",
                "\n",
                "# Cài đặt requirements của llama.cpp để đảm bảo đầy đủ thư viện\n",
                "!pip install -r llama.cpp/requirements.txt\n",
                "\n",
                "# Build llama.cpp\n",
                "print(\"⏳ Đang tiến hành build llama.cpp (Có thể mất 1 đến 3 phút)...\")\n",
                "!cd llama.cpp && make clean && make -j\n",
                "\n",
                "# Tiến hành convert sang f16 GGUF với log đầy đủ hiển thị theo thời gian thực\n",
                "print(\"⏳ Đang chuyển đổi sang định dạng f16 GGUF...\")\n",
                "output_f16 = \"/content/model-f16.gguf\"\n",
                "!python llama.cpp/convert_hf_to_gguf.py {merged_path} --outfile {output_f16}\n",
                "\n",
                "# Lượng hóa f16 sang q4_k_m\n",
                "print(\"⏳ Đang lượng hóa mô hình f16 sang Q4_K_M GGUF...\")\n",
                "output_q4 = \"/content/Qwen2.5-1.5B-ThoiSu-q4_k_m.gguf\"\n",
                "!./llama.cpp/llama-quantize {output_f16} {output_q4} q4_k_m\n",
                "\n",
                "print(f\"✅ Đã xuất mô hình GGUF lượng hóa thành công tại: {output_q4}\")\n",
                "print(\"💡 BẠN CÓ THỂ: Vào tab Files bên trái Colab, click chuột phải vào file '/content/Qwen2.5-1.5B-ThoiSu-q4_k_m.gguf' và chọn Download để tải trực tiếp bằng trình duyệt!\")\n",
                "\n",
                "# LỰA CHỌN 2 (Hữu ích để sao lưu): Copy sang Google Drive\n",
                "drive_gguf_path = \"/content/drive/MyDrive/Qwen2.5-1.5B-ThoiSu-q4_k_m.gguf\"\n",
                "# !cp {output_q4} {drive_gguf_path}\n"
            ]
            cell["source"] = new_source
            patched = True
            print("Target cell found and patched.")
            break

    if not patched:
        print("Warning: Cell with id 'export-gguf' was not found.")
        return

    with open(notebook_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print("Notebook updated successfully.")

if __name__ == "__main__":
    patch_notebook()
