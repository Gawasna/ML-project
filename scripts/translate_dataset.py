import json
import os
import sys
import time
import urllib.request
import urllib.error
import re

# Reconfigure stdout to use UTF-8 encoding to prevent crash on Windows terminal
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def translate_chunk(text, model="aya:8b", host="http://localhost:11434", max_retries=3, timeout=60):
    """
    Translates a single short chunk of text.
    Timeout is set to 60 seconds since chunks are guaranteed to be short.
    """
    url = f"{host}/api/generate"
    prompt = f"Translate the following Vietnamese text into natural and professional English. Provide only the translation, no introduction, no explanation, no quotes:\n\n{text}"
    
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.3
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
                
                # Post-clean any potential wrappers
                if translation.startswith('"') and translation.endswith('"'):
                    translation = translation[1:-1].strip()
                if translation.startswith("'") and translation.endswith("'"):
                    translation = translation[1:-1].strip()
                    
                return translation, True
        except urllib.error.URLError as e:
            print(f"  [Attempt {attempt}/{max_retries}] Connection warning: {e}", file=sys.stderr, flush=True)
            if attempt < max_retries:
                time.sleep(2 * attempt)
        except Exception as e:
            print(f"  [Attempt {attempt}/{max_retries}] Unexpected warning: {e}", file=sys.stderr, flush=True)
            if attempt < max_retries:
                time.sleep(2 * attempt)
                
    return "", False

def chunk_text(text, max_words=130):
    """
    Intelligently splits long Vietnamese text into chunks under max_words,
    keeping sentences intact to ensure translation quality.
    """
    # Split by sentence endings while retaining punctuation marks
    sentences = re.split(r'(?<=\. )|(?<=\? )|(?<=\! )|\n', text)
    chunks = []
    current_chunk = []
    current_words = 0
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        words_count = len(sentence.split())
        
        # If adding this sentence exceeds max_words, finalize current chunk
        if current_words + words_count > max_words:
            if current_chunk:
                chunks.append(" ".join(current_chunk))
            current_chunk = [sentence]
            current_words = words_count
        else:
            current_chunk.append(sentence)
            current_words += words_count
            
    if current_chunk:
        chunks.append(" ".join(current_chunk))
        
    return chunks

def translate_large_text(text, model="aya:8b"):
    """
    Splits long text into small chunks, translates each chunk sequentially,
    and merges the English translations. This completely avoids Ollama server 500 timeout.
    """
    chunks = chunk_text(text, max_words=130)
    num_chunks = len(chunks)
    
    if num_chunks > 1:
        print(f"  -> Article too long ({len(text.split())} words). Segmented into {num_chunks} chunks for safe translation.", flush=True)
        
    translations = []
    for idx, chunk in enumerate(chunks, 1):
        if num_chunks > 1:
            print(f"    * Translating segment {idx}/{num_chunks}...", end="", flush=True)
            
        rec_start = time.time()
        chunk_translation, ok = translate_chunk(chunk, model=model)
        chunk_elapsed = time.time() - rec_start
        
        if not ok:
            if num_chunks > 1:
                print(f" FAILED after {chunk_elapsed:.1f}s", flush=True)
            return "", False
            
        if num_chunks > 1:
            print(f" SUCCESS in {chunk_elapsed:.1f}s", flush=True)
            
        translations.append(chunk_translation)
        
    return " ".join(translations), True

