# Scheduler and State Flow

The scheduler coordinates jobs for Ts1 and Ts2. The state machine uses Turkish terms and is authoritative on backend.

# Scheduler ve State Flow
## States

## Jobs

Transitions follow: `başladı → devam ediyor (each job) → tamamlandı | hata`.
Stateflow ajanı, JPEG -> LLM JSON (TS1) -> Web HTML (Electron webview DOM capture) -> LLM Mapping (TS2) -> Webview Form Fill (TS3) adımlarını sıralı olarak çalıştırır.
TS3 doldurma sırasında kontrollü/maskeli inputlarda Enter komiti ve blur uygulanır (kalıcılık için).

## Geçici Veri (TmpData) Temizlik Politikası

Amaç: Her çalıştırmada yalnızca “son” çıktının kalması ve debug sürecinin sade tutulması.

- Upload (jpgDownload): Yeni yükleme öncesi `memory/TmpData/jpgDownload` klasöründeki eski JPEG’ler temizlenir, yeni dosya kaydedilir.
- TS1 (jpg2json): `/api/start-automation` çağrısı öncesi `memory/TmpData/jpg2json` temizlenir; LLM çıktısı tek bir JSON olarak kaydedilir. Dosya adı, yüklenen JPEG’in taban adı ile eşleşir (örn. `download_123.json`).
- TS2 (json2mapping): `/api/test-state-2` çağrısı öncesi `memory/TmpData/json2mapping` temizlenir; mapping tek bir JSON dosyası olarak kaydedilir (örn. `download_123_mapping.json`). Bu dosya artık silinmez; debug için klasörde kalır.

Not: `memory` içinde son `ruhsat_json`, `html`, `mapping` ve `latest_base` bellekte tutulur. TS2 sırasında bellek boşsa, sistem `jpg2json` klasöründen son JSON’u fallback olarak yükleyebilir.
