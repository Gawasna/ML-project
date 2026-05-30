import json

src_file = "extracted_the_gioi.jsonl"
tgt_file = "translated_the_gioi.jsonl"

# 1. Fetch exact source texts
oconnor_src = None
f35_src = None
roundup1_src = None
roundup2_src = None

kw_oconnor = "Bác sĩ của Nhà Trắng, TS. Kevin O'Connor khẳng định ông Biden không tái phát"
kw_f35 = "Không quân Mỹ đã tạm dừng bay với toàn bộ phi đội tiêm kích tàng hình F-35 Joint Strike Fighter"
kw_roundup1 = "Thống đốc bang Kentucky Andy Beshear cho biết con số này dự kiến tăng lên"
kw_roundup2 = "Tranh cãi về vụ pháo kích nhà tù Olenivka" # Unique inside the long war roundup

with open(src_file, "r", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            data = json.loads(line)
            vi = data.get("output", "")
            if kw_oconnor in vi:
                oconnor_src = vi
            if kw_f35 in vi:
                f35_src = vi
            if kw_roundup1 in vi:
                roundup1_src = vi
            if kw_roundup2 in vi:
                # Make sure it's the long war roundup (around 3200+ characters)
                if len(vi) > 3000 and "Igor Konashenkov" in vi:
                    roundup2_src = vi

if not oconnor_src or not f35_src or not roundup1_src or not roundup2_src:
    print(f"Error finding source texts! Oconnor={bool(oconnor_src)}, F35={bool(f35_src)}, Roundup1={bool(roundup1_src)}, Roundup2={bool(roundup2_src)}")
    exit(1)

print("Found source texts:")
print(f"Oconnor length: {len(oconnor_src)}")
print(f"F35 length: {len(f35_src)}")
print(f"Roundup1 length: {len(roundup1_src)}")
print(f"Roundup2 length: {len(roundup2_src)}")

# 2. Read target file and update
updated = 0
new_lines = []

with open(tgt_file, "r", encoding="utf-8") as f:
    for line_num, line in enumerate(f, 1):
        if line.strip():
            data = json.loads(line)
            vi = data.get("output", "")
            
            # Identify and update
            if kw_oconnor in vi:
                if vi != oconnor_src:
                    print(f"Updating Oconnor text at line {line_num}...")
                    data["output"] = oconnor_src
                    updated += 1
            elif kw_f35 in vi:
                if vi != f35_src:
                    print(f"Updating F35 text at line {line_num}...")
                    data["output"] = f35_src
                    updated += 1
            elif kw_roundup1 in vi:
                if vi != roundup1_src:
                    print(f"Updating Roundup1 text at line {line_num}...")
                    data["output"] = roundup1_src
                    updated += 1
            elif kw_roundup2 in vi:
                if vi != roundup2_src:
                    print(f"Updating Roundup2 text at line {line_num}...")
                    data["output"] = roundup2_src
                    updated += 1
            
            new_lines.append(json.dumps(data, ensure_ascii=False) + "\n")
        else:
            new_lines.append(line)

# 3. Write back target file
if updated > 0:
    with open(tgt_file, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    print(f"Successfully updated {updated} records in {tgt_file}!")
else:
    print("No updates needed, target file already matches.")
