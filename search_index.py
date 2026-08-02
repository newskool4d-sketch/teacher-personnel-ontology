"""검색 인덱스 생성 — 한글 초성 분해 포함"""
from schema import Node

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
        terms = [n.title, n.summary, n.body, *n.refs, *n.aliases]
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
