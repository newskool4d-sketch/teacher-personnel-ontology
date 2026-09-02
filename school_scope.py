"""학교급 선택이 바꾸는 데이터 범위와 공식 원문 정보를 정의한다."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class SchoolOption:
    value: str
    label: str
    official_guide_label: str
    official_guide_url: str

    def as_public_dict(self) -> dict:
        return {
            "value": self.value,
            "label": self.label,
            "officialGuide": {
                "label": self.official_guide_label,
                "url": self.official_guide_url,
            },
        }


class SchoolScopePolicy:
    """학교급 값, 공통 범위, 안내서 정보를 한 인터페이스로 제공한다."""

    def __init__(
        self,
        *,
        default: str,
        shared_scope: str,
        selection_help: str,
        options: Iterable[SchoolOption],
    ):
        self._default = default
        self._shared_scope = shared_scope
        self._selection_help = selection_help
        self._options = tuple(options)
        self._option_values = frozenset(option.value for option in self._options)
        if default not in self._option_values:
            raise ValueError(f"기본 학교급이 선택지에 없음: {default}")

    def __contains__(self, scope: str) -> bool:
        return scope == self._shared_scope or scope in self._option_values

    @property
    def valid_node_scopes(self) -> frozenset[str]:
        return self._option_values | {self._shared_scope}

    def public_contract(self) -> dict:
        return {
            "default": self._default,
            "sharedScope": self._shared_scope,
            "selectionHelp": self._selection_help,
            "options": [option.as_public_dict() for option in self._options],
        }


SCHOOL_SCOPE = SchoolScopePolicy(
    default="중등",
    shared_scope="공통",
    selection_help="학교급을 선택하면 실무도우미에서 찾을 위치와 공식 원문이 바뀝니다.",
    options=(
        SchoolOption(
            value="중등",
            label="중등교원",
            official_guide_label="2026 중등 실무도우미 공식 원문",
            official_guide_url=(
                "https://edubook.ice.go.kr/src/viewer/main.php?"
                "category=1&host=main&page=1&site=20260304_170151"
            ),
        ),
        SchoolOption(
            value="초등",
            label="초등교원",
            official_guide_label="2026 초등 실무도우미 공식 자료실",
            official_guide_url="https://ice.go.kr/ice/na/ntt/selectNttList.do?bbsId=2086&mi=12307",
        ),
    ),
)
