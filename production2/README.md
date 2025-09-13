# Production2 Architecture: FindHomePage + F1 Button

This README documents what we built in production2: the architecture, naming, components, and StateFlows (SFs) for FindHomePage and the F1 button. It also defines the FE/BE contracts and tunables.

## quick map

- Frontend (React + Electron)
  - StateFlow orchestrator: `react_ui/src/stateflows/findHomePageSF.ts`
  - Webview helpers: `react_ui/src/services/webviewDom.ts`
  - Behavior: capture → plan → click → wait → detect → LLM fallback
- Backend (FastAPI)
  - Entrypoint & routing: `backend/main.py` (REST under `/api/*`)
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

---

# goUserTaskPage + F2 Button

The goUserTaskPage feature navigates to a user-requested task page (e.g., "Yeni Trafik", "Hayat Sigortası"). It follows the same static-first then LLM-fallback approach, with an extra side-menu open step when needed.

## quick map (F2)

- Frontend (React + Electron)
  - StateFlow orchestrator: `react_ui/src/stateflows/goUserTaskPageSF.ts`
  - Trigger: Header F2 button in `react_ui/src/components/Header.tsx`
  - Behavior: capture → plan goUserPage → if no selector: open side menu → wait/detect → loop → optional LLM fallback
- Backend (FastAPI)
  - Feature: `backend/Features/goUserTaskPage.py`
  - Ops exposed under `/api/f2` (multiplexed by `op`)
  - Components:
    - `backend/Components/mappingStaticUserTask.py` (static mapping for user task buttons)
    - `backend/Components/mappingStaticSideMenu.py` (static mapping for hamburger/side menu)
    - `backend/Components/letLLMMapUserTaskPage.py` (LLM prompt/parse + candidate plans)
    - `backend/Components/detectWepPageChange.py` (HTML change detection)
    - `backend/Components/fillPageFromMapping.py` (plan builder)
  - Config helpers: `production2/config.py` (`get_go_user_task_stateflow`, `get_llm_*`)
  - API config passthrough for UI: `/api/config`
- Config & Artifacts
  - Config knobs: `production2/config.json` → `goUserTaskPage`
  - Artifacts: `production2/tmp/prompts/goUserTaskPage/`

## backend ops (F2)

All ops are multiplexed under `/api/f2` via `op`:

- op=openSideMenu
  - Input: `{ html: string }` (filtered HTML is built server-side when needed)
  - Behavior: statically detect hamburger/side menu toggle and return a click plan.
  - Output:
    - `ok: boolean`
    - On success: `{ planType: 'fillPlan', action: 'openSideMenu', mapping: { primary, alternatives?, candidateCount }, plan }`

- op=goUserPage
  - Input: `{ html: string, task_label: string, force_llm?: boolean, llm_feedback?: string, llm_attempt_index?: number }`
  - Behavior:
    - Static-first: match `task_label` against configured candidates (synonyms, selectors). If found, return a click-only plan.
    - Else LLM: return an `llmPrompt` plan with prompt/paths and optional candidate selectors (if API key configured).
  - Output (static success):
    - `{ ok, planType: 'fillPlan', action: 'goUserPage', strategy: 'static', taskLabel, match: { id, score, priority }, selector, plan }`
  - Output (LLM):
    - `{ ok, planType: 'llmPrompt', action: 'goUserPage', strategy: 'llm'|'static+llm', taskLabel, staticMatched: boolean, llmPlan: { attempt, maxAttempts, prompt, filteredHtml, hints, savedPaths, llmSuggestion?, llmCandidates? } }`

- op=checkPageChanged
  - Input: `{ prev_html: string, current_html: string, use_normalized_compare?: boolean }`
  - Output: `{ ok, action: 'checkPageChanged', result: { changed: boolean, reason?: string, before_hash?: string, after_hash?: string } }`

- op=fullFlow (optional helper)
  - Input: `{ html: string, task_label: string, open_menu_first?: boolean, llm_feedback?: string, llm_attempt_index?: number }`
  - Output: `{ ok, flow: { openSideMenu?, goUserPage }, taskLabel }`

## backend components (F2)

- mappingStaticUserTask.py
  - Base candidate(s) for user task buttons (e.g., Yeni Trafik).
  - Extensible via `config.json` under `goUserTaskPage.userTaskButtons`.
  - Functions: `get_user_task_candidates`, `find_best_user_task_button` (diacritics-insensitive scoring using exact/substring/token overlap).

- mappingStaticSideMenu.py
  - Detects hamburger/menu toggle (variants/aria/icon patterns configurable).

