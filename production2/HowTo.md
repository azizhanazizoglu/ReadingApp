# Quick How-To (Production2)

This is a quick reference for starting/stopping the new backend and UI on Windows PowerShell.

## Activate Python env (optional but recommended)

```powershell
cd C:\Users\azizh\Documents\ReadingApp\production2\backend
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Tip: To leave the venv later, run `deactivate`.

## Run the backend (FastAPI on 127.0.0.1:5100)

```powershell
cd C:\Users\azizh\Documents\ReadingApp\production2\backend
python -m uvicorn main:app --host 127.0.0.1 --port 5100 --reload
```

Health check: http://127.0.0.1:5100/health

## Build UI and start Electron app

```powershell
cd C:\Users\azizh\Documents\ReadingApp\production2
./build2run.ps1
```

What this does:
- Builds `react_ui` with Vite (generates `react_ui/dist`).
- Mirrors the build into `react_gui/dist` (Electron’s load path).
- Starts the Electron app that loads `production2/react_gui/dist/index.html`.

## Verify UI ↔ Backend match

By default both point to 127.0.0.1:5100.

Checklist:
- Backend log shows: `Uvicorn running on http://127.0.0.1:5100`.
- Electron DevTools Network calls go to `http://127.0.0.1:5100/...` (no 5001).
- GET http://127.0.0.1:5100/health returns `{ "status": "ok" }`.

If you need to change the backend URL for the UI during development:

```powershell
# Same terminal where you run the UI dev server (if you run it manually)
$env:VITE_BACKEND_URL = "http://127.0.0.1:5101"
```

Note: Electron loads the built UI and uses the default unless you rebuild with a different env.

## Where files go

- Filtered HTML captures: `production2/tmp/html/<name>.json`
- Static mappings: `production2/tmp/jsonMappings/<name>_*.json`
- Config (editable): `production2/config.json` (loaded by `production2/config.py`)

## Common issues

- UI shows Ts1/Ts2 (old UI): make sure you started via `production2/build2run.ps1` so Electron loads `production2/react_gui/dist/index.html` built from the new `react_ui`.
- F1 doesn’t capture: Web capture relies on Electron <webview>; use Electron instead of a plain browser dev server.
- Import errors in editor (fastapi/uvicorn): ensure venv is activated and `pip install -r requirements.txt` was run.
