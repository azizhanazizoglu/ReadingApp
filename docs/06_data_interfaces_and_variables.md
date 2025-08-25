# Data Interfaces and Variables

## REST API
- POST `/api/upload` → multipart JPEG file
- POST `/api/start-automation` → starts Ts1
- POST `/api/test-state-2` → runs Ts2
- GET `/api/state` → `{ state: 'başladı|devam ediyor|tamamlandı|hata', ... }`
- GET `/api/mapping` → latest mapping JSON
- GET `/api/logs` → list of `{ time, level, code, component, message, extra? }`

## Memory Object (excerpt)
- `memory['state']` → Turkish state string
- `memory['steps']` → chronological job entries
- `memory['uploaded_file']` → latest JPEG path
- `memory['latest_base']` → base name for pairing JSON and mapping
