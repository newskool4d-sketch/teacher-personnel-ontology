"""교원인사 관계 유형의 검증·공개 표현·지도 표현을 한곳에서 정의한다."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class RelationDefinition:
    target_types: frozenset[str] | None
    outgoing_label: str
    incoming_label: str
    detail_kind: str
    color_role: str
    dash: tuple[int, ...] = ()
    arrow: bool = False

    def as_public_dict(self) -> dict:
        return {
            "targetTypes": sorted(self.target_types) if self.target_types is not None else [],
            "outgoingLabel": self.outgoing_label,
            "incomingLabel": self.incoming_label,
            "detailKind": self.detail_kind,
            "visual": {
                "colorRole": self.color_role,
                "dash": list(self.dash),
                "arrow": self.arrow,
            },
        }


class RelationCatalog:
    """관계 의미를 검증과 공개 화면이 공유하도록 제공하는 Deep Module."""

    def __init__(self, definitions: Mapping[str, RelationDefinition]):
        self._definitions = dict(definitions)

    def __contains__(self, relation_type: str) -> bool:
        return relation_type in self._definitions

    @property
    def types(self) -> frozenset[str]:
        return frozenset(self._definitions)

    def allowed_targets(self, relation_type: str) -> frozenset[str] | None:
        definition = self._definitions.get(relation_type)
        return definition.target_types if definition else None

    def public_contract(self) -> dict[str, dict]:
        return {
            relation_type: definition.as_public_dict()
            for relation_type, definition in self._definitions.items()
        }


RELATIONS = RelationCatalog({
    "근거법령": RelationDefinition(
        target_types=frozenset({"법령·조문"}),
        outgoing_label="근거 법령",
        incoming_label="이 법령을 근거로 하는 항목",
        detail_kind="law",
        color_role="accent",
    ),
    "기한수치": RelationDefinition(
        target_types=frozenset({"수치·기한"}),
        outgoing_label="관련 기한·수치",
        incoming_label="이 기한·수치를 사용하는 항목",
        detail_kind="number",
        color_role="chapter-6",
        dash=(6, 4),
    ),
    "필요서식": RelationDefinition(
        target_types=frozenset({"서식"}),
        outgoing_label="필요 서식",
        incoming_label="이 서식을 사용하는 절차",
        detail_kind="form",
        color_role="chapter-7",
        dash=(2, 4),
    ),
    "관련해석": RelationDefinition(
        target_types=frozenset({"Q&A·유권해석", "감사지적사례"}),
        outgoing_label="관련 해석",
        incoming_label="이 해석을 참고하는 항목",
        detail_kind="interpretation",
        color_role="chapter-5",
        dash=(2, 5),
    ),
    "상위개념": RelationDefinition(
        target_types=None,
        outgoing_label="상위 개념",
        incoming_label="하위 항목",
        detail_kind="concept",
        color_role="chapter-1",
    ),
    "유의": RelationDefinition(
        target_types=None,
        outgoing_label="유의 사항",
        incoming_label="이 항목을 유의하는 업무",
        detail_kind="caution",
        color_role="danger",
        dash=(1, 5),
    ),
    "절차단계": RelationDefinition(
        target_types=None,
        outgoing_label="연결 절차",
        incoming_label="선행 업무·절차",
        detail_kind="process",
        color_role="chapter-4",
        arrow=True,
    ),
})
