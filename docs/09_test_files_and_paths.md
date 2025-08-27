# Test Files and Paths

Ana testler ve smoke senaryoları:
- `tests/smokeTests/test_smoke_backend.py` → Backend health, upload, TS1, TS2 (LLM ve ağ stub’lu)
- `license_llm/test_license_llm_extractor.py` → JPEG’ten LLM extraction (unit)
- `license_llm/test_pageread_llm.py` → JSON→HTML mapping prompt/parse (unit)
- `webbot/` → HTML edinme testleri (isteğe bağlı, ağ erişimi gerekebilir)
- `memory/test_ocr_to_memory.py` → kalıcılık/test entegrasyonu
- `run_all_tests.py` → orkestrasyon

Artefakt yolları (absolute olarak `PROJECT_ROOT` altına yazılır):
- `memory/TmpData/jpgDownload/*.jpg` (Upload sonucu)
- `memory/TmpData/jpg2json/*.json` (TS1: JPEG→JSON)
- `memory/TmpData/json2mapping/<base>_mapping.json` (TS2: Mapping)
- `memory/TmpData/webbot2html/page.html` (TS2: Webview DOM kaydı)
- `memory/TmpData/webbot2html/form.html` (ilk <form>, varsa)
- `memory/TmpData/webbot2html/page.json` (url, timestamp, length)
- `memory/TmpData/webbot2html/form_meta.json` (inputs/selects/textareas/buttons sayıları)

TS3 notları:
- TS3, yeni bir artefakt üretmez; `/api/mapping` ve `/api/state` ile çalışır.
- Form doldurma, Electron webview içinde yürütülür ve görsel vurgular (Highlight) isteğe bağlıdır.

Koşum notları:
- TS2 testinde LLM ve ağ çağrıları monkeypatch ile stub edilir; gerçek anahtar gerektirmez.
- Tüm smoke testleri çalıştırmak için:
	- Python: `python -m pytest -q tests\smokeTests`

