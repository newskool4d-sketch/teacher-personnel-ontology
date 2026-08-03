"""온톨로지 노드·엣지 스키마 정의 및 검증"""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import re
import yaml

VALID_TYPES = {"개념", "법령·조문", "수치·기한", "절차", "서식", "Q&A·유권해석", "감사지적사례", "NEIS작업"}
VALID_SCOPES = {"공통", "중등", "초등"}
VALID_EDGE_TYPES = {"근거법령", "기한수치", "필요서식", "관련해석", "상위개념", "유의", "절차단계"}
# 엣지 타입별 target(대상) 노드 type 제약 — 확인된 데이터 패턴이 100% 일관된 경우만 강제한다.
# (상위개념·유의·절차단계는 현재 챕터별 방향·조합이 아직 통일되지 않아 제약을 걸지 않음 — 별도 정리 필요)
EDGE_TARGET_TYPE_CONSTRAINTS = {
    "근거법령": {"법령·조문"},
    "기한수치": {"수치·기한"},
    "필요서식": {"서식"},
    "관련해석": {"Q&A·유권해석", "감사지적사례"},
}
VALID_LEGAL_REVIEW_STATES = {"verified", "partial", "needs_review", "conflict"}
VALID_LEGAL_SOURCE_STATUSES = {"현행", "시행예정"}
REQUIRED_LEGAL_REVIEW_FIELDS = {
    "state", "applicable_as_of", "checked_at", "method", "unresolved", "applicability", "sources"
}
REQUIRED_LEGAL_SOURCE_FIELDS = {
    "law_name", "article", "mst", "effective_date", "status", "official_url"
}
ID_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


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
    legal_review: dict = field(default_factory=dict)

    def validate(self) -> list[str]:
        errors = []
        if not isinstance(self.id, str):
            errors.append(f"[{self.id}] id는 문자열이어야 함(현재 타입: {type(self.id).__name__})")
        elif not ID_PATTERN.match(self.id):
            errors.append(f"[{self.id}] id는 kebab-case 영문/숫자만 허용")
        if self.type not in VALID_TYPES:
            errors.append(f"[{self.id}] 알 수 없는 type: {self.type}")
        if self.scope not in VALID_SCOPES:
            errors.append(f"[{self.id}] 알 수 없는 scope: {self.scope}")
        if not isinstance(self.chapter, int):
            errors.append(f"[{self.id}] chapter는 정수여야 함(현재 타입: {type(self.chapter).__name__})")
        elif not (0 <= self.chapter <= 7):
            errors.append(f"[{self.id}] chapter는 0~7 범위(0=부록)")
        if not self.summary:
            errors.append(f"[{self.id}] summary는 필수")
        elif len(self.summary) > 120:
            errors.append(f"[{self.id}] summary는 120자 이내 권장(현재 {len(self.summary)}자)")
        if self.verified and not DATE_PATTERN.fullmatch(self.verified):
            errors.append(f"[{self.id}] verified는 YYYY-MM-DD 형식이어야 함")
        errors.extend(self._validate_legal_review())
        return errors

    def _validate_legal_review(self) -> list[str]:
        if not isinstance(self.legal_review, dict):
            return [f"[{self.id}] legal_review는 객체여야 함"]
        if not self.legal_review:
            return []

        errors: list[str] = []
        missing = REQUIRED_LEGAL_REVIEW_FIELDS - self.legal_review.keys()
        if missing:
            errors.append(f"[{self.id}] legal_review 필수 필드 누락: {', '.join(sorted(missing))}")

        state = self.legal_review.get("state")
        if state not in VALID_LEGAL_REVIEW_STATES:
            errors.append(f"[{self.id}] 알 수 없는 legal_review.state: {state}")

        for field_name in ("applicable_as_of", "checked_at", "method", "applicability"):
            value = self.legal_review.get(field_name)
            if value is not None and (not isinstance(value, str) or not value.strip()):
                errors.append(f"[{self.id}] legal_review.{field_name}는 비어 있지 않은 문자열이어야 함")

        for field_name in ("applicable_as_of", "checked_at"):
            value = self.legal_review.get(field_name)
            if isinstance(value, str) and not DATE_PATTERN.fullmatch(value):
                errors.append(f"[{self.id}] legal_review.{field_name}는 YYYY-MM-DD 형식이어야 함")

        unresolved = self.legal_review.get("unresolved")
        if unresolved is not None and not isinstance(unresolved, list):
            errors.append(f"[{self.id}] legal_review.unresolved는 목록이어야 함")
        elif isinstance(unresolved, list):
            if any(not isinstance(item, str) or not item.strip() for item in unresolved):
                errors.append(f"[{self.id}] legal_review.unresolved 항목은 비어 있지 않은 문자열이어야 함")
            if state == "verified" and unresolved:
                errors.append(f"[{self.id}] verified 상태의 legal_review.unresolved는 비어 있어야 함")

        sources = self.legal_review.get("sources")
        if sources is not None and not isinstance(sources, list):
            errors.append(f"[{self.id}] legal_review.sources는 목록이어야 함")
        elif isinstance(sources, list):
            if state == "verified" and not sources:
                errors.append(f"[{self.id}] verified 상태의 legal_review.sources는 1개 이상이어야 함")
            for index, source in enumerate(sources, start=1):
                if not isinstance(source, dict):
                    errors.append(f"[{self.id}] legal_review.sources[{index}]는 객체여야 함")
                    continue
                source_missing = REQUIRED_LEGAL_SOURCE_FIELDS - source.keys()
                if source_missing:
                    errors.append(
                        f"[{self.id}] legal_review.sources[{index}] 필수 필드 누락: "
                        f"{', '.join(sorted(source_missing))}"
                    )
                for field_name in REQUIRED_LEGAL_SOURCE_FIELDS:
                    value = source.get(field_name)
                    if value is not None and (not isinstance(value, str) or not value.strip()):
                        errors.append(
                            f"[{self.id}] legal_review.sources[{index}].{field_name}는 "
                            "비어 있지 않은 문자열이어야 함"
                        )
                status = source.get("status")
                if status not in VALID_LEGAL_SOURCE_STATUSES:
                    errors.append(
                        f"[{self.id}] 알 수 없는 legal_review.sources[{index}].status: {status}"
                    )
                effective_date = source.get("effective_date")
                if isinstance(effective_date, str) and not DATE_PATTERN.fullmatch(effective_date):
                    errors.append(
                        f"[{self.id}] legal_review.sources[{index}].effective_date는 YYYY-MM-DD 형식이어야 함"
                    )
                official_url = source.get("official_url")
                if isinstance(official_url, str) and not official_url.startswith("https://www.law.go.kr/"):
                    errors.append(
                        f"[{self.id}] legal_review.sources[{index}].official_url은 law.go.kr 공식 링크여야 함"
                    )
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
    node_by_id: dict[str, Node] = {}
    for n in nodes:
        errors.extend(n.validate())
        if n.id in seen_ids:
            errors.append(f"중복 id: {n.id}")
        seen_ids.add(n.id)
        node_by_id[n.id] = n

    seen_edges: set[tuple[str, str, str]] = set()
    for e in edges:
        errors.extend(e.validate())
        if e.source not in seen_ids:
            errors.append(f"고아 엣지: source '{e.source}' 노드 없음 ({e.source}->{e.target})")
        if e.target not in seen_ids:
            errors.append(f"고아 엣지: target '{e.target}' 노드 없음 ({e.source}->{e.target})")
            continue
        if e.source == e.target:
            errors.append(f"자기루프 엣지: {e.source}->{e.target} ({e.type})")
        edge_key = (e.source, e.target, e.type)
        if edge_key in seen_edges:
            errors.append(f"중복 엣지: {e.source}->{e.target} ({e.type})")
        seen_edges.add(edge_key)

        if e.source in node_by_id:
            allowed_targets = EDGE_TARGET_TYPE_CONSTRAINTS.get(e.type)
            target_node = node_by_id.get(e.target)
            if allowed_targets is not None and target_node is not None and target_node.type not in allowed_targets:
                errors.append(
                    f"엣지 타입-노드 타입 불일치: {e.source}->{e.target} ({e.type})는 "
                    f"target type이 {sorted(allowed_targets)} 중 하나여야 하나 '{target_node.type}'임"
                )
    return errors
