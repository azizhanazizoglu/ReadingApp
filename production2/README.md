# Production2 Architecture: FindHomePage + F1 Button

This README documents what we built in production2: the architecture, naming, components, and StateFlows (SFs) for FindHomePage and the F1 button. It also defines the FE/BE contracts and tunables.

## quick map

- Frontend (React + Electron)
  - StateFlow orchestrator: `react_ui/src/stateflows/findHomePageSF.ts`
  - Webview helpers: `react_ui/src/services/webviewDom.ts`
  - Behavior: capture → plan → click → wait → detect → LLM fallback
- Backend (FastAPI)
  - Entrypoint & routing: `backend/app.py`, `backend/routes.py`
  - Feature: `backend/Features/findHomePage.py`
  - Components:
    - `backend/Components/getHtml.py` (HTML filtering & snapshot saving)
    - `backend/Components/fillPageFromMapping.py` (plan builder)
    - `backend/Components/letLLMMap.py` (LLM prompt/parse + candidate plans)
    - `backend/logging_utils.py` (structured logs)
- Config & Artifacts
  - Config knobs: `production2/config.json`
  - Artifacts: `production2/tmp/prompts/findHomePage/`

Note: All paths above are relative to `production2/`.

## naming and conventions

- Feature (F): A backend capability exposed via one or more stateless ops. Here: FindHomePage.
- Component (C): A reusable backend building block used by features.
- Service (S): Runtime helpers (e.g., logging).
- StateFlow (SF): A frontend orchestrator that sequences plan → execute → detect.
- F1: Shorthand label for FindHomePage ops and logs.

Core types used in FE:
- PlanAction: `{ kind: 'click' | 'set_value' | 'select_option', selector?: string, value?: any }`
- PlanItem: `{ selector: string, plan: { actions: PlanAction[], meta?: any } }`

## architecture overview

- Backend is stateless:
  - Accepts raw HTML. Filters internally for planning and detection.
  - Static mapping returns ordered PlanItems; LLM path generates additional PlanItems.
  - Detection is a dedicated op comparing prev/current HTML (hash + structure hints).
- Frontend is a simple orchestrator:
  - Captures raw HTML from the Electron webview.
  - Calls backend ops explicitly.
  - Executes plans (navigation uses only click steps).
  - Waits for webview events or timeout, then calls detection.
- Observability-first:
  - FE & BE emit structured logs.
  - Prompts/HTML/LLM I/O saved to disk for debugging and reproducibility.

## backend ops (F1)

All ops are multiplexed through a single endpoint with an `op` selector (see `backend/routes.py`).

- op=allPlanHomePageCandidates
  - Input: `{ html: string, name?: string }`
  - Behavior: filter HTML → static mapping → ordered PlanItems.
  - Output:
    - `ok: boolean`
    - `allPlanHomePageCandidates?: PlanItem[]`
    - `createCandidates?: { selectorsInOrder: string[], mapping: any }`

- op=planCheckHtmlIfChanged
  - Input: `{ prev_html: string, current_html: string, name?: string }`
  - Behavior: filters internally, compares prev/current (hash-based + small structural heuristics).
  - Output:
    - `ok: boolean`
    - `checkHtmlIfChanged?: { changed: boolean, reason?: string, before_hash?: string, after_hash?: string }`

- op=planLetLLMMap
  - Input: `{ html: string, llm_feedback?: string, llm_attempt_index?: number, name?: string }`
  - Behavior:
    - Compose prompt from `config.json` and feedback. Save prompts/meta/filtered HTML.
    - Call OpenAI if `OPENAI_API_KEY` is available (model from `LLM_MODEL` or `gpt-4o`).
    - Parse strict JSON. Handles fenced code blocks and best-effort JSON extraction.
    - Normalize selectors (prefix text:/css:/xpath:). Build minimal click-only plans via `fill_and_go`.
    - Save cleaned raw and parsed JSON for analysis.
  - Output:
    - `ok: boolean`
    - `planLetLLMMap?: { attempt, maxAttempts, prompt, filteredHtml, hints, savedPaths, llmCandidates?: PlanItem[], llmSuggestion?: {...} }`

## backend components

- getHtml.py
  - `filter_Html(raw_html)` returns a compact subset preserving interactive elements, visible text, and selected data-* attributes (e.g., data-component-name, data-component-content).
  - Snapshot saving helpers for observability.

- fillPageFromMapping.py
  - `fill_and_go(mapping, action_button_selector)` returns a minimal Plan with a click on the provided selector.

