from __future__ import annotations

from typing import Any, Dict, Optional
from pathlib import Path as _Path
from datetime import datetime
import shutil
import sys
import os

# Ensure production2 is importable
_this = _Path(__file__).resolve()
_root = _this.parents[2]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from config import (  # type: ignore
    get_llm_prompt_find_home_page_default,
    get_llm_max_attempts_find_home_page,
)
from logging_utils import log
from Components.fillPageFromMapping import fill_and_go  # type: ignore
import re as _re


def def_let_llm_map(
    filtered_html: str,
    mapping: Any,
    llm_feedback: Optional[str] = None,
    llm_attempt_index: Optional[int] = None,
) -> Dict[str, Any]:
    """Build LLM mapping plan context from filtered HTML and config.

    Inputs:
    - filtered_html: output of filter_Html(html).html
    - mapping: MappingJson dataclass from mappingStatic.map_home_page_static
    - llm_feedback: free text from UI about failed candidates/tries
    - llm_attempt_index: 0-based attempt number from UI

    Outputs:
    - On success: { ok: True, planLetLLMMap: { attempt, maxAttempts, prompt, filteredHtml, hints } }
    - On limit reached: { ok: False, error: "LLM attempt limit reached", llm: { attempt, maxAttempts } }
    """
    default_prompt = get_llm_prompt_find_home_page_default()
    attempt = llm_attempt_index if isinstance(llm_attempt_index, int) else 0
    max_attempts = get_llm_max_attempts_find_home_page()

    if attempt >= max_attempts:
        print(f"[letLLMMap] attempt={attempt} >= maxAttempts={max_attempts}; refusing to build prompt")
        return {
            "ok": False,
            "error": "LLM attempt limit reached",
            "llm": {"attempt": attempt, "maxAttempts": max_attempts},
        }

    composed_prompt = default_prompt
    fb = (llm_feedback or "").strip()
    if fb:
        composed_prompt += "\n\nContext (previous failed attempts and notes):\n" + fb

    # Extract hints from mapping (best-effort; mapping is a dataclass)
    try:
        variants = getattr(mapping.mapping, "alternatives", []) or []  # type: ignore[attr-defined]
    except Exception:
        variants = []
    try:
        primary = getattr(mapping.mapping, "primary_selector", None)  # type: ignore[attr-defined]
    except Exception:
        primary = None

    # Save prompts to tmp/prompts/findHomePage (clean once when attempt==0)
    prompts_dir = _root / "tmp" / "prompts" / "findHomePage"
    try:
        if attempt == 0:
            if prompts_dir.exists():
                for p in prompts_dir.iterdir():
                    try:
                        if p.is_file() or p.is_symlink():
                            p.unlink()
                        elif p.is_dir():
                            shutil.rmtree(p, ignore_errors=True)
                    except Exception:
                        pass
        prompts_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%fZ")
    default_path = prompts_dir / f"default_prompt_{ts}.txt"
    composed_path = prompts_dir / f"composed_prompt_attempt{attempt}_{ts}.txt"
    feedback_path = prompts_dir / f"feedback_attempt{attempt}_{ts}.txt"
    filtered_path = prompts_dir / f"filtered_attempt{attempt}_{ts}.html"
    meta_path = prompts_dir / f"meta_attempt{attempt}_{ts}.json"
    # Will be populated only if an LLM call is made
    llm_raw_path = prompts_dir / f"llm_response_attempt{attempt}_{ts}.txt"
    llm_parsed_path = prompts_dir / f"llm_parsed_attempt{attempt}_{ts}.json"
    try:
        default_path.write_text(default_prompt, encoding="utf-8")
    except Exception:
        pass
    try:
        composed_path.write_text(composed_prompt, encoding="utf-8")
    except Exception:
        pass
    try:
        if fb:
            feedback_path.write_text(fb, encoding="utf-8")
    except Exception:
        pass
    try:
        if filtered_html:
            filtered_path.write_text(filtered_html, encoding="utf-8")
    except Exception:
        pass
    try:
        import json as _json
        meta = {
            "attempt": attempt,
            "maxAttempts": max_attempts,
            "feedbackLen": len(fb),
            "promptLen": len(composed_prompt),
            "timestamp": ts,
        }
        meta_path.write_text(_json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass

    msg = f"attempt {attempt+1}/{max_attempts} fb_len={len(fb)} prompt_len={len(composed_prompt)}"
    log("INFO", "LLM-SAVED", msg, component="letLLMMap", extra={
        "attempt": attempt,
        "maxAttempts": max_attempts,
        "paths": {
            "dir": str(prompts_dir),
            "default": str(default_path),
            "composed": str(composed_path),
            "feedback": str(feedback_path) if fb else None,
            "filtered": str(filtered_path) if filtered_html else None,
            "meta": str(meta_path),
        },
        "llm": True,
    })

    # Optionally call OpenAI if key exists
    llm_suggestion: Optional[Dict[str, Any]] = None
    llm_candidates: list[Dict[str, Any]] = []
    # Build a fast lookup of selectors already tried from feedback text (best-effort)
    _fb_tried_set: set[str] = set()
    try:
        if fb:
            # extract lines like `selector=...` or raw selectors after `] `
            for line in fb.splitlines():
                line = line.strip()
                if not line:
                    continue
                if 'selector=' in line:
                    sel = line.split('selector=', 1)[1].strip()
                    if sel:
                        _fb_tried_set.add(sel)
                else:
                    # lines like [12] css:...
                    m = _re.search(r"\]\s*(.+)$", line)
                    if m:
                        _fb_tried_set.add(m.group(1).strip())
    except Exception:
        pass
    key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("LLM_MODEL", "gpt-4o")
    if key:
        try:
            # Import lazily to avoid test/runtime import issues when key is absent
            try:
                from openai import OpenAI  # type: ignore
                client = OpenAI(api_key=key)
                messages = [
                    {"role": "system", "content": "You will return ONLY strict JSON with the requested schema. No prose."},
                    {"role": "user", "content": composed_prompt},
                    {"role": "user", "content": filtered_html[:18000] if filtered_html else ""},
                ]
                resp = client.chat.completions.create(
                    model=model,
                    messages=messages,  # type: ignore[arg-type]
                    temperature=0.0,
                    max_tokens=256,
                )
                content = (resp.choices[0].message.content or "").strip()
            except Exception:
                # Fallback to legacy API path if available
                import openai  # type: ignore
                openai.api_key = key
                content = openai.chat.completions.create(  # type: ignore[attr-defined]
                    model=model,
                    messages=[
                        {"role": "system", "content": "You will return ONLY strict JSON with the requested schema. No prose."},
                        {"role": "user", "content": composed_prompt},
                        {"role": "user", "content": filtered_html[:18000] if filtered_html else ""},
                    ],
                    temperature=0.0,
                    max_tokens=256,
                ).choices[0].message.content.strip()

            # Try to parse JSON strictly; if it fails, attempt to strip code fences or extract a JSON object.
            parsed: Optional[Dict[str, Any]] = None
            raw_content = content
            def _try_parse_json(txt: str) -> Optional[Dict[str, Any]]:
                try:
                    import json as _json
                    val = _json.loads(txt)
                    return val if isinstance(val, dict) else None
                except Exception:
                    return None

            parsed = _try_parse_json(raw_content)
            cleaned = False
            if parsed is None:
                # Remove fenced blocks like ```json ... ``` or ``` ... ```
                m = _re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw_content, flags=_re.IGNORECASE)
                if m:
                    extracted = m.group(1).strip()
                    parsed = _try_parse_json(extracted)
                    if parsed is not None:
                        cleaned = True
                        raw_content = extracted
            if parsed is None:
                # As a last resort, extract substring between the first '{' and the last '}'
                try:
                    start = raw_content.find('{')
                    end = raw_content.rfind('}')
                    if start != -1 and end != -1 and end > start:
                        sub = raw_content[start:end+1]
                        tmp = _try_parse_json(sub)
                        if tmp is not None:
                            parsed = tmp
                            cleaned = True
                            raw_content = sub
                except Exception:
                    pass
            if cleaned:
                log("INFO", "LLM-CLEAN", "stripped fences/extras to parse JSON", component="letLLMMap", extra={"llm": True})
            content_to_save = raw_content
            # Persist raw and parsed responses for analysis
            try:
                if content_to_save:
                    llm_raw_path.write_text(content_to_save, encoding="utf-8")
            except Exception:
                pass
            try:
                if parsed and isinstance(parsed, dict):
                    import json as _json
                    llm_parsed_path.write_text(_json.dumps(parsed, indent=2, ensure_ascii=False), encoding="utf-8")
            except Exception:
                pass
            if parsed and isinstance(parsed, dict):
                # Normalize suggestion
                st = str(parsed.get("selectorType") or parsed.get("type") or "").lower()
                sel = parsed.get("selector") or parsed.get("value") or ""
                alts = parsed.get("alternatives") if isinstance(parsed.get("alternatives"), list) else []
                rat = parsed.get("rationale") or ""
                llm_suggestion = {
                    "selectorType": st,
                    "selector": sel,
                    "alternatives": alts,
                    "rationale": rat,
                    "raw": content_to_save,
                }
                # Build candidate selectors list (normalize + dedup)
                def _norm(v: str) -> str:
                    s = (v or "").strip()
                    if not s:
                        return s
                    low = s.lower()
                    if low.startswith("text:") or low.startswith("css:") or low.startswith("xpath:"):
                        return s
                    if s.startswith("//") or s.startswith("(//"):
                        return f"xpath:{s}"
                    if s.startswith(".") or s.startswith("#") or s.startswith("[") or s.startswith("*") or _re.search(r":nth-|\w+\[", s):
                        return f"css:{s}"
                    if st in ("text", "css", "xpath"):
                        return f"{st}:{s}"
                    return s
                raw_list = []
                if isinstance(sel, str) and sel:
                    raw_list.append(sel)
                if isinstance(alts, list):
                    raw_list.extend([a for a in alts if isinstance(a, str)])
                norm_list = []
                seen = set()
                for v in raw_list:
                    nv = _norm(v)
                    if nv and nv not in seen:
                        seen.add(nv)
                        norm_list.append(nv)
                # Filter out selectors already tried per feedback
                if _fb_tried_set:
                    before = len(norm_list)
                    norm_list = [s for s in norm_list if s not in _fb_tried_set]
                    after = len(norm_list)
                    if before != after:
                        log("DEBUG", "LLM-FILTER", f"removed_dup={before-after}", component="letLLMMap")
                # Create minimal action plans using fill_and_go (click-only)
                for s in norm_list:
                    try:
                        plan = fill_and_go(mapping={}, action_button_selector=s)
                        from dataclasses import asdict as _asdict
                        llm_candidates.append({
                            "selector": s,
                            "plan": _asdict(plan),
                        })
                    except Exception:
                        llm_candidates.append({
                            "selector": s,
                            "plan": {"actions": [{"kind": "click", "selector": s}]},
                        })
            else:
                llm_suggestion = {"raw": content}
            log("INFO", "LLM-RESP", f"ok content_len={len(content)}", component="letLLMMap", extra={"llm": True})
        except Exception as e:
            log("ERROR", "LLM-ERR", f"{type(e).__name__}: {str(e)[:160]}", component="letLLMMap", extra={"llm": True})

    # Build saved paths dict (include LLM response paths if present on disk)
    saved_paths = {
        "default": str(default_path),
        "composed": str(composed_path),
        "feedback": str(feedback_path) if fb else None,
        "filtered": str(filtered_path) if filtered_html else None,
        "meta": str(meta_path),
        "dir": str(prompts_dir),
    }
    try:
        if llm_raw_path.exists():
            saved_paths["llm_raw"] = str(llm_raw_path)
    except Exception:
        pass
    try:
        if llm_parsed_path.exists():
            saved_paths["llm_parsed"] = str(llm_parsed_path)
    except Exception:
        pass

    # Log number of LLM candidates if any
    try:
        if llm_candidates:
            log("INFO", "LLM-CANDS", f"n={len(llm_candidates)}", component="letLLMMap")
    except Exception:
        pass

    result: Dict[str, Any] = {
        "ok": True,
        "planLetLLMMap": {
            "attempt": attempt,
            "maxAttempts": max_attempts,
            "prompt": composed_prompt,
            "filteredHtml": filtered_html,
            "hints": {"variants": variants, "primary": primary},
            "savedPaths": saved_paths,
        },
    }
    if llm_suggestion is not None:
        result["planLetLLMMap"]["llmSuggestion"] = llm_suggestion  # type: ignore[index]
    if llm_candidates:
        result["planLetLLMMap"]["llmCandidates"] = llm_candidates  # type: ignore[index]
    return result
