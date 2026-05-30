import os
import re
import json
import sys

# Ensure UTF-8 encoding for stdout on Windows to prevent crash
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def audit_and_convert_range(corpus_path, output_jsonl_path, output_report_path, start_num=71, end_num=90, topic="thời sự"):
    """
    Performs both validation (verification of linear alignment) and conversion to JSONL
    for a specified range of SGML files (N0071 to N0090).
    Generates a markdown report summarizing the audit.
    """
    print(f"Starting Audit & Conversion for EVBCorpus V2 range N{start_num:04d} to N{end_num:04d}...")
    
    # Regex patterns
    title_pat = re.compile(r"<title>(.*?)</title>", re.DOTALL)
    author_pat = re.compile(r"<author[^>]*>(.*?)</author>", re.DOTALL)
    release_pat = re.compile(r"<release>(.*?)</release>", re.DOTALL)
    
    spair_pat = re.compile(r"<spair\s+id=['\"](\d+)['\"]>(.*?)</spair>", re.DOTALL)
    s_tag_pat = re.compile(r"<s\s+id=['\"](en|vn)(\d+)['\"]>(.*?)</s>", re.DOTALL)
    a_tag_pat = re.compile(r"<a\s+id=['\"]ev(\d+)['\"]>(.*?)</a>", re.DOTALL)
    
    audit_results = []
    global_id = 1
    total_records = 0
    
    try:
        with open(output_jsonl_path, 'w', encoding='utf-8') as fout:
            for i in range(start_num, end_num + 1):
                file_name = f"N{i:04d}.sgml"
                file_path = os.path.join(corpus_path, file_name)
                
                if not os.path.exists(file_path):
                    print(f"Warning: File {file_name} not found in {corpus_path}", file=sys.stderr)
                    continue
                    
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except Exception as e:
                    print(f"Error reading file {file_name}: {e}", file=sys.stderr)
                    continue
                
                # 1. Extract Metadata
                title_match = title_pat.search(content)
                author_match = author_pat.search(content)
                release_match = release_pat.search(content)
                
                title = title_match.group(1).strip() if title_match else "Unknown Title"
                author = author_match.group(1).strip() if author_match else "Unknown Author"
                release = release_match.group(1).strip() if release_match else "Unknown Release"
                
                # 2. Extract and Validate Spairs
                spair_blocks = spair_pat.findall(content)
                total_spairs = len(spair_blocks)
                
                is_linear = True
                missing_elements = 0
                id_mismatches = 0
                
                total_en_words = 0
                total_vn_words = 0
                total_alignments = 0
                
                first_pair = None
                file_records = 0
                
                for idx, (spair_id_str, spair_content) in enumerate(spair_blocks, 1):
                    spair_id = int(spair_id_str)
                    
                    if spair_id != idx:
                        is_linear = False
                        
                    s_matches = s_tag_pat.findall(spair_content)
                    a_matches = a_tag_pat.findall(spair_content)
                    
                    en_sentences = [m for m in s_matches if m[0] == 'en']
                    vn_sentences = [m for m in s_matches if m[0] == 'vn']
                    
                    # Count checks
                    if len(en_sentences) != 1 or len(vn_sentences) != 1 or len(a_matches) != 1:
                        missing_elements += 1
                        is_linear = False
                        
                    if en_sentences and vn_sentences and a_matches:
                        en_id = int(en_sentences[0][1])
                        vn_id = int(vn_sentences[0][1])
                        a_id = int(a_matches[0][0])
                        
                        # ID checks
                        if en_id != spair_id or vn_id != spair_id or a_id != spair_id:
                            id_mismatches += 1
                            is_linear = False
                            
                        en_text = en_sentences[0][2].strip()
                        vn_text = vn_sentences[0][2].strip()
                        a_text = a_matches[0][1].strip()
                        
                        # Metrics
                        en_words = len(en_text.split())
                        vn_words = len(vn_text.split())
                        align_links = len(a_text.split(';')) - 1 if a_text.endswith(';') else len(a_text.split(';'))
                        if not a_text:
                            align_links = 0
                            
                        total_en_words += en_words
                        total_vn_words += vn_words
                        total_alignments += align_links
                        
                        # Conversion process - Write record to JSONL
                        record = {
                            "id": global_id,
                            "topic": topic,
                            "instruction": f"Dịch thuật sang Tiếng việt theo chủ đề {topic}",
                            "input": en_text,
                            "output": vn_text
                        }
                        fout.write(json.dumps(record, ensure_ascii=False) + "\n")
                        
                        if idx == 1:
                            first_pair = {
                                "id": spair_id,
                                "en": en_text,
                                "vn": vn_text,
                                "align": a_text
                            }
                            
                        global_id += 1
                        total_records += 1
                        file_records += 1
                        
                avg_en = total_en_words / total_spairs if total_spairs > 0 else 0
                avg_vn = total_vn_words / total_spairs if total_spairs > 0 else 0
                avg_align = total_alignments / total_spairs if total_spairs > 0 else 0
                
                file_report = {
                    "index": i,
                    "filename": file_name,
                    "title": title,
                    "author": author,
                    "release": release,
                    "total_spairs": total_spairs,
                    "file_records": file_records,
                    "is_linear": is_linear,
                    "missing_elements": missing_elements,
                    "id_mismatches": id_mismatches,
                    "avg_en_words": round(avg_en, 2),
                    "avg_vn_words": round(avg_vn, 2),
                    "avg_align_links": round(avg_align, 2),
                    "first_pair_sample": first_pair
                }
                audit_results.append(file_report)
                print(f"Processed {file_name}: {file_records} pairs parsed, perfectly linear: {is_linear}")
                
        # Generate Markdown Report
        with open(output_report_path, 'w', encoding='utf-8') as fmd:
            fmd.write("# BÁO CÁO PHÂN TÍCH VÀ CHUYỂN ĐỔI LÔ EVBCORPUS V2 (N0071 -> N0090)\n\n")
            fmd.write("Báo cáo kiểm toán cấu trúc đồng bộ tuyến tính và thống kê chi tiết việc chuyển đổi lô từ N0071 đến N0090 sang JSONL phẳng.\n\n")
            
            fmd.write("## 1. Bảng Tổng Hợp Số Liệu Thống Kê\n\n")
            fmd.write("| Tệp | Tiêu đề | Số cặp câu | Tuyến tính | Tr.bình từ EN | Tr.bình từ VN | Liên kết Alignment |\n")
            fmd.write("| --- | --- | --- | --- | --- | --- | --- |\n")
            
            for r in audit_results:
                linear_status = "✅ Đồng bộ 100%" if r["is_linear"] else f"❌ Lỗi ({r['missing_elements']} thiếu, {r['id_mismatches']} lệch ID)"
                fmd.write(f"| `{r['filename']}` | **{r['title']}** | {r['total_spairs']} | {linear_status} | {r['avg_en_words']} | {r['avg_vn_words']} | {r['avg_align_links']} |\n")
                
            fmd.write("\n---\n\n## 2. Chi Tiết Từng Tệp & Mẫu Duyệt (Audit Samples)\n\n")
            
            for r in audit_results:
                fmd.write(f"### {r['index'] - 70:02d}. `{r['filename']}`: {r['title']}\n\n")
                fmd.write(f"*   **Tác giả:** {r['author']}\n")
                fmd.write(f"*   **Ngày phát hành:** {r['release']}\n")
                fmd.write(f"*   **Tổng số cặp câu:** {r['total_spairs']} câu\n")
                fmd.write(f"*   **Độ dài trung bình:** {r['avg_en_words']} từ (EN) | {r['avg_vn_words']} từ (VN)\n")
                fmd.write(f"*   **Mật độ căn chỉnh từ:** Trung bình {r['avg_align_links']} liên kết/câu\n")
                fmd.write(f"*   **Trạng thái cấu trúc:** " + ("Đồng bộ tuyến tính tuyệt đối (100% Safe)" if r["is_linear"] else "Có lỗi cấu trúc") + "\n\n")
                
                if r["first_pair_sample"]:
                    sample = r["first_pair_sample"]
                    fmd.write("> **Mẫu Cặp Câu Đầu Tiên (ID: " + str(sample["id"]) + "):**\n")
                    fmd.write("> *   **EN:** `" + sample["en"] + "`\n")
                    fmd.write("> *   **VN:** `" + sample["vn"] + "`\n")
                    fmd.write("> *   **Alignment Map:** `" + sample["align"] + "`\n\n")
                    
                fmd.write("---\n\n")
                
        print("\n" + "="*50)
        print("CONVERSION & AUDIT COMPLETED")
        print("="*50)
        print(f"Total files processed: {len(audit_results)}")
        print(f"Total records written: {total_records}")
        print(f"JSONL saved to:        {output_jsonl_path}")
        print(f"MD Report saved to:    {output_report_path}")
        print("="*50)
        
    except Exception as e:
        print(f"Fatal error during audit & conversion: {e}", file=sys.stderr)

if __name__ == "__main__":
    v2_path = os.path.join("raws", "EVBCorpus_EVBNews_v2.0")
    jsonl_out = "translated_thoi_su_N0071_N0090.jsonl"
    report_out = os.path.join("docs", "evbcorpus_audit_report_71_90.md")
    
    audit_and_convert_range(v2_path, jsonl_out, report_out, start_num=71, end_num=90, topic="thời sự")