def run_translation_test(input_path, output_path, limit=1000, model="aya:8b"):
    """
    Main runner for streaming dataset translation with real-time statistics reporting.
    Supports auto-resume if output file already contains translated records.
    """
    if not os.path.exists(input_path):
        print(f"Error: Input file {input_path} not found.", file=sys.stderr, flush=True)
        sys.exit(1)
        
    # Check for auto-resume
    translated_count = 0
    if os.path.exists(output_path):
        try:
            with open(output_path, 'r', encoding='utf-8') as fout_check:
                for line in fout_check:
                    if line.strip():
                        translated_count += 1
        except Exception as e:
            print(f"Warning checking output file: {e}", file=sys.stderr, flush=True)

    print(f"Starting real-time unbuffered translation of {limit} records using model '{model}'", flush=True)
    print(f"Reading from: {input_path}", flush=True)
    print(f"Saving to (append mode): {output_path}", flush=True)
    if translated_count > 0:
        print(f"--> Found {translated_count} already translated records. Resuming from record {translated_count + 1}...", flush=True)
    print("="*80, flush=True)
    
    start_time = time.time()
    success_count = translated_count
    fail_count = 0
    total_processed = translated_count
    durations = []
    
    # Open input file for reading, output file for appending ('a')
    with open(input_path, 'r', encoding='utf-8') as fin, open(output_path, 'a', encoding='utf-8') as fout:
        skipped = 0
        for line in fin:
            if not line.strip():
                continue
                
            # Skip already translated records for resume capability
            if skipped < translated_count:
                skipped += 1
                continue
                
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
                
            vietnamese_content = record.get("output", "")
            
            # Start timer for current translation
            rec_start_time = time.time()
            english_translation, ok = translate_large_text(vietnamese_content, model=model)
            duration = time.time() - rec_start_time
            
            total_processed += 1
            
            words_in = len(vietnamese_content.split())
            words_out = 0
            
            if ok and english_translation:
                success_count += 1
                durations.append(duration)
                words_out = len(english_translation.split())
                record["input"] = english_translation
            else:
                fail_count += 1
                record["input"] = "[TRANSLATION FAILED]"
                
            # Write immediately to ensure data persistence
            fout.write(json.dumps(record, ensure_ascii=False) + "\n")
            fout.flush()
            
            # Print live console stats for the current record
            status_str = "SUCCESS" if ok else "FAILED"
            words_speed = words_out / duration if (ok and duration > 0) else 0
            print(f"[{total_processed}/{limit}] Rec Size: {words_in} words -> {words_out} words | Latency: {duration:.2f}s | Speed: {words_speed:.1f} words/sec | Status: {status_str}", flush=True)
            
            # Print cumulative statistics
            elapsed = time.time() - start_time
            avg_latency = sum(durations) / len(durations) if durations else 0
            # Calculate overall speed considering only newly processed records in this run to avoid distortion
            newly_processed = total_processed - translated_count
            accumulated_speed = newly_processed / elapsed if elapsed > 0 else 0
            print(f"  └─► Cumulative Stats: Avg Latency: {avg_latency:.2f}s | Success Rate: {success_count/total_processed*100:.1f}% | Elapsed Time: {elapsed:.1f}s | Run Speed: {accumulated_speed:.3f} rec/sec", flush=True)
            print("-" * 80, flush=True)
            
            if total_processed >= limit:
                break
                
    total_elapsed = time.time() - start_time
    avg_latency = sum(durations) / len(durations) if durations else 0
    min_latency = min(durations) if durations else 0
    max_latency = max(durations) if durations else 0
    
    print("\n" + "="*80, flush=True)
    print("OLLAMA TRANSLATION TRIAL REPORT - FINAL REPORT", flush=True)
    print("="*80, flush=True)
    print(f"  - Total Processed Records    : {total_processed}", flush=True)
    print(f"  - Successfully Translated    : {success_count} ({ (success_count/total_processed)*100 if total_processed else 0:.2f}%)", flush=True)
    print(f"  - Failed Translations        : {fail_count} ({ (fail_count/total_processed)*100 if total_processed else 0:.2f}%)", flush=True)
    print(f"  - Total Elapsed Time         : {total_elapsed:.2f} seconds ({total_elapsed/60:.2f} minutes)", flush=True)
    print(f"  - Average Speed              : {total_processed/total_elapsed if total_elapsed > 0 else 0:.3f} records/second", flush=True)
    print(f"  - Record Latency Stats       : Avg: {avg_latency:.2f}s | Min: {min_latency:.2f}s | Max: {max_latency:.2f}s", flush=True)
    print(f"  - Saved Output JSONL to      : {output_path}", flush=True)
    print("="*80, flush=True)

if __name__ == "__main__":
    input_file = "extracted_the_gioi.jsonl"
    output_file = "translated_the_gioi.jsonl"
    
    run_translation_test(input_file, output_file, limit=1000)
