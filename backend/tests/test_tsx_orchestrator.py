from backend.features.tsx_orchestrator import TsxOrchestrator


def fake_llm(html: str, ruhsat: dict):
    return {
        "fields": [{"selector": "#plate", "value": ruhsat.get("plate", "") }],
        "actions": [{"selector": "#submit", "description": "final submit"}],
        "page_kind": "user_task",
        "is_final": False,
    }


def fake_analyze(html: str, mapping: dict):
    return {"#plate": 1, "#submit": 1}


def test_tsx_orchestrator_flows(tmp_path):
    orch = TsxOrchestrator(fake_llm, fake_analyze, workspace_tmp=str(tmp_path))
    # Case 1: navigation path (home/menu)
    res1 = orch.run_step("Yeni Trafik", "<html><body>Home</body></html>", {"plate": "06"})
    assert res1.state == "navigated" and res1.details["success"]

    # Case 2: mapping/fill path (user_task) when forced LLM mapping is enabled
    orch.force_llm = True
    res2 = orch.run_step("Yeni Trafik", "<html><input id='plate'/><button id='submit'></button></html>", {"plate": "06"})
    assert res2.state in {"mapped", "mapping_failed"}
