from __future__ import annotations

"""LLM fallback mapping for goUserTaskPage feature.

Builds an LLM prompt to identify the button/control that opens a user task page
based on a target task label (e.g. "Yeni Trafik"). Static mapping tries first;
if insufficient or failed, this module assembles a constrained JSON-only prompt
similar to `letLLMMap.def_let_llm_map` but specialized for user task buttons.

Returned shape (success):
{
  ok: True,
  planLetLLMMapUserTask: {
	attempt, maxAttempts,
	prompt, filteredHtml,
	taskLabel,
	hints: { staticSynonyms, triedSelectors },
	savedPaths: { ... },
	llmSuggestion?: {...},
	llmCandidates?: [...]
  }
}

No direct clicking here; higher-level flow (fillPageFromMapping) will consume
the chosen selector.
"""

from typing import Any, Dict, List, Optional
from pathlib import Path as _Path
from datetime import datetime
import shutil
import sys
import os
import re as _re

# Ensure production2 root on path
_this = _Path(__file__).resolve()
_root = _this.parents[2]
if str(_root) not in sys.path:
	sys.path.insert(0, str(_root))

from config import (  # type: ignore
	get_llm_max_attempts_go_user_task,
	get_llm_prompt_go_user_task_default,
)
from backend.logging_utils import log  # type: ignore
from backend.Components.mappingStaticUserTask import get_user_task_candidates  # type: ignore
from backend.Components.fillPageFromMapping import fill_and_go  # type: ignore


def _collect_static_synonyms() -> List[str]:
	syns: List[str] = []
	try:
		for c in get_user_task_candidates():
			for s in c.get("synonyms", []):
				if isinstance(s, str):
					syns.append(s)
	except Exception:
		pass
	# Dedup (case-insensitive)
	out = []
	seen = set()
	for s in syns:
		k = s.strip().lower()
		if k and k not in seen:
			seen.add(k)
			out.append(s)
	return out


