from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import hashlib
import shutil
import sys
import json
from pathlib import Path as _Path


@dataclass
class SaveHtmlResult:
    html_path: Path
    fingerprint: str
    timestamp: str
    name: str


"""Utilities for saving and filtering HTML.

Data types are declared in production2/memory.py (data dictionary).
This module stays stateless except for a small in-process HTML history used in dev.
"""

# Ensure project root (production2) is importable when running via uvicorn/module
_this = _Path(__file__).resolve()
_root = _this.parents[2]  # production2
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from memory import RawHtmlResult, FilteredHtmlResult, HtmlCaptureResult  # type: ignore  # noqa: E402


def _project_root() -> Path:
    # .../production2/backend/Components/getHtml.py -> parents[2] == production2
    return Path(__file__).resolve().parents[2]


def _tmp_html_dir() -> Path:
    return _project_root() / "tmp" / "html"


def _safe_name(name: str) -> str:
    return name.replace("/", "_").replace("\\", "_")


def _fingerprint(html: str) -> str:
    return hashlib.sha256((html or "").encode("utf-8")).hexdigest()


def get_Html(raw_html: Optional[str]) -> RawHtmlResult:
    """Return the HTML captured from the iframe (frontend sends it).

    For now, this is a simple normalizer/passthrough that ensures we always
    work with a string. If later we need to post-process (e.g., strip scripts,
    normalize whitespace), we can do it here without changing callers.
    """
    return RawHtmlResult(html=(raw_html or "").strip())

