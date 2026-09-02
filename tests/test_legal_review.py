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
    assert '<button type="button" class="table-sort" data-col="3">실무도우미에서 찾을 위치' in html
    assert '<button type="button" class="table-sort" data-col="5">법령 안내' in html
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
    assert '"value": "중등", "label": "중등교원"' in html
    assert '"value": "초등", "label": "초등교원"' in html
    assert "renderScopeOptions()" in html
    assert "1. 학교급 선택" in html
    assert 'id="public-footer"' in html
    assert "법적 효력이 있는 법령·공문 원문을 대체하지 않습니다" in html
    assert "업무 관계 지도" in html
    assert "목록에서 찾기" in html
    assert 'id="graph-list"' in html
    assert 'id="graph-list-jump"' in html
    assert "업무 관계 지도에서 찾기" in html
    assert "판단할 기준 확인" in html
    assert "실무도우미에서 찾을 위치" in html
    assert ".graph-instructions" in html and "font-size: 13px" in html
    assert 'id="graph-chapter-filter"' in html
    assert "클릭: 선택 고정 · Esc: 선택 해제" in html
    assert "let selectedId = null" in html
    assert "ctx.setLineDash(edgeStyle.dash)" in html
    assert "const coreIds" in html
    assert "canvas.addEventListener('pointerdown'" in html
    assert "cameraDistance = 1450" in html
    assert "shape-diamond" in html
    assert "실무도우미 수록 쪽과 관련 법령 안내 포함" in html
    assert "개 항목 모두 표시" in html
    assert '"id": "law-honors-act-4"' in html
    assert '"id": "law-honors-decree-17-2"' in html
    assert '"id": "law-civil-servant-discipline-rule-4"' in html


def test_built_html_uses_korean_labels_responsive_hero_and_official_guides(tmp_path):
    output = build(dist_path=tmp_path / "copy-source-links.html")
    html = output.read_text(encoding="utf-8")

    assert 'class="home-hero-title-line">규정은 빠르게 찾고,' in html
    assert "@media (min-width: 901px) and (max-width: 1440px)" in html
    assert "word-break: keep-all" in html
    assert "교원인사 지식지도" in html
    assert "장별 찾아보기" in html
    assert "이용 도구" in html
    assert "인쇄용 요약" in html
    assert "Knowledge Atlas" not in html
    assert "Chapter index" not in html
    assert "Reference tools" not in html
    assert "인쇄 치트시트" not in html
    assert "edubook.ice.go.kr/src/viewer/main.php" in html
    assert "ice.go.kr/ice/na/ntt/selectNttList.do" in html
    assert "2026 중등 실무도우미 공식 원문" in html
    assert "2026 초등 실무도우미 공식 자료실" in html
    assert "2026. 8. 4.." not in html


def test_eight_priority_law_nodes_have_current_bodies_and_sources():
    nodes = _nodes_by_id()
    expected = {
        "law-gyoyukgongmuwon-2": ("교육공무원법", "273345"),
        "law-gukgong-2": ("국가공무원법", "286457"),
        "law-chodeung-jungdeung-21-3": ("초ㆍ중등교육법", "285599"),
        "law-gukgong-33": ("국가공무원법", "286457"),
        "law-gyoyukgongmuwon-44": ("교육공무원법", "273345"),
        "law-gyoyukgongmuwon-45": ("교육공무원법", "273345"),
        "law-gukgong-56-66": ("국가공무원법", "286457"),
        "law-gyoyuk-jinggye-ryeong": ("교육공무원 징계령", "280455"),
    }

    for node_id, (law_name, mst) in expected.items():
        node = nodes[node_id]
        assert len(node.body.strip()) >= 160, node_id
        assert node.verified == "2026-08-04"
        assert node.legal_review["state"] == "verified"
        assert node.legal_review["applicable_as_of"] == "2026-08-04"
        assert node.legal_review["unresolved"] == []
        assert node.legal_review["sources"][0]["law_name"] == law_name
        assert node.legal_review["sources"][0]["mst"] == mst
        assert node.legal_review["sources"][0]["official_url"].startswith("https://www.law.go.kr/")

    assert "조교" in nodes["law-gyoyukgongmuwon-2"].summary
    assert "60일" in nodes["law-gyoyuk-jinggye-ryeong"].body
    assert "15일" in nodes["law-gyoyuk-jinggye-ryeong"].body


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


def test_built_html_prioritizes_detail_content_before_reference_rail_on_mobile(tmp_path):
    output = build(dist_path=tmp_path / "mobile-detail-order.html")
    html = output.read_text(encoding="utf-8")

    assert ".node-primary { order: 1; }" in html
    assert ".node-rail { position: static; order: 2; }" in html


def test_built_html_limits_initial_graph_labels_by_viewport(tmp_path):
    output = build(dist_path=tmp_path / "graph-label-density.html")
    html = output.read_text(encoding="utf-8")

    assert "const compactViewport = canvas.clientWidth < 720;" in html
    assert "const coreLimit = compactViewport ? 5 : 8;" in html
    assert "const labelLimit = compactViewport ? 18 : 28;" in html
    assert "const supportingLabelLimit = compactViewport ? 8 : 14;" in html


