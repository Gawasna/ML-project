import os
import re
import glob
import sys

# Ensure UTF-8 encoding for stdout on Windows to prevent crash
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def analyze_sgml_alignment(corpus_path):
    """
    Analyzes SGML files in the EVBCorpus directory for structural integrity and linear alignment.
    Specifically checks if every <spair> contains exactly one English sentence <s>,
    one Vietnamese sentence <s>, and one alignment link <a>, and whether their IDs match perfectly.
    """
    print(f"Starting alignment analysis on path: {corpus_path}")
    
    sgml_files = glob.glob(os.path.join(corpus_path, "*.sgml"))
    if not sgml_files:
        print(f"Error: No .sgml files found in {corpus_path}", file=sys.stderr)
        return
        
    print(f"Found {len(sgml_files)} SGML files to analyze.")
    
    total_spairs = 0
    perfect_spairs = 0
    malformed_spairs = 0
    id_mismatch_count = 0
    missing_elements_count = 0
    files_with_issues = []
    
    # Patterns to extract tags and their IDs/contents
    spair_start_pat = re.compile(r"<spair\s+id=['\"](\d+)['\"]>")
    spair_end_pat = re.compile(r"</spair>")
    s_tag_pat = re.compile(r"<s\s+id=['\"](en|vn)(\d+)['\"]>(.*?)</s>")
    a_tag_pat = re.compile(r"<a\s+id=['\"]ev(\d+)['\"]>(.*?)</a>")
    
    for file_idx, file_path in enumerate(sorted(sgml_files)):
        file_name = os.path.basename(file_path)
        
        # Read the file with utf-8 encoding
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"Error reading file {file_name}: {e}", file=sys.stderr)
            files_with_issues.append((file_name, f"Read error: {str(e)}"))
            continue
            
        in_spair = False
        current_spair_id = None
        spair_elements = [] # Buffer for lines inside current <spair>
        spair_line_start = 0
        
        file_spairs = 0
        file_issues = []
        
        for line_num, line in enumerate(lines, 1):
            line_str = line.strip()
            
            # Detect spair block start
            start_match = spair_start_pat.search(line_str)
            if start_match:
                if in_spair:
                    file_issues.append(f"Line {line_num}: Nested or unclosed <spair> block (ID: {current_spair_id}).")
                    malformed_spairs += 1
                in_spair = True
                current_spair_id = start_match.group(1)
                spair_elements = []
                spair_line_start = line_num
                continue
                
            # Detect spair block end
            if spair_end_pat.search(line_str):
                if not in_spair:
                    file_issues.append(f"Line {line_num}: </spair> tag found without a matching start tag.")
                    malformed_spairs += 1
                else:
                    in_spair = False
                    total_spairs += 1
                    file_spairs += 1
                    
                    # Analyze the content inside the spair block
                    en_sentences = []
                    vn_sentences = []
                    alignments = []
                    
                    for item in spair_elements:
                        # Find <s> tags
                        s_matches = s_tag_pat.findall(item)
                        for lang, s_id, s_content in s_matches:
                            if lang == 'en':
                                en_sentences.append((s_id, s_content))
                            elif lang == 'vn':
                                vn_sentences.append((s_id, s_content))
                                
                        # Find <a> tags
                        a_matches = a_tag_pat.findall(item)
                        for a_id, a_content in a_matches:
                            alignments.append((a_id, a_content))
                            
                    # Verification checklist
                    issue_found = False
                    
                    # 1. Check counts of elements
                    if len(en_sentences) != 1 or len(vn_sentences) != 1 or len(alignments) != 1:
                        missing_elements_count += 1
                        file_issues.append(
                            f"Spair ID {current_spair_id} (lines {spair_line_start}-{line_num}) has abnormal element counts: "
                            f"{len(en_sentences)} English, {len(vn_sentences)} Vietnamese, {len(alignments)} Alignment tags."
                        )
                        issue_found = True
                        
                    # 2. Check IDs alignment
                    if not issue_found:
                        en_id, en_text = en_sentences[0]
                        vn_id, vn_text = vn_sentences[0]
                        a_id, a_text = alignments[0]
                        
                        if en_id != current_spair_id or vn_id != current_spair_id or a_id != current_spair_id:
                            id_mismatch_count += 1
                            file_issues.append(
                                f"ID mismatch in Spair {current_spair_id} (lines {spair_line_start}-{line_num}): "
                                f"en_id='{en_id}', vn_id='{vn_id}', a_id='{a_id}'"
                            )
                            issue_found = True
                            
                    if issue_found:
                        malformed_spairs += 1
                    else:
                        perfect_spairs += 1
                        
                continue
                
            # If inside a spair, accumulate content
            if in_spair:
                spair_elements.append(line_str)
                
        if in_spair:
            file_issues.append(f"File ended with an unclosed <spair id='{current_spair_id}'> starting at line {spair_line_start}.")
            malformed_spairs += 1
            
        if file_issues:
            files_with_issues.append((file_name, file_issues))
            
    # Output final summary
    print("\n" + "="*50)
    print("ALIGNMENT ANALYSIS REPORT SUMMARY")
    print("="*50)
    print(f"Total SGML files analyzed:      {len(sgml_files)}")
    print(f"Total <spair> blocks parsed:    {total_spairs}")
    print(f"Perfectly aligned spairs:       {perfect_spairs} ({perfect_spairs/total_spairs*100:.2f}% of total)")
    print(f"Malformed or misaligned spairs: {malformed_spairs} ({malformed_spairs/total_spairs*100:.2f}% of total)")
    print(f"  - Element count issues:       {missing_elements_count}")
    print(f"  - ID mismatch issues:         {id_mismatch_count}")
    
    print("\n" + "="*50)
    if files_with_issues:
        print(f"FILES WITH ISSUES ({len(files_with_issues)}):")
        for fname, issues in files_with_issues:
            print(f"\n📁 File: {fname}")
            if isinstance(issues, list):
                for issue in issues[:10]: # Print up to 10 issues per file
                    print(f"  ⚠️ {issue}")
                if len(issues) > 10:
                    print(f"  ... and {len(issues) - 10} more issues in this file.")
            else:
                print(f"  ⚠️ {issues}")
    else:
        print("✅ SUCCESS: All files are perfectly aligned! Linear conversion is 100% safe.")
    print("="*50)

if __name__ == "__main__":
    # Analyze v2.0
    v2_path = os.path.join("raws", "EVBCorpus_EVBNews_v2.0")
    analyze_sgml_alignment(v2_path)
    
    # Analyze v1.0
    print("\n" + "-"*50 + "\n")
    v1_path = os.path.join("raws", "EVBCorpus_EVBNews_v1.0", "EVBCorpus_v1", "EVBNews")
    analyze_sgml_alignment(v1_path)
