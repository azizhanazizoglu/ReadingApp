# GitHub Actions CI

Bu doküman, repodaki GitHub Actions iş akışlarını (CI) ve ne yaptıklarını açıklar.

## Genel Bakış
- Workflow dosyası: `.github/workflows/ci-smoke.yml`
- Tetikleyiciler: `push` (main), `pull_request` (main), `workflow_dispatch` (manuel)
- İşler:
  - `smoke`: Bağımlılıklar minimal (`requirements-ci.txt`), ağ/LLM bağımlılıkları stub edilir; smoke testleri hızlıca çalıştırır ve son mapping özetini Job Summary’ye ekler, artefaktları yükler.
  - `live-llm`: Sadece `secrets.OPENAI_API_KEY` tanımlıysa çalışır; gerçek LLM ile `tests/liveTests` çalıştırır ve son mapping’i özetler.

## smoke job
1) Checkout ve Python 3.12 kurulumu
2) `pip install -r requirements-ci.txt`
3) `pytest tests/smokeTests -s -vv`
4) Son mapping JSON bulunursa `ci_artifacts/summary.md` ve `mapping_summary.json` oluşturulur.
5) PR ise özet yorum olarak eklenir; ayrıca artefaktlar upload edilir:
   - `memory/TmpData/json2mapping/*.json`
   - `ci_artifacts/*.md`, `ci_artifacts/*.json`

Üretilen özet (örnek):
```
## Smoke Mapping Output
- File: memory/TmpData/json2mapping/<base>_mapping.json
- Fields: tckimlik, dogum_tarihi, ad_soyad, plaka_no
- Actions: ["click#DEVAM"]
```

## live-llm job
- Koşul: `OPENAI_API_KEY` secret’ı boş değilse
- Adımlar:
  - `pip install -r requirements.txt`
  - Env ile çalıştır: `OPENAI_API_KEY`, `DISABLE_TS2_HEURISTIC=1`
  - `pytest tests/liveTests -s -vv`
  - Son mapping JSON varsa Job Summary’ye detaylı JSON eklenir ve artefakt yüklenir

## Secrets ve Ortam Değişkenleri
- `OPENAI_API_KEY`: live-llm job için zorunlu
- `GITHUB_TOKEN`: PR yorumları için GitHub’ın otomatik sağladığı token (config gerektirmez)

## Yerel Çalıştırma İpuçları
- Aynı smoke testlerini lokal çalıştırmak için:
```
python -m pytest -q tests/smokeTests
```
- Live testleri lokal çalıştırmak için (opsiyonel):
```
$env:OPENAI_API_KEY="sk-..."; python -m pytest -q tests\liveTests
```

## Artefaktlar ve İzlenebilirlik
- Mapping dosyaları: `memory/TmpData/json2mapping/`
- HTML artefaktları (TS2): `memory/TmpData/webbot2html/`
- CI run’larında bu dosyalar Actions arayüzünden indirilebilir.
