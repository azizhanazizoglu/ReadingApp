from __future__ import annotations

from dataclasses import dataclass
from typing import List
from bs4 import BeautifulSoup

from .types import Action
from backend.logging_utils import log_backend


@dataclass
class NavPlan:
    candidates: List[Action]


class Navigator:
    """Emits candidate navigation actions for menu/task.

    Deterministic-first: returns a prioritized list of selectors/actions
    that the shell (TS3 or in-page filler) can execute.
    """

    def navigator_open_menu_candidates(self, html: str) -> NavPlan:
        # Heuristics first
        cands = [
            Action("Open side menu", selector="button[aria-label='Menu']"),
            Action("Open side menu alt", selector=".side-menu, .menu, #menu"),
        ]
        # HTML-aware detection (e.g., Lovable preview dashboard icon)
        try:
            soup = BeautifulSoup(html or "", "html.parser")
            # Find a button that contains an svg with class 'lucide-menu'
            svg = soup.select_one("button svg.lucide-menu")
            if svg:
                cands.insert(0, Action("Open side menu (lucide)", selector="button:has(svg.lucide-menu)"))
            # Also look for any element with data-lov-name="Menu" inside a button
            lov = soup.select_one("button [data-lov-name='Menu']")
            if lov:
                cands.insert(0, Action("Open side menu (lov)", selector="button:has([data-lov-name='Menu'])"))
            # Specific Lovable preview menu button by data-lov-id (from provided HTML)
            try:
                if soup.select_one("[data-lov-id='src/pages/Dashboard.tsx:40:10']"):
                    cands.insert(0, Action("Open side menu (lov-id)", selector="[data-lov-id='src/pages/Dashboard.tsx:40:10']"))
            except Exception:
                pass
        except Exception as e:
            log_backend("[WARN] [BE-2699] Nav HTML parse failed", code="BE-2699", component="Navigator", extra={"err": str(e)})
        log_backend(
            "[INFO] [BE-2601] Nav: menu candidates",
            code="BE-2601",
            component="Navigator",
            extra={"count": len(cands)}
        )
        return NavPlan(candidates=cands)

    def navigator_go_to_task_candidates(self, user_command: str, html: str) -> NavPlan:
        label = user_command.strip()
        cands = [
            Action(f"Go to {label}", selector=f"a[title*='{label}'], button:has-text('{label}')"),
            Action(f"Go to {label} (alt)", selector=f".nav a:contains('{label}')"),
        ]
        # HTML-aware detection: find clickable elements with the text
        try:
            soup = BeautifulSoup(html or "", "html.parser")
            # Match case-insensitively on visible text
            def _norm(s: str) -> str:
                return " ".join((s or "").split()).strip().lower()

            target = _norm(label)
            # Static Lovable preview: known menu item ids for Yeni Kasko (from provided HTML)
            try:
                # Only add Kasko static selectors when the user asked for it
                if 'kasko' in target:
                    if soup.select_one("[data-lov-id='src/pages/Dashboard.tsx:100:22']"):
                        cands.insert(0, Action("Go to Yeni Kasko (lov-id span)", selector="[data-lov-id='src/pages/Dashboard.tsx:100:22']"))
                    if soup.select_one("[data-lov-id='src/pages/Dashboard.tsx:98:20']"):
                        cands.insert(0, Action("Go to Yeni Kasko (lov-id button)", selector="[data-lov-id='src/pages/Dashboard.tsx:98:20']"))
            except Exception:
                pass
            hit = None
            for tag in soup.select("a, button, [role='button']"):
                txt = _norm(tag.get_text(" "))
                if target and target in txt:
                    hit = tag
                    break
            if hit is not None:
                # Prefer an xpath text match; TS3/Playwright can use 'xpath=' prefix
                xpath = f"xpath=//button[.//*[normalize-space(text())='{label}'] or normalize-space(text())='{label}'] | //a[normalize-space(text())='{label}']"
                cands.insert(0, Action(f"Go to {label} (text)", selector=xpath))
                # Also emit a CSS-with-has() variant for engines that support :has
                cands.insert(1, Action(f"Go to {label} (css-has)", selector=f"button:has(:matchesOwn('{label}')), a:contains('{label}')"))
        except Exception as e:
            log_backend("[WARN] [BE-2698] Nav text scan failed", code="BE-2698", component="Navigator", extra={"err": str(e), "task": label})
        log_backend(
            "[INFO] [BE-2602] Nav: task candidates",
            code="BE-2602",
            component="Navigator",
            extra={"count": len(cands), "task": label}
        )
        return NavPlan(candidates=cands)

    def navigator_home_candidates(self, html: str) -> NavPlan:
        """Return prioritized candidates for 'Ana Sayfa' navigation.

        Heuristics:
        - Prefer anchors with href containing '/dashboard'.
        - Use precise selectors via data-lov-id or data-component-* when available.
        - Fallback to text match 'Ana Sayfa'.
        """
        from bs4 import BeautifulSoup
        cands: list[Action] = []
        try:
            soup = BeautifulSoup(html or "", "html.parser")
            def _norm(s: str) -> str:
                return " ".join((s or "").split()).strip().lower()
            # Turkish/EN synonyms for Home
            home_syns = {
                _norm("Ana Sayfa"),
                _norm("Anasayfa"),
                _norm("Ana Sayfaya Dön"),
                _norm("Ana Sayfaya Don"),
                _norm("Home"),
                _norm("Dashboard"),
            }

            # Collect all matching elements
            matches = []
            for tag in soup.select("a, button, [role='button']"):
                txt = _norm(tag.get_text(" "))
                if txt in home_syns or any(s in txt for s in home_syns):
                    matches.append(tag)
            # Build selectors with priority
            seen = set()
            def add_selector(desc: str, sel: str):
                if sel and sel not in seen:
                    seen.add(sel)
                    cands.append(Action(desc, selector=sel))

            # Priority 1: anchors pointing to dashboard
            for tag in matches:
                if tag.name == 'a':
                    href = (tag.get('href') or '').lower()
                    if 'dashboard' in href:
                        # Prefer attribute selector if id present
                        if tag.has_attr('data-lov-id'):
                            add_selector("Home (lov-id)", f"[data-lov-id='{tag.get('data-lov-id')}']")
                        elif tag.has_attr('id'):
                            add_selector("Home (#id)", f"#{tag.get('id')}")
                        else:
                            add_selector("Home (a[href*=dashboard])", "a[href*='dashboard']")

            # Priority 2: any element with data-lov-id
            for tag in matches:
                if tag.has_attr('data-lov-id'):
                    add_selector("Home (lov-id)", f"[data-lov-id='{tag.get('data-lov-id')}']")

            # Priority 3: component-path + line
            for tag in matches:
                if tag.has_attr('data-component-path') and tag.has_attr('data-component-line'):
                    path = tag.get('data-component-path')
                    line = tag.get('data-component-line')
                    add_selector("Home (component)", f"[data-component-path='{path}'][data-component-line='{line}']")

            # Priority 4: first and subsequent matches by index (tag and nth-of-type)
            # We will generate stable selectors using tag name + nth-of-type within parent
            for tag in matches:
                try:
                    idx = 1
                    if tag.parent is not None:
                        same = [t for t in tag.parent.find_all(tag.name, recursive=False)]
                        for i, t in enumerate(same, start=1):
                            if t is tag:
                                idx = i
                                break
                    add_selector("Home (nth)", f"{tag.name}:nth-of-type({idx})")
                except Exception:
                    pass

            # Fallback: click by text (handled by frontend)
            add_selector("Home (text)", "text=Ana Sayfa")
        except Exception as e:
            log_backend("[WARN] [BE-2697] Home candidates scan failed", code="BE-2697", component="Navigator", extra={"err": str(e)})
        # Preview up to first 3 selectors to aid debugging
        preview = [a.selector for a in cands[:3] if a.selector]
        log_backend(
            "[INFO] [BE-2603] Nav: home candidates",
            code="BE-2603",
            component="Navigator",
            extra={"count": len(cands), "preview": preview}
        )
        return NavPlan(candidates=cands)
