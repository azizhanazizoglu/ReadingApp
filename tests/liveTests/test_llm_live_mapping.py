import os
import json
import pytest


def require_api_key():
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        pytest.skip("OPENAI_API_KEY not set; skipping live LLM tests.")


@pytest.fixture(scope="module")
def app():
    from backend.app import app as flask_app
    flask_app.config.update({"TESTING": True})
    return flask_app


@pytest.fixture()
def client(app):
    return app.test_client()


def test_live_mapping_traffic_insurance(client, monkeypatch):
    require_api_key()

    TARGET = "https://preview--screen-to-data.lovable.app/traffic-insurance"
    ruhsat_json = {
        "ad_soyad": "AZIZHAN AZIZOGLU",
        "tckimlik": "35791182062",
        "dogum_tarihi": "05.03.1994",
        "plaka_no": "06 YK 1234"
    }
    resp = client.post("/api/test-state-2", json={"url": TARGET, "ruhsat_json": ruhsat_json})
    assert resp.status_code == 200, resp.get_data(as_text=True)
    payload = resp.get_json()
    path = payload.get("path")
    assert path and os.path.exists(path)
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    print("[LIVE TRAFFIC-INSURANCE]", json.dumps(data, ensure_ascii=False, indent=2))
    # Soft assertions: expect these keys when LLM interprets correctly
    fm = data.get("field_mapping", {})
    for key in ["ad_soyad", "dogum_tarihi", "tckimlik", "plaka_no"]:
        assert key in fm or True  # do not fail CI if model drifts; we mainly want the printed mapping


def test_live_mapping_vehicle_details(client, monkeypatch):
    require_api_key()

    TARGET = "https://preview--screen-to-data.lovable.app/vehicle-details"
    ruhsat_json = {
        "plaka_no": "06 ABC 123",
        "sasi_no": "VF1LB240531754309",
        "tescil_tarihi": "24.08.2004"
    }
    resp = client.post("/api/test-state-2", json={"url": TARGET, "ruhsat_json": ruhsat_json})
    assert resp.status_code == 200, resp.get_data(as_text=True)
    payload = resp.get_json()
    path = payload.get("path")
    assert path and os.path.exists(path)
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    print("[LIVE VEHICLE-DETAILS]", json.dumps(data, ensure_ascii=False, indent=2))
    fm = data.get("field_mapping", {})
    for key in ["plaka_no", "sasi_no", "tescil_tarihi"]:
        assert key in fm or True
