"""전체 빌드 파이프라인: 로드 -> 검증 -> 레이아웃 -> 검색인덱스 -> 템플릿 주입 -> dist 출력"""
import datetime
import json
import re
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from schema import load_nodes, load_edges, validate_graph
from layout import compute_layout
from search_index import build_search_index
import markdown as md_lib

BASE = Path(__file__).parent
NODES_DIR = BASE / "nodes"
EDGES_PATH = BASE / "edges.yaml"
TEMPLATE_PATH = BASE / "template.html"
DIST_PATH = BASE / "dist" / "교원인사_온톨로지.html"


PUBLIC_TEXT_REPLACEMENTS = (
    ("korean-law-mcp로 직접 확인됨", "현행 법령 원문에서 직접 확인됨"),
    ("korean-law-mcp 직접 확인됨", "현행 법령 원문에서 직접 확인됨"),
    ("korean-law-mcp로 원문 확인", "현행 법령 원문 대조 완료"),
    ("korean-law-mcp에서 원문 확인", "현행 법령 원문 대조 완료"),
    ("korean-law-mcp 조회 결과", "현행 법령 조회 결과"),
    ("korean-law-mcp 확인", "현행 법령 원문 확인"),
    ("korean-law-mcp로", "현행 법령 원문으로"),
    ("korean-law-mcp에서", "현행 법령 원문에서"),
    ("korean-law-mcp", "현행 법령 원문"),
)


def sanitize_public_text(text: str) -> str:
    """공개 HTML에서 내부 조회 도구명과 데이터베이스 식별자를 제거한다."""
    result = text
    for internal, public in PUBLIC_TEXT_REPLACEMENTS:
        result = result.replace(internal, public)
    result = re.sub(r"\bMST\s*\d+", "", result, flags=re.IGNORECASE)
    result = re.sub(r"(?:법령ID|행정규칙일련번호|행정규칙ID)\s*\d+", "", result)
    result = re.sub(r"현행 법령 원문\s+원문\s*확인", "현행 법령 원문 확인", result)
    result = re.sub(r"현행 법령 원문으로\s+원문\s*확인", "현행 법령 원문 확인", result)
    result = re.sub(
        r"이번 조회의 API 응답에\s*전문이 표시되지 않았다\s*—\s*목록 형태 재조회 시 원문 대조 권장\.?",
        "세부 각 목은 공식 법령 원문에서 추가 확인이 필요하다.",
        result,
    )
    result = result.replace("API 응답", "공식 조회 자료")
    result = result.replace(
        "세부 확인필요",
        "세부 사항은 관련 법령 및 소속 시·도교육청 지침에서 확인",
    )
    result = result.replace(
        "확인필요",
        "관련 법령 및 소속 시·도교육청 지침에서 확인",
    )
    result = re.sub(r",\s*,", ",", result)
    result = re.sub(r"\(\s*,", "(", result)
    result = re.sub(r",\s*\)", ")", result)
    result = re.sub(r"\(\s*\)", "", result)
    # 식별자를 지운 자리에 남는 군더더기 공백 정리(마크다운 들여쓰기·표는 건드리지 않는다)
    result = re.sub(r"\([ \t]+", "(", result)
    result = re.sub(r"[ \t]+\)", ")", result)
    result = re.sub(r",[ \t]{2,}", ", ", result)
    return result


def sanitize_public_value(value):
    if isinstance(value, str):
        return sanitize_public_text(value)
    if isinstance(value, list):
        return [sanitize_public_value(item) for item in value]
    if isinstance(value, dict):
        return {key: sanitize_public_value(item) for key, item in value.items()}
    return value


def public_pages(pages: dict) -> dict:
    """pages 필드는 원문 쪽수 표기용이므로 문장형 치환 대상에서 제외하고,
    '확인필요' placeholder는 빈 값으로 비워 template의 '원문 쪽수 미기재' 폴백을 쓴다."""
    return {
        scope: ("" if value.strip() == "확인필요" else value)
        for scope, value in (pages or {}).items()
    }


def public_node_dict(node) -> dict:
    """내부 검증 메타데이터를 제외한 공개용 노드 사전을 만든다."""
    raw = asdict(node)
    pages = raw.pop("pages", {})
    data = sanitize_public_value(raw)
    data["pages"] = public_pages(pages)
    data["refs"] = [
        ref for ref in data.get("refs", [])
        if ref.strip() != "관련 법령 및 소속 시·도교육청 지침에서 확인"
    ]
    data["body"] = render_body(sanitize_public_text(node.body)) if node.body else ""

    review = data.get("legal_review") or {}
    if review:
        review.pop("method", None)
        for source in review.get("sources", []):
            source.pop("mst", None)
    return data


def render_body(raw_md: str) -> str:
    return md_lib.markdown(raw_md, extensions=["tables"])