def filter_Html(raw_html: Optional[str]) -> FilteredHtmlResult:
    """Filter raw HTML and keep only interactive elements relevant for automation.

    Keeps a compact subset of the page:
    - forms (with their input/select/textarea/button controls)
    - standalone inputs/selects/textareas/buttons not within forms
    - actionable links (role=button, onclick, javascript: links)

    Removes styling and decorative content to reduce token usage.
    """
    if not raw_html:
        return FilteredHtmlResult(html="")

    try:
        from bs4 import BeautifulSoup  # type: ignore
    except Exception:
        BeautifulSoup = None  # type: ignore

    html = (raw_html or "").strip()

    # If BeautifulSoup isn't available, use a compact regex fallback.
    if BeautifulSoup is None:
        import re as _re  # Fallback: naive regex extraction of relevant controls
        patterns = [
            r"<form[^>]*>.*?</form>",
            r"<button[^>]*>.*?</button>",
            r"<input[^>]*>",
            r"<select[^>]*>.*?</select>",
            r"<textarea[^>]*>.*?</textarea>",
            r"<a[^>]*(?:role=['\"]button['\"]|onclick=|href=['\"]javascript:)[^>]*>.*?</a>",
        ]
        found: list[str] = []
        for pat in patterns:
            found += _re.findall(pat, html, flags=_re.IGNORECASE | _re.DOTALL)
        if not found:
            return FilteredHtmlResult(html="<!DOCTYPE html><html><head><meta charset='UTF-8'><title>Filtered</title></head><body><!-- no interactive elements --></body></html>")
        body = [
            "<!DOCTYPE html><html><head><meta charset='UTF-8'><title>Filtered</title></head><body>",
            "<!-- Compact interactive elements (regex fallback) -->",
        ]
        # Soft cap
        for el in found[:100]:
            # strip class/style noise, keep data-* attributes
            el = _re.sub(r"\s+(?:class|style)=['\"][^'\"]*['\"]", "", el, flags=_re.IGNORECASE)
            body.append(el)
        body.append("</body></html>")
        return FilteredHtmlResult(html="\n".join(body))

    soup = BeautifulSoup((raw_html or ""), "html.parser")

    # Remove known noise elements (e.g., builder badges/overlays)
    try:
        for bad in soup.select('#lovable-badge, #lovable-badge *, #lovable-badge-close'):
            bad.extract()
    except Exception:
        pass

    # Output skeleton
    out = BeautifulSoup("<!DOCTYPE html><html><head><meta charset='UTF-8'><title>Filtered</title></head><body></body></html>", "html.parser")
    out_body = out.body

    # Helpers
    ALLOWED_ATTRS = {
        "id", "name", "type", "value", "placeholder", "href", "onclick", "role",
        "aria-label", "aria-labelledby", "aria-describedby",
        "title", "alt", "for", "form", "checked", "selected", "disabled",
        # form-specific
        "action", "method", "enctype", "accept", "accept-charset", "autocomplete", "novalidate", "target",
        # input-specific
        "min", "max", "step", "pattern", "maxlength", "minlength", "required"
    }

    # Build a simple map of label text by input id (label[for])
    label_map: dict[str, str] = {}
    try:
        for lab in soup.find_all('label'):
            lab_for = (lab.get('for') or '').strip()
            if not lab_for:
                continue
            text = (lab.get_text(separator=' ', strip=True) or '').strip()
            if text:
                label_map[lab_for] = text if len(text) <= 120 else (text[:120] + '...')
    except Exception:
        pass

    def clone_clean(tag):
        nt = out.new_tag(tag.name)
        # copy select attributes only
        for k, v in (tag.attrs or {}).items():
            if k in ("class", "style"):
                continue
            if k.startswith("data-"):
                # keep data-* (but it's okay, often helpful for testing selectors)
                nt.attrs[k] = v
            elif k in ALLOWED_ATTRS:
                nt.attrs[k] = v
        # Attach human-friendly label if available via <label for="id">
        try:
            el_id = (tag.get('id') or '').strip()
            if el_id and el_id in label_map:
                # provide both aria-label (if missing) and data-label for LLM context
                if not nt.get('aria-label'):
                    nt.attrs['aria-label'] = label_map[el_id]
                nt.attrs['data-label'] = label_map[el_id]
        except Exception:
            pass
        # content rules
        if tag.name == "select":
            for opt in tag.find_all("option"):
                opt_new = out.new_tag("option")
                for k, v in (opt.attrs or {}).items():
                    if k in ("value", "selected", "disabled", "label"):
                        opt_new.attrs[k] = v
                text = (opt.get_text(strip=True) or "")
                if len(text) > 80:
                    text = text[:80] + "..."
                opt_new.string = text
                nt.append(opt_new)
        elif tag.name in ("button", "a"):
            text = (tag.get_text(separator=" ", strip=True) or "")
            if len(text) > 120:
                text = text[:120] + "..."
            if text:
                nt.string = text
            # Preserve minimal icon cues so static/LLM can target icon-only controls
            try:
                # Look for common icon-bearing children and clone a tiny placeholder
                icon_children = []
                # Prioritize direct children; fall back to any descendant if none
                direct = list(tag.find_all(["svg", "i", "use", "img"], recursive=False))
                if direct:
                    icon_children = direct
                else:
                    icon_children = tag.find_all(["svg", "i", "use", "img"], limit=3)

                def _trim(s: str, n: int = 120) -> str:
                    return s if len(s) <= n else (s[:n] + "...")

                kept = 0
                for ch in icon_children:
                    if kept >= 3:
                        break
                    nm = getattr(ch, "name", "") or ""
                    if nm not in ("svg", "i", "use", "img"):
                        continue
                    ic = out.new_tag(nm)
                    # Only copy a few attributes that help build selectors
                    if nm in ("svg", "i"):
                        cls = ch.get("class") or []
                        if isinstance(cls, list):
                            cls_str = " ".join(cls)
                        else:
                            cls_str = str(cls)
                        if cls_str:
                            ic.attrs["class"] = _trim(cls_str)
                        aria = ch.get("aria-label") or ch.get("title")
                        if aria:
                            ic.attrs["aria-label"] = _trim(str(aria))
                    elif nm == "use":
                        href = ch.get("href") or ch.get("xlink:href")
                        if href:
                            ic.attrs["href"] = _trim(str(href))
                    elif nm == "img":
                        alt = ch.get("alt") or ch.get("title")
                        if alt:
                            ic.attrs["alt"] = _trim(str(alt))
                    nt.append(ic)
                    kept += 1
            except Exception:
                pass
        elif tag.name == "textarea":
            # don't copy free text content (could be big / sensitive)
            placeholder = tag.get("placeholder")
            if placeholder:
                nt.attrs["placeholder"] = placeholder
        # input and others: no inner content
        return nt

    def section(title: str, sec_id: str):
        out_body.append(out.new_string(f"\n<!-- {title} -->\n"))
        div = out.new_tag("div", id=sec_id)
        out_body.append(div)
        return div

    # 1) Forms (include only controls inside)
    forms_div = section("Forms", "forms")
    forms = soup.find_all("form")
    for form in forms[:5]:  # limit big pages
        fclean = clone_clean(form)
        controls = form.find_all(["input", "select", "textarea", "button"]) or []
        for c in controls[:60]:  # cap per form
            fclean.append(clone_clean(c))
        forms_div.append(fclean)
    if len(forms) > 5:
        forms_div.append(out.new_string(f"\n<!-- ... and {len(forms)-5} more forms omitted -->\n"))

    # 2) Standalone buttons (not inside forms)
    buttons_div = section("Buttons", "buttons")
    buttons = [b for b in soup.find_all("button") if not b.find_parent("form")]
    for b in buttons[:20]:
        buttons_div.append(clone_clean(b))
    if len(buttons) > 20:
        buttons_div.append(out.new_string(f"\n<!-- ... and {len(buttons)-20} more buttons omitted -->\n"))

    # 3) Standalone inputs/selects/textareas (not inside forms)
    inputs_div = section("Inputs", "inputs")
    inputs = [i for i in soup.find_all(["input", "select", "textarea"]) if not i.find_parent("form")]
    for i in inputs[:40]:
        inputs_div.append(clone_clean(i))
    if len(inputs) > 40:
        inputs_div.append(out.new_string(f"\n<!-- ... and {len(inputs)-40} more inputs omitted -->\n"))

    # 4) Actionable links and generic clickable elements
    links_div = section("Actionable Links / Clickables", "clickables")
    links = soup.find_all("a")
    actionable: list = []
    for a in links:
        cls = " ".join(a.get("class", [])).lower()
        href = (a.get("href") or "").lower()
        role = (a.get("role") or "").lower()
        if "button" in cls or role == "button" or href.startswith("javascript:") or a.has_attr("onclick"):
            actionable.append(a)
    # also include any element with onclick that isn't already included in forms/buttons
    onclick_nodes = soup.select("[onclick]")
    actionable += onclick_nodes
    # dedup by id or stringified pointer
    seen = set()
    deduped = []
    for el in actionable:
        key = el.get("id") or str(el)
        if key in seen:
            continue
        seen.add(key)
        # skip if inside a form (already captured) or is a button
        if el.find_parent("form") or el.name == "button":
            continue
        deduped.append(el)
    for a in deduped[:20]:
        links_div.append(clone_clean(a))
    if len(deduped) > 20:
        links_div.append(out.new_string(f"\n<!-- ... and {len(deduped)-20} more clickables omitted -->\n"))

    # Summary comment
    try:
        orig_len = len(raw_html)
        new_len = len(str(out))
        ratio = max(0, 100 - int(new_len * 100 / max(1, orig_len)))
    except Exception:
        ratio = 0
    out_body.append(out.new_string(f"\n<!-- filtered: ~{ratio}% smaller -->\n"))

    return FilteredHtmlResult(html=str(out))
