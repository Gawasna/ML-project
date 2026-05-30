import os
import json
import re
import sys

# Reconfigure stdout to support UTF-8 on Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

def count_words(text):
    if not text:
        return 0
    # Clean string and split by whitespace
    words = re.findall(r'\b\w+\b', text.lower())
    return len(words)

def analyze_jsonl_file(filepath):
    stats = {
        'filename': os.path.basename(filepath),
        'filesize_mb': os.path.getsize(filepath) / (1024 * 1024),
        'row_count': 0,
        'min_words_en': float('inf'),
        'max_words_en': 0,
        'avg_words_en': 0,
        'min_words_vi': float('inf'),
        'max_words_vi': 0,
        'avg_words_vi': 0,
        'total_words_en': 0,
        'total_words_vi': 0,
        'instructions': set()
    }
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                stats['row_count'] += 1
                
                # Instruction
                inst = data.get('instruction', '')
                if inst:
                    stats['instructions'].add(inst)
                
                # English Input
                en_text = data.get('input', '')
                en_words = count_words(en_text)
                stats['total_words_en'] += en_words
                stats['min_words_en'] = min(stats['min_words_en'], en_words)
                stats['max_words_en'] = max(stats['max_words_en'], en_words)
                
                # Vietnamese Output
                vi_text = data.get('output', '')
                vi_words = count_words(vi_text)
                stats['total_words_vi'] += vi_words
                stats['min_words_vi'] = min(stats['min_words_vi'], vi_words)
                stats['max_words_vi'] = max(stats['max_words_vi'], vi_words)
            except Exception as e:
                pass
                
    if stats['row_count'] > 0:
        stats['avg_words_en'] = stats['total_words_en'] / stats['row_count']
        stats['avg_words_vi'] = stats['total_words_vi'] / stats['row_count']
    else:
        stats['min_words_en'] = 0
        stats['min_words_vi'] = 0
        
    return stats

def main():
    prepared_dir = r"C:\Users\hungl\Documents\trae_projects\ML-project\data\train\prepared"
    output_report = r"C:\Users\hungl\Documents\trae_projects\ML-project\docs\prepared_stats_detailed.txt"
    
    if not os.path.exists(prepared_dir):
        print(f"Directory not found: {prepared_dir}")
        return
        
    files = [f for f in os.listdir(prepared_dir) if f.endswith('.jsonl')]
    print(f"Found {len(files)} JSONL files in prepared directory.")
    
    all_stats = []
    total_rows = 0
    total_size_mb = 0.0
    
    for filename in sorted(files):
        filepath = os.path.join(prepared_dir, filename)
        print(f"Analyzing {filename}...")
        stats = analyze_jsonl_file(filepath)
        all_stats.append(stats)
        total_rows += stats['row_count']
        total_size_mb += stats['filesize_mb']
        
    # Write report to file to prevent console encoding issues
    with open(output_report, 'w', encoding='utf-8') as out:
        out.write("="*80 + "\n")
        out.write("DETAILED DATASET STATISTICS REPORT\n")
        out.write("="*80 + "\n")
        out.write(f"Total files: {len(files)}\n")
        out.write(f"Total Rows (samples): {total_rows:,}\n")
        out.write(f"Total Size: {total_size_mb:.2f} MB\n")
        out.write("="*80 + "\n\n")
        
        for stats in all_stats:
            out.write(f"File: {stats['filename']}\n")
            out.write(f"  - Size: {stats['filesize_mb']:.3f} MB\n")
            out.write(f"  - Rows: {stats['row_count']:,}\n")
            out.write(f"  - Unique Instructions: {list(stats['instructions'])}\n")
            out.write(f"  - English input (words): Min={stats['min_words_en']}, Max={stats['max_words_en']}, Avg={stats['avg_words_en']:.2f}\n")
            out.write(f"  - Vietnamese output (words): Min={stats['min_words_vi']}, Max={stats['max_words_vi']}, Avg={stats['avg_words_vi']:.2f}\n")
            out.write("-"*80 + "\n")
            
    print(f"Successfully generated detailed report at: {output_report}")

if __name__ == "__main__":
    main()
