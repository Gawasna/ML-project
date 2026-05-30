import os
import re
import json
import sys

# Ensure UTF-8 encoding for stdout on Windows to prevent crash
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def audit_files_range(corpus_path, start_num=2, end_num=15):
    """
    Audits a range of SGML files (from N0002 to N0015 by default) in the EVBCorpus.
    Extracts metadata, sentence pair stats, alignment maps, and verifies linear consistency.
    """
    print(f"Auditing EVBCorpus range N{start_num:04d} to N{end_num:04d} inside: {corpus_path}")
    
    audit_results = []
    
    # Regex patterns for extracting metadata and tags
    title_pat = re.compile(r"<title>(.*?)</title>", re.DOTALL)
    author_pat = re.compile(r"<author[^>]*>(.*?)</author>", re.DOTALL)
    release_pat = re.compile(r"<release>(.*?)</release>", re.DOTALL)
    
    spair_pat = re.compile(r"<spair\s+id=['\"](\d+)['\"]>(.*?)</spair>", re.DOTALL)
    s_tag_pat = re.compile(r"<s\s+id=['\"](en|vn)(\d+)['\"]>(.*?)</s>", re.DOTALL)
    a_tag_pat = re.compile(r"<a\s+id=['\"]ev(\d+)['\"]>(.*?)</a>", re.DOTALL)
    
    for i in range(start_num, end_num + 1):
        file_name = f"N{i:04d}.sgml"
        file_path = os.path.join(corpus_path, file_name)
        
        if not os.path.exists(file_path):
            print(f"Warning: File {file_name} does not exist in {corpus_path}", file=sys.stderr)
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
        
        # 2. Extract Spairs
        spair_blocks = spair_pat.findall(content)
        total_spairs = len(spair_blocks)
        
        # 3. Analyze Linear Consistency & Stats
        is_linear = True
        missing_elements = 0
        id_mismatches = 0
        
        total_en_words = 0
        total_vn_words = 0
        total_alignments = 0
        
        spair_details = []
        
        for idx, (spair_id_str, spair_content) in enumerate(spair_blocks, 1):
            spair_id = int(spair_id_str)
            
            # Check if IDs increment strictly from 1 to N
            if spair_id != idx:
                is_linear = False
                
            s_matches = s_tag_pat.findall(spair_content)
            a_matches = a_tag_pat.findall(spair_content)
            
            en_sentences = [m for m in s_matches if m[0] == 'en']
            vn_sentences = [m for m in s_matches if m[0] == 'vn']
            
            # Element count verification
            if len(en_sentences) != 1 or len(vn_sentences) != 1 or len(a_matches) != 1:
                missing_elements += 1
                is_linear = False
                
            # ID match verification
            if en_sentences and vn_sentences and a_matches:
                en_id = int(en_sentences[0][1])
                vn_id = int(vn_sentences[0][1])
                a_id = int(a_matches[0][0])
                
                if en_id != spair_id or vn_id != spair_id or a_id != spair_id:
                    id_mismatches += 1
                    is_linear = False
                    
                # Word stats
                en_text = en_sentences[0][2].strip()
                vn_text = vn_sentences[0][2].strip()
                a_text = a_matches[0][1].strip()
                
                en_words = len(en_text.split())
                vn_words = len(vn_text.split())
                align_links = len(a_text.split(';')) - 1 if a_text.endswith(';') else len(a_text.split(';'))
                if not a_text:
                    align_links = 0
                    
                total_en_words += en_words
                total_vn_words += vn_words
                total_alignments += align_links
                
                # Keep first spair as sample
                if idx == 1:
                    spair_details.append({
                        "id": spair_id,
                        "en": en_text,
                        "vn": vn_text,
                        "align": a_text
                    })
                    
        avg_en_len = total_en_words / total_spairs if total_spairs > 0 else 0
        avg_vn_len = total_vn_words / total_spairs if total_spairs > 0 else 0
        avg_align = total_alignments / total_spairs if total_spairs > 0 else 0
        
        file_report = {
            "index": i,
            "filename": file_name,
            "title": title,
            "author": author,
            "release": release,
            "total_spairs": total_spairs,
            "is_linear": is_linear,
            "missing_elements": missing_elements,
            "id_mismatches": id_mismatches,
            "avg_en_words": round(avg_en_len, 2),
            "avg_vn_words": round(avg_vn_len, 2),
            "avg_align_links": round(avg_align, 2),
            "first_pair_sample": spair_details[0] if spair_details else None
        }
        
        audit_results.append(file_report)
        print(f"Audited {file_name}: {total_spairs} spairs, perfectly linear: {is_linear}")
        
    return audit_results

