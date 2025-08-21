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

## Main Test Files & Paths
- `license_llm/test_license_llm_extractor.py`: Tests LLM extraction & mapping
- `webbot/test_webbot_html_mapping.py`: Tests web page download & HTML reading
- `memory/test_ocr_to_memory.py`: Tests OCR/LLM result integration & storage
- `master.py`: End-to-end integration test & workflow

## User Stories (Summary)
- Extract data from ruhsat images for insurance automation
- Dynamically map data to any web form
- Run integration tests for full data flow
- Extend system to new forms/data types easily

## For More Details
See the `docs/` folder for full documentation on requirements, architecture, methodology, and test strategy.