def build_llm_prompt_user_task(
	filtered_html: str,
	task_label: str,
	llm_feedback: Optional[str] = None,
	llm_attempt_index: Optional[int] = None,
) -> Dict[str, Any]:
	"""Compose LLM plan for locating user task button.

	Parameters:
	  filtered_html: compact HTML (already filtered outside)
	  task_label: canonical or user-entered label (e.g. "Yeni Trafik")
	  llm_feedback: prior attempt notes (selectors tried, etc.)
	  llm_attempt_index: 0-based attempt counter
	"""
	default_prompt = get_llm_prompt_go_user_task_default()
	attempt = llm_attempt_index if isinstance(llm_attempt_index, int) else 0
	max_attempts = get_llm_max_attempts_go_user_task()

	if attempt >= max_attempts:
		return {
			"ok": False,
			"error": "LLM attempt limit reached",
			"llm": {"attempt": attempt, "maxAttempts": max_attempts},
		}

	static_synonyms = _collect_static_synonyms()
	fb = (llm_feedback or "").strip()

	composed_prompt = (
		f"Target user task label: '{task_label}'\n\n" +
		"If label not exact, use fuzzy / semantic match with synonyms (TR/EN).\n" +
		default_prompt
	)
	if static_synonyms:
		composed_prompt += "\n\nKnown synonyms (case-insensitive):\n- " + "\n- ".join(static_synonyms[:80])
	if fb:
		composed_prompt += "\n\nContext (previous failed attempts / feedback):\n" + fb

	# Feedback tried selectors extraction
	tried_selectors: set[str] = set()
	if fb:
		try:
			for line in fb.splitlines():
				line = line.strip()
				if not line:
					continue
				if 'selector=' in line:
					sel = line.split('selector=', 1)[1].strip()
					if sel:
						tried_selectors.add(sel)
				else:
					m = _re.search(r"\]\s*(.+)$", line)
					if m:
						tried_selectors.add(m.group(1).strip())
		except Exception:
			pass

	# File save structure
	prompts_dir = _root / "tmp" / "prompts" / "goUserTaskPage"
	try:
		if attempt == 0 and prompts_dir.exists():
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
	filtered_path = prompts_dir / f"filtered_attempt{attempt}_{ts}.html"
	feedback_path = prompts_dir / f"feedback_attempt{attempt}_{ts}.txt"
	meta_path = prompts_dir / f"meta_attempt{attempt}_{ts}.json"
	llm_raw_path = prompts_dir / f"llm_response_attempt{attempt}_{ts}.txt"
	llm_parsed_path = prompts_dir / f"llm_parsed_attempt{attempt}_{ts}.json"

	try:
		default_path.write_text(default_prompt, encoding="utf-8")
		composed_path.write_text(composed_prompt, encoding="utf-8")
		if fb:
			feedback_path.write_text(fb, encoding="utf-8")
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
			"taskLabel": task_label,
			"timestamp": ts,
		}
		meta_path.write_text(_json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
	except Exception:
		pass

	log("INFO", "LLM-UTASK-SAVED", f"attempt {attempt+1}/{max_attempts}", component="letLLMMapUserTask")

	# Optional LLM call
	llm_suggestion: Optional[Dict[str, Any]] = None
	llm_candidates: List[Dict[str, Any]] = []
	key = os.getenv("OPENAI_API_KEY")
	model = os.getenv("LLM_MODEL", "gpt-4o")

	if key:
		try:
			from openai import OpenAI  # type: ignore
			client = OpenAI(api_key=key)
			messages = [
				{"role": "system", "content": "Return ONLY strict JSON with required schema. No prose."},
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
			try:
				import openai  # type: ignore
				openai.api_key = key
				content = openai.chat.completions.create(  # type: ignore[attr-defined]
					model=model,
					messages=[
						{"role": "system", "content": "Return ONLY strict JSON with required schema. No prose."},
						{"role": "user", "content": composed_prompt},
						{"role": "user", "content": filtered_html[:18000] if filtered_html else ""},
					],
					temperature=0.0,
					max_tokens=256,
				).choices[0].message.content.strip()
			except Exception as e:  # pragma: no cover
				content = ""
				log("ERROR", "LLM-UTASK-ERR", str(e)[:160], component="letLLMMapUserTask")

		raw_content = content
		parsed: Optional[Dict[str, Any]] = None

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
			m = _re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw_content, flags=_re.IGNORECASE)
			if m:
				extracted = m.group(1).strip()
				parsed = _try_parse_json(extracted)
				if parsed is not None:
					raw_content = extracted
					cleaned = True
		if parsed is None:
			try:
				start = raw_content.find('{')
				end = raw_content.rfind('}')
				if start != -1 and end != -1 and end > start:
					sub = raw_content[start:end+1]
					p2 = _try_parse_json(sub)
					if p2 is not None:
						parsed = p2
						raw_content = sub
						cleaned = True
			except Exception:
				pass
		if parsed and isinstance(parsed, dict):
			st = str(parsed.get("selectorType") or parsed.get("type") or "").lower()
			sel = parsed.get("selector") or parsed.get("value") or ""
			alts = parsed.get("alternatives") if isinstance(parsed.get("alternatives"), list) else []
			rat = parsed.get("rationale") or ""
			llm_suggestion = {
				"selectorType": st,
				"selector": sel,
				"alternatives": alts,
				"rationale": rat,
				"raw": raw_content,
			}

			def _norm(v: str) -> str:
				s = (v or "").strip()
				if not s:
					return s
				low = s.lower()
				if low.startswith(("text:", "css:", "xpath:")):
					return s
				if s.startswith("//") or s.startswith("(//"):
					return f"xpath:{s}"
				if s.startswith(".") or s.startswith("#") or s.startswith("[") or s.startswith("*"):
					return f"css:{s}"
				if st in ("text", "css", "xpath"):
					return f"{st}:{s}"
				return s

			raw_list: List[str] = []
			if isinstance(sel, str) and sel:
				raw_list.append(sel)
			if isinstance(alts, list):
				raw_list.extend([a for a in alts if isinstance(a, str)])
			norm_list: List[str] = []
			seen: set[str] = set()
			for v in raw_list:
				nv = _norm(v)
				if nv and nv not in seen and nv not in tried_selectors:
					seen.add(nv)
					norm_list.append(nv)

			for s in norm_list:
				try:
					plan = fill_and_go(mapping={}, action_button_selector=s)
					from dataclasses import asdict as _asdict
					llm_candidates.append({"selector": s, "plan": _asdict(plan)})
				except Exception:
					llm_candidates.append({"selector": s, "plan": {"actions": [{"kind": "click", "selector": s}]}})
		else:
			llm_suggestion = {"raw": raw_content}

	saved_paths = {
		"default": str(default_path),
		"composed": str(composed_path),
		"filtered": str(filtered_path) if filtered_html else None,
		"feedback": str(feedback_path) if fb else None,
		"meta": str(meta_path),
		"dir": str(prompts_dir),
	}
	try:
		if llm_raw_path.exists():
			saved_paths["llm_raw"] = str(llm_raw_path)
		if llm_parsed_path.exists():
			saved_paths["llm_parsed"] = str(llm_parsed_path)
	except Exception:
		pass

	result: Dict[str, Any] = {
		"ok": True,
		"planLetLLMMapUserTask": {
			"attempt": attempt,
			"maxAttempts": max_attempts,
			"prompt": composed_prompt,
			"filteredHtml": filtered_html,
			"taskLabel": task_label,
			"hints": {"staticSynonyms": static_synonyms, "triedSelectors": list(tried_selectors)},
			"savedPaths": saved_paths,
		},
	}
	if llm_suggestion is not None:
		result["planLetLLMMapUserTask"]["llmSuggestion"] = llm_suggestion  # type: ignore[index]
	if llm_candidates:
		result["planLetLLMMapUserTask"]["llmCandidates"] = llm_candidates  # type: ignore[index]
	return result


if __name__ == "__main__":  # quick manual smoke test
	demo_html = """
	<div>
	  <button><span>Yeni Trafik</span></button>
	  <button aria-label="Yeni Trafik Kaydı"></button>
	</div>
	"""
	out = build_llm_prompt_user_task(demo_html, "Yeni Trafik", llm_feedback=None, llm_attempt_index=0)
	print(json_dump := __import__("json").dumps(out, indent=2, ensure_ascii=False)[:800])
