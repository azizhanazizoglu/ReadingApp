# TsX Orchestrator and Integration Tests

This document describes the TsX orchestrator, how it maps to TSX_MAIN stateflow, and how to run live integration tests against preview pages.

## Orchestrator Overview
- Entry: `backend/features/tsx_orchestrator.py` → `TsxOrchestrator.run_step(user_command, html, ruhsat_json, prev_html=None)` returns `StepResult { state, details }`.
- Classification: `ClassifyPage.classify(html)` → `PageKind` and `is_final`.
- Branches:
  - Dashboard/Home/Menu → `FindHomePage.run(user_command, html)`
  - User task / Unknown → `MapAndFill.run(html, ruhsat_json, prev_html)`

## Feature: FindHomePage (side-menu checks + bounded retries)
- Components:
  - `Navigator.navigator_open_menu_candidates(html)` produces menu open actions.
  - `Navigator.navigator_go_to_task_candidates(cmd, html)` produces task navigation actions.
  - `DiffService.diff(prev, new)` checks page change.
  - `HtmlCaptureService.persist_html(html, name)` stores snapshots under `memory/TmpData/webbot2html/*`.
  - `ErrorManager.error_tick_and_decide("homeNav")` counts attempts and aborts after threshold.
- Behavior:
  - Tries up to N times (default 3) to find a change while “opening menu → going to task”.
  - If no change: ticks error; if threshold reached, aborts (handover to LLM step if desired by higher-level flow in future).

## Feature: MapAndFill (mapping, validate, fill, diff, final)
- Components:
  - `map_form_fields_llm(html, ruhsat_json)` adapter to `license_llm.pageread_llm.map_json_to_html_fields`.
  - `MappingValidator.validate_mapping_selectors(html, mapping)` adapter to `/api/ts3/analyze-selectors`.
  - `ScriptFiller.generate_and_execute_fill_script(mapping)` bridges to TS3 injection script (dev mode).
  - `DiffService.diff(prev, new)` and `FinalDetector/Finalizer`.
  - `ErrorManager` for bounded mapping retries.
- Result: `MapFillResult(mapping_valid, changed, is_final, attempts)`.

## State Mapping (TSX_MAIN → Implementation)
See `docs/diagrams/TSX_MAIN_GPT.puml` for a function-first mapping view.

## Integration Tests (Live URLs)
- Location: `tests/integration/test_tsx_live_urls.py`
- URLs covered:
  - Dashboard: https://preview--screen-to-data.lovable.app/dashboard → expects state "navigated"
  - Task pages: `traffic-insurance`, `vehicle-details`, `insurance-quote` → expect state "mapped"
- Notes:
  - Tests run only when `RUN_LIVE_TESTS=1` to avoid network in CI by default.
  - LLM mapping and selector analysis are stubbed for determinism.

### Run Live Tests (optional)
Windows PowerShell:
```
$env:RUN_LIVE_TESTS="1"
python -m pytest tests/integration -q
```

## Developer Endpoint
- `POST /api/tsx/dev-run` runs one orchestrator step from FE developer mode.
- Body: `{ user_command?, html?, ruhsat_json?, prev_html? }`
- Returns: `{ state, details }` and logs BE-31xx + component BE-25xx..29xx codes.

## Side-Menu Not Open? LLM Fallback
- Covered via `FindHomePage` retries (ErrorManager: `homeNav`). After attempts, feature aborts.
- Mapping fallback path is handled in `MapAndFill` via LLM mapping retries (`mapping` counter) if classification sees a user task.
- Future enhancement: inject LLM-assisted navigation for home discovery when pure deterministic steps fail.

## Files and Artifacts
- HTML snapshots: `memory/TmpData/webbot2html/*` (written by `HtmlCaptureService` or `/api/test-state-2`).
- Mapping JSON: `memory/TmpData/json2mapping/*` when TS2 endpoint is used; in orchestrator tests, mapping stays in-memory.

## Logs
- Structured logs with codes:
  - `FindHomePage`: BE-2701/2702
  - `MapAndFill`: BE-2801/2802
  - Validator: BE-2501; Classifier: BE-2201..2204; Finalization: BE-2901..2902
  - Dev endpoint: BE-3101..3102

## Troubleshooting
- If live tests fail due to network, run locally or set corporate proxy for requests.
- If OpenAI env vars are missing, it doesn’t affect these tests (LLM is stubbed).