def test_built_html_uses_readable_supporting_text_and_stable_display_font(tmp_path):
    output = build(dist_path=tmp_path / "readable-type.html")
    html = output.read_text(encoding="utf-8")

    assert "--text-support: 13px; --muted-readable: .74;" in html
    assert "font-size: var(--text-support);" in html
    assert "opacity: var(--muted-readable);" in html
    assert "--font-display: Batang, 'AppleMyungjo', 'Noto Serif CJK KR', 'Nanum Myeongjo', serif;" in html
    assert "MaruBuri" not in html


def test_built_html_provides_keyboard_entry_to_main_content(tmp_path):
    output = build(dist_path=tmp_path / "keyboard-entry.html")
    html = output.read_text(encoding="utf-8")

    assert '<a class="skip-link" href="#main-content">본문으로 바로가기</a>' in html
    assert '<main id="main-content" tabindex="-1">' in html
    assert ".skip-link:focus-visible" in html
    assert ".search-panel .search-bar:focus-visible" in html


def test_built_html_orients_users_after_spa_route_changes(tmp_path):
    output = build(dist_path=tmp_path / "route-context.html")
    html = output.read_text(encoding="utf-8")

    assert "function updateRouteContext(main, focusContent = false)" in html
    assert "document.title = pageTitle === APP_TITLE ? APP_TITLE : `${pageTitle} | ${APP_TITLE}`;" in html
    assert "heading.setAttribute('tabindex', '-1');" in html
    assert "heading.focus();" in html
    assert "render({ focusContent: true });" in html
    assert "function initSkipLink()" in html


def test_built_html_announces_search_result_counts_without_repeating_the_list(tmp_path):
    output = build(dist_path=tmp_path / "search-status.html")
    html = output.read_text(encoding="utf-8")

    assert '<div id="search-status" class="sr-only" role="status" aria-live="polite" aria-atomic="true"></div>' in html
    assert '<div id="search-results" class="search-results"></div>' in html
    assert "status.textContent = `${scope} 기준 ${allMatches.length}개 항목`" in html


def test_built_html_announces_filtered_table_count(tmp_path):
    output = build(dist_path=tmp_path / "table-status.html")
    html = output.read_text(encoding="utf-8")

    assert '<span id="table-count" class="table-count" role="status" aria-live="polite" aria-atomic="true">' in html


def test_built_html_exposes_keyboard_table_sorting_and_direction(tmp_path):
    output = build(dist_path=tmp_path / "table-sort.html")
    html = output.read_text(encoding="utf-8")

    assert html.count('class="table-sort"') == 6
    assert html.count('aria-sort="none"') == 6
    assert "document.querySelectorAll('#numeric-table .table-sort')" in html
    assert "activeHeader.setAttribute('aria-sort', asc ? 'ascending' : 'descending');" in html


def test_built_html_explains_and_focuses_horizontally_scrollable_table(tmp_path):
    output = build(dist_path=tmp_path / "table-scroll.html")
    html = output.read_text(encoding="utf-8")

    assert '<p id="table-scroll-help" class="table-scroll-help">' in html
    assert 'class="table-wrap" tabindex="0" role="region" aria-label="수치·기한 통합표" aria-describedby="table-scroll-help"' in html
    assert ".table-wrap:focus-visible" in html


def test_built_html_keeps_build_metadata_readable(tmp_path):
    output = build(dist_path=tmp_path / "readable-build-info.html")
    html = output.read_text(encoding="utf-8")

    assert ".build-info { grid-column: 1 / -1; margin: -10px 0 0; color: var(--ink); font-size: 13px; opacity: .68; }" in html


def test_built_html_keeps_active_scope_contrast_in_both_themes(tmp_path):
    output = build(dist_path=tmp_path / "scope-contrast.html")
    html = output.read_text(encoding="utf-8")

    assert ".scope-option.active { background: var(--accent); color: var(--bg);" in html
    assert ".scope-option.active { background: var(--accent); color: #fff;" not in html


def test_built_html_names_repeated_navigation_landmarks(tmp_path):
    output = build(dist_path=tmp_path / "named-landmarks.html")
    html = output.read_text(encoding="utf-8")

    assert '<aside id="left-nav" aria-label="업무 탐색">' in html
    assert '<nav class="left-nav-chapters" aria-label="장별 업무 탐색">' in html
    assert '<nav class="left-nav-quicklinks" aria-label="빠른 탐색">' in html
    assert '<aside class="node-rail" aria-label="출처와 관련 정보">' in html


def test_built_html_uses_semantic_sections_for_named_home_groups(tmp_path):
    output = build(dist_path=tmp_path / "semantic-home-groups.html")
    html = output.read_text(encoding="utf-8")

    assert '<section class="home-stats" aria-label="데이터 현황">' in html
    assert '<section class="getting-started" aria-label="사이트 이용 순서">' in html
    assert '<div class="home-stats" aria-label="데이터 현황">' not in html
    assert '<div class="getting-started" aria-label="사이트 이용 순서">' not in html


def test_built_html_prints_footer_without_dark_glass_background(tmp_path):
    output = build(dist_path=tmp_path / "print-footer.html")
    html = output.read_text(encoding="utf-8")

    assert "#public-footer { background: #fff !important; color: #000; border-color: #999; -webkit-backdrop-filter: none; backdrop-filter: none; }" in html
    assert ".public-footer-grid section h2, #public-footer a { color: #000; }" in html


def test_built_html_does_not_print_transient_focus_outlines(tmp_path):
    output = build(dist_path=tmp_path / "print-focus.html")
    html = output.read_text(encoding="utf-8")

    assert "#main-content:focus, #main-content h1:focus { outline: none; }" in html
