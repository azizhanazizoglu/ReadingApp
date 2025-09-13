from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


def _is_truthy_text(v: Any) -> bool:
    try:
        if v is None:
            return False
        s = str(v).strip()
        return len(s) > 0
    except Exception:
        return False


def _value_from_after(after: Dict[str, Any]) -> Tuple[bool, Any]:
    """Return (hasValue, normalized) from ts3InPageFiller getInfo after object.
    Handles input/textarea/select structures.
    """
    try:
        tag = str(after.get('tag') or '').lower()
        typ = str(after.get('type') or '').lower()
        if tag == 'input':
            if typ == 'checkbox':
                return (bool(after.get('value')) or bool(after.get('checked')), bool(after.get('value')))
            if typ == 'radio':
                # radios report value only if selected; treat non-empty string as filled
                return (_is_truthy_text(after.get('value')), after.get('value'))
            return (_is_truthy_text(after.get('value')), after.get('value'))
        if tag == 'textarea':
            return (_is_truthy_text(after.get('value')), after.get('value'))
        if tag == 'select':
            sv = after.get('value')
            if isinstance(sv, dict):
                # { value, text }
                return (_is_truthy_text(sv.get('value')) or _is_truthy_text(sv.get('text')), sv)
            return (_is_truthy_text(sv), sv)
    except Exception:
        pass
    # fallback
    v = after.get('value') if isinstance(after, dict) else None
    return (_is_truthy_text(v), v)


def detect_forms_filled(
    details: Optional[List[Dict[str, Any]]] = None,
    html: Optional[str] = None,
    min_filled: int = 2,
) -> Dict[str, Any]:
    """Determine whether at least `min_filled` fields have been filled.

    Prefer `details` produced by ts3InPageFiller (has before/after snapshots).
    Fallback to a basic HTML parse checking non-empty value attributes.
    """
    method = 'none'
    count = 0
    changed = 0
    try:
        if isinstance(details, list) and details:
            method = 'details'
            for d in details:
                try:
                    after = d.get('after') if isinstance(d, dict) else None
                    before = d.get('before') if isinstance(d, dict) else None
                    has_val, val = _value_from_after(after or {})
                    if has_val:
                        count += 1
                        # changed if before differs from after in a basic sense
                        bv = before.get('value') if isinstance(before, dict) else None
                        if str(bv) != str(val):
                            changed += 1
                except Exception:
                    pass
        elif isinstance(html, str) and html:
            method = 'html'
            try:
                from bs4 import BeautifulSoup  # type: ignore
                soup = BeautifulSoup(html, 'html.parser')
                # Count inputs and textareas with non-empty value attribute, selects with selected option
                # Also count elements marked by our filler with data-ts3-filled="1"
                try:
                    for el in soup.select('[data-ts3-filled]'):
                        try:
                            v = el.get('data-ts3-filled')
                            if str(v).strip() in ('1', 'true', 'yes'):  # explicit mark from filler
                                count += 1
                        except Exception:
                            pass
                except Exception:
                    pass
                for el in soup.select('input, textarea'):
                    try:
                        val = el.get('value')
                        if _is_truthy_text(val):
                            count += 1
                    except Exception:
                        pass
                for sel in soup.select('select'):
                    try:
                        # If any option is selected and has non-empty text/value
                        opt = None
                        for o in sel.select('option'):
                            if o.has_attr('selected'):
                                opt = o
                                break
                        if opt is None:
                            continue
                        if _is_truthy_text(opt.get('value')) or _is_truthy_text(opt.get_text(' ').strip()):
                            count += 1
                    except Exception:
                        pass
            except Exception:
                pass
    except Exception:
        method = 'error'

    ok = count >= max(1, int(min_filled))
    return {
        'ok': ok,
        'count': count,
        'changed': changed,
        'threshold': int(min_filled),
        'method': method,
    }


if __name__ == '__main__':  # quick smoke
    print(detect_forms_filled(details=[{'before':{'tag':'input','value':''}, 'after':{'tag':'input','value':'ABC'}}, {'before':{'tag':'input','value':''}, 'after':{'tag':'input','value':'123'}}]))