- letLLMMapUserTaskPage.py
  - Prompt composition using `config.json` + `config.py` helpers.
  - Saves artifacts under `tmp/prompts/goUserTaskPage/` (default/composed/filtered/meta/feedback + optional raw/parsed LLM outputs).
  - Returns structured `llmPlan` with `llmCandidates` (click plans) and an optional `llmSuggestion` (primary + alternatives).

- detectWepPageChange.py
  - Same detection utility used by F1; compares prev/current raw HTML.

- fillPageFromMapping.py
  - Minimal click-only plan for a given selector; used for both static and LLM candidates.

## frontend stateflow (goUserTaskPageSF)

File: `react_ui/src/stateflows/goUserTaskPageSF.ts`

Loop behavior:
1) Capture raw HTML from webview (and URL for context).
2) Call backend `goUserPage` with the user-entered label.
   - If returned `fillPlan`, click it and wait → recapture → change-detection.
   - If no direct selector and static tries remain, call `openSideMenu` and click the hamburger; wait/recapture.
3) Repeat for up to `maxLoops`, tracking per-type limits:
   - `maxStaticTries` caps static selector attempts.
   - `maxLLMTries` caps LLM prompt attempts (enabled from loop 2+ by default).
4) If LLM plan present (and allowed), consume `llmCandidates` and/or `llmSuggestion` selectors in order, sending feedback (selectors tried) on each attempt.

Click robustness:
- Synthetic pointer/mouse event sequence to improve reliability.
- Side-menu fallbacks: `css:button:has(svg.lucide-menu)` and clicking the closest clickable ancestor of `svg.lucide-menu` when needed.

Header F2 wiring:
- `react_ui/src/components/Header.tsx` binds F2 to run this SF and fetches `/api/config` once to load stateflow defaults.

## config and tuning (F2)

`production2/config.json` (goUserTaskPage):
- `staticMaxCandidates`: cap for static DOM scan (backend-side, where used).
- `mapping.max_alternatives`: number of alternatives when building mapping artifacts.
- `userTaskButtons`: extend/override static candidates:
  - Example entries:
    - `userTask.newTraffic` with synonyms/selectors for "Yeni Trafik".
    - `userTask.lifeInsurance` with synonyms/selectors for "Hayat Sigortası" (diacritics-insensitive matching; also accepts "Hayat Sigortasi").
- `sideMenuToggle`: variants, aria keywords, and icon patterns to detect the hamburger.
- `letLLMMap_goUserTask`:
  - `defaultPrompt`: focused on identifying the user-task button (strict JSON output).
  - `maxAttempts`: cap attempts per run.
- `stateflow` (read by UI via `/api/config`):
  - `maxLoops` (default: 6)
  - `maxStaticTries` (default: 8)
  - `maxLLMTries` (default: 3)
  - `waitAfterClickMs` (default: 800)

`production2/config.py` provides helpers:
- `get_llm_prompt_go_user_task_default()`, `get_llm_max_attempts_go_user_task()`
- `get_go_user_task_stateflow(key)`

## contracts (inputs/outputs)

PlanItem (UI executor input) is the same as F1.

F2Response by op (selected fields):
```ts
// openSideMenu
{ ok: boolean, planType?: 'fillPlan', action?: 'openSideMenu', mapping?: { primary: string, alternatives?: string[], candidateCount: number }, plan?: { actions: any[] } }

// goUserPage (static success)
{ ok: boolean, planType: 'fillPlan', action: 'goUserPage', strategy: 'static', taskLabel: string, match: { id?: string, score?: number, priority?: number }, selector: string, plan: { actions: any[] } }

// goUserPage (LLM plan)
{ ok: boolean, planType: 'llmPrompt', action: 'goUserPage', strategy: 'llm'|'static+llm', taskLabel: string, staticMatched: boolean, llmPlan: { attempt: number, maxAttempts: number, prompt: string, filteredHtml: string, hints: any, savedPaths: any, llmSuggestion?: any, llmCandidates?: Array<{ selector: string, plan: { actions: any[] } }> } }

// checkPageChanged
{ ok: boolean, action: 'checkPageChanged', result: { changed: boolean, reason?: string, before_hash?: string, after_hash?: string } }
```

## observability

Artifacts: `tmp/prompts/goUserTaskPage/`
- default_prompt_*.txt, composed_prompt_attemptN_*.txt, feedback_attemptN_*.txt
- filtered_attemptN_*.html, meta_attemptN_*.json
- llm_response_attemptN_*.txt (cleaned), llm_parsed_attemptN_*.json (if LLM executed)

