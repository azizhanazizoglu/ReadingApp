# Test Files and Paths

- `license_llm/test_license_llm_extractor.py` → LLM extraction from JPEG
- `license_llm/test_pageread_llm.py` → LLM mapping from JSON to HTML fields
- `webbot/` (if applicable) → HTML retrieval tests
- `memory/test_ocr_to_memory.py` → persistence integrity
- `backend/test_flask_server.py` or root `test_flask_server.py` → API smoke
- `run_all_tests.py` → orchestrated run

Artifacts:
- `memory/TmpData/jpgDownload/*.jpg`
- `memory/TmpData/jpg2json/*.json`
- `memory/TmpData/json2mapping/*_mapping.json`
