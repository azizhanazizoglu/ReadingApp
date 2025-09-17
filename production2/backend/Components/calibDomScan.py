from __future__ import annotations

"""Calibration DOM scan utilities.

Extract candidate form inputs and actions from HTML. Uses BeautifulSoup if
available, falls back to regex-based extraction otherwise (best-effort).
"""

from typing import Any, Dict, List
import re

try:
    from bs4 import BeautifulSoup  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    BeautifulSoup = None  # type: ignore

from .calibSelectorUtils import build_selector


def _soup(html: str):
    if not BeautifulSoup:
        return None
    try:
        return BeautifulSoup(html or "", "html.parser")
    except Exception:
        return None


def extract_form_elements(html: str) -> List[Dict[str, Any]]:
    s = _soup(html)
    out: List[Dict[str, Any]] = []
    if s is None:
        # Minimal regex fallback (attributes only)
        for m in re.finditer(r"<(input|select|textarea)\b[^>]*>", html, re.IGNORECASE):
            tag = (m.group(1) or "input").lower()
            t = m.group(0)
            def _attr(a: str) -> str:
                mm = re.search(rf'{a}\s*=\s*"(.*?)"', t, re.IGNORECASE) or re.search(rf"{a}\s*=\s*'(.*?)'", t, re.IGNORECASE)
                return (mm.group(1) if mm else "").strip()
            attrs = {
                "tag": tag,
                "type": _attr("type"),
                "id": _attr("id"),
                "name": _attr("name"),
                "placeholder": _attr("placeholder"),
                "aria_label": _attr("aria-label"),
                "class": _attr("class"),
                "label_text": "",
            }
            attrs["selector"] = build_selector(attrs)
            out.append(attrs)
        return out

    for el in s.find_all(["input", "select", "textarea"]):
        attrs: Dict[str, Any] = {
            "tag": el.name,
            "type": el.get("type", ""),
            "id": el.get("id", ""),
            "name": el.get("name", ""),
            "placeholder": el.get("placeholder", ""),
            "aria_label": el.get("aria-label", ""),
            "class": " ".join(el.get("class", [])),
        }
        label_text = ""
        try:
            if attrs["id"]:
                lab = s.find("label", {"for": attrs["id"]})
                if lab:
                    label_text = lab.get_text(" ", strip=True)
            if not label_text:
                parent = el.parent
                if parent:
                    lab = parent.find("label")
                    if lab:
                        label_text = lab.get_text(" ", strip=True)
            if not label_text:
                prev = el.find_previous_sibling("label")
                if prev:
                    label_text = prev.get_text(" ", strip=True)
        except Exception:
            pass
        attrs["label_text"] = label_text
        attrs["selector"] = build_selector(attrs)
        out.append(attrs)
    return out


def detect_actions(html: str) -> List[Dict[str, Any]]:
    s = _soup(html)
    out: List[Dict[str, Any]] = []
    if s is None:
        for m in re.finditer(r"<(button|input)\b[^>]*>(.*?)</button>|<(input)\b[^>]*>", html, re.IGNORECASE | re.DOTALL):
            out.append({"text": "", "selector": "button"})
        return out
    for b in s.find_all(["button", "input", "a"]):
        if b.name == "input" and b.get("type") not in ["submit", "button"]:
            continue
        text = (b.get_text(" ", strip=True) or b.get("value", "") or "").strip()
        attrs = {
            "tag": b.name,
            "id": b.get("id", ""),
            "name": b.get("name", ""),
            "aria_label": b.get("aria-label", ""),
            "class": " ".join(b.get("class", [])),
        }
        sel = build_selector(attrs)
        out.append({"text": text, "selector": sel})
    return out
