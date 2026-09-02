"""검색 인덱스 생성 — 한글 초성 분해 포함"""
import re

from schema import Node

# 본문 상호참조 링크 `[한글 제목](#/node/아이디)` — 검색어에는 보이는 제목만 남긴다.
# 제목 안에 대괄호가 들어가는 경우까지 링크 전체를 잡아내야 주소가 검색어에 새지 않는다.
BODY_LINK = re.compile(r"\[((?:[^\[\]]|\[[^\[\]]*\])+)\]\(#/node/[a-z0-9-]+\)")

CHOSUNG = ["ㄱ", "ㄲ", "ㄴ", "ㄷ", "ㄸ", "ㄹ", "ㅁ", "ㅂ", "ㅃ", "ㅅ", "ㅆ",
           "ㅇ", "ㅈ", "ㅉ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ"]
HANGUL_BASE = 0xAC00
HANGUL_END = 0xD7A3
JUNG_COUNT = 21
JONG_COUNT = 28


def to_chosung(text: str) -> str:
    result = []
    for ch in text:
        code = ord(ch)
        if HANGUL_BASE <= code <= HANGUL_END:
            idx = (code - HANGUL_BASE) // (JUNG_COUNT * JONG_COUNT)
            result.append(CHOSUNG[idx])
        else:
            result.append(ch)
    return "".join(result)


def build_search_index(nodes: list[Node]) -> list[dict]:
    index = []
    for n in nodes:
        terms = [n.title, n.summary, BODY_LINK.sub(r"\1", n.body), *n.refs, *n.aliases]
        haystack = " ".join(terms)
        index.append({
            "id": n.id,
            "title": n.title,
            "summary": n.summary,
            "type": n.type,
            "chapter": n.chapter,
            "scope": n.scope,
            "pages": n.pages,
            "chosung": to_chosung(haystack),
            "haystack": haystack,
        })
    return index
