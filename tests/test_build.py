import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from build import (
    build,
    build_payload,
    format_korean_date,
    latest_review_date,
    public_node_dict,
    render_body,
    sanitize_public_text,
    NODES_DIR,
    EDGES_PATH,
)
from schema import Node
from schema import load_nodes, load_edges, validate_graph

FIXTURES = Path(__file__).parent / "fixtures"


def test_render_body_converts_bold_and_table():
    html = render_body("**굵게**\n\n| a | b |\n| --- | --- |\n| 1 | 2 |")
    assert "<strong>굵게</strong>" in html
    assert "<table>" in html


def test_public_text_removes_internal_law_lookup_markers():
    raw = "korean-law-mcp로 원문 확인(2026-08-02, MST 279617, 법령ID 001427). korean-law-mcp 원문 확인. 확인필요"
    public = sanitize_public_text(raw)
    assert "korean-law-mcp" not in public
    assert "MST" not in public
    assert "법령ID" not in public
    assert "현행 법령 원문" in public
    assert "현행 법령 원문 원문" not in public
    assert "확인필요" not in public
    assert "관련 법령 및 소속 시·도교육청 지침에서 확인" in public


def test_public_node_dict_removes_internal_review_metadata_and_unknown_pages():
    node = Node(
        id="sample-node",
        type="법령·조문",
        title="샘플",
        chapter=1,
        scope="공통",
        summary="공개 요약",
        pages={"중등": "확인필요", "초등": "12-13"},
        legal_review={
            "state": "partial",
            "applicable_as_of": "2026-08-01",
            "checked_at": "2026-08-02",
            "method": "내부 검토",
            "unresolved": ["확인필요"],
            "applicability": "공통",
            "sources": [{
                "law_name": "예시법",
                "article": "제1조",
                "mst": "123",
                "effective_date": "2026-01-01",
                "status": "현행",
                "official_url": "https://www.law.go.kr/법령/예시법/제1조",
            }],
        },
    )

    public = public_node_dict(node)

    assert public["pages"] == {"중등": "", "초등": "12-13"}
    assert "method" not in public["legal_review"]
    assert "mst" not in public["legal_review"]["sources"][0]
    assert "확인필요" not in public["legal_review"]["unresolved"][0]


def test_review_date_helpers_use_latest_iso_date():
    nodes = [
        Node(id="a", type="개념", title="A", chapter=1, scope="공통", summary="a",
             legal_review={"checked_at": "2026-08-01"}),
        Node(id="b", type="개념", title="B", chapter=1, scope="공통", summary="b",
             legal_review={"checked_at": "2026-08-04"}),
        Node(id="c", type="개념", title="C", chapter=1, scope="공통", summary="c"),
    ]

    assert latest_review_date(nodes) == "2026-08-04"
    assert format_korean_date("2026-08-04") == "2026. 8. 4."


def test_build_payload_separates_validated_data_from_file_output():
    nodes = load_nodes(FIXTURES / "sample_nodes")
    edges = load_edges(FIXTURES / "sample_edges.yaml")

    payload = build_payload(nodes, edges)

    assert payload["meta"] == {"nodeCount": 2, "edgeCount": 1}
    assert set(payload) == {"nodes", "edges", "layout", "search", "meta"}


def test_build_produces_valid_html_with_embedded_json(tmp_path):
    dist_path = tmp_path / "out.html"
    result_path = build(
        nodes_dir=FIXTURES / "sample_nodes",
        edges_path=FIXTURES / "sample_edges.yaml",
        template_path=FIXTURES / "min_template.html",
        dist_path=dist_path,
    )
    assert result_path == dist_path
    content = dist_path.read_text(encoding="utf-8")
    assert "__ONTOLOGY_DATA__" not in content

    start = content.index("const ONTOLOGY = ") + len("const ONTOLOGY = ")
    end = content.index(";", start)
    data = json.loads(content[start:end])
    assert data["meta"]["nodeCount"] == 2
    assert len(data["layout"]) == 2
    assert len(data["search"]) == 2


def test_build_raises_on_schema_error(tmp_path, monkeypatch):
    bad_edges = tmp_path / "bad_edges.yaml"
    bad_edges.write_text("- {source: leave-childcare, target: no-such-node, type: 유의}\n", encoding="utf-8")
    dist_path = tmp_path / "out.html"
    try:
        build(nodes_dir=FIXTURES / "sample_nodes", edges_path=bad_edges,
              template_path=FIXTURES / "min_template.html", dist_path=dist_path)
        assert False, "SystemExit이 발생해야 함"
    except SystemExit as e:
        assert "고아 엣지" in str(e)


def test_real_data_builds_clean_and_meets_minimum_scale(tmp_path):
    """실제 nodes/+edges.yaml 기준 스모크 테스트 — 정확한 수 하드코딩 대신 하한선만 검증해
    데이터가 늘어나도 깨지지 않게 한다."""
    nodes = load_nodes(NODES_DIR)
    edges = load_edges(EDGES_PATH)

    errors = validate_graph(nodes, edges)
    assert errors == [], f"실데이터 스키마 검증 오류 {len(errors)}건: {errors}"
    assert len(nodes) >= 220, f"노드 수 {len(nodes)}개 — 220개 미만"
    assert len(edges) >= 250, f"엣지 수 {len(edges)}개 — 250개 미만"

    dist_path = tmp_path / "real.html"
    result_path = build(dist_path=dist_path)
    assert result_path == dist_path
    assert dist_path.exists()
    public_html = dist_path.read_text(encoding="utf-8")
    internal_markers = (
        "korean-law-mcp",
        "MST ",
        '"mst":',
        '"method":',
        "법령ID",
        "행정규칙일련번호",
        "행정규칙ID",
        "API 응답",
        "확인필요",
        "근거 보완 필요",
    )
    found_markers = [marker for marker in internal_markers if marker in public_html]
    assert found_markers == [], f"공개 HTML에 내부 표식 잔존: {found_markers}"