def get_save_Html(
    content: "str | RawHtmlResult | FilteredHtmlResult",
    name: Optional[str] = None,
    stage: Optional[str] = None,
) -> HtmlCaptureResult:
    """Save provided HTML to tmp/html as JSON (pure saver, no filtering).

    - content: HTML string or a dataclass with an 'html' field.
    - name: optional base name; if omitted, a timestamp-based name is used.
    - stage: optional label to prefix the filename (e.g., 'nonfiltered', 'filtered').

    Produces tmp/html/[stage_]name.json and returns metadata.
    """
    # Extract HTML string from various inputs
    if isinstance(content, str):
        html_str = content
    elif isinstance(content, (RawHtmlResult, FilteredHtmlResult)):
        html_str = content.html
    else:
        # Best-effort
        html_str = str(content)

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%fZ")
    use_name = _safe_name(name or f"page_{ts}")
    prefix = f"{stage}_" if stage else ""

    out_dir = _tmp_html_dir()
    out_dir.mkdir(parents=True, exist_ok=True)

    fp = _fingerprint(html_str)

    json_data = {
        "html": html_str,
        "metadata": {
            "fingerprint": fp,
            "timestamp": ts,
            "name": use_name,
            "stage": stage or "default",
            "captured_at": datetime.utcnow().isoformat() + "Z",
        },
    }

    out_path = out_dir / f"{prefix}{use_name}.json"
    out_path.write_text(json.dumps(json_data, indent=2, ensure_ascii=False), encoding="utf-8")

    result = HtmlCaptureResult(html_path=str(out_path), fingerprint=fp, timestamp=ts, name=use_name)
    return result


def remember_raw_html(html: str, meta: Optional[Dict[str, Any]] = None) -> RawHtmlResult:
    """Normalize raw HTML only (stateless; no storage)."""
    return get_Html(html)
