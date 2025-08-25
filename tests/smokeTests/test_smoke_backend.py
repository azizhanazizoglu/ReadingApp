import io
import json
import os
import types

import pytest
import sys


@pytest.fixture(scope="module")
def app():
    # Provide a dummy 'openai' module so imports in license_llm/* don't fail during tests
    if 'openai' not in sys.modules:
        dummy = types.SimpleNamespace()
        class _DummyClient:
            def __init__(self, *a, **k):
                pass
        # Attributes possibly accessed by imported modules
        dummy.OpenAI = _DummyClient
        dummy.api_key = None
        dummy.chat = types.SimpleNamespace(completions=types.SimpleNamespace(create=lambda *a, **k: None))
        sys.modules['openai'] = dummy
    # Import the Flask app
    from backend.app import app as flask_app
    flask_app.config.update({
        "TESTING": True,
    })
    return flask_app


@pytest.fixture()
def client(app):
    return app.test_client()


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data == {"status": "ok"}


def test_upload_jpeg(client, tmp_path):
    # Create a tiny fake jpg file
    jpg_bytes = b"\xff\xd8\xff\xdbFAKEJPEGDATA\xff\xd9"
    data = {
        'file': (io.BytesIO(jpg_bytes), 'test.jpg')
    }
    resp = client.post("/api/upload", data=data, content_type='multipart/form-data')
    assert resp.status_code == 200
    payload = resp.get_json()
    assert "file_path" in payload
    assert os.path.exists(payload["file_path"])  # saved into memory/TmpData/jpgDownload


def test_ts1_start_automation(client, monkeypatch):
    # Monkeypatch the OpenAI-based extractor to avoid external dependency
    from backend import stateflow_agent as sfa

    def fake_extract_vehicle_info_from_image(path: str):
        return {
            "tckimlik": "35791182456",
            "dogum_tarihi": "05.03.1994",
            "ad_soyad": "Aziz Serdar",
            "plaka_no": "06 AK 8886",
            "belge_seri": "VF1LB240531754309",
            "sasi_no": "VF1LB240531754309",
            "model_yili": "2005",
            "tescil_tarihi": "24.08.2004"
        }

    monkeypatch.setattr(sfa, "extract_vehicle_info_from_image", fake_extract_vehicle_info_from_image)

    # Ensure there is at least one JPEG in jpgDownload (independent of upload test order)
    jpg_dir = os.path.join('memory', 'TmpData', 'jpgDownload')
    os.makedirs(jpg_dir, exist_ok=True)
    any_jpg = next((f for f in os.listdir(jpg_dir) if f.lower().endswith('.jpg')), None)
    if not any_jpg:
        with open(os.path.join(jpg_dir, 'dummy.jpg'), 'wb') as f:
            f.write(b"\xff\xd8\xff\xdbFAKEJPEGDATA\xff\xd9")

    resp = client.post("/api/start-automation")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "TS1" in data.get("result", "")

    # Ensure jpg2json has a JSON output
    out_dir = os.path.join('memory', 'TmpData', 'jpg2json')
    if os.path.isdir(out_dir):
        files = [f for f in os.listdir(out_dir) if f.lower().endswith('.json')]
        assert len(files) >= 1


def test_ts2_mapping_required_fields_for_target_site(client, monkeypatch):
        # Target website (kept for reference in request, but we stub network)
        TARGET_URL = "https://preview--screen-to-data.lovable.app/traffic-insurance"

        # Stub readWebPage to avoid network and provide a minimal HTML resembling the target form
        import backend.app as app_mod

        def fake_readWebPage(url=None):
                return """
                <form>
                    <div>
                        <label for="identity">Kimlik Bilgisi</label>
                        <input id="identity" name="identity" type="text" />
                    </div>
                    <div>
                        <label for="birthDate">Doğum Tarihi</label>
                        <input id="birthDate" name="birthDate" type="text" />
                    </div>
                    <div>
                        <label for="name">Ad/Soyad</label>
                        <input id="name" name="name" type="text" />
                    </div>
                    <div>
                        <label for="plate">Plaka No</label>
                        <input id="plate" name="plate" type="text" />
                    </div>
                    <button id="DEVAM">DEVAM</button>
                </form>
                """

        def fake_map_json_to_html_fields(html, ruhsat_json):
                # Return code-fenced JSON to exercise extraction and include all required fields
                return """
```json
{
    "field_mapping": {
        "tckimlik": "input#identity",
        "dogum_tarihi": "input#birthDate",
        "ad_soyad": "input#name",
        "plaka_no": "input#plate"
    },
    "actions": ["click#DEVAM"]
}
```
""".strip()

        monkeypatch.setattr(app_mod, "readWebPage", fake_readWebPage)
        monkeypatch.setattr(app_mod, "map_json_to_html_fields", fake_map_json_to_html_fields)

        ruhsat_json = {
                "tckimlik": "35791182456",
                "dogum_tarihi": "05.03.1994",
                "ad_soyad": "AZIZHAN A*****Ü",
                "plaka_no": "06 YK 0000"
        }

        # Pass URL to align with real usage, though HTML is stubbed
        resp = client.post("/api/test-state-2", json={"url": TARGET_URL, "ruhsat_json": ruhsat_json})
        assert resp.status_code == 200
        payload = resp.get_json()
        assert payload.get("result") == "Mapping kaydedildi"
        path = payload.get("path")
        assert path and os.path.exists(path)
        print(f"[SMOKE] Mapping saved: {path}")
        # Record for terminal summary
        try:
            from tests.smokeTests.conftest import recorded_paths
            recorded_paths.append(path)
        except Exception:
            pass

        # Validate saved JSON structure and required fields
        with open(path, encoding="utf-8") as f:
                saved = json.load(f)
        fm = saved.get("field_mapping", {})
        assert isinstance(fm, dict) and len(fm) >= 4
        for key in ["tckimlik", "dogum_tarihi", "ad_soyad", "plaka_no"]:
                assert key in fm and isinstance(fm[key], str) and fm[key].startswith("input#")
        actions = saved.get("actions", [])
        assert isinstance(actions, list) and "click#DEVAM" in actions
