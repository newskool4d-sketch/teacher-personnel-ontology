"""3장 표본 데이터 검증 — 노드/엣지 수와 스키마 오류를 출력"""
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))
from schema import load_nodes, load_edges, validate_graph

nodes = load_nodes(BASE / "nodes")
edges = load_edges(BASE / "edges.yaml")
errors = validate_graph(nodes, edges)
print(f"노드 {len(nodes)}개, 엣지 {len(edges)}개, 오류 {len(errors)}건")
for e in errors:
    print(" -", e)