# 공개 화면에 남아서는 안 되는 표현 — 내부 조회 도구·식별자와 일반 독자가 모르는 그래프 용어
FORBIDDEN_PUBLIC_TERMS = (
    ("내부 조회 도구명", re.compile(r"korean-law-mcp")),
    ("내부 식별자", re.compile(r"\bMST\b|법령ID|행정규칙일련번호|행정규칙ID")),
    ("그래프 전문용어", re.compile(r"노드|엣지|온톨로지")),
    ("영문 기술용어", re.compile(r"\bAPI\b|\brefs\b|\bcaveat\b|\bplaceholder\b")),
    ("내부 조회 함수명", re.compile(r"\b(?:get|search|legal)_[a-z_]+\b")),
)


def assert_public_text_clean(public_nodes: list[dict], search: list[dict], node_ids: set[str]) -> None:
    """공개 텍스트에 내부 용어나 영문 항목 ID가 남아 있으면 빌드를 중단한다.

    본문 상호참조는 `[한글 제목](#/node/아이디)` 링크로만 노출되어야 하며,
    링크 href는 검사 대상에서 제외한다. 화면에 그려지는 노드 텍스트와
    검색어로 쓰이는 haystack을 함께 검사한다.
    """
    id_like = re.compile(r"(?<![\w/#-])([a-z][a-z0-9]*(?:-[a-z0-9]+)+)(?![\w-])")
    problems: list[str] = []

    targets = [(d["id"], "본문", f"{d['title']}\n{d['summary']}\n{d['body']}") for d in public_nodes]
    targets += [(d["id"], "검색어", d["haystack"]) for d in search]

    for node_id, where, text in targets:
        if where == "검색어" and "#/node/" in text:
            problems.append(
                f"[{node_id}] 검색어에 링크 주소가 남음 — 검색 인덱스는 보이는 제목만 담아야 함"
            )
        visible = re.sub(r'href="#/node/[a-z0-9-]+"', "", text)

        for label, pattern in FORBIDDEN_PUBLIC_TERMS:
            found = pattern.search(visible)
            if found:
                problems.append(f"[{node_id}] {where}에 {label} 노출: {found.group(0)!r}")

        for match in id_like.finditer(visible):
            if match.group(1) in node_ids:
                problems.append(
                    f"[{node_id}] {where}에 영문 항목 ID 노출: {match.group(1)!r} "
                    "— `[한글 제목](#/node/아이디)` 형태의 링크로 작성할 것"
                )

    # 괄호가 이어진 문장이 마크다운 링크로 잘못 변환되면 본문이 깨진 링크가 된다
    for data in public_nodes:
        for href in re.findall(r'<a href="([^"]*)"', data["body"]):
            if not (href.startswith("#/node/") or href.startswith("http")):
                problems.append(
                    f"[{data['id']}] 잘못된 본문 링크 주소: {href!r} "
                    "— 대괄호 뒤에 괄호가 이어져 마크다운 링크로 해석된 것은 아닌지 확인할 것"
                )

    if problems:
        raise SystemExit(
            f"공개 텍스트 검사 실패 ({len(problems)}건):\n" + "\n".join(problems)
        )


def latest_review_date(nodes) -> str:
    """전체 노드의 legal_review.checked_at 중 최댓값(가장 최근 검토일)을 구한다."""
    dates = [
        n.legal_review["checked_at"]
        for n in nodes
        if n.legal_review and n.legal_review.get("checked_at")
    ]
    return max(dates) if dates else datetime.date.today().isoformat()


def format_korean_date(iso_date: str) -> str:
    year, month, day = iso_date.split("-")
    return f"{year}. {int(month)}. {int(day)}."


def build_payload(nodes, edges) -> dict:
    """검증된 도메인 객체를 공개 HTML에 주입할 직렬화 payload로 변환한다."""
    errors = validate_graph(nodes, edges)
    if errors:
        raise SystemExit(f"스키마 검증 실패 ({len(errors)}건):\n" + "\n".join(errors))

    public_nodes = [public_node_dict(node) for node in nodes]
    search = sanitize_public_value(build_search_index(nodes))
    assert_public_text_clean(public_nodes, search, {node.id for node in nodes})

    return {
        "nodes": public_nodes,
        "edges": [asdict(e) for e in edges],
        "layout": compute_layout(nodes, edges),
        "search": search,
        "meta": {"nodeCount": len(nodes), "edgeCount": len(edges)},
    }


def build(nodes_dir=NODES_DIR, edges_path=EDGES_PATH, template_path=TEMPLATE_PATH, dist_path=DIST_PATH) -> Path:
    nodes = load_nodes(nodes_dir)
    edges = load_edges(edges_path)
    data = build_payload(nodes, edges)

    template_html = Path(template_path).read_text(encoding="utf-8")
    data_json = json.dumps(data, ensure_ascii=False)
    output_html = template_html.replace("__ONTOLOGY_DATA__", data_json)
    output_html = output_html.replace("__BUILD_DATE__", datetime.date.today().isoformat())
    output_html = output_html.replace("__REVIEW_AS_OF__", format_korean_date(latest_review_date(nodes)))

    dist_path = Path(dist_path)
    dist_path.parent.mkdir(parents=True, exist_ok=True)
    dist_path.write_text(output_html, encoding="utf-8")
    print(f"빌드 완료: {dist_path} (노드 {len(nodes)}개, 엣지 {len(edges)}개)")
    return dist_path


if __name__ == "__main__":
    build()
