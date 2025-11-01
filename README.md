## ReadingApp

Modern, modüler bir LLM + Otomasyon platformu. Ruhsat JPEG → LLM → JSON → HTML mapping → Form doldurma akışını uçtan uca sağlar. React (Vite + TS) ve opsiyonel Electron arayüz, Python Flask backend, yapılandırılmış loglama ve izlenebilirlik ile gelir.

Bu README ana giriş noktasıdır. Tüm ayrıntılı dokümantasyon profesyonel Markdown formatında `docs/` altındadır.

## İçindekiler
- [Özellikler ve Güncellemeler](#features-updates)
- [Monorepo Yapısı ve Bileşenler](#monorepo-components)
- [Hızlı Başlangıç (Backend, React UI, Electron)](#quick-start)
- [API Özeti ve Sözleşmeler](#api-summary-contracts)
- [Test, Raporlama ve İzlenebilirlik](#tests-traceability)
- [Smoke Tests (Hızlı Sağlık Kontrolü)](#smoke-tests)
- [Statik-Önce Akış ve LLM Fallback](#static-first)
- [Kalibrasyon (C Modu) — Çok Sayfalı Eşleme](#calibration)
- [TsX Orchestrator ve Entegrasyon Testleri](#tsx-orchestrator-tests)
 - [Stateflows Hızlı Şema](#stateflows-cheatsheet)
- [Loglama, Hata Kodları ve Geçici Klasörler](#logging-error-tmp)
- [Güvenlik ve Emniyet Odaklı Gelişim (V-Model)](#safety-vmodel)
- [Sorun Giderme (Troubleshooting)](#troubleshooting)
- [Hızlı Link Rehberi (Deep Links)](#deep-links)
- [Git Flow ve PR Kılavuzu](#git-flow-pr)

---

# Teknik El Kitabı (Academic Style)

Bu bölüm, tüm alt klasörlerdeki bilgileri tek bir “kitapçık” formatında toplar. Profesyonel akademik üslupta, tek README ile tam kapsama sağlar.

## İçindekiler (Index)
1. [Özet (Abstract)](#abstract)
## Production2 — Modern Automation Prototype (Single Focus README)

This repository now documents only the Production2 prototype. Earlier experiments (e.g., the older `react_ui` root) are considered Prototype A. Production2 is Prototype B and is the product we iterate on.

- UI: React + Vite + Electron (desktop) under `production2/react_ui` and `production2/electron_app`
- Backend: FastAPI under `production2/backend` with structured logs and stateflow endpoints
- Automation: Static-first with LLM fallback, plus a Calibration panel for deterministic multi‑page mappings
- Data areas: clearly separated input, output and temp folders under `production2/tmp`

This README is the single place to learn how Production2 works end‑to‑end.

## Table of contents
- What’s included
- Quick start (Windows)
- UI overview and main actions
- Automation flows (F1/F2/F3 and Thunderbolt)
- Calibration (multi‑page static mapping)
- Data directories (input/output/temp)
- Config knobs
- Folder structure (Production2 only)
- Troubleshooting

---

## What’s included

Production2 contains everything needed to run the end-to-end flow:

- Electron app with a webview and a professional two‑row header
	- Always-visible User Task input
	- Thunderbolt button for full automation
	- Calibrate icon (crosshair) that opens the docked calibration panel
	- Debug toggle that expands developer actions (Auto, Find Home, Go to Task, Fill Static, Fill LLM, Home)
- FastAPI backend providing feature endpoints for navigation and filling
- A static‑first filling engine with TS3 selectors and robust verification
- Calibration tooling and a merge step into `config.json`

## Quick start (Windows)

Prereqs: Node.js 18+, npm or pnpm; Python 3.10+; PowerShell.

Run the helper script from Production2:

```
cd production2
./build2run.ps1
```

What it does:
- Builds `production2/react_ui`
- Mirrors the UI into `production2/react_gui/dist`
- Starts Electron via `production2/electron_app/start_all.ps1` (falls back to repo `electron_app` if needed)
- If Electron isn’t present, starts the Vite dev server instead

## UI overview and main actions

Top header (always visible):
- Back / Forward / Refresh / Go (address)
- Thunderbolt (full automation)
- Upload (JPG)
- Calibrate (crosshair icon)
- User Task input (e.g., “Yeni Trafik”)
- Theme + Debug toggle

When Debug is ON, header extends to show developer actions:
- Auto (Master flow)
- Find Home (F1)
- Go to Task (F2)
- Fill (Static)
- Fill (LLM)
- Home (quick open)

Design principles:
- No horizontal sliders; two‑row responsive layout
- Icon-only where space matters; tooltips and accessible labels everywhere
- “User Task” stays visible even when Debug is OFF

## Automation flows

F1 Find Home
- Captures DOM/URL, asks backend for candidate plans, clicks, waits for navigation events, then detects change
- Logs selectors and detection reasons; LLM fallback is available where configured

F2 Go to Task
- Uses the “User Task” label (e.g., Yeni Trafik)
- Static-first: find the correct button; if not, open the side menu; optional LLM planning
- Early‑exit as soon as a real change is detected (improves speed and avoids 6 loops)

F3 Fill Forms (Static-first)
- Loads ruhsat (from Vision LLM output under tmp) and analyzes current page
- Fills sequentially with verify/commit; runs actions (e.g., Devam)
- Detects final page and captures PDF when applicable

Thunderbolt — Full automation
- Runs F1 → F2 (with the current User Task) → Auto/Master (static → LLM as needed)
- Uses a “fast profile”: shorter waits (3s webview settle), reduced F2 loops (4), and early exits on success

## Calibration (multi‑page static mapping)

The Calibration panel lets you build a deterministic mapping per site/task:
- Pick/Live selectors with status and HTML snippets
- Actions list with drag order
- Multi‑page: Page Name, URL sample/pattern, Add Next Page, Mark as Last Page
- Save Draft → `production2/calib.json`
- Finalize → merges into `production2/config.json` under `staticFormMapping.sites[host][task]`

Why use calibration?
- Faster, cheaper, and reliable automation (static-first) with LLM only as a fallback

## Data directories (production2/tmp)

Input, temp, outputs are kept under `production2/tmp`:

- tmp/data — image staging for uploads (e.g., Ruhsat.jpg)
- tmp/ruhsat_json — normalized ruhsat JSON saved by ingestion
- tmp/jsonDatafromLLM — raw/parsed Vision LLM outputs
- tmp/prompts/findHomePage — F1 prompt/meta/filtered artifacts
- tmp/prompts/goUserTaskPage — F2 prompt/meta/filtered artifacts
- tmp/pdf — generated/captured PDFs

Cleanup policy
- Workspaces are reused across runs; critical paths overwrite prior results (last run wins) where applicable

## Config knobs

Location: `production2/config.json` and helpers in `production2/config.py`.

- findHomePage: prompts and attempt limits
- goUserTaskPage:
	- userTaskButtons (synonyms/selectors)
	- sideMenuToggle detection
	- stateflow defaults (maxLoops, waits)
- goFillForms:
	- llm.mappingPrompt and model
	- stateflow timings (per field waits, verify delays, actions wait)
- staticFormMapping: target site/task mappings merged from calibration

## Folder structure (Production2)

```
production2/
	backend/               # FastAPI app and features
	react_ui/              # React UI (Vite + TS)
	electron_app/          # Electron starter used by build2run.ps1
	react_gui/dist/        # Mirrored UI build for Electron
	calib.json             # Calibration drafts (by host/task)
	config.json            # Runtime configuration (includes staticFormMapping)
	tmp/                   # Input/output/temp artifacts (see Data directories)
	build2run.ps1          # Build + run helper (prefers production2 electron)
	start_all.ps1          # Convenience starter (Electron)
	tests...               # Production2 test suites
```

## Troubleshooting

- UI doesn’t start with Electron: build2run falls back to Vite dev server; check Node/pnpm and reinstall deps
- Backend config or timing feels slow: adjust waits/loops in `config.json`; Thunderbolt fast profile already reduces waits
- Go to Task loops even after click: fixed — stateflow now early‑exits once a change is detected
- PDF capture didn’t appear: check logs for final‑page detection and see `production2/tmp/pdf`

---

Contributions
- Branch: `fea/calibration-improvements` (current)
- Open a PR to `main` when ready
- Backend endpoint: `POST /api/f3-static` ve `POST /api/tsx/dev-run`
- Davranış:
	1) Statik analiz (etiket, eşanlamlılar, attribute skorlama) + varsa kalibrasyon kayıtlarını kullanır.
	2) Yeterli alan bulunamazsa, TsX dev-run akışıyla LLM destekli gezinme/doldurma devreye alınır.
	3) Doldurma planı üretildiğinde TS3 çalışır; final sayfa/PDF doğrulaması yapılır.

Güçlü Yanlar:
- Hızlı başarım (statik), düşük maliyet; başarısız olduğunda akıllı fallback (LLM).
- Zengin loglar ve “dry-run plan” ile şeffaflık.

<a id="calibration"></a>
## Kalibrasyon (C Modu) — Çok Sayfalı Eşleme
Kalibrasyon paneli, site/iş (host/task) için per-sayfa kalıcı ve deterministik mapping oluşturur. Statik-önce akışı besler; LLM’e daha az bağımlılık sağlar.

Öne Çıkanlar:
- İframe destekli Pick/Live: İmleçle highlight ve tek tıkla seçici yakalama.
- Gerçek-zamanlı doğrulama: Girdi alanı geçerli mi? Anında renk/ikon ve kısa descriptor metni.
- HTML Snippet: Seçilen elementin outerHTML’i panelde genişletilebilir ve kopyalanabilir.
- Actions Listesi: Ruhsat alanlarına benzer arayüz; Label + Selector, Pick/Live, doğrulama, HTML, sürükle-bırak sıra.
- Çok-Sayfa: Page Name, URL Sample (Capture URL), opsiyonel URL Pattern, Page chips (gezinme), “+ Add Next Page”, “Mark as Last Page”.
- Finish Automation: Hızlı sonlandırma (current sayfayı last işaretle + kaydet).
- Finalize to Config: Tüm sayfaları `config.json` → `staticFormMapping.sites[host][task]` altına yazar.

Kaydetme Yapısı (özet):
```jsonc
{
	// geriye dönük uyum için üst seviye alanlar: ilk sayfadan türetilir
	"fieldSelectors": { "plaka_no": "#plateNo", "model_yili": "..." },
	"actions": ["Devam"],
	"executionOrder": ["sasi_no", "motor_no", "plaka_no", "model_yili"],
	"criticalFields": ["plaka_no", "model_yili", "sasi_no", "motor_no"],

	// yeni çok sayfa yapısı
	"pages": [
		{
			"id": "p_...",
			"name": "Form",
			"urlSample": "https://.../traffic-insurance",
			"urlPattern": "traffic-insurance",
			"fieldSelectors": { "plaka_no": "#plateNo" },
			"executionOrder": ["plaka_no"],
			"actionsDetail": [ { "id": "a1", "label": "Devam", "selector": "button[type=submit]" } ],
			"criticalFields": ["plaka_no"],
			"isLast": false
		},
		{
			"id": "p_...",
			"name": "Özet",
			"urlSample": "https://.../summary",
			"fieldSelectors": {},
			"executionOrder": [],
			"actionsDetail": [ { "id": "a2", "label": "Teklif Al", "selector": "#quote" } ],
			"criticalFields": [],
			"isLast": true
		}
	],
	"multiPage": true
}
```

Panel Akışı (özet):
- C butonu → startSession (host/task + ruhsat + adaylar)
- Alan seçimi (Pick/Live) → preview + doğrulama + HTML
- Actions seçimi (Pick/Live) + sıra
- Capture URL, Page Name, Add Next Page / Mark Last Page
- Save Draft → diske `calib/<host>/<task>.json`
- Test Plan (opsiyonel) → “dry-run” doldurma planı
- Finalize to Config → `config.json` altına merge (çok sayfa dahil)

<a id="stateflows-cheatsheet"></a>
## Stateflows Hızlı Şema
Metin formatında özet akışlar ve sözleşme noktaları.

1) F1 — FindHomePage
- Input: current DOM/URL
- Steps: home link/button tespiti → click → bekle
- Output: home reached (heuristic)

2) F2 — GoUserTaskPage (örn. "Yeni Trafik")
- Input: label (task adı), current DOM/URL
- Steps: menü/arama içinde task bağlantısını bul → click → bekle
- Output: task page reached

3) F3 — FillForms Static-First (+ LLM Fallback)
- Input: ruhsat JSON, current DOM/URL, config.staticFormMapping
- Steps:
	- Static analyzer → selectors & order (use calibration if present)
	- If insufficient → TsX dev-run (LLM-assisted) to navigate/fill
	- When mapping ready → TS3 fill, then final check (PDF/summary)
- Output: filled form or reason

4) TsX Loop (Dev)
- Input: command label, html snapshot, executed_action?
- Steps: analyze → decide actions → optionally click one → wait → repeat
- Output: phase, details (mapping_ready | actions list)

5) Calibration (C)
- Input: html/url snapshot, ruhsat JSON
- Steps: startSession → human-guided mapping (fields + actions, multi-page) → save/test/finalize
- Output: calib draft (disk) and config.json site mapping

<a id="deep-links"></a>
## Hızlı Link Rehberi (Deep Links)
- Backend (Flask)
	- Uygulama: [`backend/app.py`](backend/app.py) — Routes, TS1/TS2 uçları, loglar
	- Stateflow ajanı: [`backend/stateflow_agent.py`](backend/stateflow_agent.py) — TS1 (run_ts1_extract), tam akış (stateflow_agent)
	- Bellek/depolama: [`backend/memory_store.py`](backend/memory_store.py), [`backend/file_upload.py`](backend/file_upload.py), [`backend/logging_utils.py`](backend/logging_utils.py)
	- Eski/ek yapılar: [`backend/stateflow.py`](backend/stateflow.py), [`backend/routes.py`](backend/routes.py)
- LLM bileşenleri
	- Ruhsat çıkarımı: [`license_llm/license_llm_extractor.py`](license_llm/license_llm_extractor.py)
	- HTML mapping: [`license_llm/pageread_llm.py`](license_llm/pageread_llm.py)
- WebBot
	- HTML indirme: [`webbot/test_webbot_html_mapping.py`](webbot/test_webbot_html_mapping.py) (readWebPage)
- React UI
	- Giriş sayfası: [`react_ui/index.html`](react_ui/index.html)
	- Yapılandırma: [`react_ui/package.json`](react_ui/package.json), [`react_ui/README.md`](react_ui/README.md)
- Testler
	- Smoke: [`tests/smokeTests/test_smoke_backend.py`](tests/smokeTests/test_smoke_backend.py) — TS1/TS2 doğrulamaları ve JSON yazdırma
	- Smoke terminal özeti: [`tests/smokeTests/conftest.py`](tests/smokeTests/conftest.py)
	- Entegrasyon: [`tests/test_integration_end_to_end.py`](tests/test_integration_end_to_end.py)
- Komut/Scripts
	- Son mapping’i yazdır: [`scripts/show_latest_mapping.py`](scripts/show_latest_mapping.py)
- CI
	- GitHub Actions: [`.github/workflows/ci-smoke.yml`](.github/workflows/ci-smoke.yml)

	<a id="git-flow-pr"></a>
	## Git Flow ve PR Kılavuzu
	- Branch adlandırma
		- feature/<kısa-konu> (örn. feature/ts2-mapping-robust)
		- fix/<kısa-konu> (örn. fix/footer-truncation)
		- chore/<kısa-konu> (örn. chore/ci-smoke)
	- Commit mesajı (öneri)
		- tür(scope): kısa özet — örn. feat(backend): TS2 mapping JSON parse’ını güçlendir
		- Gerekirse alt satırlarda detay; “Refs: #<issue>” eklenebilir.
	- PR açma adımları
		1) Lokal doğrulama: `python -m pytest tests/smokeTests -s -vv` (mapping JSON’da tckimlik/dogum_tarihi/ad_soyad/plaka_no ve actions: click#DEVAM beklenir)
		2) README ve doküman güncellemeleri (API/test/CI davranışı değiştiyse)
		3) PR başlığı: kısa ve eylem odaklı; açıklama: değişiklik özeti + etkilenen modüller
		4) En az 1 reviewer iste (tercihen backend+tests odaklı kişi)

### Continuous Integration (CI)
- GitHub Actions workflow: `.github/workflows/ci-smoke.yml`
- İşler:
	- `smoke`: hızlı, deterministik smoke testler (LLM/ağ stub’lu). Son mapping özeti Job Summary’de.
	- `live-llm`: `OPENAI_API_KEY` mevcutsa gerçek LLM ile `tests/liveTests`.
- Detaylar ve kullanım: `docs/ci_github_actions.md`
		5) CI sonuçlarını kontrol et (Actions → CI - Smoke). PR’a otomatik mapping özeti yorumu düşer.
	- Merge stratejisi
		- Squash and merge önerilir (temiz tarihçe). Branch silinebilir.
	- Sürümleme / Tag (opsiyonel)
		- Anlamlı bir kilometretaşı sonrası `vX.Y.Z` etiketi atılabilir.
		- Üretilen mapping JSON’lar
		- `mapping_summary.json` (fields/actions/preview)
		- `summary.md` (PR yorumuna da eklenir)
- Önerilen komutlar (lokalde):
	- Tüm smoke detaylarını görmek için: `python -m pytest tests/smokeTests -s -vv`
- Jenkins gibi mi çalıştırırım?
	- Eşdeğer “pipeline” yapısı: job = workflow, stage = step (Actions’ta steps)
	- YAML’da ek stage/step ekleyerek bağımlılık kurulumunu, testleri, artifact yüklemeyi yönetirsin.
	- On-prem Jenkins istersen: aynı pytest komutlarını Jenkins pipeline’da çalıştır; artifact arşivlemesi için “Archive the artifacts” ile `memory/TmpData/json2mapping/*.json` ve `ci_artifacts/*` path’lerini ekle.
	- Secrets (OPENAI_API_KEY vb.) GitHub → Settings → Secrets üzerinden Actions’a tanımlanır; Jenkins’te “Credentials” ile benzer mantık.
	- Koşum tetikleme: Jenkins’te “Build Now” analog olarak Actions’ta “Run workflow”.

<a id="logging-error-tmp"></a>
## Loglama, Hata Kodları ve Geçici Klasörler
- Hata kodları: Backend BE-xxxx ve FE (HD-/IDX-/UAH-): `docs/error_codes.md`
- Geçici klasörler: `memory/TmpData/jpgDownload`, `jpg2json`, `json2mapping`

<a id="safety-vmodel"></a>
## Güvenlik ve Emniyet Odaklı Gelişim
V-Model, güvenlik hedefleri, doğrulama ve izlenebilirlik yaklaşımı: `docs/SAFETY_ASSURANCE_AND_TRACEABILITY.md`

## Sorun Giderme (Troubleshooting)
- Backend başlamıyor veya hata ile çıkıyor:
	- Doğru Python sürümü ve bağımlılıkların kurulu olduğundan emin olun: `pip install -r ocr_agent/requirements.txt`
		- Port çakışması olup olmadığını kontrol edin (bu proje backend: 5001).
	- Konsol çıktısındaki traceback’i inceleyin ve eksik paketleri yükleyin.
- React UI derlenmiyor:
	- Node 18+ ve pnpm kurulu olmalı. `pnpm install` sonrası `pnpm dev` ile başlayın.
- Electron (isteğe bağlı) açılmıyor:
	- Electron bağımlılıklarını kurup `pnpm start` ile başlatın; hata durumunda konsolu kontrol edin.

## Lisans ve Katkı
- Lisans: (gerekiyorsa ekleyin)
- Katkı rehberi: (PR kuralları, kod stili vb.)

