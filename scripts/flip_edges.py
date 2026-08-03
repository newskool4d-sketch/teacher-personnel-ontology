"""엣지 방향 불일치 정리: ch4~6의 '수치→개관, type: 상위개념' 33건을
ch3 패턴('개관→수치, type: 기한수치')으로 통일한다.
"""
import re

with open("edges.yaml", encoding="utf-8") as fh:
    lines = fh.readlines()

pattern = re.compile(
    r"^- \{source: (num-[a-z0-9-]+), target: ([a-z0-9-]+), type: 상위개념\}\s*$"
)

flipped = 0
out = []
for line in lines:
    m = pattern.match(line)
    if m:
        num_id, overview_id = m.group(1), m.group(2)
        out.append(f"- {{source: {overview_id}, target: {num_id}, type: 기한수치}}\n")
        flipped += 1
    else:
        out.append(line)

with open("edges.yaml", "w", encoding="utf-8") as fh:
    fh.writelines(out)

print(f"flipped {flipped} edges")
