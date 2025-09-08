from __future__ import annotations

"""Detect web page change utilities.

Compares previous vs current page using:
- hash (sha256 of raw HTML)
- strict string compare (raw HTML)
- optional normalized comparison (collapse whitespace)

Relies on production2/memory.py for last captures when prev/current not provided.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
import hashlib
import sys
from pathlib import Path as _Path


# Ensure project root (production2) is importable
_this = _Path(__file__).resolve()
_root = _this.parents[2]
if str(_root) not in sys.path:
	sys.path.insert(0, str(_root))

from memory import memory  # type: ignore  # noqa: E402


def _sha256(s: str) -> str:
	return hashlib.sha256((s or "").encode("utf-8")).hexdigest()


def _normalize_spaces(s: str) -> str:
	# Collapse redundant whitespace to compare semantically-same HTML markup
	return " ".join((s or "").split())


@dataclass
class PageChangeResult:
	changed: bool
	reason: str
	before_hash: Optional[str] = None
	after_hash: Optional[str] = None
	details: Optional[Dict[str, Any]] = None


def detect_web_page_change(
	current_raw_html: Optional[str] = None,
	prev_raw_html: Optional[str] = None,
	use_normalized_compare: bool = True,
) -> PageChangeResult:
	"""Detect if the page changed using raw HTML.

	Inputs:
	- current_raw_html: the latest raw HTML to evaluate; if None uses memory.raw_html.last
	- prev_raw_html: the previous raw HTML to compare; if None uses memory.raw_html.history[-2]
	- use_normalized_compare: also compare whitespace-collapsed versions to reduce noise

	Output:
	- PageChangeResult with changed flag and hashes, plus reason.
	"""
	# Default to memory stores when not provided
	if current_raw_html is None:
		current_raw_html = memory.raw_html.get_last_html()
	if prev_raw_html is None:
		hist = memory.raw_html.get_history()
		if len(hist) >= 2:
			prev_raw_html = hist[-2]["html"]
		elif len(hist) == 1:
			prev_raw_html = hist[0]["html"]
		else:
			prev_raw_html = None

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

	# Hash same; try direct string compare
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

