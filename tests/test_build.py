import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from build import build, render_body

FIXTURES = Path(__file__).parent / "fixtures"


def test_render_body_converts_bold_and_table():
    html = render_body("**굵게**\n\n| a | b |\n| --- | --- |\n| 1 | 2 |")
    assert "<strong>굵게</strong>" in html
    assert "<table>" in html


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
