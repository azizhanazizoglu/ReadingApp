from __future__ import annotations

from typing import Any, Dict, List, Optional


class HtmlMemoryStore:
    """In-RAM store for HTML captures with a small history (dev/debug).

    - last_html: most recent HTML string
    - history: list of {"html": str, ...meta}
    - max_history: cap to avoid unbounded growth
    """

    def __init__(self, max_history: int = 50) -> None:
        self.max_history = max_history
        self.last_html: Optional[str] = None
        self.history: List[Dict[str, Any]] = []

    def remember(self, html: str, meta: Dict[str, Any]) -> None:
        self.last_html = html
        self.history.append({"html": html, **meta})
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history :]

    def get_last_html(self) -> Optional[str]:
        return self.last_html

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self.history)


class Memory:
    """General shared in-memory registry for dev/debug data.

    Holds category-specific stores (e.g., html). Extend later with JSON mappings, etc.
    """

    def __init__(self) -> None:
        # Filtered HTML captures (post-processed/compact)
        self.html = HtmlMemoryStore()
        # Raw HTML captures (as-is, not filtered) for accurate diffs/comparisons
        self.raw_html = HtmlMemoryStore()
        # Placeholder for future categories, e.g.:
        # self.mappings = {}


# Global singleton registry
memory = Memory()
