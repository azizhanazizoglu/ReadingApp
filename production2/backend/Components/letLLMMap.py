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

            parsed: Optional[Dict[str, Any]] = None
            try:
                import json as _json
                parsed = _json.loads(content)
            except Exception:
                parsed = None
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
                    "raw": content,
                }
            else:
                llm_suggestion = {"raw": content}
            log("INFO", "LLM-RESP", f"ok content_len={len(content)}", component="letLLMMap", extra={"llm": True})
        except Exception as e:
            log("ERROR", "LLM-ERR", f"{type(e).__name__}: {str(e)[:160]}", component="letLLMMap", extra={"llm": True})

    result: Dict[str, Any] = {
        "ok": True,
        "planLetLLMMap": {
            "attempt": attempt,
            "maxAttempts": max_attempts,
            "prompt": composed_prompt,
            "filteredHtml": filtered_html,
            "hints": {"variants": variants, "primary": primary},
            "savedPaths": {
                "default": str(default_path),
                "composed": str(composed_path),
                "feedback": str(feedback_path) if fb else None,
                "filtered": str(filtered_path) if filtered_html else None,
                "meta": str(meta_path),
                "dir": str(prompts_dir),
            },
        },
    }
    if llm_suggestion is not None:
        result["planLetLLMMap"]["llmSuggestion"] = llm_suggestion  # type: ignore[index]
    return result
