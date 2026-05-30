import os
import re
import glob
import json
import sys

# Ensure UTF-8 encoding for stdout on Windows to prevent crash
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def convert_v2_to_jsonl(corpus_path, output_file_path, topic="thời sự"):
    """
    Converts SGML files from EVBCorpus v2.0 into a flat JSONL format.
    Each JSON line has: topic, instruction, input (English), and output (Vietnamese).
    """
    print(f"Starting conversion of EVBCorpus V2 from: {corpus_path}")
    print(f"Target Output Path: {output_file_path}")
    
    sgml_files = glob.glob(os.path.join(corpus_path, "*.sgml"))
    if not sgml_files:
        print(f"Error: No .sgml files found in {corpus_path}", file=sys.stderr)
        return
        
    print(f"Found {len(sgml_files)} SGML files to process.")
    
    # Patterns to extract <s> tags and their contents
    s_tag_pat = re.compile(r"<s\s+id=['\"](en|vn)\d+['\"]>(.*?)</s>", re.DOTALL)
    
    total_records = 0
    file_count = 0
    
    try:
        with open(output_file_path, 'w', encoding='utf-8') as fout:
            # Sort files to maintain deterministic sequential order
            for file_path in sorted(sgml_files):
                file_name = os.path.basename(file_path)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as fin:
                        content = fin.read()
                except Exception as e:
                    print(f"Error reading file {file_name}: {e}", file=sys.stderr)
                    continue
                
                # Split by <spair> blocks to keep sentence pairs together
                spair_blocks = re.findall(r"<spair\s+id=['\"]\d+['\"]>(.*?)</spair>", content, re.DOTALL)
                
                for block in spair_blocks:
                    s_matches = s_tag_pat.findall(block)
                    
                    en_text = None
                    vn_text = None
                    
                    for lang, s_content in s_matches:
                        # Clean up text (strip whitespaces and remove XML tags if any nested)
                        clean_text = s_content.strip()
                        if lang == 'en':
                            en_text = clean_text
                        elif lang == 'vn':
                            vn_text = clean_text
                            
                    # If both English and Vietnamese sentences exist in the block, write to JSONL
                    if en_text is not None and vn_text is not None:
                        record = {
                            "topic": topic,
                            "instruction": f"Dịch thuật sang Tiếng việt theo chủ đề {topic}",
                            "input": en_text,
                            "output": vn_text
                        }
                        fout.write(json.dumps(record, ensure_ascii=False) + "\n")
                        total_records += 1
                        
                file_count += 1
                if file_count % 100 == 0:
                    print(f"Processed {file_count} files... Accumulated {total_records} records.")
                    
        print("\n" + "="*50)
        print("CONVERSION COMPLETED SUCCESSFULLY")
        print("="*50)
        print(f"Total files processed: {file_count}")
        print(f"Total records written: {total_records}")
        print(f"Output saved to:       {output_file_path}")
        print("="*50)
        
    except Exception as e:
        print(f"Fatal error during conversion: {e}", file=sys.stderr)

if __name__ == "__main__":
    v2_path = os.path.join("raws", "EVBCorpus_EVBNews_v2.0")
    output_path = "translated_thoi_su.jsonl"
    convert_v2_to_jsonl(v2_path, output_path, topic="thời sự")
