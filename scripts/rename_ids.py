"""id 명명 규약 통일: 교육공무원법 접두사 통일 + num- 접두사 강제.

- 교육공무원법 조문 id를 law-gyoyukgongmuwon-* 로 통일 (기존 law-gongmuwon-*, law-gyoyuggongmuwonbeop-* 혼재 정리)
- 공무원보수규정(교육공무원법이 아님, gukgong-*과도 다름) id는 law-bosugyujeong-* 로 분리
- 수치·기한 타입 노드 중 num- 접두사가 없는 8건에 num- 접두사 부여

nodes/*.yaml, edges.yaml 전체에서 정규식 경계 매치로 일괄 치환한다.
"""
import glob
import re

RENAME_MAP = {
    "law-gyoyuggongmuwon-act": "law-gyoyukgongmuwon-act",
    "law-gongmuwon-2": "law-gyoyukgongmuwon-2",
    "law-gongmuwon-44": "law-gyoyukgongmuwon-44",
    "law-gongmuwon-45": "law-gyoyukgongmuwon-45",
    "law-gongmuwon-qualification": "law-gyoyukgongmuwon-qualification",
    "law-gyoyuggongmuwonbeop-32": "law-gyoyukgongmuwon-32",
    "law-gongmuwon-bosu-14": "law-bosugyujeong-14",
    "moonlight-approval-period": "num-moonlight-approval-period",
    "moonlight-survey": "num-moonlight-survey",
    "moonlight-hour-limit": "num-moonlight-hour-limit",
    "outside-lecture-fee": "num-outside-lecture-fee",
    "outside-lecture-approval": "num-outside-lecture-approval",
    "work-hours-teacher": "num-work-hours-teacher",
    "work-business-trip-distance": "num-work-business-trip-distance",
    "work-part-time": "num-work-part-time",
}

FILES = sorted(glob.glob("nodes/*.yaml")) + ["edges.yaml"]

# 긴 id부터 치환(부분 문자열 충돌 방지) + 앞뒤가 [a-z0-9]가 아닐 때만 매치(경계 보장)
ordered = sorted(RENAME_MAP.items(), key=lambda kv: -len(kv[0]))
patterns = [
    (re.compile(r"(?<![a-z0-9])" + re.escape(old) + r"(?![a-z0-9])"), new)
    for old, new in ordered
]

total_subs = 0
for path in FILES:
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    new_text = text
    for pat, new in patterns:
        new_text, n = pat.subn(new, new_text)
        total_subs += n
    if new_text != text:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(new_text)
        print(f"updated {path}")

print(f"total substitutions: {total_subs}")
