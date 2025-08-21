# ReadingApp: Modules & Test Overview

## Modules & Main Scripts

### license_llm
- **license_llm_agent.py**: Orchestrates LLM-based extraction from images.
- **license_llm_extractor.py**: Extracts structured data (e.g., ruhsat fields) from images using LLM.
- **pageread_llm.py**: Maps extracted JSON data to HTML form fields using LLM.

### webbot
- **pageread_llm.py**: (If present) Handles LLM-based HTML mapping (see license_llm for main logic).
- **test_webbot_html_mapping.py**: Tests web page download and HTML reading.
- **__init__.py**: Module init.

### memory
- **data_dictionary.py**: Defines data structures and dictionaries for storage.
- **db.py**: Handles data storage and retrieval (e.g., SQLite).
- **test_ocr_to_memory.py**: Tests integration of OCR/LLM results into memory.

### master
- **master.py**: Orchestrates the full workflow and runs end-to-end integration tests.

---

## Test Files & Paths

| Module      | Script/Test File               | Path                                   | Purpose                                                   |
|-------------|-------------------------------|----------------------------------------|-----------------------------------------------------------|
| license_llm | test_license_llm_extractor.py | license_llm/test_license_llm_extractor.py | Tests LLM-based extraction and mapping from ruhsat images |
| webbot      | test_webbot_html_mapping.py   | webbot/test_webbot_html_mapping.py     | Tests web page download and HTML reading                  |
| memory      | test_ocr_to_memory.py         | memory/test_ocr_to_memory.py           | Tests OCR/LLM result integration and storage in memory/db |
| master      | master.py                     | master.py                              | End-to-end integration test and workflow orchestration    |

---

## How to Run Tests

- Run all tests: `pytest`
- Run a specific test: `pytest path/to/test_file.py`

---

> For more details, see the `docs/` folder and the main `README.md`.
