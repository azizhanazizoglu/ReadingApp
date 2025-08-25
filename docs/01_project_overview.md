# Project Overview

ReadingApp is a modular LLM-assisted automation system that extracts data from Turkish vehicle registration images (ruhsat), maps it to arbitrary web forms, and automates filling. It provides a professional, testable architecture with unified logging and clear state handling.

## Goals
- Reliable end-to-end flow from JPEG → JSON → HTML mapping → Form fill
- Minimal maintenance via LLM-assisted mapping
- Professional logging with codes, levels, and components
- Clear developer UX with Developer Mode tools

## Current Highlights (2025-08-25)
- Structured backend logging (levels, BE-xxxx codes) exposed via `/api/logs`
- Ts1 (jpeg→llm→json) and Ts2 (webbot→mapping) implemented
- Temp folders standardized: `memory/TmpData/jpgDownload`, `jpg2json`, `json2mapping`
- Turkish state machine synced front/back: "başladı → devam ediyor → tamamlandı | hata"
- Frontend Developer Mode with Home/Ts1/Ts2, compact SearchBar, and unified log panel
