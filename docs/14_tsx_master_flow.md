# TSX Master Mind: Requirements and Orchestration Flow

This document captures the TsX (Master Mind) feature: what it does, which components it orchestrates (TS1/TS2/TS3, TsW, Ts2L), and a precise, numbered signal flow showing data movement and order of operations. The DOT diagram is not modified in this change.

## Scope and Goals

- Add a new user-facing button “Master (TsX)” that behaves like a conductor: it can trigger TS1, TS2, TS3 sequences like a user would, but with logic and LLM reasoning.
- Default intent: “Yeni Trafik” (traffic insurance). TsX can ask the user for intent; if not provided, it assumes “Yeni Trafik”.
- TsX uses LLM prompts (OpenAI) to analyze the current page HTML captured from the webview and decide where to go next, what to click, and when to fill forms.
- TsX produces and/or consumes mapping JSON (saved to memory and to `memory/TmpData/json2mapping/`). For TsX-first analysis, the file should be named `InTsXHtml.json`.

## Terminology

- TS1: JPEG → LLM → ruhsat_json
- TS2: HTML+JSON → mapping (split into TsW and Ts2L)
  - TsW: Webbot capture (records HTML to memory and artifacts)
  - Ts2L: LLM mapping from HTML + ruhsat_json
- TS3: Fill form and perform actions in the webview
- TsX: Master Mind (this doc) orchestrating the above
- Memory: in-process store with keys like `html`, `mapping`, `ruhsat_json`, `latest_base`
- Artifacts: `memory/TmpData/webbot2html/*` and `memory/TmpData/json2mapping/*`

## Preconditions and Assumptions

- ruhsat_json should exist for TS2/TS3 to work well. If missing, TsX can instruct to run TS1 first or rely on TS2 backend’s jpg2json fallback. Prefer TS1 beforehand for accuracy.
- Browser/webview (Iframe) is loaded; TsW can read HTML from memory/body or, as fallback, by URL.
- LLM provider: OpenAI via existing `license_llm/pageread_llm.py` prompts (extend with TsX prompts as needed).

## UI Trigger and Contract

- UI: Add a new button in “Kullanıcı / UI”: label “Master (TsX)”, symbol “TsX”.
- Backend: Add a new TsX handler endpoint (e.g., `POST /api/tsx/master`) to run the orchestration.
- Request shape (suggested):
  - `intent: string` (optional, default "Yeni Trafik")
  - `html?: string` or `url?: string` (optional; TsX will capture via TsW anyway)
- Success: orchestration reaches a stable state (e.g., PDF produced or main page ready); returns a status log and last known artifacts.

## Components Reference (invoked by TsX)

- TsW: `webbot/test_webbot_html_mapping.py::readWebPage` (+ optional `webbot/selenium_fetcher.py`)
- Ts2L: `license_llm/pageread_llm.py::map_json_to_html_fields`
- TS2 Endpoint: `backend/app.py` or `backend/routes.py` `/api/test-state-2` (triggers TsW→Ts2L via AND gate)
- TS3 Endpoint: `backend/routes.py` `/api/ts3/generate-script` (in-page filler/actions)
- Memory and artifacts writer: `backend/app.py` (writes `webbot2html/page.html`, optional `form.html`, `page.json`, `form_meta.json`; writes `json2mapping/<base>_mapping.json`)

## Numbered Signals (order of operations)

