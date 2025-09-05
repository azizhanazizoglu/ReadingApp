from __future__ import annotations

from dataclasses import dataclass
from typing import List

from backend.logging_utils import log_backend


@dataclass
class LLMHomeResult:
    actions: List[str]


class FindLLMHomePageButton:
    """LLM-style heuristic finder for Home/Task buttons.

    This component mimics an LLM-assisted search by scanning the DOM text and
    emitting executable actions. It is used when static navigation fails.
    """

    def __init__(self) -> None:
        # future: accept a real LLM client or prompts
        pass

    def run(self, html: str, user_command: str) -> LLMHomeResult:
        try:
            log_backend(
                "[INFO] [BE-2750] FindLLMHomePageButton start",
                code="BE-2750",
                component="FindLLMHomePageButton",
                extra={"llm": True, "html_len": len(html) if isinstance(html, str) else 0, "user_command": user_command},
            )
        except Exception:
            pass

        actions: List[str] = []
        try:
            from bs4 import BeautifulSoup as _BS

            soup = _BS(html or "", "html.parser")

            def norm(s: str) -> str:
                return " ".join((s or "").split()).strip().lower()

            # Home synonyms across TR/EN
            home_texts = [
                "ana sayfa",
                "anasayfa",
                "home",
                "dashboard",
                "ana menü",
                "menu",
            ]
            # Task command as hint (e.g., 'Yeni Trafik')
            ulabel = norm(user_command or "")

            # Collect candidate nodes and their raw labels for both exact and contains matches
            nodes: List[tuple] = []  # (raw_label, element)
            for tag in soup.select("a, button, [role='button']"):
                raw_label = (tag.get_text(" ") or "").strip()
                label = norm(raw_label)
                if not label:
                    continue
                # Exact matches or task label
                if label in home_texts or (ulabel and label == ulabel):
                    nodes.append((raw_label, tag))
                    continue
                # Contains variations (e.g., "ana sayfaya dön")
                if "ana sayfa" in label or "anasayfa" in label or "go home" in label or "back to home" in label:
                    nodes.append((raw_label, tag))

            # Deduplicate by normalized label while preserving order; prefer plain 'ana sayfa' first
            seen = set()
            ordered: List[tuple] = []
            # Put exact 'ana sayfa' first if present
            for raw_label, el in nodes:
                if norm(raw_label) == "ana sayfa" and norm(raw_label) not in seen:
                    seen.add(norm(raw_label))
                    ordered.append((raw_label, el))
            for raw_label, el in nodes:
                key = norm(raw_label)
                if key not in seen:
                    seen.add(key)
                    ordered.append((raw_label, el))

            # Emit click by text and, when possible, a css selector using data-lov-id for robustness
            for raw_label, el in ordered:
                actions.append(f"click#{raw_label}")
                try:
                    lov_id = el.get("data-lov-id")
                    if lov_id:
                        actions.append(f"css#[data-lov-id='{lov_id}']")
                except Exception:
                    pass

            log_backend(
                "[INFO] [BE-2751] FindLLMHomePageButton candidates",
                code="BE-2751",
                component="FindLLMHomePageButton",
                extra={"llm": True, "count": len(actions)},
            )
        except Exception as e:
            log_backend(
                f"[WARN] [BE-2752] FindLLMHomePageButton error: {e}",
                code="BE-2752",
                component="FindLLMHomePageButton",
                extra={"llm": True},
            )

        return LLMHomeResult(actions=actions)
