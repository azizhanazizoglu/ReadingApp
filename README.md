

# ReadingApp: Safety-Critical Software Assurance & Test Traceability Guide

## LLM ile Web Form Otomasyonu (HTML üzerinden mapping)

- LLM, sadece HTML ve JSON ile form alanlarını otomatik eşleştirir. Ekran görüntüsüne gerek yoktur.
- Webbot, Qt gibi farklı teknolojilerle entegre çalışabilir. Her sayfa değişiminde HTML alınır, LLM'e gönderilir, mapping alınır ve otomasyon devam eder.
- Mapping çıktısı: field_mapping (JSON anahtarından HTML input/select'e) ve actions (ör: hangi butona tıklanacak).


## What is ReadingApp?
ReadingApp is a modular, safety-critical Python system for extracting, mapping, and filling web forms using Large Language Models (LLMs). It is designed for:
- Extracting structured data from Turkish vehicle registration (ruhsat) images using LLMs.
- Dynamically mapping extracted data to any web form, even if the web page changes.
- Automating web form filling and submission with minimal maintenance.
- Professional, decoupled, and testable architecture.
- **Traceable, auditable, and standards-compliant test and reporting for software assurance (ASIL/DO-178C/IEC 61508 inspiration).**


## Why This Architecture?
- **Minimal Maintenance:** LLM-based mapping adapts to web page changes, reducing manual updates.
- **Modular Design:** Each component (extraction, mapping, web automation, memory) is independent and testable.
- **Professional Practices:** V-Model, automated tests, clear documentation, and code review.
- **Safety-Critical Focus:** All test requirements are explicitly documented, mapped to code, and every test run produces a professional PDF report for traceability and audit.
- **CI/CD Ready:** All tests can be run in a single command, with summary and PDF output for each, suitable for continuous integration and external assessment.

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


## Test Files, Requirements & Traceability

All main test files are mapped to explicit requirements and produce PDF reports for each run. This enables full traceability from requirement to test result, as required in safety-critical software development.

| Module      | Script/Test File               | Path                                   | Purpose                                                   | Requirement (from docs/09_test_files_and_paths.txt) |
|-------------|-------------------------------|----------------------------------------|-----------------------------------------------------------|-----------------------------------------------------|
| license_llm | test_license_llm_extractor.py | license_llm/test_license_llm_extractor.py | Tests LLM-based extraction and mapping from ruhsat images | Extract ruhsat info from image, output dict with keys like 'plaka_no', 'ad_soyad', etc. |
| webbot      | test_webbot_html_mapping.py   | webbot/test_webbot_html_mapping.py     | Tests web page download and HTML reading                  | Download HTML from a real web page, print first 2000 chars, and assert HTML is non-empty. |
| memory      | test_ocr_to_memory.py         | memory/test_ocr_to_memory.py           | Tests OCR/LLM result integration and storage in memory/db | Store and retrieve OCR/LLM results, check data integrity and correct storage. |
| integration | test_integration_end_to_end.py| tests/test_integration_end_to_end.py   | End-to-end integration test for HTML fetch, LLM mapping, and output validation | Fetch HTML, map ruhsat JSON to HTML fields with LLM, print and check mapping JSON for required keys ('field_mapping', 'actions'). |

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




## Test Reporting, PDF Reports & Auditability

**Technologies Used for Reporting:**
- PDF reports are generated using the `reportlab` Python library.
- Reports are saved in `tdsp/test_reports/`.

**Test Reporting Process:**
- All main tests automatically generate a PDF report in `tdsp/test_reports/` after each run (if `reportlab` is installed).
- Each report includes:
	- Test requirement (from docs/09_test_files_and_paths.txt, traceable to code)
	- Input data
	- Expected output
	- Actual output
	- Pass/Fail result
	- Error details (if any)
- Reports are timestamped and named by test and date for audit trail.
- Reports are designed for external assessment, traceability, and safety-critical software assurance.

**CI/CD & Assessment:**
- All tests can be run with `python run_all_tests.py` for a full summary and PDF output, suitable for CI/CD pipelines and external audits.
- Each test's requirement, input, and output are traceable in both terminal and PDF report.
- Reports can be archived for regulatory or customer review.

**Traceability & Coverage:**
- Each test is mapped to a requirement and a code component.
- The mapping is maintained in `docs/09_test_files_and_paths.txt` and this README.
- (Planned) A traceability matrix and diagram will be added for full requirement-to-test-to-code coverage.

---


---

## Requirement-to-Test Traceability & Audit Process

### Traceability Matrix
All requirements, test files, code components ve PDF raporları birebir eşlenmiştir. Tam tablo için: `docs/traceability_matrix.md`.

| Req ID     | Requirement Summary                                                      | Test File                                 | Code Component(s)                        | PDF Report Example                                 |
|------------|-------------------------------------------------------------------------|--------------------------------------------|-------------------------------------------|----------------------------------------------------|
| REQ-LLM-01 | Extract ruhsat info from image, output dict with keys like 'plaka_no'... | license_llm/test_license_llm_extractor.py  | license_llm/license_llm_extractor.py      | tdsp/test_reports/license_llm_test_report_*.pdf    |
| REQ-WEB-01 | Download HTML from a real web page, print first 2000 chars, assert HTML  | webbot/test_webbot_html_mapping.py         | webbot/test_webbot_html_mapping.py        | tdsp/test_reports/webbot_test_report_*.pdf         |
| REQ-MEM-01 | Store and retrieve OCR/LLM results, check data integrity and storage     | memory/test_ocr_to_memory.py               | memory/db.py, memory/data_dictionary.py   | tdsp/test_reports/memory_test_report_*.pdf         |
| REQ-INT-01 | Fetch HTML, map ruhsat JSON to HTML fields with LLM, check mapping JSON  | tests/test_integration_end_to_end.py       | license_llm/pageread_llm.py, webbot/..., master.py | (integration test, see summary)                    |

### How to Track & Audit
- Her gereksinim (requirement) için benzersiz bir Req ID atanır ve docs/traceability_matrix.md dosyasında tutulur.
- Her test çalıştırıldığında, PDF raporu otomatik olarak oluşturulur ve test gereksinimi, input, output, hata ve sonuç içerir.
- PDF raporları, testin adı ve tarih/saat ile arşivlenir. Her rapor, ilgili gereksinim ve kod ile eşleştirilebilir.
- Tüm gereksinimlerin test coverage'ı ve kod ile eşleşmesi, traceability matrix ile denetlenebilir.
- CI/CD pipeline'ında veya manuel olarak `python run_all_tests.py` ile tüm testler ve raporlar topluca üretilebilir.
- Herhangi bir değişiklikte hem README, hem docs/09_test_files_and_paths.txt hem de traceability_matrix.md güncellenmelidir.

#### Dış Denetim ve Regülasyonlar İçin
- Tüm PDF raporları ve traceability matrix, dış denetçilere veya müşteri kalite ekiplerine sunulabilir.
- Gereksinim değişikliği, yeni test veya kod güncellemesi olduğunda, izlenebilirlik ve coverage tekrar kontrol edilmelidir.

---

## For More Details
See the `docs/` folder for full documentation on requirements, architecture, methodology, test strategy, and traceability. Traceability matrix: `docs/traceability_matrix.md`.
