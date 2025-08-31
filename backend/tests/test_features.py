from pathlib import Path

from backend.components.navigator import Navigator
from backend.components.diff_service import DiffService
from backend.components.html_capture_service import HtmlCaptureService
from backend.components.mapping_validator import MappingValidator
from backend.components.script_filler import ScriptFiller
from backend.components.finalization import FinalDetector, Finalizer
from backend.features.find_home_page import FindHomePage
from backend.features.map_and_fill import MapAndFill


def test_feature_find_home_page(tmp_path: Path):
    nav = Navigator()
    diff = DiffService()
    cap = HtmlCaptureService(tmp_path)
    feat = FindHomePage(nav, diff, cap)
    res = feat.run("Yeni Trafik", "<html><body>menu</body></html>")
    assert res.success and res.attempts >= 1

def test_feature_find_home_page_emits_home_action(tmp_path: Path):
        nav = Navigator()
        diff = DiffService()
        cap = HtmlCaptureService(tmp_path)
        feat = FindHomePage(nav, diff, cap)
        html = """
        <html>
            <body>
                <button>Ana Sayfa</button>
            </body>
        </html>
        """
        res = feat.run("Yeni Trafik", html)
        assert res.success
        assert any(a.lower() == 'click#ana sayfa' for a in res.actions)


def test_feature_map_and_fill():
    def fake_llm(html: str, ruhsat: dict):
        return {
            "fields": [{"selector": "#plate", "value": ruhsat.get("plate", "") }],
            "actions": [{"selector": "#submit", "description": "final submit"}],
            "page_kind": "user_task",
            "is_final": True,
        }

    def fake_analyze(html: str, mapping: dict):
        # Count hits: assume both selectors exist for test purposes
        return {"#plate": 1, "#submit": 1}

    validator = MappingValidator(fake_analyze, min_hits=2)
    filler = ScriptFiller()
    diff = DiffService()
    final_detector = FinalDetector()
    finalizer = Finalizer()
    feat = MapAndFill(fake_llm, validator, filler, diff, final_detector, finalizer)
    res = feat.run("<html><input id='plate'/><button id='submit'></button></html>", {"plate": "06ANK06"})
    assert res.mapping_valid is True
    assert res.changed is True
    # Our fake_llm marks is_final True and detector uses markers; not guaranteed here
