from __future__ import annotations
from dataclasses import dataclass
from typing import List
from backend.logging_utils import log_backend
import re
from bs4 import BeautifulSoup

@dataclass
class LLMTaskActions:
    actions: List[str]

class FindLLMTaskPageButton:
    """Heuristic / lightweight LLM-like task button finder.

    Generates selector candidates targeting the user command (task) text and
    related variants, prioritizing stable anchors/buttons over menu toggles.
    This is a placeholder for a future true LLM invocation, but keeps
    interface similar to FindLLMHomePageButton.
    """
    def run(self, html: str, user_command: str) -> LLMTaskActions:
        try:
            log_backend(
                "[INFO] [BE-2760] FindLLMTaskPageButton start",
                code="BE-2760",
                component="FindLLMTaskPageButton",
                extra={
                    "html_len": len(html) if isinstance(html, str) else 0,
                    "user_command": user_command,
                    "llm": True
                }
            )
        except Exception:
            pass
        actions: List[str] = []
        if not user_command:
            return LLMTaskActions(actions)
        uc_raw = user_command.strip()
        uc = uc_raw.lower()
        # Turkish / spacing variants (very light)
        variants = {uc_raw, uc_raw.replace('İ', 'i'), uc_raw.replace('  ', ' ')}
        # Word boundary partials: if two words, also attempt each
        parts = [p for p in re.split(r"\s+", uc_raw) if p]
        if len(parts) > 1:
            for p in parts:
                if len(p) > 2:
                    variants.add(p)
        # Opportunistically detect hamburger/menu button and prepend it
        try:
            soup = BeautifulSoup(html or '', 'html.parser')
            has_menu = False
            # aria-label="Menu"
            if soup.select_one("button[aria-label='Menu']"):
                has_menu = True
            # lucide-menu icon within a button
            if soup.select_one("svg.lucide-menu"):
                has_menu = True
            # data-lov-name=Menu
            if soup.select_one("button[data-lov-name='Menu']"):
                has_menu = True
            if has_menu:
                # Prepend common menu toggles; runner has debounce after these
                actions.extend([
                    "css#button:has([data-lov-name='Menu'])",
                    "css#button:has(svg.lucide-menu)",
                    "css#button[aria-label='Menu']",
                ])
        except Exception:
            pass
        # Build selectors
        for v in variants:
            v_strip = v.strip()
            if not v_strip:
                continue
            # Prefer text-driven selectors first (runner maps these to text click across many nodes)
            actions.append(f"css#text={v_strip}")
            # Anchors / buttons by own text
            actions.append(f"css#button:has(:matchesOwn('{v_strip}')), a:contains('{v_strip}')")
            # XPath precise match or descendant text
            actions.append("css#xpath=//button[.//*[normalize-space(text())='" + v_strip + "'] or normalize-space(text())='" + v_strip + "'] | //a[normalize-space(text())='" + v_strip + "']")
            # Title / aria attributes
            actions.append(f"css#a[title*='{v_strip}'], button[title*='{v_strip}']")
            # Side menu / menuitems / generic containers
            actions.append(f"css#[role='menuitem']:has(:matchesOwn('{v_strip}'))")
            actions.append(f"css#li:has(:matchesOwn('{v_strip}'))")
            actions.append(f"css#span:contains('{v_strip}')")
        # De-duplicate preserving order
        seen = set()
        dedup: List[str] = []
        for a in actions:
            if a not in seen:
                seen.add(a)
                dedup.append(a)
        try:
            # Log first few selectors for visibility
            log_backend(
                "[INFO] [BE-2761] FindLLMTaskPageButton candidates",
                code="BE-2761",
                component="FindLLMTaskPageButton",
                extra={"count": len(dedup), "llm": True, "preview": dedup[:5]}
            )
        except Exception:
            pass
        return LLMTaskActions(dedup)
