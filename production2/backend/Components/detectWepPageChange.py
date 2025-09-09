from __future__ import annotations

"""Detect web page change utilities.

Compares previous vs current page using:
- hash (sha256 of raw HTML)
- strict string compare (raw HTML)
- optional normalized comparison (collapse whitespace)

Relies on production2/memory.py for last captures when prev/current not provided.
"""

from typing import Optional, Dict, Any
import hashlib
import sys
from pathlib import Path as _Path


# Ensure project root (production2) is importable
_this = _Path(__file__).resolve()
_root = _this.parents[2]
if str(_root) not in sys.path:
	sys.path.insert(0, str(_root))

from memory import PageChangeResult, PageChangeRequest  # type: ignore  # noqa: E402


def _sha256(s: str) -> str:
	return hashlib.sha256((s or "").encode("utf-8")).hexdigest()


def _normalize_spaces(s: str) -> str:
	# Collapse redundant whitespace to compare semantically-same HTML markup
	return " ".join((s or "").split())


def detect_web_page_change(
	current_raw_html: Optional[str] = None,
	prev_raw_html: Optional[str] = None,
	use_normalized_compare: bool = True,
) -> PageChangeResult:
	"""Detect if the page changed using raw HTML (stateless).

	Provide current_raw_html and prev_raw_html explicitly. No global memory fallback.
	Returns a PageChangeResult dataclass defined in memory.py.
	"""
	if current_raw_html is None or prev_raw_html is None:
		return PageChangeResult(
			changed=False,
			reason="insufficient_data",
			details={
				"have_current": current_raw_html is not None,
				"have_prev": prev_raw_html is not None,
			},
		)

	before_hash = _sha256(prev_raw_html)
	after_hash = _sha256(current_raw_html)

	if before_hash != after_hash:
		return PageChangeResult(
			changed=True,
			reason="hash_changed",
			before_hash=before_hash,
			after_hash=after_hash,
		)

	if current_raw_html != prev_raw_html:
		return PageChangeResult(
			changed=True,
			reason="raw_string_changed",
			before_hash=before_hash,
			after_hash=after_hash,
		)

	if use_normalized_compare:
		if _normalize_spaces(current_raw_html) != _normalize_spaces(prev_raw_html):
			return PageChangeResult(
				changed=True,
				reason="normalized_changed",
				before_hash=before_hash,
				after_hash=after_hash,
			)

	return PageChangeResult(
		changed=False,
		reason="no_change",
		before_hash=before_hash,
		after_hash=after_hash,
	)


def detect_web_page_change_req(req: PageChangeRequest) -> PageChangeResult:
	"""Request-object wrapper using dataclasses from memory.py."""
	return detect_web_page_change(
		current_raw_html=req.current_html,
		prev_raw_html=req.prev_html,
		use_normalized_compare=req.normalize_whitespace,
	)

