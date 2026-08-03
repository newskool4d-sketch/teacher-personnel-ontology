import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from build import build, NODES_DIR
from schema import load_nodes


def _nodes_by_id():
    return {node.id: node for node in load_nodes(NODES_DIR)}


def test_targeted_legal_corrections_and_review_states():
    nodes = _nodes_by_id()

    vacancy = nodes["num-vacancy-fill-6m"]
    assert "3개월" not in vacancy.summary
    assert "6개월" in vacancy.summary
    assert vacancy.legal_review["state"] == "verified"
    assert vacancy.legal_review["sources"][0]["mst"] == "273697"

    reinstate = nodes["num-reinstate-30d"]
    assert "§73②" in reinstate.body
    assert "§73③" in reinstate.body
    assert reinstate.legal_review["state"] == "verified"

    dui = nodes["num-discipline-dui-standard"]
    assert any("공무원 징계령 시행규칙 별표1의5" in ref for ref in dui.refs)
    assert not any("교육공무원 징계양정" in ref for ref in dui.refs)
    assert dui.legal_review["sources"][0]["mst"] == "282271"

    tuberculosis = nodes["num-tb-test-1m"]
    assert tuberculosis.legal_review["state"] == "partial"
    assert tuberculosis.legal_review["unresolved"]
    assert "검진기록" in tuberculosis.legal_review["unresolved"][0]

    contract = nodes["contract-childcare-leave"]
    assert contract.legal_review["state"] == "partial"
    assert "국공립" in contract.legal_review["applicability"]
    assert "사립" in contract.legal_review["applicability"]
    assert "근로자" in contract.summary

    amendment = nodes["num-contract-childcare-2025-amendment"]
    assert amendment.legal_review["state"] == "verified"
    assert "근로자" in amendment.summary


def test_honor_nodes_use_pdf_detail_and_current_law_review():
    nodes = _nodes_by_id()

    overview = nodes["honor-overview"]
    assert "확인필요" not in overview.body
    assert "상훈법" in overview.body
    assert overview.pages == {"중등": "247-255", "초등": "257-266"}
    assert overview.legal_review["state"] == "partial"
    assert {source["mst"] for source in overview.legal_review["sources"]} == {
        "279617",
        "215477",
        "261999",
    }

    retirement = nodes["num-honor-retirement-years"]
    assert "청조근정훈장(1등급)" in retirement.body
    assert "대학총장 경력자 특별추천" in retirement.body
    assert "40년 이상 | 황조근정훈장(2등급)" in retirement.body
    assert "36년 이상~38년 미만 | 녹조근정훈장(4등급)" in retirement.body
    assert "40년 이상 | 청조근정훈장" not in retirement.body

    reaward = nodes["num-honor-reaward-ban"]
    assert "훈장 7년" in reaward.body
    assert "같은 종류·동급 또는 하위등급" in reaward.body
    assert reaward.legal_review["state"] == "partial"

    first_award = nodes["num-honor-first-award-period"]
    assert "실근무기간" in first_award.body
    assert first_award.legal_review["sources"] == []

    deadline = nodes["num-honor-recommend-deadline"]
    assert "행정기관의 착오·과실" in deadline.body
    assert deadline.pages["중등"] == "248, 252"

    restriction = nodes["honor-recommend-restriction"]
    assert "200만원 미만" in restriction.body
    assert "100만원 미만" in restriction.body
    assert "제14호까지" in restriction.body
    assert restriction.legal_review["state"] == "conflict"
    assert restriction.legal_review["sources"][-1]["mst"] == "282271"

    honors_law = nodes["law-honors-act-4"]
    assert honors_law.legal_review["state"] == "verified"
    assert honors_law.legal_review["sources"][0]["mst"] == "279617"

    regrant = nodes["law-honors-decree-17-2"]
    assert "같은 종류의 동급·하위" in regrant.summary
    assert regrant.legal_review["sources"][0]["mst"] == "215477"

    current_discipline_rule = nodes["law-civil-servant-discipline-rule-4"]
    assert "제14호까지" in current_discipline_rule.body
    assert current_discipline_rule.legal_review["sources"][0]["mst"] == "282271"


def test_built_html_exposes_review_state_in_detail_and_numeric_table(tmp_path):
    output = build(dist_path=tmp_path / "legal-review.html")
    html = output.read_text(encoding="utf-8")

    assert "기준과 관련 법령" in html
    assert "<th data-col=\"3\">원문 위치</th>" in html
    assert "<th data-col=\"5\">기준 안내</th>" in html
    assert "기존 확인일 기록" not in html
    assert "적용 시 확인" in html
    assert "시·도교육청 지침 확인" in html
    assert 'class="review-reason"' in html
    assert "review-needs-review" in html
    assert '"legal_review": {"state": "partial"' in html


def test_built_html_contains_editorial_navigation_and_honor_law_nodes(tmp_path):
    output = build(dist_path=tmp_path / "editorial-honor.html")
    html = output.read_text(encoding="utf-8")

    assert 'class="home-hero-grid"' in html
    assert 'class="node-detail-grid"' in html
    assert 'id="review-filter"' in html
    assert 'aria-label="학교급 선택"' in html
    assert 'data-scope="중등">중등교원' in html
    assert 'data-scope="초등">초등교원' in html
    assert "1. 학교급 선택" in html
    assert 'id="public-footer"' in html
    assert "법적 효력이 있는 법령·공문 원문을 대체하지 않습니다" in html
    assert "3D 지식 지도" in html
    assert 'id="graph-chapter-filter"' in html
    assert "왼쪽 버튼을 누른 채 드래그하여 회전" in html
    assert "canvas.addEventListener('pointerdown'" in html
    assert "cameraDistance = 1450" in html
    assert "shape-diamond" in html
    assert "실무도우미 원문 쪽수와 관련 법령 안내 포함" in html
    assert "개 항목 모두 표시" in html
    assert '"id": "law-honors-act-4"' in html
    assert '"id": "law-honors-decree-17-2"' in html
    assert '"id": "law-civil-servant-discipline-rule-4"' in html


def test_built_html_contains_persistent_dark_mode_and_glass_surfaces(tmp_path):
    output = build(dist_path=tmp_path / "glass-theme.html")
    html = output.read_text(encoding="utf-8")

    assert 'data-theme="dark"' in html
    assert 'id="theme-toggle"' in html
    assert "ontology-theme" in html
    assert "prefers-color-scheme: dark" in html
    assert "function initThemeToggle()" in html
    assert "--glass:" in html
    assert "backdrop-filter: blur(18px)" in html
