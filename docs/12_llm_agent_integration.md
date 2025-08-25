# LLM Agent Integration and API

## Endpoints
- POST `/api/upload`
  - Body: multipart/form-data with `file` (JPEG)
  - Effect: clears older JPEGs, saves new to `jpgDownload`, updates memory and logs (BE-1001..)
- POST `/api/start-automation` (Ts1)
  - Starts background thread; runs LLM extract; saves JSON to `jpg2json`
- POST `/api/test-state-2` (Ts2)
  - Runs webbot + LLM mapping; saves mapping to `json2mapping`
- GET `/api/state`
  - Returns current Turkish state and context
- GET `/api/mapping`
  - Returns latest mapping JSON
- GET `/api/logs`
  - Returns structured backend logs `{ time, level, code, component, message, extra? }`
- GET `/health`

## Logging Model
- Codes: `BE-xxxx` backend; FE codes: `HD-`, `IDX-`, `UA-`, `UAH-`
- Levels: INFO, WARN, ERROR
- Stored in backend ring buffer and displayed by React UI

## Temp Folder Contract
- `memory/TmpData/jpgDownload` → source JPEG
- `memory/TmpData/jpg2json` → extracted JSON
- `memory/TmpData/json2mapping` → mapping JSON
