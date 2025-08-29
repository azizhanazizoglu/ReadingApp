# TS3: Form Autofill and Developer Debugging

TS3 fills the current page’s form inside the in-app browser without using any LLM. It runs primarily via a backend-generated injection script executed in the Electron webview (testable), or an in-page filler fallback. It uses the TS2 mapping plus TS1 data.

## What TS3 Does
- Reads latest mapping from GET `/api/mapping` (produced by TS2)
- Reads current state and TS1 data from GET `/api/state`
- Resolves values for mapping keys from TS1 JSON (with synonyms) and, if needed, from raw free text (`rawresponse`) via regex
- Injects a script into the Electron webview to fill inputs, selects, textareas, radios/checkboxes, and dates
- Simulates typing with keydown/keyup for masked/React-controlled inputs and visually highlights touched fields
- Commits values with Enter + blur to ensure persistence across navigation (controlled/masked inputs)
- Optionally clicks mapped actions (e.g., Next/Devam)

## Data Resolution Pipeline
TS3 resolves field values using this order:
1) Deep-flatten TS1 JSON and match by exact key and synonyms
2) Substring key match fallback
3) Raw text extraction if `rawresponse` exists (plate/TC/DOB/name)

Synonyms used (normalized):
- plaka_no: [plaka, plakaNo, plate, plateNo, aracPlaka, vehiclePlate]
- ad_soyad: [adsoyad, isim, ad, soyad, name, fullname]
- tckimlik: [tc, tckimlik, kimlik, kimlikno, tcno, identity, nationalid]
- dogum_tarihi: [dogumtarihi, d_tarihi, dtarihi, birthdate, birth_date, dob]

Normalizations:
- plaka_no → uppercase and single spaces (e.g., 34 ABC 123)
- tckimlik → digits only (11 chars expected)
- dogum_tarihi → accepts dd.mm.yyyy, dd/mm/yyyy, dd-mm-yyyy, normalizes to yyyy-MM-dd when possible

## Element Discovery and Filling
TS3 first tries mapping selectors. If a selector fails, it tries a semantic fallback:
- Scores inputs/selects/textarea by nearby text: label[for], placeholder, aria-label, name, title, and some parent text
- Matches against key and synonyms (normalized)

Supported field handling:
- input[type=text|password|email|tel|...] and textarea: set native value; if "Simulate Typing" is ON, dispatches keydown/keyup and input/change events per character
- input[type=date]: normalizes to yyyy-MM-dd and sets native value
- select: tries by value, then equals text, then includes text
- checkbox/radio: toggles via native "checked" or clicks a matching radio value

## Developer Settings Panel (UI)
Available in Developer Mode in the React UI:
- Highlight filled fields (green outline + fade)
- Simulate Typing (keydown/keyup) for masked/controlled inputs
- Step Delay (ms) between fields

These options are passed to TS3 and affect the injected script. Persistence implemented via Enter commit + blur.

## Logs and Troubleshooting
Frontend (React) emits IDX-TS3-* logs:
- IDX-TS3-START: begins TS3
- IDX-TS3-MAP-KEYS: mapping keys
- IDX-TS3-DATA-KEYS: flattened TS1 keys
- IDX-TS3-RAW-SUMMARY: first chars of rawresponse, if any
- IDX-TS3-EXTRACT: values parsed from rawresponse
- IDX-TS3-RESOLVE: per-field source path and value chosen
- IDX-TS3-FILL: { ok, filled }
- IDX-TS3-DETAILS-N: per-field before/after snapshots and selector info (chunked)
- IDX-TS3-ACTIONS: action click attempts and results

If a field isn’t filled:
- Check IDX-TS3-RESOLVE for N/A or empty value
- Check IDX-TS3-DETAILS for not-found or unsupported type
- Ensure TS2 mapping exists and selector points to an element on current page
- For masked inputs, enable Simulate Typing and increase Step Delay

## Artifacts and Endpoints
- TS3 persists no new artifacts; it relies on:
  - Mapping JSON: memory/TmpData/json2mapping/<base>_mapping.json
  - HTML artifacts from TS2 capture: memory/TmpData/webbot2html/
- Endpoints used: GET `/api/mapping`, GET `/api/state`
- Helper endpoints (optional diagnostics): POST `/api/ts3/plan`, `/api/ts3/analyze-selectors`, `/api/ts3/generate-script`

## Flow Recap
1) TS1 (JPEG → JSON)
2) TS2 (DOM capture → LLM mapping)
3) TS3 (webview fill using TS2 + TS1; no LLM; commit Enter)
4) Final sayfaysa mapping içindeki actions çalıştırılabilir (örn. “Poliçeyi Aktifleştir”).

## Known Limitations and Next Steps
- Shadow DOM and nested iframes aren’t handled yet
- Optional: persist TS3 settings (localStorage)
- Optional: smarter candidate scoring and multi-field disambiguation
