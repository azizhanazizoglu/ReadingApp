# Diyagramlar (Graphviz DOT)

Bu klasörde TS1 → TS2 → TS3 akışını gösteren bir Graphviz (DOT) dosyası var.

- Dosya: `docs/diagrams/ts1_ts2_ts3_flow.dot`

## VS Code içinde nasıl görüntülerim?
1) VS Code’a bir Graphviz eklentisi kurun (örn. “Graphviz (dot) language support” veya benzeri bir önizleme eklentisi).
2) `ts1_ts2_ts3_flow.dot` dosyasını açın.
3) Eklenti menüsünden “Preview”/“Open Preview to the Side” ile diyagramı görüntüleyin.

Alternatif: Komut satırıyla PNG üretmek için Graphviz kuruluysa:
- Windows PowerShell (Graphviz yüklü varsayılarak):
  ```powershell
  dot -Tpng docs/diagrams/ts1_ts2_ts3_flow.dot -o docs/diagrams/ts1_ts2_ts3_flow.png
  ```

## Diyagram içeriği (özet)
- TS1: `/api/start-automation` → ruhsat JSON üretir, `jpg2json` klasörüne yazar ve belleğe set eder.
- TS2: `/api/test-state-2` → iframe HTML + ruhsat JSON’dan mapping üretir, artefaktları `webbot2html` ve JSON’u `json2mapping` klasörüne yazar, belleğe set eder.
- TS3: `/api/ts3/generate-script` (veya in-page filler) → webview içinde alanları doldurur, gerekiyorsa `actions` tıklar.

Not: TS4 kaldırıldı; final sayfa aksiyonları TS3 içindeki `actions` ile yapılır.
