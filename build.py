"""전체 빌드 파이프라인: 로드 -> 검증 -> 레이아웃 -> 검색인덱스 -> 템플릿 주입 -> dist 출력"""
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
        "확인필요",
        "세부 적용은 소속 시·도교육청 지침 또는 관련 법령 확인",
    )
    result = re.sub(r",\s*,", ",", result)
    result = re.sub(r"\(\s*,", "(", result)
    result = re.sub(r",\s*\)", ")", result)
    result = re.sub(r"\(\s*\)", "", result)
    return result


def sanitize_public_value(value):
    if isinstance(value, str):
        return sanitize_public_text(value)
    if isinstance(value, list):
        return [sanitize_public_value(item) for item in value]
    if isinstance(value, dict):
        return {key: sanitize_public_value(item) for key, item in value.items()}
    return value


def public_node_dict(node) -> dict:
    """내부 검증 메타데이터를 제외한 공개용 노드 사전을 만든다."""
    data = sanitize_public_value(asdict(node))
    data["refs"] = [
        ref for ref in data.get("refs", [])
        if ref.strip() != "세부 적용은 소속 시·도교육청 지침 또는 관련 법령 확인"
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


def build(nodes_dir=NODES_DIR, edges_path=EDGES_PATH, template_path=TEMPLATE_PATH, dist_path=DIST_PATH) -> Path:
    nodes = load_nodes(nodes_dir)
    edges = load_edges(edges_path)

    errors = validate_graph(nodes, edges)
    if errors:
        raise SystemExit(f"스키마 검증 실패 ({len(errors)}건):\n" + "\n".join(errors))

    coords = compute_layout(nodes, edges)
    search_idx = sanitize_public_value(build_search_index(nodes))

    node_dicts = []
    for n in nodes:
        node_dicts.append(public_node_dict(n))

    data = {
        "nodes": node_dicts,
        "edges": [asdict(e) for e in edges],
        "layout": coords,
        "search": search_idx,
        "meta": {"nodeCount": len(nodes), "edgeCount": len(edges)},
    }

    template_html = Path(template_path).read_text(encoding="utf-8")
    data_json = json.dumps(data, ensure_ascii=False)
    output_html = template_html.replace("__ONTOLOGY_DATA__", data_json)

    dist_path = Path(dist_path)
    dist_path.parent.mkdir(parents=True, exist_ok=True)
    dist_path.write_text(output_html, encoding="utf-8")
    print(f"빌드 완료: {dist_path} (노드 {len(nodes)}개, 엣지 {len(edges)}개)")
    return dist_path


if __name__ == "__main__":
    build()
