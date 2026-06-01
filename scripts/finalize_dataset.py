"""
finalize_dataset.py
-------------------
Bước hoàn thiện sau clean_dataset.py:

  1. Xóa train_EVB_42987.jsonl khỏi cleaned/ (duplicate hoàn toàn của thoisu_3)
  2. Re-clean train_895_thoisu_4.jsonl với hard length cap (eng<=150, vi<=200 tokens)
     vì file chứa toàn bài báo toàn văn, Z-score không lọc được.
  3. Nén toàn bộ cleaned/*.jsonl thành prepared.rar tại
     data/train/prepared/clean/prepared.rar
"""

import json
import os
import subprocess
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent.parent
CLEANED_DIR  = PROJECT_ROOT / "data" / "train" / "cleaned"
OUTPUT_RAR   = PROJECT_ROOT / "data" / "train" / "prepared" / "clean" / "prepared.rar"
WINRAR_EXE   = Path(r"C:\Program Files\WinRAR\rar.exe")

# Hard length cap for document-level file (train_895)
ENG_HARD_MAX = 150   # words
VI_HARD_MAX  = 200   # words

# ---------------------------------------------------------------------------
# Step 1: Remove EVB42987 from cleaned dir (already 0 records, just delete)
# ---------------------------------------------------------------------------

def step1_remove_evb():
    evb_file = CLEANED_DIR / "train_EVB_42987.jsonl"
    if evb_file.exists():
        evb_file.unlink()
        print(f"[Step 1] Removed: {evb_file.name}")
    else:
        print("[Step 1] train_EVB_42987.jsonl already absent — skip")


# ---------------------------------------------------------------------------
# Step 2: Re-clean train_895_thoisu_4.jsonl with hard length cap
#         Source: original prepared/, not cleaned/ (to re-apply all filters fresh)
# ---------------------------------------------------------------------------

def step2_reclean_895():
    src = PROJECT_ROOT / "data" / "train" / "prepared" / "train_895_thoisu_4.jsonl"
    dst = CLEANED_DIR / "train_895_thoisu_4.jsonl"

    if not src.exists():
        print(f"[Step 2] Source not found: {src} — skip")
        return

    kept = dropped_short = dropped_cap = dropped_ratio = 0
    seen: set[str] = set()

    with open(src, encoding="utf-8", errors="replace") as fin, \
         open(dst, "w", encoding="utf-8") as fout:

        for line in fin:
            line = line.strip()
            if not line:
                continue

            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                dropped_short += 1
                continue

            inp = rec.get("input", "")
            out = rec.get("output", "")
            if not isinstance(inp, str) or not isinstance(out, str):
                dropped_short += 1
                continue

            eng_tokens = inp.split()
            vi_tokens  = out.split()
            eng_len    = len(eng_tokens)
            vi_len     = len(vi_tokens)

            # F2: min 3 tokens each side
            if eng_len < 3 or vi_len < 3:
                dropped_short += 1
                continue

            # Hard cap: reject document-length records entirely
            # (truncation would corrupt the translation pair)
            if eng_len > ENG_HARD_MAX or vi_len > VI_HARD_MAX:
                dropped_cap += 1
                continue

            # Ratio guard
            ratio = vi_len / eng_len
            if not (0.3 <= ratio <= 4.0):
                dropped_ratio += 1
                continue

            # Dedup within file
            key = f"{inp.strip()}|||{out.strip()}"
            import hashlib
            h = hashlib.sha1(key.encode("utf-8", errors="replace")).hexdigest()
            if h in seen:
                continue
            seen.add(h)

            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
            kept += 1

    total = kept + dropped_short + dropped_cap + dropped_ratio
    print(f"[Step 2] train_895_thoisu_4.jsonl re-cleaned:")
    print(f"         total={total}  kept={kept}  "
          f"short={dropped_short}  cap(>{ENG_HARD_MAX}eng|{VI_HARD_MAX}vi)={dropped_cap}  "
          f"ratio={dropped_ratio}")


# ---------------------------------------------------------------------------
# Step 3: Pack all cleaned JSONL into prepared.rar with WinRAR
# ---------------------------------------------------------------------------

def step3_pack_rar():
    OUTPUT_RAR.parent.mkdir(parents=True, exist_ok=True)

    # Collect all cleaned jsonl files
    files = sorted(CLEANED_DIR.glob("*.jsonl"))
    if not files:
        print("[Step 3] No JSONL files found in cleaned/ — abort")
        return

    print(f"[Step 3] Packing {len(files)} files into RAR:")
    for f in files:
        size_mb = f.stat().st_size / 1024 / 1024
        print(f"         {f.name:<50} {size_mb:>8.1f} MB")

    # Remove existing RAR first (WinRAR appends by default)
    if OUTPUT_RAR.exists():
        OUTPUT_RAR.unlink()
        print(f"         Removed existing: {OUTPUT_RAR.name}")

    # Build WinRAR command
    # -m3  : compression level 3 (normal) — good balance speed/size for text
    # -ep  : exclude paths from names (store filenames only, no dir prefix)
    # -y   : assume Yes to all queries
    cmd = [
        str(WINRAR_EXE),
        "a",            # add to archive
        "-m3",          # compression level normal
        "-ep",          # no path prefix in archive
        "-y",           # no prompts
        str(OUTPUT_RAR),
    ] + [str(f) for f in files]

    print(f"\n         Running WinRAR...")
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")

    if result.returncode == 0:
        rar_size = OUTPUT_RAR.stat().st_size / 1024 / 1024
        print(f"[Step 3] RAR created: {OUTPUT_RAR}")
        print(f"         Archive size: {rar_size:.1f} MB")
    else:
        print(f"[Step 3] WinRAR failed (exit {result.returncode})")
        print(result.stdout[-2000:] if result.stdout else "")
        print(result.stderr[-500:] if result.stderr else "")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 70)
    print("Finalize Dataset — 3 steps")
    print("=" * 70)

    step1_remove_evb()
    print()
    step2_reclean_895()
    print()
    step3_pack_rar()

    print("\n" + "=" * 70)
    print("DONE — cleaned dataset packed and ready for Colab upload.")
    print(f"  RAR: {OUTPUT_RAR}")
    print("=" * 70)


if __name__ == "__main__":
    main()
