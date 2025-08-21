
# ReadingApp: Overview & Quick Guide

## What is ReadingApp?
ReadingApp is a modular Python system for extracting, mapping, and filling web forms using Large Language Models (LLMs). It is designed for:
- Extracting structured data from Turkish vehicle registration (ruhsat) images using LLMs.
- Dynamically mapping extracted data to any web form, even if the web page changes.
- Automating web form filling and submission with minimal maintenance.
- Professional, decoupled, and testable architecture.

## Why This Architecture?
- **Minimal Maintenance:** LLM-based mapping adapts to web page changes, reducing manual updates.
- **Modular Design:** Each component (extraction, mapping, web automation, memory) is independent and testable.
- **Professional Practices:** V-Model, automated tests, clear documentation, and code review.

## Key Components (Simple Overview)
- **license_llm:** Extracts data from images and maps JSON fields to HTML forms using LLMs.
- **webbot:** Downloads web pages, interacts with forms, automates browser actions.
- **memory:** Stores HTML, mappings, and extracted data in a decoupled way.
- **master:** Orchestrates the workflow and runs integration tests.

## Data Flow (How it Works)
1. **Extract:** license_llm extracts data from ruhsat image → JSON.
2. **Download:** webbot downloads HTML → memory.
3. **Map:** license_llm maps JSON fields to HTML inputs → mapping JSON.
4. **Fill:** webbot fills the form using mapping JSON.

## Technologies Used
- Python 3.12+, OpenAI API (gpt-4o, Vision), pytest, SQLite
- JSON for all data exchange

---

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

## User Stories (Summary)
- Extract data from ruhsat images for insurance automation
- Dynamically map data to any web form
- Run integration tests for full data flow
- Extend system to new forms/data types easily




## Environment Setup & .env File Best Practices

**Important:** Only one `.env` file should exist in the project, located at the project root (e.g., `C:/Users/azizh/Documents/ReadingApp/.env`).

- Remove all `.env` files from subfolders (like `license_llm/.env`, `llm_agent/.env`, etc.) to avoid conflicts.
- All scripts and tests will load environment variables from the root `.env` file.
- This prevents confusion and ensures consistent environment variable usage across all components.

Example `.env` (do not share your real key):
```
OPENAI_API_KEY=sk-...
```

Before running tests that use the LLM, you must set your OpenAI API key. The project uses a `.env` file for convenience:

```
OPENAI_API_KEY=sk-...  # (your real key)
```

To load this automatically, you can use the `python-dotenv` package or set the variable manually in your terminal:

**PowerShell (Windows):**
```powershell
$env:OPENAI_API_KEY="sk-..."
pytest tests/test_integration_end_to_end.py
```

Or install `python-dotenv` and add this to your test files or a `conftest.py`:
```python
from dotenv import load_dotenv
load_dotenv()
```

---



## Test Reporting & PDF Reports

**Technologies Used for Reporting:**
- PDF reports are generated using the `reportlab` Python library.
- Reports are saved in `tdsp/test_reports/`.


All main tests automatically generate a PDF report in `tdsp/test_reports/` after each run (if `reportlab` is installed). Each report includes:
- Test requirement
- Input data
- Expected output
- Actual output
- Pass/Fail result

This is designed for safety-critical software assurance and traceability.


You can run all tests or target specific modules/components as needed. Here are the main commands:

### Run All Tests

```bash
pytest
```

### Run a Specific Test File

```bash
pytest path/to/test_file.py
```

### Main Test Files & Example Commands

| Purpose/Component         | Test File Path                              | Command to Run                                   |
|--------------------------|---------------------------------------------|--------------------------------------------------|
| LLM Extraction/Mapping   | license_llm/test_license_llm_extractor.py   | `pytest license_llm/test_license_llm_extractor.py`|
| Webbot HTML Download     | webbot/test_webbot_html_mapping.py          | `pytest webbot/test_webbot_html_mapping.py`       |
| Memory Integration       | memory/test_ocr_to_memory.py                | `pytest memory/test_ocr_to_memory.py`             |
| End-to-End Integration   | tests/test_integration_end_to_end.py        | `pytest tests/test_integration_end_to_end.py`     |

### Main Test Files, Requirements & Example Commands

| Purpose/Component         | Test File Path                              | Command to Run                                   | Test Requirement & Expected Output |
|--------------------------|---------------------------------------------|--------------------------------------------------|-------------------------------------|
| LLM Extraction/Mapping   | license_llm/test_license_llm_extractor.py   | `pytest license_llm/test_license_llm_extractor.py`| Extracts ruhsat info from image, returns dict with keys like 'plaka_no', 'ad_soyad', etc. |
| Webbot HTML Download     | webbot/test_webbot_html_mapping.py          | `pytest webbot/test_webbot_html_mapping.py`       | Downloads HTML, prints first 2000 chars, asserts HTML is non-empty. |
| Memory Integration       | memory/test_ocr_to_memory.py                | `pytest memory/test_ocr_to_memory.py`             | Stores and retrieves OCR/LLM results, checks data integrity. |
| End-to-End Integration   | tests/test_integration_end_to_end.py        | `pytest tests/test_integration_end_to_end.py`     | Fetches HTML, maps ruhsat JSON to HTML fields with LLM, prints and checks mapping JSON. |

> You can add `-s` to see print output, e.g. `pytest -s tests/test_integration_end_to_end.py`

---

## For More Details
See the `docs/` folder for full documentation on requirements, architecture, methodology, and test strategy.
