import json
import hashlib
import sys
import argparse
import os
import re

def calculate_md5(text):
    """Calculate MD5 hash of the stripped text in UTF-8."""
    return hashlib.md5(text.strip().encode("utf-8")).hexdigest()

def main():
    # Force UTF-8 output encoding for Windows compatibility
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(description="Generic CLI tool to search for text segment matches in source files and find their line indices.")
    parser.add_argument("-q", "--query", action="append", help="Text query to search for. Can be specified multiple times.")
    parser.add_argument("--src-file", type=str, default="extracted_the_gioi.jsonl", help="Path to the source file")
    parser.add_argument("--stdin", action="store_true", help="Read queries from standard input (one query per line)")
    parser.add_argument("-i", "--ignore-case", action="store_true", help="Perform case-insensitive search")
    parser.add_argument("-r", "--regex", action="store_true", help="Treat query as a regular expression pattern")

    args = parser.parse_args()

    queries = []
    if args.query:
        queries.extend(args.query)

    if args.stdin:
        print("Reading queries from stdin (press Ctrl+Z then Enter on Windows to end):")
        for line in sys.stdin:
            cleaned = line.strip()
            if cleaned:
                queries.append(cleaned)

    if not queries:
        print("Error: No search queries specified. Use -q/--query or --stdin.")
        sys.exit(1)

    if not os.path.exists(args.src_file):
        print(f"Error: Source file '{args.src_file}' not found.")
        sys.exit(1)

    print(f"Searching for {len(queries)} query/queries in '{args.src_file}'...")

    # Load all source lines
    src_lines = []
    with open(args.src_file, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f, 1):
            if line.strip():
                try:
                    data = json.loads(line)
                    src_lines.append((idx, data.get("output", "")))
                except json.JSONDecodeError:
                    print(f"Warning: Skipping invalid JSON on line {idx}")
                    continue

    print(f"Total source lines loaded: {len(src_lines)}")

    results = {}
    for i, q in enumerate(queries):
        found = False
        print(f"\n--- Search Result for Query {i+1}: '{q[:50]}' ---")
        
        # Compile regex if regex flag is set
        pattern = None
        if args.regex:
            try:
                flags = re.IGNORECASE if args.ignore_case else 0
                pattern = re.compile(q, flags)
            except re.error as e:
                print(f"Error: Invalid regular expression pattern: {e}")
                results[i] = -1
                continue

        for idx, vi_text in src_lines:
            match = False
            if args.regex and pattern:
                if pattern.search(vi_text):
                    match = True
            else:
                if args.ignore_case:
                    if q.lower() in vi_text.lower():
                        match = True
                else:
                    if q in vi_text:
                        match = True

            if match:
                h = calculate_md5(vi_text)
                print(f"  Match found at Line {idx}:")
                print(f"    Text: {vi_text[:120]}...")
                print(f"    MD5: {h}")
                results[i] = idx
                found = True
                break
                
        if not found:
            print("  Status: NOT FOUND")
            results[i] = -1

    print("\n=== Search Summary ===")
    for i, q in enumerate(queries):
        idx = results.get(i, -1)
        status = f"Line {idx}" if idx != -1 else "NOT FOUND"
        print(f"  Query {i+1} ('{q[:30]}') -> {status}")

if __name__ == "__main__":
    main()
