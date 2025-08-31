# TSX Modular Architecture: Logic Gates, Dead-Loop Guards, and Reusable Blocks

This document translates the TSX state machine into logic gates and small, testable components. It highlights dead points/loops and proposes minimal interfaces so we can compose solutions for different websites (e.g., Yeni Trafik, Sağlık, vb.).

## 1) Logic-Gate View (Signals and Guards)

- G0 Start: Btn.TSX && TS1.ready → enter TsX
- G1 Capture Trigger: (UI.Webview.ready || urlProvided) → TsW.capture
- G2 Ts2L Trigger (AND-gate): TsW.html_ready && RuhsatJSON.ready → Ts2L.map
- G3 Navigate Home: (SideMenu.visible || Click(Hamburger)) AND TargetExists(“Home”|“Ana Sayfa”) → Action(Home)
- G4 Navigate UserTask: (SideMenu.open || Home.page) AND TargetExists(UserTask) → Action(UserTask)
- G5 Fill Loop (AND-join): Mapping.valid AND (Page.notFinal) → TS3.fill
- G6 Change-Detection: After(TS3.fill) AND (Diff(prevHtml, postHtml) || Retry.count < K) → Continue | Retry
- G7 Escalation to LLM: (Mapping.invalid OR Page.unchanged) AND (Retry.count in [1..N]) → Ts2L.variant
- G8 Final Page: Classify(Page).isFinal OR Has(Action("Poliçeyi Aktifleştir")) → Action(Final)
- G9 Abort: Any(Error) AND (Counter ≥ Max) → TsXErrorManager.stop

Counters: `retryMapping`, `retryNavigateHome`, `retryNavigateTask`, `retryFill`, `pageHops ≤ 5`.

## 2) Dead Points / Dead Loops

- D1 Menu not detected, URL doesn’t change: Fix with deterministic Hamburger click first, then LLM discovery. Cap attempts (e.g., 3), else abort with evidence.
- D2 Mapping invalid loop: Add `ts3/analyze-selectors` gate (must have ≥X valid selectors) before Fill. After N variants → abort.
- D3 Page unchanged after Fill: Use HTML diff metrics (len/hash/“key markers”); after M retries → re-capture and re-map; after N→ abort.
- D4 Infinite navigation: cap page hops (≤5) and require either FinalPage or at least one field filled across hops; else abort.
- D5 Final action missing: require either LLM final classification OR explicit presence of known labels ("Poliçeyi Aktifleştir"). If neither within R retries → abort.

## 3) Page Applicability (Selectors/Heuristics)

Pages (sample URLs and cues):
- Dashboard `/dashboard`: Has Hamburger button and left menu; text includes “Ana Sayfa”, “Üretim”, “Yeni Trafik”.
- User Task 1 `/traffic-insurance`: Has headings “Trafik Sigortası”, “Sigortalı Bilgileri”, button “DEVAM”.
- User Task 2 `/vehicle-details`: Headings “Kayıt Bilgileri”, “Şasi numarası”, buttons “Geri”/“Devam”.
- Final `/insurance-quote`: Text includes “Poliçeyi Aktifleştir” and “Ana Sayfaya Dön”.

Heuristic classifier (no LLM): regex on outerHTML for key tokens above. LLM fallback: ask TS2L to classify and return `{ page_kind, is_final_page, actions }`.

## 4) Small, Testable Components (Interfaces)

- CaptureService (TsW)
  - captureFromWebview(): string → HTML
  - saveArtifacts(html): writes webbot2html/page.html (+form.html, meta)

- MappingService (Ts2L)
  - map(html, ruhsat_json, mode='standard'|'variant'): MappingJSON
  - validate(mapping, html): { validCount, errors }

- ActionService (TS3)
  - buildAndExecute(mapping, options): { ok, filled[] }

- PageClassifier
  - classify(html): { page_kind: 'dashboard'|'user_task'|'final'|..., is_final_page: boolean, evidence: [] }

- Navigator
  - nextFor(kind, userCommand): MappingJSONWithActions (e.g., click Side Menu → Yeni Trafik)

- DiffService
  - changed(prev, post): { changed: boolean, score: number, markers: [] }

- PdfDetector
  - detect(html): { is_final: boolean, actionSelector?: string }

- ErrorManager
  - tick(key): number; reset(key)

Each component is mockable and has a single responsibility.

## 5) Data Contracts (minimal)

- MappingJSON (from Ts2L):
```json
{
  "field_mapping": { "plaka_no": "input[name=plate]", "dogum_tarihi": "#dob" },
  "actions": [ { "type": "click", "selector": "button:contains('DEVAM')" } ],
  "page_kind": "traffic_insurance|vehicle_details|final",
  "is_final_page": false,
  "final_reason": "",
  "evidence": ["h1:Trafik Sigortası"]
}
```

- ClassifyResult: `{ page_kind, is_final_page, evidence, actions? }`
- DiffResult: `{ changed: boolean, score: number }`

## 6) Wiring to Existing Code (reuse-first)

- TsW capture and artifacts → POST `/api/test-state-2` with `{ html }` (already saves to `memory/TmpData/webbot2html/` and sets `memory['html']`).
- Ts2L mapping → `license_llm.pageread_llm.map_json_to_html_fields(html, ruhsat_json)` (already used in `/api/test-state-2`).
- Mapping validation → POST `/api/ts3/analyze-selectors`.
- Fill → POST `/api/ts3/generate-script` + execute via React webview (see `react_ui/src/services/ts3ScriptClient.ts`).
- Counters/logs → `backend.logging_utils.log_backend`, `backend.memory_store.memory`.

## 7) Minimal Additions (low-risk)

- Frontend
  - add captureOuterHTML(): gets webview DOM and POSTs `/api/test-state-2`.
  - add simpleDiff(prev, post): length/hash diff + key-marker presence.
  - add counters in UI state; display in Dev panel.

- Backend
  - optional `/api/tsx/classify-page` (regex heuristic; LLM fallback): returns `{ page_kind, is_final_page, evidence }`.
  - optional `/api/tsx/diff` if we want server-side diff.

## 8) Modularity for Other Sites

- Only `PageClassifier` and `Navigator.nextFor` need site-specific rules.
- Keep Ts2L prompt site-agnostic; it reads HTML + ruhsat_json and emits mapping/actions.
- Define a small plugin file per site: provides token regexes and preferred action labels.

## 9) Testing

- Unit: mock HTMLs of 4 pages; assert classifier, diff, pdf detector.
- Integration: TS2 mapping validation via `/api/ts3/analyze-selectors`.
- E2E (smoke): capture → map → fill one field; assert diff.changed.

---

This architecture keeps TS3 execution in the webview (as required), reuses existing endpoints, and limits new code to small, easily swappable blocks. It avoids dead loops via explicit counters and gates, enabling reuse across different user tasks and websites.
