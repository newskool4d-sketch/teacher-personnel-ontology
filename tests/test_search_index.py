import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from schema import Node
from search_index import to_chosung, build_search_index


def test_chosung_basic():
    assert to_chosung("육아휴직") == "ㅇㅇㅎㅈ"


def test_chosung_mixed_with_ascii():
    assert to_chosung("호봉 14") == "ㅎㅂ 14"


def test_build_search_index_length_matches_nodes():
    nodes = [
        Node(id="leave-childcare", type="개념", title="육아휴직", chapter=3, scope="공통",
             summary="자녀 1명당 3년", body="복직 신청 절차를 포함한다.",
             refs=["교육공무원법 제44조"], pages={"중등": "100-101"}, aliases=["육휴"]),
    ]
    idx = build_search_index(nodes)
    assert len(idx) == 1
    assert idx[0]["id"] == "leave-childcare"
    assert idx[0]["chosung"].startswith("ㅇㅇㅎㅈ")
    assert "육휴" in idx[0]["haystack"]
    assert "복직 신청" in idx[0]["haystack"]
    assert "교육공무원법 제44조" in idx[0]["haystack"]
    assert idx[0]["scope"] == "공통"
    assert idx[0]["pages"]["중등"] == "100-101"