Logs:
- Backend: LLM-UTASK-SAVED, LLM-UTASK-ERR, and standard feature/component tags.
- Frontend: UTASK loop traces (static/LLM tries, side-menu clicks, detection). 

## try it (F2)

- Enter a task label in the TsX input (e.g., "Yeni Trafik", "Hayat Sigortası").
- Click F2.
- Watch logs: you should see menu open (if closed) and a click on the matched task button; on success, detection logs report `changed=true`.

---

# fillFormsUserTaskPage + F3 Button

The F3 feature ingests ruhsat data (file or Vision LLM), analyzes the current page, fills fields with high reliability, verifies persistence, gates on “enough fields filled,” then runs follow-up actions (e.g., Devam/İleri).

## quick map (F3)

- Frontend (Electron + React)
  - StateFlow orchestrator: `react_ui/src/stateflows/fillFormsUserTaskPageSF.ts`
  - Services: `react_ui/src/services/ts3InPageFiller.ts`, `ts3ActionRunner.ts`, `webviewDom.ts`
    - Per-field sequential fill with retries, Enter + clickOutside + change + blur/focusout commits
    - Selector-level verification (`checkSelectorHasValue`) and `data-ts3-filled` markers
- Backend (FastAPI)
  - Feature: `backend/Features/fillFormsUserTaskPage.py`
  - Components:
    - `backend/Components/letLLMMapUserPageForms.py` (LLM mapping; prefers id/name and unique data-lov-id; Turkish synonyms)
    - `backend/Components/detectFormsAreFilled.py` (committed count via HTML + ts3 markers)
    - `backend/Components/fillPageFromMapping.py` (plan builder for set_value/select_option + optional clicks)
    - `backend/Components/detectWepPageChange.py` (page change check)
  - API: `/api/f3` multiplexed ops

## backend ops (F3)

POST `/api/f3` with `op`:
- `loadRuhsatFromTmp` → auto-ingest ruhsat (from `goFillForms.input.imageDir` or prepared JSON)
- `analyzePage` → returns `{ page_kind: 'fill_form'|'final_activation', field_mapping?, actions? }`
- `buildFillPlan` → mapping + ruhsat_json → ordered FillPlan
- `detectFinalPage` → static CTA detection using configured final labels
- `checkPageChanged` → raw HTML diff (same as F2)
- `detectFormsFilled` → counts committed fields; accepts `min_filled` override

Notes:
- LLM prompt for mapping is centralized: `goFillForms.llm.mappingPrompt` (see config below).
- Analyze results are cached per-HTML on the UI to avoid repeated LLM calls in the same loop.

## frontend stateflow (F3)

File: `react_ui/src/stateflows/fillFormsUserTaskPageSF.ts`
- Fetches `/api/config` once to read timing knobs.
- Sequential per-field fill with up to 3 attempts (configurable backoff).
- After each attempt, selector-level verification; only proceed on success.
- Global HTML-only filled check with a dynamic threshold; only then run actions.
- Prioritizes critical fields like `sasi_no`, `motor_no`, `tescil_tarihi` when present.

## config and tuning (F3)

`production2/config.json` and defaults in `production2/config.py`:
- `goFillForms.llm`:
  - `model` (default `gpt-4o`), `temperature`
  - `mappingPrompt` (centralized LLM prompt for mapping; editable without code changes)
- `goFillForms.stateflow` (consumed by UI):
  - `perFieldAttemptWaits`: e.g., `[250, 400, 600]` ms for 3 attempts
  - `postFillVerifyDelayMs`: extra delay before per-field verify
  - `htmlCheckDelayMs`: delay before global HTML-only check
  - `waitAfterActionMs`: pause after click actions
  - `commitEnter`, `clickOutside`: commit behavior flags
  - `maxLoops`, `maxLLMTries` (where applicable)
- `goFillForms.input.imageDir`: image staging dir used by upload

Backend exposes selected config to UI via `/api/config`.

## upload pipeline

- Endpoint: `POST /api/upload` (JPEG/PNG)
  - Stages into `goFillForms.input.imageDir` (default: `tmp/data`)
  - Emits structured logs; filename returned for inspection

## observability

- Mapping artifacts and normalized outputs are written under `production2/tmp/` (see feature code for exact folders).
- UI/BE logs show per-field attempts, selector verifications, gating decisions, and actions.

## build/run notes

- `production2/build2run.ps1` prefers `production2/electron_app` starter and restores working dir. It mirrors built assets when needed and prints the chosen starter.

## try it (F3)

1) Start backend and the Electron app.
2) Use the F3 flow in UI. Optionally upload a ruhsat image via `/api/upload` beforehand.
3) Watch logs for sequential fill attempts, verification, gating, and final actions.
