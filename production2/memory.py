from __future__ import annotations

from typing import Any, Dict, List, Optional
from dataclasses import dataclass


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


# =====================
# Data dictionary types
# =====================

@dataclass
class HtmlCaptureInput:
    """Input to HTML capture/save component."""
    html: str
    name: Optional[str] = None


@dataclass
class HtmlCaptureResult:
    """Result from HTML capture/save component."""
    html_path: str
    fingerprint: str
    timestamp: str
    name: str


@dataclass
class FilteredHtmlRequest:
    """Request to produce mapping from filtered HTML."""
    filtered_html: Optional[str] = None
    name: Optional[str] = None


@dataclass
class RawHtmlResult:
    """Normalized raw HTML string (post-capture, pre-filter)."""
    html: str


@dataclass
class FilteredHtmlResult:
    """Filtered HTML string retaining only interactive elements."""
    html: str

@dataclass
class MappingCandidate:
    """A single UI element candidate for an action (e.g., Home button)."""
    type: str
    text: str
    attributes: Dict[str, Any]
    selectors: Dict[str, List[str]]
    score: int
    action: str


@dataclass
class MappingMeta:
    """Metadata for a mapping run/output."""
    timestamp: str
    source: str
    variants: List[str]
    html_fingerprint: Optional[str] = None


@dataclass
class MappingAction:
    """Primary action and alternative selectors to try."""
    primary_selector: Optional[str]
    action: str
    alternatives: List[str]


@dataclass
class MappingJson:
    """Top-level mapping JSON structure returned to callers and saved to disk."""
    meta: MappingMeta
    mapping: MappingAction
    candidates: List[MappingCandidate]


@dataclass
class MappingRequest:
    """Request to generate a mapping (e.g., Home button) from filtered HTML."""
    filtered_html: str
    name: Optional[str] = None


@dataclass
class PageChangeRequest:
    """Input to change-detection component."""
    current_html: str
    prev_html: Optional[str] = None
    normalize_whitespace: bool = False


@dataclass
class PageChangeResult:
    """Output from change-detection component."""
    changed: bool
    reason: str
    before_hash: Optional[str] = None
    after_hash: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


@dataclass
class FillAction:
    """A single UI automation step derived from a mapping."""
    kind: str  # e.g., "set_value" | "select_option" | "click"
    selector: str
    value: Optional[str] = None
    option: Optional[str] = None


@dataclass
class FillPlan:
    """Planned set of UI actions to apply on the page."""
    actions: List[FillAction]
    meta: Optional[Dict[str, Any]] = None


@dataclass
class RequestContext:
    """Optional context carrier for per-task/session correlation, if needed."""
    task_id: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