- letLLMMap.py
  - Prompt composition from `config.json` + optional feedback.
  - LLM call (lazy import; supports new and legacy OpenAI clients).
  - JSON parsing with fence stripping and substring fallback.
  - Selector normalization and de-dup.
  - Produces `llmCandidates` (PlanItems) and a `llmSuggestion` object (primary + alternatives).
  - Saves artifacts under `tmp/prompts/findHomePage/`:
    - default/composed/feedback/filtered/meta
    - llm_response_attemptN.txt (cleaned raw response)
    - llm_parsed_attemptN.json (parsed JSON)

- logging_utils.py
  - Emits structured logs with component tags (e.g., LLM-SAVED, LLM-CLEAN, LLM-RESP, LLM-CANDS, F1-MAP, F1-DET).

## frontend stateflow (findHomePageSF)

File: `react_ui/src/stateflows/findHomePageSF.ts`

Steps:
1) Capture raw HTML from webview (and current URL for context).
2) Call `allPlanHomePageCandidates`; iterate ordered plans:
   - Execute only click actions for navigation.
   - Wait for webview navigation events or timeout.
   - Call `planCheckHtmlIfChanged(prev_html, current_html)`.
   - If changed, return success with `{ index, selector }`.
3) If static candidates don’t change the page, enter LLM fallback:
   - Multi-attempt loop (default: 3 attempts; from `config.json`).
   - Cumulative feedback includes all selectors already tried to avoid repeats.
   - Try `llmCandidates` (already PlanItems) first, then `llmSuggestion` (primary + alternatives).
   - On success, return `{ index: -1, selector }` to denote LLM-origin.

Selector normalization:
- Prevent `text:xpath://...` mistakes.
- Infer `xpath:` for `//...` and `css:` for common CSS patterns when missing.

Logging highlights:
- Static iteration: total, per-plan selector, click result, wait result, detection.
- LLM: attempt counter, savedPaths (prompt, filtered HTML, raw/parsed LLM JSON), candidate order `i:selector`, per-candidate outcomes.

## config and tuning

File: `production2/config.json`

- `findHomePage.letLLMMap_findHomePage.defaultPrompt`
  - TR/EN synonyms and trap guidance.
  - Strict JSON output schema.
  - Requests up to 10 alternatives (aim 8–10) for richer coverage.
- `findHomePage.letLLMMap_findHomePage.maxAttempts`
  - Default 3; increase for more LLM rounds with feedback (cost/latency tradeoff).

## contracts (inputs/outputs)

PlanItem (UI executor input):
```ts
{
  selector: string,
  plan: {
    actions: Array<{ kind: 'click'|'set_value'|'select_option', selector?: string, value?: any }>
    meta?: any
  }
}
```

F1Response by op (selected fields):
```ts
// allPlanHomePageCandidates
{ ok: boolean, allPlanHomePageCandidates?: PlanItem[], createCandidates?: { selectorsInOrder: string[], mapping: any } }

// planCheckHtmlIfChanged
{ ok: boolean, checkHtmlIfChanged?: { changed: boolean, reason?: string, before_hash?: string, after_hash?: string } }

// planLetLLMMap
{ ok: boolean, planLetLLMMap?: { attempt: number, maxAttempts: number, prompt: string, filteredHtml: string, hints?: any, savedPaths?: any, llmCandidates?: PlanItem[], llmSuggestion?: any } }
```

## observability

Artifacts: `tmp/prompts/findHomePage/`
- default_prompt_*.txt, composed_prompt_*.txt, feedback_*.txt
- filtered_attempt*.html, meta_attempt*.json
- llm_response_attempt*.txt (cleaned), llm_parsed_attempt*.json

Logs:
- Backend: LLM-SAVED, LLM-CLEAN, LLM-RESP, LLM-CANDS, F1-MAP, F1-DET.
- Frontend: F1 plan/LLM iteration, selectorsInOrder, click/wait/detect traces.

## extending the system

- Expand synonyms/traps: edit `config.json` prompt.
- Increase alternatives per call: update “Provide up to … alternatives” in prompt.
- More attempts: increase `maxAttempts`.
- Additional features: add new Feature ops and wire a new SF following the same plan/execute/detect pattern.

## environment

- `OPENAI_API_KEY` (optional): enables live LLM planning.
- `LLM_MODEL` (optional): defaults to `gpt-4o`.

## try it (high-level)

- Run backend (FastAPI/uvicorn) and the Electron+React app.
- Navigate to a target page and run the FindHomePage flow.
- Watch the FE/BE logs and inspect `tmp/prompts/findHomePage/` for artifacts.
