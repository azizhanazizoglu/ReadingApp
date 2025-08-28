# TS4 Orchestration (TS2 → TS3 → Next)

## Overview
TS4, frontend tarafında TS2 (LLM-only mapping) tamamlandıktan sonra TS3 (deterministic form fill) adımını arka arkaya tetikleyen hafif bir orkestratördür. Amaç, bir sayfayı doldurup sonraki adıma geçişi stabilize etmektir.

## Inputs
- Latest TS2 mapping: GET `/api/mapping`
- Latest TS1 JSON: GET `/api/state` → `ruhsat_json`
- Raw response (optional): Extracted from state for resolver heuristics (client-only; LLM yok)

## Behavior
- Uses Electron in-app webview only (no external Chrome).
- TS3 executes via backend-generated injection script by default (`/api/ts3/generate-script`) with options:
  - `highlight` (default: true)
  - `simulateTyping` (default: true)
  - `stepDelayMs` (default: 0)
  - `commitEnter` (default: true) — ensures persistence on controlled/masked inputs
- If `page_kind = final_activation` and `is_final_page = true`, `actions` array is executed (e.g., `click#Poliçeyi Aktifleştir`).

## Output
- Visual: fields highlighted as they are filled; logs streamed in Developer Mode (`IDX-TS3-*`).
- No new artifacts; relies on `json2mapping` and `webbot2html` from TS2.

## Developer Notes
- Frontend modules: `ts4Service.ts` orchestrates TS2→TS3. TS3 split services: resolver, plan client, script client, in-page filler, action runner.
- Backend helpers (testable): `webbot/webbot_filler.py` provides planning, selector analysis, and script generation.
- Logging: Use `IDX-TS2-*`, `IDX-TS3-*`, `BE-3xxx/4xxx` codes to trace.

## Edge Cases
- Empty values from TS1: TS3 can fall back to mapping sample values or optional dummy values (dev mode).
- Controlled inputs: rely on `commitEnter` and `blur` to persist.
- Final page with no fields: mapping may have empty `field_mapping`; run `actions` only.
