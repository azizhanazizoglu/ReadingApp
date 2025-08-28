# Documentation

All documents are in Markdown. This index replaces old .txt files.

## Contents
- 01_project_overview.md
- 02_vmodel_and_methodology.md
- 03_user_stories.md
- 04_software_requirements.md
- 05_architecture_and_components.md
- 06_data_interfaces_and_variables.md
- 07_technologies_and_methods.md
- 08_test_strategy.md
- 09_test_files_and_paths.md
- 10_electron_react_desktop_user_story.md
- 10_qt_browser_user_story.md
- 11_scheduler_and_state_flow.md
- 12_llm_agent_integration.md
- 13_ts3_autofill_and_debugging.md
- 13_ts4_orchestration.md
- error_codes.md
- FOLDER_STRUCTURE_AND_NAMING_CONVENTION.md
- traceability_matrix.md

Additional:
- SAFETY_ASSURANCE_AND_TRACEABILITY.md

## Recent Updates (2025-08-28)
- TS2 schema now includes `page_kind`, `is_final_page`, `final_reason`, `evidence`, `actions`; strict code-fenced JSON required.
- TS3 injection script commits values (Enter + blur) for persistence.
- TS3 helper endpoints added: `/api/ts3/plan`, `/api/ts3/analyze-selectors`, `/api/ts3/generate-script`.
- TS4 orchestration doc added; frontend orchestrator runs TS2 then TS3 and handles final activation.

## Recent Updates (2025-08-27)
- TS2 akışı: Electron webview DOM → backend → HTML ve meta artefaktları diske kaydediliyor
- TS3 eklendi: Mapping + TS1 ile form doldurma, Developer Mode ayar paneli (Highlight, Simulate Typing, Step Delay)
- IDX-TS3-* logları ve sorun giderme rehberi eklendi
- Test dosyaları ve artefakt yolları dokümantasyonu güncellendi
