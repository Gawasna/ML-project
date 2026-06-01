"""
clean_dataset.py
----------------
Loại độc dữ liệu khỏi toàn bộ JSONL trong data/train/prepared/ bằng 6 bộ lọc thuật toán.

Filters (theo thứ tự chi phí tăng dần — early rejection):
  F1. Schema check     : bản ghi phải có đủ 3 field {instruction, input, output}
  F2. Empty/short      : input >= 3 tokens, output >= 3 tokens
  F3. Z-score length   : eng_len và vi_len nằm trong [mean ± 3*std] của chính file đó
  F4. Length ratio     : vi_len / eng_len nằm trong [0.3, 4.0]  (tiếng Việt thường dài hơn EN ~1.2–1.8x)
  F5. Script detection : output phải chứa >= 30% ký tự Latin + dấu tiếng Việt (lọc câu bị mã hoá lỗi, Latin chèn lộn)
  F6. Exact dedup      : hash SHA-1(input.strip() + "|||" + output.strip()) — loại bản ghi trùng lặp hoàn toàn

Output:
  - data/train/cleaned/<original_filename>  : file đã lọc
  - data/train/cleaned/cleaning_report.json : báo cáo chi tiết từng file
"""

import hashlib
import json
import os
import re
import sys
import time

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

INPUT_DIR   = Path(__file__).parent.parent / "data" / "train" / "prepared"
OUTPUT_DIR  = Path(__file__).parent.parent / "data" / "train" / "cleaned"
REPORT_PATH = OUTPUT_DIR / "cleaning_report.json"

# Files to skip (test/valid dùng riêng, không cần clean train pipeline)
SKIP_PATTERNS = {"test", "valid", ".gitkeep", "dataset", "README", ".rar"}

# F4: length ratio bounds (vi_words / eng_words)
RATIO_MIN = 0.3
RATIO_MAX = 4.0

# F5: minimum fraction of Vietnamese-compatible characters in output
# Vietnamese uses Latin + combining diacritics; Unicode block 0x00C0–0x024F + 0x1E00–0x1EFF
VI_CHAR_PATTERN = re.compile(r"[a-zA-ZÀ-ÿÁ-ỹ\u00C0-\u024F\u1E00-\u1EFF]")
VI_MIN_FRACTION = 0.30

# Z-score sample cap per file (avoid OOM on 2.87M file — sample first N for stats)
ZSCORE_SAMPLE_CAP = 200_000

# Streaming chunk size for large files
READ_CHUNK = 50_000


# ---------------------------------------------------------------------------
# Filter implementations
# ---------------------------------------------------------------------------

def has_valid_schema(record: dict) -> bool:
    """F1: required fields present and non-None."""
    return (
        isinstance(record.get("input"), str)
        and isinstance(record.get("output"), str)
        and isinstance(record.get("instruction"), str)
    )


def tokenize(text: str) -> list[str]:
    """Lightweight whitespace tokenizer — no NLTK dependency."""
    return text.split()


def passes_length_check(eng_tokens: list[str], vi_tokens: list[str]) -> bool:
    """F2: both sides must have at least 3 tokens."""
    return len(eng_tokens) >= 3 and len(vi_tokens) >= 3


def passes_ratio(eng_len: int, vi_len: int) -> bool:
    """F4: vi/eng word ratio guard."""
    if eng_len == 0:
        return False
    ratio = vi_len / eng_len
    return RATIO_MIN <= ratio <= RATIO_MAX


def vi_script_fraction(text: str) -> float:
    """F5: fraction of characters that are Vietnamese-alphabet compatible."""
    if not text:
        return 0.0
    vi_chars = len(VI_CHAR_PATTERN.findall(text))
    total_alpha = sum(1 for c in text if c.isalpha())
    if total_alpha == 0:
        return 0.0
    return vi_chars / total_alpha


def record_hash(inp: str, out: str) -> str:
    """F6: SHA-1 fingerprint for exact dedup."""
    key = f"{inp.strip()}|||{out.strip()}"
    return hashlib.sha1(key.encode("utf-8", errors="replace")).hexdigest()


# ---------------------------------------------------------------------------
# Two-pass approach for Z-score (F3)
# ---------------------------------------------------------------------------

def compute_zscore_bounds(jsonl_path: Path) -> tuple[tuple[float, float], tuple[float, float]]:
    """
    Pass 1: sample up to ZSCORE_SAMPLE_CAP records to compute
    (eng_mean, eng_std) and (vi_mean, vi_std).
    Returns ((eng_lo, eng_hi), (vi_lo, vi_hi)).
    """
    eng_lens: list[int] = []
    vi_lens: list[int] = []

    with open(jsonl_path, encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f):
            if i >= ZSCORE_SAMPLE_CAP:
                break
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not has_valid_schema(rec):
                continue
            eng_lens.append(len(tokenize(rec["input"])))
            vi_lens.append(len(tokenize(rec["output"])))

    if len(eng_lens) < 10:
        # Not enough data for stats — return very wide bounds (effectively disabled)
        return (0, 10_000), (0, 10_000)

    def bounds(vals: list[int]) -> tuple[float, float]:
        m = mean(vals)
        s = stdev(vals) if len(vals) > 1 else 0.0
        return max(0.0, m - 3 * s), m + 3 * s

    return bounds(eng_lens), bounds(vi_lens)


# ---------------------------------------------------------------------------
# Main cleaning loop
# ---------------------------------------------------------------------------

