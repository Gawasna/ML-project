import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

with open("translated_the_gioi.jsonl", "r", encoding="utf-8") as f:
    lines = f.read().splitlines()

print(f"Current lines: {len(lines)}")
# Keep only first 301 lines
lines_301 = lines[:301]

with open("translated_the_gioi.jsonl", "w", encoding="utf-8") as f:
    for line in lines_301:
        f.write(line + "\n")

print("Successfully restored translated file to exactly 301 lines!")