Notation: [S#] Source → Target: action — data (inputs) ⇒ results (outputs)

1. [S1] User → TsX: click Master (TsX) — intent (optional) ⇒ start TsX session
2. [S2] TsX → FS: cleanup — delete `json2mapping/InTsXHtml.json` if exists; clear `webbot2html/*` ⇒ clean slate
3. [S3] TsX → TsW: capture current page — html/url (from webview or memory) ⇒ memory.html; artifacts `webbot2html/page.html`, `form.html?`, `page.json`, `form_meta.json`
4. [S4] TsX → LLM: analyze HTML for intent — html + intent (default: "Yeni Trafik") + prompts ⇒ decision: target button/route (e.g., “Yeni Trafik”, or fallback “Ana Sayfa”)
5. [S5] TsX → Disk/Memory: write mapping (discovery) — decision ⇒ memory.mapping, `json2mapping/InTsXHtml.json`
6. [S6] TsX → Actions (TS3 recommended): navigate/click — target selector from mapping ⇒ page navigation started
7. [S7] TsX → TsW: recapture page — html after navigation ⇒ memory.html updated; artifacts updated
8. [S8] TsX → Classifier (LLM): is this a form page? — new html + prompts (reuse TS2-style cues) ⇒ boolean + rationale
9. [S9] TsX → TS2: if form page then produce full mapping — memory.html + ruhsat_json ⇒ memory.mapping; `json2mapping/<base>_mapping.json`
10. [S10] TsX → Check: if TS2 produced mapping with origin=TsX or flag — skip TsX-LLM next cycle for efficiency
11. [S11] TsX → TsW: snapshot pristine pre-fill HTML — current page html ⇒ memory.prev_html (do not overwrite main snapshot)
12. [S12] TsX → TS3: fill and act — mapping + ruhsat_json + context ⇒ DOM filled, clicks executed
13. [S13] TsX → TsW: capture post-fill HTML — html ⇒ memory.post_html; artifacts updated
14. [S14] TsX → Diff: compare HTML (ignore form fields) — prev_html vs post_html ⇒ page_changed? (significant nav or state change)
15. [S15] TsX → Loop: if changed and not final — goto [S9] (TS2) then [S12] (TS3)
16. [S16] TsX → Detector: PDF ready? — html/URL/state ⇒ if produced, finish flow
17. [S17] TsX → TS3: navigate back to main page — actions/mapping for “Ana Sayfa” ⇒ ready state
18. [S18] TsX → TsW: final capture — html ⇒ memory.html updated; artifacts updated; idle

Tips:
- If `ruhsat_json` is missing, insert “TS1 run” as [S0] (optional) to produce it from the latest JPEG (`jpg2json` fallback also exists in backend TS2).
- When [S9] runs, it’s the same TS2 handler: TS2 → Gate → TsW → Ts2L; TsX waits until mapping is saved (memory + `json2mapping`).

## LLM Prompts Outline for TsX

- Intent extraction: if no user intent provided, assume “Yeni Trafik”.
- Discovery prompt: given full page HTML, find candidates for buttons/links for “Yeni Trafik” (Turkish synonyms allowed) or fallback “Ana Sayfa”. Return a compact JSON with target selector(s) and confidence.
- Form page classifier: given HTML, decide whether this is a fillable form page (use signals similar to TS2 prompts: presence of <form>, inputs/selects/textareas/buttons counts, labels, etc.).
- Diff prompt (if needed): describe non-form structural changes between prev and post html to determine navigation events.

## Data Artifacts and Naming

- HTML snapshots: `memory/TmpData/webbot2html/page.html` (always), `form.html?`, `page.json`, `form_meta.json`
- Mapping by TsX discovery: `memory/TmpData/json2mapping/InTsXHtml.json`
- Full mapping by TS2: `memory/TmpData/json2mapping/<base>_mapping.json`
- Memory keys used by TsX: `html`, `prev_html`, `post_html`, `mapping`, `ruhsat_json`, `latest_base`

## Error Handling and Edge Cases

- No “Yeni Trafik” found: search for “Ana Sayfa”; if still none, surface a helpful error with a snippet of the page.
- HTML missing/empty: retry TsW with URL fallback; if network error, return actionable message.
- ruhsat_json missing: run TS1 or load latest from `jpg2json/` (backend TS2 already tries this).
- TS2 parse failure (mapping JSON): fallback to minimal mapping (empty field_mapping/actions) and keep going; ask user to retry.
- Infinite loops: cap iteration count for [S9]-[S15] cycle; log decisions and exits.

## Observability

- Reuse backend logging utilities (codes like BE-3001*, BE-3002, etc.).
- For TsX steps, add step IDs matching [S#] in logs, so UI can present a clear timeline.

## Minimal API Sketch (optional)

- `POST /api/tsx/master`
  - body: `{ intent?: string }`
  - returns: `{ status: "ok", steps: Array<{id:string, ok:boolean, msg?:string}>, artifacts?: {...} }`

## Implementation Notes

- Keep TsX orchestration stateless between runs as much as possible; use memory only for the current session snapshots and diffing.
- Clicking/navigation should be performed via TS3 (consistent with current architecture). TsW records before/after HTML.
- Do not modify DOT in this change; integrate TsX visually later once the spec stabilizes.

---

If you want, I can add a compact legend and step-numbered overlay to the diagram afterwards; for now, this Markdown acts as the single source of truth for TsX behavior.