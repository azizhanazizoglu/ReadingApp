# Requirement-to-Test Traceability Matrix

This matrix provides a full mapping from high-level requirements to test files and code components. It is designed for safety-critical software assurance, external assessment, and regulatory review.

| Requirement ID | Requirement Description                                                                 | Test File                                 | Code Component(s)                        | PDF Report Example                                 |
|---------------|----------------------------------------------------------------------------------------|--------------------------------------------|-------------------------------------------|----------------------------------------------------|
| REQ-LLM-01    | Extract ruhsat info from image, output dict with keys like 'plaka_no', 'ad_soyad', etc. | license_llm/test_license_llm_extractor.py  | license_llm/license_llm_extractor.py      | tdsp/test_reports/license_llm_test_report_*.pdf    |
| REQ-WEB-01    | Download HTML from a real web page, print first 2000 chars, and assert HTML is non-empty.| webbot/test_webbot_html_mapping.py         | webbot/test_webbot_html_mapping.py        | tdsp/test_reports/webbot_test_report_*.pdf         |
| REQ-MEM-01    | Store and retrieve OCR/LLM results, check data integrity and correct storage.            | memory/test_ocr_to_memory.py               | memory/db.py, memory/data_dictionary.py   | tdsp/test_reports/memory_test_report_*.pdf         |
| REQ-INT-01    | Fetch HTML, map ruhsat JSON to HTML fields with LLM, print and check mapping JSON.       | tests/test_integration_end_to_end.py       | license_llm/pageread_llm.py, webbot/..., master.py | (integration test, see summary)                    |

- Each requirement is uniquely identified (REQ-*) and mapped to its test and code.
- PDF reports are generated for each test run and archived for audit.
- This matrix is maintained in sync with README.md and docs/09_test_files_and_paths.txt.

---

# Traceability Diagram (Planned)

A visual diagram will be added to show the links from requirements → test files → code components → PDF reports, for full traceability and assessment.

---

For any change in requirements, tests, or code, update this matrix and the documentation to maintain traceability and compliance.
