import json
import os
import sys
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter

# Set UTF-8 encoding for Windows terminal
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def calculate_stats(counter):
    """Calculate statistical metrics from a Counter of word counts"""
    total_samples = sum(counter.values())
    if total_samples == 0:
        return 0, 0, 0, 0, 0
        
    # Expand to sorted list to calculate median
    all_lengths = sorted(counter.elements())
    
    min_val = all_lengths[0]
    max_val = all_lengths[-1]
    mean_val = sum(k * v for k, v in counter.items()) / total_samples
    median_val = all_lengths[total_samples // 2]
    
    return total_samples, min_val, max_val, mean_val, median_val

def main():
    cleaned_dir = r"C:\Users\hungl\Documents\trae_projects\ML-project\data\train\cleaned"
    output_dir = r"C:\Users\hungl\Documents\trae_projects\ML-project\docs\plots"
    output_image_path = os.path.join(output_dir, "dataset_length_distribution.png")
    
    os.makedirs(output_dir, exist_ok=True)
    
    print("=" * 80)
    print("ANALYZING DATASET WORD LENGTH DISTRIBUTIONS (O(1) SPACE OPTIMIZED)")
    print("=" * 80)
    
    files = [f for f in os.listdir(cleaned_dir) if f.endswith(".jsonl")]
    
    dataset_counters = {}
    global_counter = Counter()
    
    for file_name in files:
        file_path = os.path.join(cleaned_dir, file_name)
        print(f"Processing: {file_name}...")
        
        file_counter = Counter()
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                    eng_text = record.get("input", "").strip()
                    if eng_text:
                        word_count = len(eng_text.split())
                        file_counter[word_count] += 1
                        global_counter[word_count] += 1
                except Exception:
                    pass
                    
        dataset_counters[file_name] = file_counter
        
    print("\n" + "=" * 80)
    print("STATISTICAL SUMMARY REPORT")
    print("=" * 80)
    print(f"{'Dataset File':<30} | {'Total':<10} | {'Min':<5} | {'Max':<5} | {'Mean':<6} | {'Median':<6}")
    print("-" * 75)
    
    for file_name, counter in dataset_counters.items():
        total, min_v, max_v, mean_v, median_v = calculate_stats(counter)
        print(f"{file_name:<30} | {total:<10,} | {min_v:<5} | {max_v:<5} | {mean_v:<6.2f} | {median_v:<6.1f}")
        
    total_g, min_g, max_v_g, mean_g, median_g = calculate_stats(global_counter)
    print("-" * 75)
    print(f"{'GLOBAL TOTAL':<30} | {total_g:<10,} | {min_g:<5} | {max_v_g:<5} | {mean_g:<6.2f} | {median_g:<6.1f}")
    print("=" * 80)
    
    # -------------------------------------------------------------
    # PLOTTING CHARTS (High Resolution, Modern Design)
    # -------------------------------------------------------------
    print("\nGenerating high-resolution plots...")
    
    # Set modern plot style
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['text.color'] = '#1e293b'
    plt.rcParams['axes.labelcolor'] = '#1e293b'
    plt.rcParams['xtick.color'] = '#475569'
    plt.rcParams['ytick.color'] = '#475569'
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6), dpi=300)
    fig.patch.set_facecolor('#f8fafc') # premium light slate gray background
    
    # Plot 1: Overall Histogram Distribution
    ax1.set_facecolor('#ffffff')
    lengths = sorted(global_counter.keys())
    counts = [global_counter[l] for l in lengths]
    
    # Using a elegant deep indigo gradient look
    ax1.bar(lengths, counts, color='#4f46e5', width=0.8, alpha=0.85, edgecolor='#3730a3', linewidth=0.5, label='Sentence Count')
    
    # Highlight mean & median
    ax1.axvline(mean_g, color='#ef4444', linestyle='dashed', linewidth=1.5, label=f'Mean: {mean_g:.2f}')
    ax1.axvline(median_g, color='#f59e0b', linestyle='dotted', linewidth=2, label=f'Median: {median_g:.1f}')
    
    ax1.set_title("Overall Sentence Word Count Distribution", fontsize=14, fontweight='bold', pad=15)
    ax1.set_xlabel("Sentence Word Length (English Input)", fontsize=12, labelpad=10)
    ax1.set_ylabel("Frequency (Number of Sentences)", fontsize=12, labelpad=10)
    ax1.set_xlim(0, 60)
    ax1.grid(True, linestyle='--', alpha=0.3, color='#94a3b8')
    ax1.legend(frameon=True, facecolor='#ffffff', edgecolor='#e2e8f0')
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.spines['left'].set_color('#cbd5e1')
    ax1.spines['bottom'].set_color('#cbd5e1')
    
    # Plot 2: Density Comparison across major datasets (normalized to 100% total per file)
    ax2.set_facecolor('#ffffff')
    
    # Focus on files with > 500 records to keep plot clean
    colors = ['#06b6d4', '#10b981', '#f43f5e', '#3b82f6', '#8b5cf6']
    color_idx = 0
    
    for file_name, counter in dataset_counters.items():
        total_records = sum(counter.values())
        if total_records < 500:
            continue # skip tiny datasets to keep chart neat
            
        x_vals = sorted(counter.keys())
        # Calculate percentage (density) for fair comparison
        y_vals = [counter[x] / total_records * 100 for x in x_vals]
        
        # Smooth line via rolling average or plot directly
        ax2.plot(x_vals, y_vals, label=f"{file_name} ({total_records:,} recs)", color=colors[color_idx % len(colors)], linewidth=2, alpha=0.85)
        ax2.fill_between(x_vals, y_vals, alpha=0.1, color=colors[color_idx % len(colors)])
        color_idx += 1
        
    ax2.set_title("Density Comparison Across Datasets (Normalized %)", fontsize=14, fontweight='bold', pad=15)
    ax2.set_xlabel("Sentence Word Length", fontsize=12, labelpad=10)
    ax2.set_ylabel("Proportion of Dataset (%)", fontsize=12, labelpad=10)
    ax2.set_xlim(0, 60)
    ax2.grid(True, linestyle='--', alpha=0.3, color='#94a3b8')
    ax2.legend(frameon=True, facecolor='#ffffff', edgecolor='#e2e8f0', fontsize=9)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.spines['left'].set_color('#cbd5e1')
    ax2.spines['bottom'].set_color('#cbd5e1')
    
    # Adjust layout and save
    plt.tight_layout()
    plt.savefig(output_image_path, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    
    print(f"\nSuccessfully generated and saved high-resolution distribution plot at:")
    print(f"  {output_image_path}")
    print("=" * 80)

if __name__ == "__main__":
    main()