def clean_file(
    src_path: Path,
    dst_path: Path,
    seen_hashes: set[str],
    global_stats: dict,
) -> dict:
    """Clean a single JSONL file. Returns per-file stats dict."""

    print(f"\n  Scanning for Z-score bounds: {src_path.name}")
    t0 = time.perf_counter()
    eng_bounds, vi_bounds = compute_zscore_bounds(src_path)
    print(f"    eng bounds: [{eng_bounds[0]:.1f}, {eng_bounds[1]:.1f}]  "
          f"vi bounds: [{vi_bounds[0]:.1f}, {vi_bounds[1]:.1f}]  "
          f"({time.perf_counter()-t0:.1f}s)")

    stats = defaultdict(int)
    dst_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"  Filtering: {src_path.name}")
    t1 = time.perf_counter()

    with (
        open(src_path, encoding="utf-8", errors="replace") as fin,
        open(dst_path, "w", encoding="utf-8") as fout,
    ):
        for line in fin:
            line = line.strip()
            if not line:
                continue

            stats["total"] += 1

            # F1: schema
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                stats["dropped_schema"] += 1
                continue
            if not has_valid_schema(rec):
                stats["dropped_schema"] += 1
                continue

            eng_tokens = tokenize(rec["input"])
            vi_tokens  = tokenize(rec["output"])
            eng_len    = len(eng_tokens)
            vi_len     = len(vi_tokens)

            # F2: min length
            if not passes_length_check(eng_tokens, vi_tokens):
                stats["dropped_length"] += 1
                continue

            # F3: Z-score bounds
            if not (eng_bounds[0] <= eng_len <= eng_bounds[1]):
                stats["dropped_zscore_eng"] += 1
                continue
            if not (vi_bounds[0] <= vi_len <= vi_bounds[1]):
                stats["dropped_zscore_vi"] += 1
                continue

            # F4: length ratio
            if not passes_ratio(eng_len, vi_len):
                stats["dropped_ratio"] += 1
                continue

            # F5: Vietnamese script check
            frac = vi_script_fraction(rec["output"])
            if frac < VI_MIN_FRACTION:
                stats["dropped_script"] += 1
                continue

            # F6: dedup (global — across all files)
            h = record_hash(rec["input"], rec["output"])
            if h in seen_hashes:
                stats["dropped_dedup"] += 1
                continue
            seen_hashes.add(h)

            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
            stats["kept"] += 1

            # Progress heartbeat every 500k
            if stats["total"] % 500_000 == 0:
                elapsed = time.perf_counter() - t1
                rate = stats["total"] / elapsed / 1000
                print(f"    [{src_path.name}] {stats['total']:,} processed, "
                      f"{stats['kept']:,} kept | {rate:.0f}k rec/s")

    elapsed = time.perf_counter() - t1
    drop_total = stats["total"] - stats["kept"]
    drop_pct   = drop_total / stats["total"] * 100 if stats["total"] > 0 else 0

    print(f"    Done in {elapsed:.1f}s | "
          f"{stats['kept']:,} kept / {stats['total']:,} total "
          f"({drop_pct:.1f}% dropped)")
    print(f"    Breakdown — schema:{stats['dropped_schema']} "
          f"length:{stats['dropped_length']} "
          f"zscore_eng:{stats['dropped_zscore_eng']} "
          f"zscore_vi:{stats['dropped_zscore_vi']} "
          f"ratio:{stats['dropped_ratio']} "
          f"script:{stats['dropped_script']} "
          f"dedup:{stats['dropped_dedup']}")

    return dict(stats)


def main():
    print("=" * 70)
    print("Dataset Cleaner — 6-filter pipeline")
    print(f"  Input  : {INPUT_DIR}")
    print(f"  Output : {OUTPUT_DIR}")
    print("=" * 70)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Collect files to process (skip test/valid/non-jsonl)
    src_files = sorted(
        p for p in INPUT_DIR.glob("*.jsonl")
        if not any(pat in p.name for pat in SKIP_PATTERNS)
    )

    if not src_files:
        print("No training JSONL files found. Check INPUT_DIR.")
        sys.exit(1)

    print(f"\nFiles to process ({len(src_files)}):")
    for p in src_files:
        size_mb = p.stat().st_size / 1024 / 1024
        print(f"  {p.name:<50} {size_mb:>8.1f} MB")

    # Global dedup hash set — shared across all files
    seen_hashes: set[str] = set()
    all_report: dict[str, dict] = {}
    t_global = time.perf_counter()

    for src_path in src_files:
        dst_path = OUTPUT_DIR / src_path.name
        print(f"\n{'─'*70}".encode('ascii', 'replace').decode('ascii').replace(b'?'.decode(), '-'))
        print(f"Processing: {src_path.name}")
        file_stats = clean_file(src_path, dst_path, seen_hashes, all_report)
        all_report[src_path.name] = file_stats

    # Summary
    total_in  = sum(s.get("total", 0) for s in all_report.values())
    total_out = sum(s.get("kept", 0) for s in all_report.values())
    elapsed_total = time.perf_counter() - t_global

    print(f"\n{'='*70}")
    print("CLEANING COMPLETE")
    print(f"  Total processed : {total_in:>12,}")
    print(f"  Total kept      : {total_out:>12,}")
    print(f"  Total dropped   : {total_in - total_out:>12,}  ({(total_in-total_out)/total_in*100:.1f}%)")
    print(f"  Elapsed         : {elapsed_total/60:.1f} min")
    print(f"  Unique hash set : {len(seen_hashes):,} entries in RAM")

    # Write JSON report
    report_data = {
        "summary": {
            "total_input": total_in,
            "total_kept": total_out,
            "total_dropped": total_in - total_out,
            "drop_pct": round((total_in - total_out) / total_in * 100, 2) if total_in else 0,
            "elapsed_seconds": round(elapsed_total, 1),
            "unique_pairs_kept": len(seen_hashes),
        },
        "per_file": all_report,
    }
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    print(f"\n  Report saved: {REPORT_PATH}")
    print("=" * 70)


if __name__ == "__main__":
    main()
