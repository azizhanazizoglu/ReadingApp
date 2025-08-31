from pathlib import Path

from backend.components.diff_service import DiffService
from backend.components.classify_page import ClassifyPage, PageKind


def test_diff_service_change_detection():
    s = DiffService()
    a = "<html><body>v1</body></html>"
    b = "<html><body>v2</body></html>"
    r1 = s.diff(a, a)
    r2 = s.diff(a, b)
    assert r1.changed is False
    assert r2.changed is True


def test_classify_page_basic():
    # Simulate a home/menu page
    html = "<html><body><div>Side Menu</div><a>Home</a></body></html>"
    clf = ClassifyPage()
    res = clf.classify(html)
    assert res.kind in {PageKind.home, PageKind.dashboard}
