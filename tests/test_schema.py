import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from schema import Node, Edge, SchemaError, load_nodes, load_edges, validate_graph

FIXTURES = Path(__file__).parent / "fixtures"


def test_valid_node_has_no_errors():
    n = Node(id="leave-sick", type="개념", title="질병휴직", chapter=3,
              scope="공통", summary="1년 이내 직권휴직")
    assert n.validate() == []


def test_invalid_id_rejected():
    n = Node(id="Leave_Sick!", type="개념", title="질병휴직", chapter=3,
              scope="공통", summary="요약")
    errors = n.validate()
    assert any("id" in e for e in errors)


def test_invalid_type_rejected():
    n = Node(id="leave-sick", type="없는타입", title="질병휴직", chapter=3,
              scope="공통", summary="요약")
    errors = n.validate()
    assert any("type" in e for e in errors)


def test_load_nodes_from_yaml_dir():
    nodes = load_nodes(FIXTURES / "sample_nodes")
    assert len(nodes) == 2
    assert {n.id for n in nodes} == {"leave-childcare", "leave-sick"}


def test_load_edges_from_yaml():
    edges = load_edges(FIXTURES / "sample_edges.yaml")
    assert len(edges) == 1
    assert edges[0].type == "상위개념"


def test_validate_graph_detects_orphan_edge():
    nodes = load_nodes(FIXTURES / "sample_nodes")
    bad_edges = [Edge(source="leave-childcare", target="no-such-node", type="유의")]
    errors = validate_graph(nodes, bad_edges)
    assert any("고아 엣지" in e for e in errors)


def test_validate_graph_detects_duplicate_id():
    nodes = load_nodes(FIXTURES / "sample_nodes") + load_nodes(FIXTURES / "sample_nodes")
    errors = validate_graph(nodes, [])
    assert any("중복 id" in e for e in errors)


def test_validate_graph_clean_data_has_no_errors():
    nodes = load_nodes(FIXTURES / "sample_nodes")
    edges = load_edges(FIXTURES / "sample_edges.yaml")
    assert validate_graph(nodes, edges) == []


def test_validate_rejects_string_chapter_without_crashing():
    # 실제 사례: YAML에서 chapter: "3" 처럼 따옴표를 쳐서 문자열로 파싱된 경우
    n = Node(id="leave-sick", type="개념", title="x", chapter="3",
              scope="공통", summary="s")
    errors = n.validate()
    assert any("chapter" in e for e in errors)


def test_validate_rejects_non_string_id_without_crashing():
    # 실제 사례: YAML에서 id: 2024 처럼 따옴표 없는 숫자로 파싱된 경우
    n = Node(id=2024, type="수치·기한", title="x", chapter=3,
              scope="공통", summary="s")
    errors = n.validate()
    assert any("id" in e for e in errors)
