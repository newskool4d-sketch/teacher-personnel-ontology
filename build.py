"""전체 빌드 파이프라인: 로드 -> 검증 -> 레이아웃 -> 검색인덱스 -> 템플릿 주입 -> dist 출력"""
import json
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


def render_body(raw_md: str) -> str:
    return md_lib.markdown(raw_md, extensions=["tables"])


def _embed_json(payload: object) -> str:
    # <script> 블록에 그대로 삽입되므로 HTML/JS를 깨는 문자를 이스케이프한다.
    # (node title/summary/body에 </script> 리터럴이 있어도 스크립트 조기 종료를
    # 막는다. JSON 값 안에서는 JS가 동일 문자로 디코딩해 표시에는 영향 없음.)
    text = json.dumps(payload, ensure_ascii=False)
    esc = chr(92)  # backslash for \uXXXX JSON escapes
    return (
        text.replace("<", esc + "u003c")
        .replace(">", esc + "u003e")
        .replace("&", esc + "u0026")
        .replace(chr(0x2028), esc + "u2028")
        .replace(chr(0x2029), esc + "u2029")
    )


def build(nodes_dir=NODES_DIR, edges_path=EDGES_PATH, template_path=TEMPLATE_PATH, dist_path=DIST_PATH) -> Path:
    nodes = load_nodes(nodes_dir)
    edges = load_edges(edges_path)

    errors = validate_graph(nodes, edges)
    if errors:
        raise SystemExit(f"스키마 검증 실패 ({len(errors)}건):\n" + "\n".join(errors))

    coords = compute_layout(nodes, edges)
    search_idx = build_search_index(nodes)

    node_dicts = []
    for n in nodes:
        d = asdict(n)
        d["body"] = render_body(n.body) if n.body else ""
        node_dicts.append(d)

    data = {
        "nodes": node_dicts,
        "edges": [asdict(e) for e in edges],
        "layout": coords,
        "search": search_idx,
        "meta": {"nodeCount": len(nodes), "edgeCount": len(edges)},
    }

    template_html = Path(template_path).read_text(encoding="utf-8")
    data_json = _embed_json(data)
    output_html = template_html.replace("__ONTOLOGY_DATA__", data_json)

    dist_path = Path(dist_path)
    dist_path.parent.mkdir(parents=True, exist_ok=True)
    dist_path.write_text(output_html, encoding="utf-8")
    print(f"빌드 완료: {dist_path} (노드 {len(nodes)}개, 엣지 {len(edges)}개)")
    return dist_path


if __name__ == "__main__":
    build()
