#!/usr/bin/env python3
"""
Validate .jsonl dataset files — format + duplicate detection.
Usage:
  python scripts/validate_dataset.py                   # toàn bộ data/train/
  python scripts/validate_dataset.py --file foo.jsonl  # 1 file
  python scripts/validate_dataset.py --similarity 0.9  # ngưỡng fuzzy (default 0.85)
"""
import json, hashlib, argparse, sys
from pathlib import Path

DATA_DIR       = Path("data/train")
REQUIRED_KEYS  = {"instruction", "output"}
MAX_INSTR_LEN  = 2000
MAX_OUT_LEN    = 8000

def normalize(t): return " ".join(t.lower().split())
def sha(t):       return hashlib.sha256(normalize(t).encode()).hexdigest()
def ngrams(t, n=3):
    t = normalize(t)
    return set(t[i:i+n] for i in range(len(t)-n+1))
def jaccard(a, b):
    if not a and not b: return 1.0
    return len(a & b) / len(a | b)

class Validator:
    def __init__(self, threshold=0.85):
        self.threshold = threshold
        self.errors    = []
        self.warnings  = []
        self.seen_hash = {}      # sha → (file, line)
        self.seen_ng   = []      # [(ngrams, file, line, preview)]

    def err(self, m):  self.errors.append(m);   print(f"  [ERROR] {m}")
    def warn(self, m): self.warnings.append(m); print(f"  [WARN]  {m}")

    def check(self, rec, fpath, lno):
        ok = True
        miss = REQUIRED_KEYS - rec.keys()
        if miss:
            self.err(f"{fpath}:{lno} — Thiếu field: {miss}"); return False

        ins, out = rec.get("instruction",""), rec.get("output","")
        if not ins.strip(): self.err(f"{fpath}:{lno} — instruction rỗng"); ok=False
        if not out.strip(): self.err(f"{fpath}:{lno} — output rỗng");      ok=False
        if len(ins) > MAX_INSTR_LEN: self.warn(f"{fpath}:{lno} — instruction quá dài ({len(ins)})")
        if len(out) > MAX_OUT_LEN:   self.warn(f"{fpath}:{lno} — output quá dài ({len(out)})")

        h = sha(ins)
        if h in self.seen_hash:
            pf, pl = self.seen_hash[h]
            self.err(f"{fpath}:{lno} — TRÙNG CHÍNH XÁC với {pf}:{pl} → \"{ins[:60]}\"")
            ok = False
        else:
            self.seen_hash[h] = (fpath, lno)

        ng = ngrams(ins)
        for pngs, pf, pl, pv in self.seen_ng:
            sim = jaccard(ng, pngs)
            if sim >= self.threshold:
                self.warn(f"{fpath}:{lno} — Có thể trùng ({sim:.0%}) với {pf}:{pl}\n"
                          f"           Hiện tại: \"{ins[:60]}\"\n"
                          f"           Trước đó: \"{pv[:60]}\"")
        self.seen_ng.append((ng, fpath, lno, ins))
        return ok

    def validate_file(self, path):
        ok = err = 0
        print(f"\nKiểm tra: {path}")
        with open(path, encoding="utf-8") as f:
            for lno, raw in enumerate(f, 1):
                raw = raw.strip()
                if not raw: continue
                try:    rec = json.loads(raw)
                except json.JSONDecodeError as e:
                    self.err(f"{path}:{lno} — JSON không hợp lệ: {e}"); err+=1; continue
                if self.check(rec, str(path), lno): ok+=1
                else: err+=1
        return ok, err

    def report(self):
        print("\n" + "═"*55)
        print(f"Kết quả: {len(self.errors)} lỗi  |  {len(self.warnings)} cảnh báo")
        if self.errors:
            print("CI FAIL — sửa lỗi trên rồi push lại."); return False
        print("OK!" if not self.warnings else "PASS — xem xét các cảnh báo.")
        return True

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--file",       type=Path)
    p.add_argument("--dir",        type=Path, default=DATA_DIR)
    p.add_argument("--similarity", type=float, default=0.85)
    args = p.parse_args()

    v = Validator(args.similarity)
    tok = terr = 0
    files = [args.file] if args.file else sorted(args.dir.glob("**/*.jsonl"))
    if not files:
        print(f"Không tìm thấy .jsonl trong {args.dir}"); sys.exit(1)
    for f in files:
        ok, err = v.validate_file(f); tok+=ok; terr+=err
    print(f"\nTổng: {tok+terr} records  |  {tok} hợp lệ  |  {terr} lỗi")
    sys.exit(0 if v.report() else 1)

if __name__ == "__main__": main()
