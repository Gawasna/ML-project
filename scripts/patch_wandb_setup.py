import json
import os

def patch_wandb_setup():
    notebook_path = r"C:\Users\hungl\Documents\trae_projects\ML-project\train\LoRA_Training.ipynb"
    if not os.path.exists(notebook_path):
        print(f"Error: Notebook not found at {notebook_path}")
        return

    with open(notebook_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    cells = data.get("cells", [])
    new_cells = []
    
    patched_install = False
    inserted_login = False

    for cell in cells:
        cell_id = cell.get("metadata", {}).get("id")
        
        # 1. Cập nhật cài đặt thư viện ở Bước 1
        if cell_id == "install-libs":
            source = cell.get("source", [])
            new_source = []
            for line in source:
                if "scikit-learn" in line and "wandb" not in line:
                    line = line.replace("scikit-learn", "scikit-learn wandb")
                new_source.append(line)
            cell["source"] = new_source
            patched_install = True
            print("Step 1: Added 'wandb' to installation library cell.")
            
        # 2. Chèn cell đăng nhập WandB trước cell chạy train-lora
        if cell_id == "train-lora":
            # Tạo cell Markdown hướng dẫn
            wandb_md_cell = {
                "cell_type": "markdown",
                "metadata": {
                    "id": "wandb-login-md"
                },
                "source": [
                    "### HƯỚNG DẪN KẾT NỐI VÀ ĐĂNG NHẬP WEIGHTS & BIASES (WANDB)\n",
                    "Để theo dõi trực quan quá trình huấn luyện (Loss, Learning Rate, Perplexity) theo thời gian thực và lưu trữ báo cáo học thuật, vui lòng chạy cell dưới đây và nhập mã API Key từ tài khoản Weights & Biases của bạn."
                ]
            }
            # Tạo cell Code đăng nhập
            wandb_code_cell = {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {
                    "id": "wandb-login-code"
                },
                "outputs": [],
                "source": [
                    "import wandb\n",
                    "# Thực hiện đăng nhập chủ động để tránh treo cell khi khởi chạy Trainer\n",
                    "wandb.login()"
                ]
            }
            new_cells.append(wandb_md_cell)
            new_cells.append(wandb_code_cell)
            inserted_login = True
            print("Step 8: Inserted active WandB login cells before the trainer cell.")
            
        new_cells.append(cell)

    if not patched_install or not inserted_login:
        print(f"Warning: Patching incomplete. Install patch: {patched_install}, Login insert: {inserted_login}")
        return

    data["cells"] = new_cells

    with open(notebook_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print("Notebook updated successfully with proactive WandB setup.")

if __name__ == "__main__":
    patch_wandb_setup()
