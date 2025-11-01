import sys
import os
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
from Components.llmFeedbackManager import LLMFeedbackManager


def test_convert_mappings_orders_traffic_first():
    mgr = LLMFeedbackManager()
    # Vehicle details mapping intentionally placed first (wrong chronological order)
    vehicle_mapping = {
        "ok": True,
        "page_kind": "fill_form",
        "field_mapping": {
            "plaka_no": "[data-lov-id='src/pages/VehicleDetails.tsx:79:16']",
            "motor_no": "[data-lov-id='src/pages/VehicleDetails.tsx:87:16']",
        },
        "actions": ["Devam"]
    }
    traffic_mapping = {
        "ok": True,
        "page_kind": "fill_form",
        "field_mapping": {
            "plaka_no": "#plateNo",
            "tckimlik": "#identity"
        },
        "actions": ["Devam"]
    }
    final_mapping = {
        "ok": True,
        "page_kind": "final_activation",
        "field_mapping": {},
        "actions": ["Poliçeyi Aktifleştir"]
    }
    result = mgr.convert_mappings_to_calib_format([vehicle_mapping, traffic_mapping, final_mapping], "example.com", "TaskX")
    assert result["ok"] is True
    # Root must reflect traffic page (#plateNo present) not vehicle details data-lov-id selectors
    assert result["fieldSelectors"].get("plaka_no") == "#plateNo"
    assert "#identity" in result["fieldSelectors"].values() or "tckimlik" in result["fieldSelectors"]
    # Pages ordering: first page's urlSample should be traffic-insurance if classification logic later enhanced
    # For now we just assert first page fieldSelectors uses #plateNo
    first_page = result["pages"][0]
    assert first_page["fieldSelectors"].get("plaka_no") == "#plateNo"
    # Ensure vehicle details mapping still present as a later page
    assert any("VehicleDetails" in str(v) for p in result["pages"][1:] for v in p.get("fieldSelectors", {}).values())
