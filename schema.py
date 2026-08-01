"""온톨로지 노드·엣지 스키마 정의 및 검증"""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import re
import yaml

VALID_TYPES = {"개념", "법령·조문", "수치·기한", "절차", "서식", "Q&A·유권해석", "감사지적사례", "NEIS작업"}
VALID_SCOPES = {"공통", "중등", "초등"}
VALID_EDGE_TYPES = {"근거법령", "기한수치", "필요서식", "관련해석", "상위개념", "유의", "절차단계"}
ID_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


class SchemaError(Exception):
    pass


@dataclass
class Node:
    id: str
    type: str
    title: str
    chapter: int
    scope: str
    summary: str
    body: str = ""
    refs: list[str] = field(default_factory=list)
    pages: dict[str, str] = field(default_factory=dict)
    aliases: list[str] = field(default_factory=list)
    verified: str = ""

    def validate(self) -> list[str]:
        errors = []
        if not ID_PATTERN.match(self.id):
            errors.append(f"[{self.id}] id는 kebab-case 영문/숫자만 허용")
        if self.type not in VALID_TYPES:
            errors.append(f"[{self.id}] 알 수 없는 type: {self.type}")
        if self.scope not in VALID_SCOPES:
            errors.append(f"[{self.id}] 알 수 없는 scope: {self.scope}")
        if not (0 <= self.chapter <= 7):
            errors.append(f"[{self.id}] chapter는 0~7 범위(0=부록)")
        if not self.summary:
            errors.append(f"[{self.id}] summary는 필수")
        elif len(self.summary) > 120:
            errors.append(f"[{self.id}] summary는 120자 이내 권장(현재 {len(self.summary)}자)")
        return errors


@dataclass
class Edge:
    source: str
    target: str
    type: str

    def validate(self) -> list[str]:
        if self.type not in VALID_EDGE_TYPES:
            return [f"[{self.source}->{self.target}] 알 수 없는 edge type: {self.type}"]
        return []


def load_nodes(nodes_dir: Path) -> list[Node]:
    nodes: list[Node] = []
    for yml_file in sorted(Path(nodes_dir).glob("*.yaml")):
        with open(yml_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or []
        for raw in data:
            try:
                nodes.append(Node(**raw))
            except TypeError as e:
                raise SchemaError(f"{yml_file.name}: 필드 오류 - {e} (id={raw.get('id', '?')})") from e
    return nodes


def load_edges(edges_path: Path) -> list[Edge]:
    with open(edges_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or []
    try:
        return [Edge(**raw) for raw in data]
    except TypeError as e:
        raise SchemaError(f"{Path(edges_path).name}: 필드 오류 - {e}") from e


def validate_graph(nodes: list[Node], edges: list[Edge]) -> list[str]:
    errors: list[str] = []
    seen_ids: set[str] = set()
    for n in nodes:
        errors.extend(n.validate())
        if n.id in seen_ids:
            errors.append(f"중복 id: {n.id}")
        seen_ids.add(n.id)

    for e in edges:
        errors.extend(e.validate())
        if e.source not in seen_ids:
            errors.append(f"고아 엣지: source '{e.source}' 노드 없음 ({e.source}->{e.target})")
        if e.target not in seen_ids:
            errors.append(f"고아 엣지: target '{e.target}' 노드 없음 ({e.source}->{e.target})")
    return errors
