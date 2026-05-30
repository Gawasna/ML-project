import os
import re
import json
import sys

# Ensure UTF-8 encoding for stdout on Windows to prevent crash
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def convert_range_to_jsonl(corpus_path, output_file_path, start_num=2, end_num=15, topic="thời sự"):
    """
    Converts a specific range of SGML files (N0002 to N0015) into a flat JSONL format,
    while adding a global incremental ID to each sentence pair.
    """
    print(f"Converting EVBCorpus V2 range N{start_num:04d} to N{end_num:04d} to JSONL...")
    print(f"Target Output Path: {output_file_path}")
    
    s_tag_pat = re.compile(r"<s\s+id=['\"](en|vn)\d+['\"]>(.*?)</s>", re.DOTALL)
    
    global_id = 1
    file_count = 0
    total_records = 0
    
    try:
        with open(output_file_path, 'w', encoding='utf-8') as fout:
            for i in range(start_num, end_num + 1):
                file_name = f"N{i:04d}.sgml"
                file_path = os.path.join(corpus_path, file_name)
                
                if not os.path.exists(file_path):
                    print(f"Warning: File {file_name} does not exist inside {corpus_path}", file=sys.stderr)
                    continue
                    
                try:
                    with open(file_path, 'r', encoding='utf-8') as fin:
                        content = fin.read()
                except Exception as e:
                    print(f"Error reading file {file_name}: {e}", file=sys.stderr)
                    continue
                
                # Split content into spair blocks to keep en and vn sentences aligned
                spair_blocks = re.findall(r"<spair\s+id=['\"]\d+['\"]>(.*?)</spair>", content, re.DOTALL)
                
                file_records = 0
                for block in spair_blocks:
                    s_matches = s_tag_pat.findall(block)
                    
                    en_text = None
                    vn_text = None
                    
                    for lang, s_content in s_matches:
                        clean_text = s_content.strip()
                        if lang == 'en':
                            en_text = clean_text
                        elif lang == 'vn':
                            vn_text = clean_text
                            
                    if en_text is not None and vn_text is not None:
                        record = {
                            "id": global_id,
                            "topic": topic,
                            "instruction": f"Dịch thuật sang Tiếng việt theo chủ đề {topic}",
                            "input": en_text,
                            "output": vn_text
                        }
                        fout.write(json.dumps(record, ensure_ascii=False) + "\n")
                        global_id += 1
                        total_records += 1
                        file_records += 1
                        
                file_count += 1
                print(f"Processed {file_name}: extracted {file_records} pairs.")
                
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
    output_path = "translated_thoi_su_N0002_N0015.jsonl"
    convert_range_to_jsonl(v2_path, output_path, start_num=2, end_num=15, topic="thời sự")
