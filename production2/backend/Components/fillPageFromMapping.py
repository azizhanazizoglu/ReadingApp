from __future__ import annotations

"""Map-and-fill component (ts3-style action executor).

Given a mapping of selectors -> values and an action spec (e.g., click a submit
button), this component decides target elements and returns an action plan the
frontend (or another executor) can apply.

We keep it UI-agnostic here: produce a simple list of actions. The actual
execution (via webview/electron) will be done on the UI side.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Literal


ActionType = Literal["set_value", "select_option", "click"]


@dataclass
class Action:
	type: ActionType
	selector: str
	value: Optional[str] = None
	meta: Optional[Dict[str, Any]] = None


@dataclass
class MapAndFillPlan:
	actions: List[Action]
	summary: str


def map_and_fill(
	mapping: Dict[str, Any],
	action_button_selector: Optional[str] = None,
) -> MapAndFillPlan:
	"""Create a plan of actions to fill a page and optionally click a button.

	Contract:
	- Inputs:
	  - mapping: { css/xpath/aria selector -> value }
	  - action_button_selector: selector to click at the end (e.g., submit)
	- Output:
	  - MapAndFillPlan with ordered actions to execute on the UI side

	Notes:
	- We do not execute actions here; only return a plan for the caller.
	- Selectors are opaque strings; the UI/executor decides how to interpret.
	"""
	actions: List[Action] = []

	for sel, val in mapping.items():
		if val is None:
			# Skip empty values
			continue
		# Heuristic: if selector hints select/option, use select_option
		low = sel.lower()
		if any(tok in low for tok in ["select#", "[role=combobox]", " option:"]):
			actions.append(Action(type="select_option", selector=sel, value=str(val)))
		else:
			actions.append(Action(type="set_value", selector=sel, value=str(val)))

	if action_button_selector:
		actions.append(Action(type="click", selector=action_button_selector))

	summary = f"{len(actions)} action(s): " + ", ".join(a.type for a in actions)
	return MapAndFillPlan(actions=actions, summary=summary)

