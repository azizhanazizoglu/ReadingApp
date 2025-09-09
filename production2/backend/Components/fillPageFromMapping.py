from __future__ import annotations

"""Map-and-fill component (ts3-style action executor).

Given a mapping of selectors -> values and an action spec (e.g., click a submit
button), this component decides target elements and returns an action plan the
frontend (or another executor) can apply.

We keep it UI-agnostic here: produce a simple list of actions. The actual
execution (via webview/electron) will be done on the UI side.
"""

from typing import Any, Dict, List, Optional, Literal
import sys
from pathlib import Path as _Path

# Ensure production2 is importable for shared dataclasses
_this = _Path(__file__).resolve()
_root = _this.parents[2]
if str(_root) not in sys.path:
	sys.path.insert(0, str(_root))

from memory import FillAction, FillPlan  # type: ignore


def fill_and_go(
	mapping: Dict[str, Any],
	action_button_selector: Optional[str] = None,
) -> FillPlan:
	"""Create a plan of actions to fill a page and optionally click a button.

	Contract:
	- Inputs:
	  - mapping: { css/xpath/aria selector -> value }
	  - action_button_selector: selector to click (e.g., submit / next)
	- Output:
	  - FillPlan with ordered actions to execute on the UI side

	Notes:
	- We do not execute actions here; only return a plan for the caller.
	- Selectors are opaque strings; the UI/executor decides how to interpret.
	"""
	actions: List[FillAction] = []

	# Dynamically decide based on provided mapping and optional click
	for sel, val in mapping.items():
		if val is None:
			# Skip empty values
			continue
		# Heuristic: if selector hints select/option, use select_option
		low = sel.lower()
		if any(tok in low for tok in ["select#", "[role=combobox]", " option:"]):
			actions.append(FillAction(kind="select_option", selector=sel, option=str(val)))
		else:
			actions.append(FillAction(kind="set_value", selector=sel, value=str(val)))

	if action_button_selector:
		actions.append(FillAction(kind="click", selector=action_button_selector))

	summary = f"{len(actions)} action(s): " + ", ".join(a.kind for a in actions)
	return FillPlan(actions=actions, meta={"summary": summary})


