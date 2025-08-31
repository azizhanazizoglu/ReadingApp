import os
import pytest
import requests

from backend.features.tsx_orchestrator import TsxOrchestrator
from webbot.test_webbot_html_mapping import readWebPage


RUN_LIVE = os.getenv("RUN_LIVE_TESTS", "0") == "1"


def _fetch_html(url: str) -> str:
    try:
        # Prefer local helper (handles timeout);
        return readWebPage(url)
    except Exception:
        # Fallback to requests if helper signature changes
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        return r.text


def _fake_llm_mapping(html: str, ruhsat_json: dict) -> dict:
    """Return a deterministic mapping JSON, independent of real DOM, for test purposes."""
    # Minimal but valid mapping structure
    return {
        "version": 1,
        "page_kind": "fill_form",
        "is_final_page": False,
        "field_mapping": {
            "tckimlik": "#tc",
            "ad_soyad": "#name",
            "dogum_tarihi": "#birth",
        },
        "actions": ["click#DEVAM"],
    }


def _fake_analyze_selectors(html: str, mapping: dict) -> dict:
    """Return selector hit counts ignoring actual CSS; just ensure >= min_hits (3)."""
    return {"sel1": 2, "sel2": 2}


def _ruhsat_sample() -> dict:
    return {
        "ad_soyad": "Test Kullanıcı",
        "tckimlik": "12345678901",
        "dogum_tarihi": "01.01.1990",
        "plaka_no": "34ABC123",
    }


@pytest.mark.skipif(not RUN_LIVE, reason="Set RUN_LIVE_TESTS=1 to run live URL integration tests")
@pytest.mark.parametrize(
    "url, expect_state",
    [
    ("https://preview--screen-to-data.lovable.app/dashboardA", "navigated"),
        ("https://preview--screen-to-data.lovable.app/dashboard", "navigated"),
        ("https://preview--screen-to-data.lovable.app/traffic-insurance", "mapped"),
        ("https://preview--screen-to-data.lovable.app/vehicle-details", "mapped"),
        ("https://preview--screen-to-data.lovable.app/insurance-quote", "mapped"),
    ],
)
def test_tsx_orchestrator_live_pages(url: str, expect_state: str, tmp_path):
    html = _fetch_html(url)
    assert isinstance(html, str) and len(html) > 100, "HTML empty from live URL"

    orch = TsxOrchestrator(_fake_llm_mapping, _fake_analyze_selectors, workspace_tmp=str(tmp_path))
    res = orch.run_step(
        user_command="Traffic Insurance",  # arbitrary; only used by navigator
        html=html,
        ruhsat_json=_ruhsat_sample(),
        prev_html=None,
    )

    assert res.state == expect_state, f"Expected {expect_state} for {url}, got {res}"
    # Additional sanity on details
    assert isinstance(res.details, dict)
    if expect_state == "navigated":
        assert "attempts" in res.details
        assert 1 <= int(res.details.get("attempts", 0)) <= 3
    if expect_state == "mapped":
        assert "changed" in res.details
        assert "is_final" in res.details
