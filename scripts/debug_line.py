import json
import hashlib
import sys
import argparse
import os

def calculate_md5(text):
    """Calculate MD5 hash of the stripped text in UTF-8."""
    return hashlib.md5(text.strip().encode("utf-8")).hexdigest()

def find_matching_target_line(src_text, tgt_file):
    """Find a line in target file that matches the source text's MD5 hash."""
    src_hash = calculate_md5(src_text)
    if not os.path.exists(tgt_file):
        return None, None
    with open(tgt_file, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f, 1):
            if line.strip():
                try:
                    data = json.loads(line)
                    tgt_text = data.get("output", "")
                    if calculate_md5(tgt_text) == src_hash:
                        return idx, tgt_text
                except json.JSONDecodeError:
                    continue
    return None, None

def main():
    # Force UTF-8 output encoding for Windows command line compatibility
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(description="Generic CLI tool to debug and compare lines in source and target files.")
    parser.add_argument("--src-line", type=int, help="Line number in the source file")
    parser.add_argument("--tgt-line", type=int, help="Line number in the target file. If omitted, the tool will attempt to auto-locate a matching line based on MD5.")
    parser.add_argument("--src-file", type=str, default="extracted_the_gioi.jsonl", help="Path to the source file")
    parser.add_argument("--tgt-file", type=str, default="translated_the_gioi.jsonl", help="Path to the target file")

    args = parser.parse_args()

    if args.src_line is None and args.tgt_line is None:
        print("Error: Please specify at least --src-line or --tgt-line.")
        sys.exit(1)

    src_text = None
    tgt_text = None
    actual_tgt_line = args.tgt_line

    # Load source line if specified
    if args.src_line is not None:
        if not os.path.exists(args.src_file):
            print(f"Error: Source file '{args.src_file}' not found.")
            sys.exit(1)
        with open(args.src_file, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f, 1):
                if idx == args.src_line:
                    try:
                        data = json.loads(line)
                        src_text = data.get("output", "")
                    except json.JSONDecodeError:
                        print(f"Error: Invalid JSON on line {idx} in source file.")
                        sys.exit(1)
                    break
        if src_text is None:
            print(f"Error: Line {args.src_line} not found in {args.src_file}")
            sys.exit(1)

    # Load target line if specified or try to auto-locate if only source is specified
    if actual_tgt_line is not None:
        if not os.path.exists(args.tgt_file):
            print(f"Error: Target file '{args.tgt_file}' not found.")
            sys.exit(1)
        with open(args.tgt_file, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f, 1):
                if idx == actual_tgt_line:
                    try:
                        data = json.loads(line)
                        tgt_text = data.get("output", "")
                    except json.JSONDecodeError:
                        print(f"Error: Invalid JSON on line {idx} in target file.")
                        sys.exit(1)
                    break
        if tgt_text is None:
            print(f"Error: Line {actual_tgt_line} not found in {args.tgt_file}")
            sys.exit(1)
    elif src_text is not None:
        # Auto-mapping mode: find matching target line by MD5
        matched_idx, matched_text = find_matching_target_line(src_text, args.tgt_file)
        if matched_idx is not None:
            actual_tgt_line = matched_idx
            tgt_text = matched_text
            print(f"Auto-mapped Source Line {args.src_line} to Target Line {actual_tgt_line} (matching MD5)")
        else:
            print(f"Warning: No matching line found in target file for Source Line {args.src_line} based on MD5.")

    # Output individual info if comparison is not possible
    if src_text is not None and tgt_text is None:
        src_hash = calculate_md5(src_text)
        print(f"\n--- Source Line {args.src_line} Info ---")
        print(f"  Length: {len(src_text)} characters")
        print(f"  MD5: {src_hash}")
        print(f"  Text: {src_text}")
    elif tgt_text is not None and src_text is None:
        tgt_hash = calculate_md5(tgt_text)
        print(f"\n--- Target Line {actual_tgt_line} Info ---")
        print(f"  Length: {len(tgt_text)} characters")
        print(f"  MD5: {tgt_hash}")
        print(f"  Text: {tgt_text}")
    elif src_text is not None and tgt_text is not None:
        # Comparison mode
        src_hash = calculate_md5(src_text)
        tgt_hash = calculate_md5(tgt_text)

        print(f"\n--- Comparison Summary ---")
        print(f"Source Line {args.src_line} (len {len(src_text)}): {src_text[:80]}...")
        print(f"Target Line {actual_tgt_line} (len {len(tgt_text)}): {tgt_text[:80]}...")
        print(f"Source MD5: {src_hash}")
        print(f"Target MD5: {tgt_hash}")

        if src_text == tgt_text:
            print("\nResult: SUCCESS - The strings are 100% identical!")
        else:
            print("\nResult: MISMATCH - The strings differ!")
            # Find the exact character mismatch point
            mismatch_found = False
            for i, (c1, c2) in enumerate(zip(src_text, tgt_text)):
                if c1 != c2:
                    print(f"\nFirst mismatch found at character index {i}:")
                    print(f"  Source context: ...{repr(src_text[max(0, i-25):i+25])}...")
                    print(f"  Target context: ...{repr(tgt_text[max(0, i-25):i+25])}...")
                    print(f"  Mismatch character: Source = {repr(c1)} | Target = {repr(c2)}")
                    mismatch_found = True
                    break
            if not mismatch_found:
                if len(src_text) != len(tgt_text):
                    print(f"\nLength mismatch: Source length = {len(src_text)} | Target length = {len(tgt_text)}")
                    min_len = min(len(src_text), len(tgt_text))
                    if len(src_text) > min_len:
                        print(f"  Extra Source characters: {repr(src_text[min_len:])}")
                    else:
                        print(f"  Extra Target characters: {repr(tgt_text[min_len:])}")

if __name__ == "__main__":
    main()
