import json
import os
from typing import List

recorded_paths: List[str] = []


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    if not recorded_paths:
        return
    latest = recorded_paths[-1]
    terminalreporter.write_sep("-", "Smoke Mapping Output")
    terminalreporter.write_line(f"Latest mapping file: {latest}")
    try:
        with open(latest, encoding="utf-8") as f:
            data = json.load(f)
        fm = data.get("field_mapping", {})
        actions = data.get("actions", [])
        keys = ", ".join(sorted(fm.keys()))
        terminalreporter.write_line(f"Fields: {keys}")
        terminalreporter.write_line(f"Actions: {actions}")
        terminalreporter.write_line("Full JSON:")
        terminalreporter.write_line(json.dumps(data, ensure_ascii=False, indent=2))
    except Exception as e:
        terminalreporter.write_line(f"(Could not read mapping: {e})")


def pytest_sessionfinish(session, exitstatus):
    # Redundant print at session end to ensure visibility even with -q
    try:
        if not recorded_paths:
            return
        latest = recorded_paths[-1]
        tr = session.config.pluginmanager.get_plugin("terminalreporter")
        if not tr:
            return
        tr.write_sep("-", "Smoke Mapping Output (session)")
        tr.write_line(f"Latest mapping file: {latest}")
        with open(latest, encoding="utf-8") as f:
            data = json.load(f)
        tr.write_line(json.dumps(data, ensure_ascii=False, indent=2))
    except Exception:
        pass
