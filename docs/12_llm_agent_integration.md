# LLM Agent Integration and API

## Endpoints
- POST `/api/upload`
  - Body: multipart/form-data with `file` (JPEG)
  - Effect: clears older JPEGs, saves new to `jpgDownload`, updates memory and logs (BE-1001..)
- POST `/api/start-automation` (Ts1)
  - Starts background thread; runs LLM extract; saves JSON to `jpg2json`
- POST `/api/test-state-2` (Ts2)
  - Runs webbot + LLM mapping; saves mapping to `json2mapping`
  - Output schema (strict, code-fenced JSON only):
    ```json
    {
      "version": "1.0",
      "page_kind": "fill_form" | "final_activation",
      "is_final_page": false,
      "final_reason": "",
      "evidence": {
        "url": "",
        "title": "",
        "h1": ""
      },
      "field_mapping": {
        "tckimlik": "CSS_SELECTOR",
        "dogum_tarihi": "CSS_SELECTOR",
        "ad_soyad": "CSS_SELECTOR",
        "plaka_no": "CSS_SELECTOR"
      },
      "actions": ["click#DEVAM"]
    }
    ```
  - Kurallar:
    - LLM-yalnız karar; heuristik yok.
    - Yalnızca üçlü backtick içinde `json` kod bloğu çıkışı kabul edilir.
    - Final sayfada `page_kind = final_activation`, `is_final_page = true`, `field_mapping` boş olabilir; `actions` içinde aktivasyon butonu (örn. `click#Poliçeyi Aktifleştir`) yer alır.
- GET `/api/state`
  - Returns current Turkish state and context
- GET `/api/mapping`
  - Returns latest mapping JSON
- GET `/api/logs`
  - Returns structured backend logs `{ time, level, code, component, message, extra? }`
- GET `/health`

## TS3 Helper Endpoints
- POST `/api/ts3/plan`: Mapping ve TS1 verisine göre doldurma planı ve `resolved` değerler üretir.
- POST `/api/ts3/analyze-selectors`: Seçicileri ve aday alanları analiz eder (geliştirici modu için).
- POST `/api/ts3/generate-script`: Highlight, simulateTyping, stepDelayMs, commitEnter parametreleriyle injection script üretir; FE bu scripti webview içinde çalıştırır.

## Notlar (Akış)
- TS2 sonucunda `page_kind = final_activation` ise, TS3 `actions` içinde final CTA’yı (örn. “Poliçeyi Aktifleştir”) tıklayabilir.

## Logging Model
- Codes: `BE-xxxx` backend; FE codes: `HD-`, `IDX-`, `UA-`, `UAH-`
- Levels: INFO, WARN, ERROR
- Stored in backend ring buffer and displayed by React UI

## Temp Folder Contract
- `memory/TmpData/jpgDownload` → source JPEG
- `memory/TmpData/jpg2json` → extracted JSON
- `memory/TmpData/json2mapping` → mapping JSON