def generate_markdown_report(results, output_path):
    """
    Generates a beautifully structured markdown report for the audited files.
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# BÁO CÁO PHÂN TÍCH CHI TIẾT LÔ EVBCORPUS V2 (N0002 -> N0015)\n\n")
        f.write("Báo cáo kiểm toán cấu trúc, nội dung tiêu đề và tính đồng bộ tuyến tính của các tệp từ N0002 đến N0015 thuộc bộ dữ liệu EVBCorpus V2.\n\n")
        
        f.write("## 1. Bảng Tổng Hợp Thống Kê Số Liệu\n\n")
        f.write("| Tệp | Tiêu đề | Số cặp câu | Tuyến tính | Tr.bình từ EN | Tr.bình từ VN | Liên kết Alignment |\n")
        f.write("| --- | --- | --- | --- | --- | --- | --- |\n")
        
        for r in results:
            linear_status = "✅ Đồng bộ 100%" if r["is_linear"] else f"❌ Lỗi ({r['missing_elements']} thiếu, {r['id_mismatches']} lệch ID)"
            f.write(f"| `{r['filename']}` | **{r['title']}** | {r['total_spairs']} | {linear_status} | {r['avg_en_words']} | {r['avg_vn_words']} | {r['avg_align_links']} |\n")
            
        f.write("\n---\n\n## 2. Chi Tiết Từng Tệp & Mẫu Duyệt (Audit Samples)\n\n")
        
        for r in results:
            f.write(f"### {r['index'] - 1:02d}. `{r['filename']}`: {r['title']}\n\n")
            f.write(f"*   **Tác giả:** {r['author']}\n")
            f.write(f"*   **Ngày phát hành:** {r['release']}\n")
            f.write(f"*   **Tổng số cặp câu:** {r['total_spairs']} câu\n")
            f.write(f"*   **Độ dài trung bình:** {r['avg_en_words']} từ (EN) | {r['avg_vn_words']} từ (VN)\n")
            f.write(f"*   **Mật độ căn chỉnh từ:** Trung bình {r['avg_align_links']} liên kết/câu\n")
            f.write(f"*   **Trạng thái cấu trúc:** " + ("Đồng bộ tuyến tính tuyệt đối (100% Safe)" if r["is_linear"] else "Có lỗi bất thường") + "\n\n")
            
            if r["first_pair_sample"]:
                sample = r["first_pair_sample"]
                f.write("> **Mẫu Cặp Câu Đầu Tiên (ID: " + str(sample["id"]) + "):**\n")
                f.write("> *   **EN:** `" + sample["en"] + "`\n")
                f.write("> *   **VN:** `" + sample["vn"] + "`\n")
                f.write("> *   **Alignment Map:** `" + sample["align"] + "`\n\n")
                
            f.write("---\n\n")
            
    print(f"Markdown report generated successfully at: {output_path}")

if __name__ == "__main__":
    v2_path = os.path.join("raws", "EVBCorpus_EVBNews_v2.0")
    results = audit_files_range(v2_path, start_num=2, end_num=15)
    
    # Save structured JSON data in scratch for future tasks
    scratch_json_path = os.path.join("scratch", "audit_results_N0002_N0015.json")
    with open(scratch_json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    print(f"Audit results JSON saved to: {scratch_json_path}")
    
    # Generate clean markdown report in docs
    report_md_path = os.path.join("docs", "evbcorpus_audit_report.md")
    generate_markdown_report(results, report_md_path)
