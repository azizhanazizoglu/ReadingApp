import os
import pytest

RUN_E2E = os.getenv("RUN_E2E", "0") == "1"


@pytest.mark.skipif(not RUN_E2E, reason="Set RUN_E2E=1 to run Playwright-backed navigation test")
def test_playwright_clicks_menu_and_yeni_trafik():
    from backend.helpers.playwright_utils import open_menu_and_click_label

    start_url = "https://preview--screen-to-data.lovable.app/dashboardA"
    final_url, html = open_menu_and_click_label(start_url, "Yeni Trafik", headless=True)

    assert isinstance(html, str) and len(html) > 100
    # Expect to end up on traffic-insurance page
    assert "traffic-insurance" in final_url
