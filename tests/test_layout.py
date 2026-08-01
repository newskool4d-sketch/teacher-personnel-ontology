import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from schema import Node, Edge
from layout import compute_layout

NODES = [
    Node(id="a", type="개념", title="A", chapter=3, scope="공통", summary="a"),
    Node(id="b", type="개념", title="B", chapter=3, scope="공통", summary="b"),
    Node(id="c", type="개념", title="C", chapter=3, scope="공통", summary="c"),
]
EDGES = [Edge(source="a", target="b", type="상위개념")]


def test_all_node_ids_present_in_layout():
    coords = compute_layout(NODES, EDGES)
    assert set(coords.keys()) == {"a", "b", "c"}


def test_coordinates_are_floats():
    coords = compute_layout(NODES, EDGES)
    for p in coords.values():
        assert isinstance(p["x"], float)
        assert isinstance(p["y"], float)


def test_layout_is_deterministic_with_fixed_seed():
    coords1 = compute_layout(NODES, EDGES, seed=42)
    coords2 = compute_layout(NODES, EDGES, seed=42)
    assert coords1 == coords2


def test_isolated_node_still_gets_coordinates():
    # 'c' 는 엣지가 없는 고립 노드
    coords = compute_layout(NODES, EDGES)
    assert "c" in coords
