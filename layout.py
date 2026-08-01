"""그래프 좌표 사전계산 — networkx spring_layout, 결정론적 시드"""
import networkx as nx
from schema import Node, Edge


def compute_layout(nodes: list[Node], edges: list[Edge], seed: int = 42, scale: int = 1000) -> dict[str, dict[str, float]]:
    graph = nx.Graph()
    for n in nodes:
        graph.add_node(n.id)
    for e in edges:
        if e.source in graph and e.target in graph:
            graph.add_edge(e.source, e.target)

    pos = nx.spring_layout(graph, seed=seed, scale=scale)
    return {node_id: {"x": round(float(xy[0]), 2), "y": round(float(xy[1]), 2)} for node_id, xy in pos.items()}
