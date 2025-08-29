# TS1 → TS2 → TS3 Akışı (Mermaid)

Aşağıdaki diyagram VS Code’da Mermaid eklentisiyle (veya GitHub üzerinde) önizlenebilir; Graphviz gerekmez.

```mermaid
flowchart LR
  %% Stil
  classDef grp fill:#f8fafc,stroke:#94a3b8,stroke-width:1px,color:#0f172a;
  classDef node fill:#ecfeff,stroke:#94a3b8,stroke-width:1px,color:#0f172a,rx:6,ry:6;
  classDef store fill:#fff7ed,stroke:#fb923c,color:#7c2d12,rx:6,ry:6;
  classDef file fill:#f0f9ff,stroke:#38bdf8,color:#0c4a6e,rx:6,ry:6;

  subgraph UI[ Kullanıcı / UI ]
    direction TB
    Upload["JPEG Yükle\nPOST /api/upload"]:::node
    Iframe["Iframe: Hedef Sayfa\n(React/Electron Webview)"]:::node
  end:::grp

  subgraph BE[ Backend (Flask) ]
    direction TB
    TS1["TS1: JPEG → LLM → JSON\nPOST /api/start-automation\n(run_ts1_extract)"]:::node
    TS2["TS2: HTML + JSON → Mapping\nPOST /api/test-state-2\n(map_json_to_html_fields)"]:::node
    TS3["TS3: Form Doldurma (LLM yok)\nPOST /api/ts3/generate-script\n(+ in-page filler)"]:::node
  end:::grp

  subgraph TMP[ Artefaktlar (memory/TmpData) ]
    direction TB
    JPGDL["jpgDownload/*.jpg"]:::file
    J2J["jpg2json/<base>.json"]:::file
    W2H["webbot2html/page.html\n+ form.html + meta.json"]:::file
    J2M["json2mapping/<base>_mapping.json"]:::file
  end:::grp

  MEM[("Bellek (memory_store)\nruhsat_json, html, mapping, latest_base")]:::store

  Upload --> JPGDL
  JPGDL --> TS1
  TS1 --> J2J
  TS1 --> MEM

  Iframe --> TS2
  MEM --> TS2
  TS2 --> W2H
  TS2 --> J2M
  TS2 --> MEM

  MEM --> TS3
  Iframe <---> TS3

  %% Not
  N1["TS2 mapping JSON, sadece ```json kod bloğu içinden parse edilir."]:::file
  TS2 -.-> N1
```

Eğer Mermaid görünmezse (eklenti yoksa) aşağıdaki ASCII özetini kullan:

```
Kullanıcı/UI                         Backend (Flask)                     TmpData
─────────────                        ───────────────                     ───────
 [JPEG Yükle] --/api/upload--> [TS1: start-automation] --> jpg2json/<base>.json
                                      │                                   ▲
                                      └──> memory.ruhsat_json             │
 [Iframe URL/HTML] --(body)-------> [TS2: test-state-2]  --> webbot2html/*│
                                      │            └──────> json2mapping/<base>_mapping.json
                                      └──> memory.mapping
 memory.(ruhsat_json+mapping) --> [TS3: ts3/generate-script] --(fill/actions)--> Iframe
```

Özet:
- TS1: JPEG’i işler, `jpg2json` dosyası ve `ruhsat_json` (bellek) üretir.
- TS2: Iframe HTML + `ruhsat_json` ile mapping üretir; `webbot2html` ve `json2mapping` dosyalarını yazar; mapping’i belleğe set eder.
- TS3: Mapping + `ruhsat_json` ile webview’de form doldurur; gerekirse `actions` tıklar.
