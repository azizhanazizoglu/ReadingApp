# Production2: Backend + React UI

This folder contains the new FastAPI backend and the new React UI (with F1/F2/F3 and TsX controls).

## Prerequisites
- Windows PowerShell 5.1 or newer
- Python 3.10+ with pip
- Node.js 18+ (npm or pnpm)

## 1) Start the backend (FastAPI on 127.0.0.1:5100)
Option A: without venv

```powershell
cd c:\Users\azizh\Documents\ReadingApp\production2\backend
pip install -r requirements.txt
py -m uvicorn main:app --host 127.0.0.1 --port 5100 --reload
```

Option B: with venv (recommended for isolation)

```powershell
cd c:\Users\azizh\Documents\ReadingApp\production2\backend
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 5100 --reload
```

Health check: http://127.0.0.1:5100/health

## 2) Start the UI (React + Electron)
Full functionality (F1 capture) requires Electron because the app uses the Electron <webview> for DOM access.

Use the helper script inside production2 to build the UI and start Electron:

```powershell
c:\Users\azizh\Documents\ReadingApp\production2\build2run.ps1
```

- This builds `production2/react_ui` and then starts the Electron app.
- If Electron isn’t available, it falls back to running the Vite dev server (browser). In browser mode, F1 DOM capture is disabled because <webview> APIs aren’t available.

## 3) Developer Mode and F1/F2/F3
- Toggle Developer Mode via the right-side toggle in the header to reveal TsX and F1/F2/F3 buttons.
- F1 posts the current page DOM to the backend (`POST /api/f1`) and saves a filtered JSON copy under:
  - `production2/tmp/html/<name>.json`

## 4) Backend URL override (optional)
The UI defaults to `http://127.0.0.1:5100`. To override during development:

```powershell
# In the same shell where you run the UI dev server
$env:VITE_BACKEND_URL = "http://127.0.0.1:5101"
```

## 5) Troubleshooting
- If the UI shows older Ts1/Ts2 buttons, ensure you’re running the UI from `production2/react_ui` (Electron will load its `dist/index.html`).
- If `/api/logs` shows empty, that’s expected—logs are minimal in this backend. Use the in-app Developer Log panel (Log button bottom-right).
- If `F1` does nothing in the browser dev server, start the Electron app instead so the webview is available.

## Endpoints (current)
- GET `/health`
- POST `/api/f1` (saves filtered HTML JSON)
- POST `/api/html/capture` (also saves filtered HTML JSON)
- POST `/api/tsx/dev-run` (placeholder)
- GET `/api/logs` and POST `/api/logs/clear` (minimal)