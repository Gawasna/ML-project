import json
import sys
import argparse

def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(description="Synchronize target file output field with source file exact values to align MD5 hashes.")
    parser.add_argument("--src-start", type=int, help="Starting line number in the source file")
    parser.add_argument("--count", type=int, default=5, help="Number of lines to process")
    parser.add_argument("--src-indices", type=str, help="Comma-separated source line numbers (overrides --src-start and --count)")
    parser.add_argument("--tgt-start", type=int, required=True, help="Starting line number in the target file to overwrite")
    parser.add_argument("--src-file", type=str, default="extracted_the_gioi.jsonl", help="Path to the source jsonl file")
    parser.add_argument("--tgt-file", type=str, default="translated_the_gioi.jsonl", help="Path to the target jsonl file")

    args = parser.parse_args()

    # Determine source indices
    if args.src_indices:
        try:
            src_indices = [int(x.strip()) for x in args.src_indices.split(",") if x.strip()]
        except ValueError:
            print("Error: --src-indices must be a comma-separated list of integers.")
            sys.exit(1)
    else:
        if args.src_start is None:
            print("Error: Either --src-start or --src-indices must be provided.")
            sys.exit(1)
        src_indices = list(range(args.src_start, args.src_start + args.count))

    print(f"Source indices to process: {src_indices}")
    print(f"Target starting index: {args.tgt_start}")

    # Read corresponding source lines
    src_lines = {}
    with open(args.src_file, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f, 1):
            if idx in src_indices:
                src_data = json.loads(line)
                src_lines[idx] = src_data.get("output", "")

    # Check if we found all source lines
    missing_src = [idx for idx in src_indices if idx not in src_lines]
    if missing_src:
        print(f"Error: Could not find source lines {missing_src} in {args.src_file}")
        sys.exit(1)

    # Read all target lines
    tgt_lines = []
    with open(args.tgt_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                tgt_lines.append(json.loads(line))

    # Validate target indices
    max_needed_tgt = args.tgt_start + len(src_indices) - 1
    if len(tgt_lines) < max_needed_tgt:
        print(f"Error: Target file only has {len(tgt_lines)} lines, but we need at least {max_needed_tgt} lines to update.")
        sys.exit(1)

    # Fix target lines
    for offset, src_idx in enumerate(src_indices):
        tgt_idx = args.tgt_start + offset
        tgt_lines[tgt_idx - 1]["output"] = src_lines[src_idx]
        print(f"Mapping: Target line {tgt_idx} -> Source line {src_idx}")

    # Overwrite target file
    with open(args.tgt_file, "w", encoding="utf-8") as f:
        for data in tgt_lines:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")

    print(f"Successfully aligned target lines {args.tgt_start}-{max_needed_tgt} with source lines.")

if __name__ == "__main__":
    main()
