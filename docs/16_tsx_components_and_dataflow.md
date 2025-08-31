# TSX Components and Data Flow (Production-ready, Reusable)

This doc lists small, swappable components that align with the refined TSX state machine. Names match the diagram to maximize reuse (like Simulink Subsystem References).

## Components (stable contracts)

1) CaptureService (TsW)
- Purpose: read outerHTML from webview and persist artifacts
- API:
  - captureFromWebview(): Promise<string>
  - persist(html: string): Promise<{ htmlPath: string }>
- Reuses: backend POST `/api/test-state-2` (already writes `webbot2html/*` and sets `memory.html`)

2) MappingService (Ts2L)
- Purpose: produce mapping + actions from HTML + ruhsat_json
- API:
  - map(html: string, ruhsat: object, mode?: 'standard'|'variant'): Promise<MappingJSON>
  - validate(mapping: MappingJSON, html: string): Promise<{ validCount: number; errors: string[] }>
- Reuses: `license_llm.pageread_llm.map_json_to_html_fields` and backend `/api/ts3/analyze-selectors`

3) ActionService (TS3)
- Purpose: execute mapping (fields+actions) inside webview
- API:
  - execute(mapping: MappingJSON, ruhsat: object, options?): Promise<{ ok: boolean; filled: string[] }>
- Reuses: backend `/api/ts3/generate-script` + React webview execution

4) PageClassifier
- Purpose: determine page_kind and final status
- API:
  - classify(html: string): { page_kind: string; is_final_page: boolean; evidence: string[] }
- Impl: regex markers (site plugin) with optional LLM fallback (use MappingService.map schema if present)

5) Navigator
- Purpose: generate actions to reach targets (menu open, task pages)
- API:
  - nextFor(kind: 'dashboard'|'home'|'menu'|'user_task'|..., userCommand: string): MappingJSONWithActions
- Impl: site plugin (label synonyms/selectors). Executed via ActionService.

6) DiffService
- Purpose: decide if page changed after actions
- API:
  - changed(prev: string, post: string): { changed: boolean; score: number; markers: string[] }
- Impl: fast heuristics (len/hash; presence of new headings/buttons)

7) PdfDetector
- Purpose: detect final page/action
- API:
  - detect(html: string): { is_final: boolean; actionSelector?: string }
- Impl: regex markers + Navigator-provided action labels

8) ErrorManager
- Purpose: counters, gating, and backoff
- API:
  - tick(key: string): number
  - reset(key: string): void
- Reuses: backend memory/logs; or maintain in FE state and send summaries

## Data Contracts

- MappingJSON
```json
{
  "field_mapping": {"plaka_no": "input[name=plate]"},
  "actions": [{"type": "click", "selector": "button:contains('DEVAM')"}],
  "page_kind": "traffic_insurance",
  "is_final_page": false,
  "final_reason": "",
  "evidence": ["h1:Trafik Sigortası"]
}
```

- ClassifyResult: `{ page_kind, is_final_page, evidence }`
- DiffResult: `{ changed, score }`

## Data Flow (happy path)

1) captureFromWebview → persist → memory.html + artifacts
2) classify(html) → (dashboard/menu/home/user_task/final)
3) if dashboard/menu → Navigator.nextFor → ActionService.execute → recapture → loop
4) if user_task → MappingService.map → validate → ActionService.execute → recapture → DiffService.changed → loop until final
5) if final → PdfDetector.detect → ActionService.execute(final action) → done

## Reuse across sites

- Keep MappingService and ActionService generic.
- Provide site plugins for PageClassifier and Navigator only.
- Unit-test with stored HTML fixtures per site.

## Where current code fits

- Capture + persist: POST `/api/test-state-2` (already implemented)
- Map: `pageread_llm.map_json_to_html_fields` (already implemented)
- Validate: `/api/ts3/analyze-selectors` (already implemented)
- Execute: `/api/ts3/generate-script` + webview (already implemented)

This splits concerns cleanly, allows component reuse, and gives you replaceable “subsystem references” for different websites without touching core logic.
