from __future__ import annotations

"""Calibration selector utilities.

Helpers to normalize strings and build reasonably stable CSS selectors
from common HTML attributes. Keep this module dependency-free.
"""

from typing import Any, Dict, Optional
import re
import unicodedata
import hashlib


def normalize(s: Optional[str]) -> str:
    """Lowercase, trim, remove accents, collapse whitespace."""
    s = (s or "").strip()
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s


def sha(s: str, n: int = 10) -> str:
    return hashlib.sha1((s or "").encode("utf-8", errors="ignore")).hexdigest()[:n]


def build_selector(attrs: Dict[str, Any]) -> str:
    """Construct a selector from attributes, preferring stable ones.

    Priority: id > data-* > name > aria-label > placeholder > classes > tag
    """
    tag = (attrs.get("tag") or "input").strip() or "input"

    tid = (attrs.get("id") or "").strip()
    if tid:
        return f"#{tid}"

    # stable data-* attributes
    for k, v in list(attrs.items()):
        if not isinstance(k, str):
            continue
        if k.startswith("data-") and v:
            vv = str(v).replace("'", "\\'")
            return f"[{k}='{vv}']"

    name = (attrs.get("name") or "").strip()
    if name:
        nv = name.replace("'", "\\'")
        return f"{tag}[name='{nv}']"

    aria = (attrs.get("aria_label") or "").strip()
    if aria:
        av = aria.replace("'", "\\'")
        return f"{tag}[aria-label='{av}']"

    ph = (attrs.get("placeholder") or "").strip()
    if ph:
        pv = ph.replace("'", "\\'")
        return f"{tag}[placeholder='{pv}']"

    cls = (attrs.get("class") or "").strip()
    if cls:
        parts = [c for c in re.split(r"\s+", cls) if c]
        if parts:
            return f"{tag}." + ".".join(parts[:3])

    return tag
