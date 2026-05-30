import json
import os
import sys
import time
import urllib.request
import urllib.error
import math
from collections import Counter

# Reconfigure stdout to use UTF-8 encoding to prevent crash on Windows terminal
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def ngrams(sequence, n):
    return [tuple(sequence[i:i+n]) for i in range(len(sequence)-n+1)]

def calculate_bleu(reference, candidate):
    # Basic tokenization by lowering and splitting
    # Remove basic punctuation for clean n-gram evaluation
    import string
    translator = str.maketrans('', '', string.punctuation)
    ref_tokens = reference.lower().translate(translator).split()
    cand_tokens = candidate.lower().translate(translator).split()
    
    if not cand_tokens or not ref_tokens:
        return 0.0
        
    ref_len = len(ref_tokens)
    cand_len = len(cand_tokens)
    
    if cand_len > ref_len:
        bp = 1.0
    else:
        bp = math.exp(1 - ref_len / cand_len) if cand_len > 0 else 0.0
        
    precisions = []
    for n in range(1, 5):
        ref_ngrams = ngrams(ref_tokens, n)
        cand_ngrams = ngrams(cand_tokens, n)
        
        if not cand_ngrams:
            precisions.append(0.0)
            continue
            
        ref_counts = Counter(ref_ngrams)
        cand_counts = Counter(cand_ngrams)
        
        clipped_counts = {ngram: min(count, ref_counts[ngram]) for ngram, count in cand_counts.items()}
        precision = sum(clipped_counts.values()) / len(cand_ngrams)
        precisions.append(precision)
        
    # Smoothing for zero precision in higher n-grams
    precisions = [p if p > 0 else 0.1 for p in precisions]
        
    s = sum(math.log(p) for p in precisions)
    score = bp * math.exp(s / 4)
    return score

def translate_en_to_vi(text, model="qwen2.5:3b", host="http://127.0.0.1:11434", max_retries=3, timeout=60):
    url = f"{host}/api/generate"
    prompt = f"Dịch đoạn văn tiếng Anh sau đây sang tiếng Việt một cách tự nhiên và chuyên nghiệp. Chỉ cung cấp duy nhất bản dịch, không thêm lời mở đầu, giải thích hay đặt trong dấu ngoặc kép:\n\n{text}"
    
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.3,
            "num_ctx": 4096
        }
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=data,
        headers={'Content-Type': 'application/json'}
    )
    
    for attempt in range(1, max_retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                res_data = response.read().decode('utf-8')
                res_obj = json.loads(res_data)
                translation = res_obj.get("response", "").strip()
                
                # Remove potential surrounding double quotes
                if translation.startswith('"') and translation.endswith('"'):
                    translation = translation[1:-1].strip()
                if translation.startswith("'") and translation.endswith("'"):
                    translation = translation[1:-1].strip()
                    
                return translation, True
        except Exception as e:
            print(f"  [Attempt {attempt}/{max_retries}] Exception: {e}", file=sys.stderr, flush=True)
            if attempt < max_retries:
                time.sleep(2 * attempt)
                
    return "", False

def run_baseline_validation(input_path, output_path, limit=5, model="qwen2.5:3b"):
    if not os.path.exists(input_path):
        print(f"Error: Input file {input_path} not found.", file=sys.stderr)
        sys.exit(1)
        
    records = []
    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    records.append(json.loads(line))
                except Exception:
                    pass
                    
    # Take the first N records
    eval_records = records[:limit]
    
    print(f"Evaluating baseline performance for {model} on {len(eval_records)} samples...")
    
    results = []
    total_bleu = 0.0
    total_time = 0.0
    
    for idx, rec in enumerate(eval_records, 1):
        eng_text = rec.get("input", "")
        ref_vi = rec.get("output", "")
        
        print(f"[{idx}/{len(eval_records)}] Translating article ({len(eng_text.split())} words)...")
        start = time.time()
        translated_vi, ok = translate_en_to_vi(eng_text, model=model)
        elapsed = time.time() - start
        
        if not ok:
            print(f"  -> Translation FAILED")
            results.append({
                "index": idx,
                "english": eng_text,
                "reference": ref_vi,
                "candidate": "[TRANSLATION FAILED]",
                "bleu": 0.0,
                "latency": elapsed,
                "status": "FAILED"
            })
            continue
            
        bleu = calculate_bleu(ref_vi, translated_vi)
        total_bleu += bleu
        total_time += elapsed
        
        print(f"  -> SUCCESS | BLEU: {bleu*100:.2f}% | Latency: {elapsed:.2f}s")
        results.append({
            "index": idx,
            "english": eng_text,
            "reference": ref_vi,
            "candidate": translated_vi,
            "bleu": bleu,
            "latency": elapsed,
            "status": "SUCCESS"
        })
        
    avg_bleu = total_bleu / len(eval_records) if eval_records else 0
    avg_latency = total_time / len(eval_records) if eval_records else 0
    
    # Save validation report in markdown
    report = []
    report.append(f"# English to Vietnamese Translation Baseline Report")
    report.append(f"")
    report.append(f"- **Validation Date**: 2026-05-30")
    report.append(f"- **Evaluated Model**: `{model}` (Local via Ollama)")
    report.append(f"- **Dataset Path**: `{input_path}`")
    report.append(f"- **Evaluation Samples**: {len(eval_records)}")
    report.append(f"")
    report.append(f"## Metrics Summary")
    report.append(f"")
    report.append(f"| Metric | Value | Description |")
    report.append(f"| :--- | :--- | :--- |")
    report.append(f"| **Average BLEU Score** | {avg_bleu*100:.2f}% | Multi-ngram precision overlap |")
    report.append(f"| **Average Latency** | {avg_latency:.2f}s | Processing speed per article |")
    report.append(f"")
    report.append(f"## Detailed Sample Comparison")
    report.append(f"")
    
    for res in results:
        report.append(f"### Sample #{res['index']}")
        report.append(f"")
        report.append(f"- **Status**: `{res['status']}`")
        report.append(f"- **Latency**: `{res['latency']:.2f} seconds`")
        report.append(f"- **BLEU Score**: `{res['bleu']*100:.2f}%`")
        report.append(f"")
        report.append(f"#### 1. Source English Content")
        report.append(f"> {res['english']}")
        report.append(f"")
        report.append(f"#### 2. Translations Side-by-Side")
        report.append(f"")
        report.append(f"| Model: `{model}` (Baseline) | Reference (a2.jsonl) |")
        report.append(f"| :--- | :--- |")
        # Replace newlines with <br> for table markdown compatibility
        cand_fmt = res['candidate'].replace('\n', '<br>')
        ref_fmt = res['reference'].replace('\n', '<br>')
        report.append(f"| {cand_fmt} | {ref_fmt} |")
        report.append(f"")
        report.append(f"---")
        report.append(f"")
        
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(report))
        
    print(f"\nBaseline validation finished successfully!")
    print(f"Average BLEU: {avg_bleu*100:.2f}%")
    print(f"Average Latency: {avg_latency:.2f}s")
    print(f"Report saved to: {output_path}")

if __name__ == "__main__":
    input_file = "C:/Users/hungl/Documents/trae_projects/ML-project/temp/labs-ml/a2.jsonl"
    output_file = "C:/Users/hungl/Documents/trae_projects/ML-project/docs/baseline_en2vi_report.md"
    run_baseline_validation(input_file, output_file, limit=5)
