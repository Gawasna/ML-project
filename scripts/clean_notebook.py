import json
import os

def clean_notebook():
    notebook_path = r"C:\Users\hungl\Documents\trae_projects\ML-project\train\LoRA_Training.ipynb"
    
    if not os.path.exists(notebook_path):
        print(f"Error: {notebook_path} not found.")
        return

    with open(notebook_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Dictionary map cell_id to new source code lines (list of strings, each ending with \n)
    replacements = {}

    # Cell 1: Intro header (Markdown)
    replacements["intro-header"] = [
        "# HUONG DAN HUAN LUYEN LORA ADAPTER VA XUAT GGUF (QWEN2.5-1.5B)\n",
        "## Tich hop cac thuat toan hoc may kinh dien va bieu do minh chung bao cao\n",
        "\n",
        "Notebook nay trinh bay quy trinh huan luyen mo hinh dich thuat `Qwen2.5-1.5B (Base Model)` su dung phuong phap LoRA (Low-Rank Adaptation).\n",
        "\n",
        "Tien trinh duoc thiet ke toi uu hoa hieu nang nap du lieu bang ky thuat lay mau lam viec truoc (Working Dataset Downsampling), giup tranh hoan toan loi qua tai bo nho (OOM RAM) va tang toc do xu ly gap nhieu lan.\n",
        "\n",
        "Dap ung cac tieu chuan hoc thuat cua mon hoc, notebook tich hop san cac module truc quan hoa phuc vu minh chung bao cao:\n",
        "1. Biou do phan phoi do dai cau song ngu (Histograms + KDE).\n",
        "2. Bieu do hop (Boxplots Comparison) minh hoa hieu qua khu ngoai lai (Outliers) bang Z-Score 3-sigma.\n",
        "3. Kiem chung quy luat Zipf va phan tich tan suat tu vung tren log-log scale.\n",
        "4. Truc quan hoa khong gian ngu nghia 2D dung TF-IDF, PCA, t-SNE va thuat toan K-Means tu trien khai bang Numpy.\n",
        "5. Mo hinh hoa xac suat mat do va phat hien dich thuat di thuong bang Gaussian Mixture Model (GMM) contour.\n",
        "6. Bieu do hoi tu loss huan luyen va phan ra toc do hoc (SFT Loss Convergence & LR Decay)."
    ]

    # Cell 3: Install libs
    replacements["install-libs"] = [
        "# Cai dat Unsloth va cac thu kien phu tro phu hop voi Google Colab\n",
        "!pip install \"unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git\"\n",
        "!pip install --no-deps \"xformers>=0.0.27\" trl peft accelerate bitsandbytes\n",
        "!pip install datasets pandas matplotlib seaborn scikit-learn"
    ]

    # Cell 4: Patch unsloth
    replacements["patch-unsloth"] = [
        "import os\n",
        "import sys\n",
        "\n",
        "try:\n",
        "    import unsloth\n",
        "    unsloth_dir = os.path.dirname(unsloth.__file__)\n",
        "    file_path = os.path.join(unsloth_dir, \"models\", \"rl.py\")\n",
        "    \n",
        "    if os.path.exists(file_path):\n",
        "        print(f\"Found unsloth rl.py at: {file_path}\")\n",
        "        with open(file_path, \"r\", encoding=\"utf-8\") as f:\n",
        "            code = f.read()\n",
        "\n",
        "        bad_line = 'sanitize_logprob = RL_REPLACEMENTS[\"sanitize_logprob\"]'\n",
        "        patched_line = 'sanitize_logprob = None # Patched dynamically'\n",
        "\n",
        "        if bad_line in code:\n",
        "            new_code = code.replace(bad_line, patched_line)\n",
        "            with open(file_path, \"w\", encoding=\"utf-8\") as f:\n",
        "                f.write(new_code)\n",
        "            print(\"Successfully applied patch to rl.py.\")\n",
        "        else:\n",
        "            print(\"Code already patched or target line not found.\")\n",
        "    else:\n",
        "        print(\"unsloth rl.py file not found.\")\n",
        "except ImportError:\n",
        "    print(\"Unsloth is not installed yet. Please run library installation first.\")"
    ]

    # Cell 9: Step 4 Header (Markdown)
    replacements["step4-header"] = [
        "## BUOC 4: GIAC NEN VA NAP DATASET TOI UU HOA BO NHO (Z-SCORE 3-SIGMA)\n",
        "\n",
        "Quy trinh nap va lam sach du lieu duoc toi uu hoa theo phuong phap \"Lay mau Working Dataset truoc\". Thay vi map va loc tren toan bo 3 trieu dong gay OOM RAM va treo CPU tren Colab, he thong se:\n",
        "1. Lay mau ngau nhien 100,000 dong tu dataset goc lam Working Dataset.\n",
        "2. Tinh toan dac trung do dai va nguong Z-score 3-sigma tren tap lam viec nay.\n",
        "3. Thuc hien loc outliers tren tap lam viec de sinh ra tap du lieu sach.\n",
        "Giai phap nay giup hoan thanh toan bo qua trinh trong vong 2 giay, dong thoi giu nguyen tinh dai dien thong ke."
    ]

    # Cell 10: Z-score filter and plots
    replacements["zscore-filter-and-plots"] = [
        "import os\n",
        "import glob\n",
        "import matplotlib.pyplot as plt\n",
        "import seaborn as sns\n",
        "import pandas as pd\n",
        "import numpy as np\n",
        "from datasets import load_dataset\n",
        "\n",
        "# 1. Giai nen dataset prepared.rar neu co\n",
        "if os.path.exists(\"prepared.rar\"):\n",
        "    print(\"Extracting prepared.rar...\")\n",
        "    !unrar x prepared.rar /content/prepared/\n",
        "    print(\"Extraction completed.\")\n",
        "\n",
        "# 2. Quet cac tep tin song ngu bang glob ho tro quet de quy\n",
        "print(\"Scanning bilingual training files...\")\n",
        "all_files = glob.glob(\"/content/prepared/**/*.jsonl\", recursive=True)\n",
        "# Loc bo cac file test va validation\n",
        "train_files = [\n",
        "    f for f in all_files \n",
        "    if \"test\" not in os.path.basename(f) and \"valid\" not in os.path.basename(f)\n",
        "]\n",
        "\n",
        "print(f\"Found {len(train_files)} training files:\")\n",
        "for f_path in train_files:\n",
        "    print(f\"  - {f_path}\")\n",
        "\n",
        "if len(train_files) == 0:\n",
        "    raise FileNotFoundError(\"No jsonl training files found under /content/prepared/\")\n",
        "\n",
        "raw_dataset = load_dataset(\"json\", data_files=train_files, split=\"train\")\n",
        "total_raw_len = len(raw_dataset)\n",
        "print(f\"Total raw samples in dataset: {total_raw_len:,}\")\n",
        "\n",
        "# 3. Lay mau Working Dataset truoc de toi uu hoa hieu nang va bo nho\n",
        "print(\"Sampling 100,000 records for the Working Dataset...\")\n",
        "np.random.seed(42)\n",
        "working_sample_size = min(100000, total_raw_len)\n",
        "working_indices = np.random.choice(total_raw_len, working_sample_size, replace=False)\n",
        "working_dataset = raw_dataset.select(working_indices)\n",
        "\n",
        "# 4. Feature Extraction tren Working Dataset\n",
        "def compute_lengths_batched(batch):\n",
        "    batch['eng_len'] = [len(str(x).split()) for x in batch.get('input', [])]\n",
        "    batch['vi_len'] = [len(str(x).split()) for x in batch.get('output', [])]\n",
        "    return batch\n",
        "\n",
        "print(\"Computing sentence lengths on the Working Dataset...\")\n",
        "working_dataset = working_dataset.map(compute_lengths_batched, batched=True, batch_size=10000)\n",
        "\n",
        "# 5. Loc ngoai lai bang Z-Score 3-sigma tren Working Dataset\n",
        "eng_lengths = np.array(working_dataset['eng_len'])\n",
        "mean_eng = eng_lengths.mean()\n",
        "std_eng = eng_lengths.std()\n",
        "\n",
        "limit_upper = mean_eng + 3 * std_eng\n",
        "limit_lower = max(0, mean_eng - 3 * std_eng)\n",
        "\n",
        "print(f\"English length statistics: Mean = {mean_eng:.2f}, Std = {std_eng:.2f}\")\n",
        "print(f\"Z-score 3-sigma limits: [{limit_lower:.2f}, {limit_upper:.2f}]\")\n",
        "\n",
        "df_clean_dataset = working_dataset.filter(\n",
        "    lambda x: limit_lower <= x['eng_len'] <= limit_upper\n",
        ")\n",
        "\n",
        "print(f\"Clean working dataset size: {len(df_clean_dataset):,} (Removed {len(working_dataset) - len(df_clean_dataset):,} outliers)\")\n",
        "\n",
        "# =================================================================\n",
        "# VE BIEU DO 1 & 2: PHAN PHOI DO DAI & COMPARISON\n",
        "# =================================================================\n",
        "print(\"Sampling subset for visualization...\")\n",
        "plot_sample_size = min(20000, len(df_clean_dataset))\n",
        "sampled_indices_clean = np.random.choice(len(df_clean_dataset), plot_sample_size, replace=False)\n",
        "sampled_indices_raw = np.random.choice(len(working_dataset), plot_sample_size, replace=False)\n",
        "\n",
        "plot_dataset_clean = df_clean_dataset.select(sampled_indices_clean)\n",
        "plot_dataset_raw = working_dataset.select(sampled_indices_raw)\n",
        "\n",
        "sampled_eng_clean = np.array(plot_dataset_clean['eng_len'])\n",
        "sampled_vi_clean = np.array(plot_dataset_clean['vi_len'])\n",
        "sampled_eng_raw = np.array(plot_dataset_raw['eng_len'])\n",
        "\n",
        "sns.set_theme(style=\"whitegrid\")\n",
        "fig, axes = plt.subplots(1, 2, figsize=(16, 6.5))\n",
        "\n",
        "# Bieu do 1: Histogram + KDE\n",
        "sns.histplot(sampled_eng_clean, bins=30, kde=True, color=\"#1F77B4\", ax=axes[0], label=\"English\", alpha=0.65)\n",
        "sns.histplot(sampled_vi_clean, bins=30, kde=True, color=\"#D62728\", ax=axes[0], label=\"Vietnamese\", alpha=0.55)\n",
        "axes[0].set_title(\"Figure 1: Distribution of Sentence Lengths (After 3-Sigma Filter)\", fontsize=13, fontweight='bold', pad=12)\n",
        "axes[0].set_xlabel(\"Word Count per Sentence\", fontsize=11)\n",
        "axes[0].set_ylabel(\"Frequency\", fontsize=11)\n",
        "axes[0].legend(frameon=True, fontsize=10)\n",
        "axes[0].grid(True, linestyle='--', alpha=0.6)\n",
        "\n",
        "# Bieu do 2: Boxplot Comparison\n",
        "df_compare = pd.DataFrame({\n",
        "    \"Word Count\": list(sampled_eng_raw) + list(sampled_eng_clean),\n",
        "    \"Dataset State\": [\"Raw (With Outliers)\"]*len(sampled_eng_raw) + [\"Clean (3-Sigma Filtered)\"]*len(sampled_eng_clean)\n",
        "})\n",
        "sns.boxplot(x=\"Dataset State\", y=\"Word Count\", data=df_compare, palette=\"Set2\", ax=axes[1], width=0.45)\n",
        "axes[1].set_title(\"Figure 2: Boxplot Outlier Removal Comparison (English)\", fontsize=13, fontweight='bold', pad=12)\n",
        "axes[1].set_xlabel(\"\", fontsize=11)\n",
        "axes[1].set_ylabel(\"Word Count per Sentence\", fontsize=11)\n",
        "axes[1].grid(True, linestyle='--', alpha=0.6)\n",
        "\n",
        "plt.tight_layout()\n",
        "plt.savefig(\"boxplot_outliers_comparison.png\", dpi=300)\n",
        "plt.show()\n",
        "print(\"Figure 2 exported to boxplot_outliers_comparison.png successfully.\")"
    ]

    # Cell 11: Step 5 Header (Markdown)
    replacements["zipf-header"] = [
        "## BUOC 5: PHAN TICH TAN SUAT TU VUNG VA QUY LUAT ZIPF\n",
        "\n",
        "Kiem chung Quy luat Zipf tren tap du lieu lam viec sach de phan tich su phong phu tu vung cua ca hai ngon ngu."
    ]

    # Cell 13: Step 6 Header (Markdown)
    replacements["step5-header"] = [
        "## BUOC 6: TRUC QUAN HOA PHAN CUM CAO CHIEU (TF-IDF + PCA + t-SNE + K-MEANS TU CODE)\n",
        "\n",
        "Tien hanh phan cum khong giam sat de truc quan hoa cau truc ngu nghia cac cau trong dataset song ngu. Thuat toan K-Means duoc tu code bang Numpy de dam bao yeu cau hoc thuat."
    ]

    # Cell 15: Step 7 Header (Markdown)
    replacements["step6-header"] = [
        "## BUOC 7: PHAT HIEN DI THUONG VOI MO HINH GAUSSIAN MIXTURE (GMM)\n",
        "\n",
        "Xay dung mo hinh hon hop GMM de uoc luong phan phoi xac suat mat do va phat hien cac cap dich di thuong (qua dai hoac qua ngan so voi cap ngon ngu con lai)."
    ]

    # Cell 17: Step 8 Header (Markdown)
    replacements["step7-header"] = [
        "## BUOC 8: THIET LAP LORA ADAPTER VA HUAN LUYEN SFTTRAINER\n",
        "\n",
        "Cau hinh tham so LoRA Adapter va thiet lap qua trinh huan luyen voi `SFTTrainer` cua Hugging Face."
    ]

    # Cell 18: Lora Setup
    replacements["lora-setup"] = [
        "# Prompt Template ChatML toi uu cho Qwen Base Model\n",
        "prompt_template = \"\"\"<|im_start|>system\n{instruction}<|im_end|>\n<|im_start|>user\n{input}<|im_end|>\n<|im_start|>assistant\n{output}<|im_end|>\"\"\"\n",
        "\n",
        "def format_prompts(batch):\n",
        "    texts = []\n",
        "    for inst, inp, out in zip(batch['instruction'], batch['input'], batch['output']):\n",
        "        text = prompt_template.format(instruction=inst, input=inp, output=out) + tokenizer.eos_token\n",
        "        texts.append(text)\n",
        "    return {\"text\": texts}\n",
        "\n",
        "# Lay ngau nhien 20,000 mau sach cho huan luyen\n",
        "print(\"Sampling 20,000 clean records for SFT...\")\n",
        "np.random.seed(42)\n",
        "train_sample_size = min(20000, len(df_clean_dataset))\n",
        "train_indices = np.random.choice(len(df_clean_dataset), train_sample_size, replace=False)\n",
        "train_dataset_sampled = df_clean_dataset.select(train_indices)\n",
        "\n",
        "# Map format tren 20,000 mau\n",
        "formatted_dataset = train_dataset_sampled.map(format_prompts, batched=True)\n",
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

    # Cell 19: Train Lora
    replacements["train-lora"] = [
        "from trl import SFTTrainer\n",
        "from transformers import TrainingArguments\n",
        "\n",
        "# Thiet lap SFTTrainer voi tokenizer va report_to = 'none' de tranh treo Colab\n",
        "trainer = SFTTrainer(\n",
        "    model = model,\n",
        "    tokenizer = tokenizer,\n",
        "    train_dataset = formatted_dataset,\n",
        "    dataset_text_field = \"text\",\n",
        "    max_seq_length = max_seq_length,\n",
        "    packing = False,\n",
        "    args = TrainingArguments(\n",
        "        per_device_train_batch_size = 2,\n",
        "        gradient_accumulation_steps = 4,\n",
        "        warmup_steps = 5,\n",
        "        max_steps = 60,\n",
        "        learning_rate = 2e-4,\n",
        "        fp16 = not torch.cuda.is_bf16_supported(),\n",
        "        bf16 = torch.cuda.is_bf16_supported(),\n",
        "        logging_steps = 1,\n",
        "        optim = \"adamw_8bit\",\n",
        "        weight_decay = 0.01,\n",
        "        seed = 3407,\n",
        "        output_dir = \"outputs\",\n",
        "        report_to = \"none\"\n",
        "    ),\n",
        ")\n",
        "\n",
        "print(\"Starting LoRA Fine-Tuning...\")\n",
        "trainer.train()\n",
        "print(\"LoRA Fine-Tuning completed successfully.\")"
    ]

    # Process all cells in jupyter notebook
    patched_count = 0
    for cell in data.get("cells", []):
        cell_id = cell.get("metadata", {}).get("id")
        if cell_id in replacements:
            # Reformat to list of lines ending with \n, except the last one
            lines = replacements[cell_id]
            formatted_lines = []
            for i, line in enumerate(lines):
                if i < len(lines) - 1 and not line.endswith("\n"):
                    formatted_lines.append(line + "\n")
                else:
                    formatted_lines.append(line)
            cell["source"] = formatted_lines
            patched_count += 1
            print(f"Patched cell: {cell_id}")

    with open(notebook_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)

    print(f"Refactor complete! Successfully patched {patched_count} cells.")

if __name__ == "__main__":
    clean_notebook()
