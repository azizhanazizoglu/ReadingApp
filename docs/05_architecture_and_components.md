# Architecture and Components

## High-Level
- Backend (Flask): routes, file upload, stateflow agent, logging utils, memory
- Frontend (React + Vite + TS): Header, MainLayout, log panel, Developer Mode
- Electron (optional): desktop packaging

## Backend Modules
- `backend/app.py`: Routes including `/api/upload`, `/api/start-automation`, `/api/test-state-2`, `/api/state`, `/api/mapping`, `/api/logs`, `/health`
- `backend/stateflow_agent.py`: Jobs for Ts1/Ts2; saves artifacts to temp dirs; sets Turkish states
- `backend/file_upload.py`: Cleans old JPEGs, saves upload, updates memory and logs
- `backend/logging_utils.py`: Structured logs with ring buffer and memory integration

## Frontend
- `react_ui/src/components/Header.tsx`: Developer Mode controls (Home, Ts1, Ts2), SearchBar, toggles
- `react_ui/src/components/MainLayout.tsx`: Fetches `/api/logs`, renders unified logs
- `react_ui/src/pages/Index.tsx`: Wires handlers; Ts2 now calls backend

## Data & Temp Folders
- `memory/TmpData/jpgDownload`: latest uploaded JPEG
- `memory/TmpData/jpg2json`: LLM output JSON
- `memory/TmpData/json2mapping`: mapping outputs

### TmpData Temizlik Politikası (Standart)
- Upload: `jpgDownload` eski JPEG'leri temizler; yalnızca son yüklenen dosya kalır.
- TS1 (/api/start-automation): başlamadan önce `jpg2json` temizlenir; yalnızca son LLM JSON'u yazılır.
- TS2 (/api/test-state-2): başlamadan önce `json2mapping` temizlenir; yalnızca son mapping JSON'u yazılır ve saklanır (silinmez).

### UI Durum Gösterimi (Footer)
- Footer yükseklik: sabit 60px; metin tek satır ve kısaltılmış (ellipsis).
- Gösterim formatı: `[BİLGİ|UYARI|HATA|DEBUG] KOD: kısa_metin (klasör/dosya)`; tüm log türleri için tek tip Türkçe format.
