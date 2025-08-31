from pathlib import Path
import json

from backend.components.ensure_inputs import EnsureInputs
from backend.components.navigator import Navigator
from backend.components.html_capture_service import HtmlCaptureService
from backend.components.finalization import FinalDetector, Finalizer


def test_ensure_inputs_select_latest(tmp_path: Path):
    d = tmp_path / "jpg2json"
    d.mkdir()
    (d / "a.json").write_text(json.dumps({"plate": "01ABC01"}), encoding="utf-8")
    (d / "b.json").write_text(json.dumps({"plate": "34XYZ34"}), encoding="utf-8")
    ei = EnsureInputs()
    res = ei.select_latest_or_merge_ruhsat_json(d)
    assert res and res.ruhsat_json["plate"] in {"01ABC01", "34XYZ34"}


def test_ensure_inputs_extract_from_jpg(tmp_path: Path):
    d = tmp_path / "jpgDownload"
    d.mkdir()
    jpg = d / "img.jpg"
    jpg.write_bytes(b"fakejpg")

    def fake_extractor(p: Path):
        return {"plate": "06ANK06", "path": str(p)}

    ei = EnsureInputs()
    res = ei.extract_ruhsat_from_jpg(d, fake_extractor)
    assert res.ruhsat_json["plate"] == "06ANK06"


def test_navigator_candidates():
    nav = Navigator()
    plan1 = nav.navigator_open_menu_candidates("<div>Menu</div>")
    plan2 = nav.navigator_go_to_task_candidates("Yeni Trafik", "<html>")
    assert len(plan1.candidates) >= 1
    assert any("Yeni Trafik" in a.description for a in plan2.candidates)


def test_navigator_detects_lovable_dashboard_menu_and_yeni_trafik():
    nav = Navigator()
    # Provided button snippets (trimmed for brevity but keep key attributes)
    side_btn = (
        '<button class="inline-flex"><svg class="lucide lucide-menu"><line x1="4" x2="20" y1="12" y2="12"></line></svg></button>'
    )
    yeni_btn = (
        '<button class="flex items-center"><span>Yeni Trafik</span></button>'
    )
    html = f"<html><body>{side_btn}<div id='menu'>{yeni_btn}</div></body></html>"
    plan_menu = nav.navigator_open_menu_candidates(html)
    plan_task = nav.navigator_go_to_task_candidates("Yeni Trafik", html)
    # Expect our HTML-aware candidates to be prioritized
    assert any("lucide" in a.description or "lov" in a.description for a in plan_menu.candidates)
    assert any("Yeni Trafik" in a.description for a in plan_task.candidates)


def test_html_capture_persist(tmp_path: Path):
    svc = HtmlCaptureService(tmp_path)
    out = svc.persist_html("<html>ok</html>")
    assert out.html_path.exists()
    assert out.fingerprint and len(out.fingerprint) > 10


def test_finalization():
    det = FinalDetector()
    assert det.detect_final_page("Poliçeyi Aktifleştir")
    fin = Finalizer()
    mapping = {"actions": [{"description": "final submit", "selector": "#go"}]}
    assert fin.click_final_action(mapping) == "#go"
