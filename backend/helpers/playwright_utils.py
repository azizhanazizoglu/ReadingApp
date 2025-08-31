from __future__ import annotations

from typing import Tuple


def open_menu_and_click_label(url: str, label: str, timeout_ms: int = 15000, headless: bool = True) -> Tuple[str, str]:
    """Use Playwright (if installed) to open the page, click side menu, then click a menu item by label.

    Returns (final_url, html). Raises ImportError if playwright not installed.
    """
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:  # pragma: no cover - optional dep
        raise ImportError("playwright not installed") from e

    with sync_playwright() as p:  # pragma: no cover - integration path
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()
        page.set_default_timeout(timeout_ms)
        page.goto(url, wait_until="domcontentloaded")

        # Try multiple menu triggers
        menu_selectors = [
            "button:has(svg.lucide-menu)",
            "button:has([data-lov-name='Menu'])",
            "button[aria-label='Menu']",
        ]
        for sel in menu_selectors:
            loc = page.locator(sel).first
            if loc.count() > 0:
                try:
                    loc.click()
                    break
                except Exception:
                    pass

        # Click the label
        page.get_by_text(label, exact=True).first.click()
        try:
            page.wait_for_load_state("networkidle")
        except Exception:
            page.wait_for_load_state("domcontentloaded")

        html = page.content()
        final_url = page.url
        context.close()
        browser.close()
        return final_url, html
