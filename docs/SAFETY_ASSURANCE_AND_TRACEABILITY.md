# Safety-Critical Software Assurance & Test Traceability

This document captures the safety-critical mindset behind ReadingApp: explicit requirements, verifiable tests, auditable artifacts, and end-to-end traceability.

## Why This Architecture?
- Minimal maintenance via LLM-based mapping that adapts to web changes
- Modular components: extraction, mapping, web automation, memory
- Professional practices: V-Model, automated tests, clear docs, code review
- Safety focus: requirements ↔ tests ↔ code mapped and logged; evidence kept
- CI/CD ready: single-command test runs with artifacts suitable for audits

## What is ReadingApp?
A modular Python + React system to extract, map, and fill web forms using LLMs.
- Extract structured data from Turkish vehicle registration (ruhsat) images
- Map extracted JSON to HTML form inputs dynamically
- Automate form filling and submission
- Unified logging and clear Turkish state machine

## Data Flow
1) Extract: ruhsat JPEG → JSON
2) Download: HTML snapshot via webbot → memory
3) Map: JSON → HTML fields (mapping JSON)
4) Fill: webbot uses mapping to fill and submit

## Modules & Main Scripts
- license_llm
  - license_llm_agent.py — orchestrates LLM extraction
  - license_llm_extractor.py — extracts structured fields from images
  - pageread_llm.py — maps JSON to HTML inputs using LLM
- webbot — HTML retrieval and automation helpers/tests
- memory — persistence utilities and tests
- master — orchestration and integration testing (if used)

## Environment Setup & .env Best Practices
- Single `.env` at project root (e.g., `C:/Users/azizh/Documents/ReadingApp/.env`)
- Example:
  - OPENAI_API_KEY=sk-...
- Load with python-dotenv or shell env; avoid multiple .env files in subfolders

## Test Reporting & Auditability
- Evidence:
  - Structured backend logs via `/api/logs` with level, code (BE-xxxx), component
  - Temp artifacts: `memory/TmpData/jpg2json`, `json2mapping`
  - (Planned) PDF reports for external audits
- CI/CD:
  - Run `python run_all_tests.py` to execute suites and gather outputs

## Requirement-to-Test Traceability
- See `docs/traceability_matrix.md` for full mapping
- Example mapping:
  - REQ-LLM-01: Extract ruhsat info from image → license_llm/test_license_llm_extractor.py → license_llm/license_llm_extractor.py → (PDF planned)
  - REQ-WEB-01: Download HTML snapshot → webbot tests → webbot modules
  - REQ-MEM-01: Persist/restore artifacts → memory tests → memory/db.py
  - REQ-INT-01: End-to-end mapping validity → tests/test_integration_end_to_end.py

## Test Files & Paths (overview)
- license_llm/test_license_llm_extractor.py — LLM extraction
- license_llm/test_pageread_llm.py — LLM mapping
- memory/test_ocr_to_memory.py — persistence
- tests/test_integration_end_to_end.py — E2E
- Artifacts: `jpgDownload` (JPEG), `jpg2json` (JSON), `json2mapping` (mapping JSON)

## Turkish State Machine
- başladı → devam ediyor (per job) → tamamlandı | hata
- Authoritative state on backend; reflected in React UI

## Logging Model
- Backend BE-xxxx codes, INFO/WARN/ERROR levels, component, message, time, extra
- `/api/logs` returns structured list for UI log panel
- Frontend developer logs (HD-/IDX-/UA-/UAH-) complement backend for UI events

## Acceptance & Evidence
- Mapping JSON saved to `json2mapping` with expected shape
- `/api/logs` contains BE-2xxx/3xxx/4xxx infos and BE-9xxx errors if any
- State ends with `tamamlandı` on success, `hata` on failure
