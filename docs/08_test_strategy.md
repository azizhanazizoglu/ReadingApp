# Test Strategy

This project uses a layered test strategy with traceability:

## Levels
- Unit tests: core helpers and isolated logic
- Integration tests: Ts1 (jpeg→llm→json), Ts2 (webbot→mapping)
- End-to-end: upload → automation → mapping persisted → state/logs verified

## Artifacts and Evidence
- Structured logs available at `/api/logs` collected during runs
- Temp outputs in `memory/TmpData/jpg2json` and `json2mapping`
- Optional PDF reports (planned) for audits

## Scenarios
- Happy paths for Ts1 and Ts2
- Error paths: missing JPEG, LLM error, file write failure → ensure BE-9xxx codes logged

## How to Run
- Python tests: `python run_all_tests.py`
- Frontend smoke: start backend, run React UI dev server, exercise Ts1/Ts2

## Acceptance Criteria
- State transitions strictly follow Turkish states and end with `tamamlandı` on success
- Mapping JSON contains required keys and is saved to `json2mapping`
- `/api/logs` contains BE-2xxx/3xxx/4xxx infos and BE-9xxx on errors
