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
2. [Sistem Mimarisi (Architecture)](#architecture)
3. [Bileşen Özeti (Components Overview)](#components-overview)
4. [Veri Akışı ve Durum Makinesi (TS1/TS2)](#ts-flow)
5. [Geçici Veri Politikası (TmpData)](#tmpdata-policy)
6. [API Tanımı (Flask Endpoints)](#api)
7. [Frontend (React UI)](#frontend)
8. [Zamanlayıcı (Scheduler)](#scheduler)
9. [LLM Bileşenleri (llm_agent, license_llm)](#llm-components)
10. [WebBot Bileşeni (webbot)](#webbot)
11. [Qt Browser ve Electron](#qt-electron)
12. [Girdi HTML’leri (input_htmls)](#input-htmls)
13. [Test ve İzlenebilirlik](#tests-traceability)
14. [Loglama ve Hata Kodları](#logging-errors)
15. [Kurulum ve Çalıştırma](#setup-run)
16. [Sorun Giderme ve Destek](#troubleshooting)
17. [Belgeler Dizini (docs/ Index)](#docs-index)

<a id="abstract"></a>
## 1) Özet (Abstract)
ReadingApp, ruhsat JPEG → LLM JSON → HTML mapping → form doldurma akışını uçtan uca yöneten modüler bir platformdur. Frontend (React + Vite + TS) ve Backend (Flask) arasında yapılandırılmış loglama ve izlenebilirlik ilkeleri esastır. Geçici veri politikası, her çalıştırmada yalnızca “son” çıktıların kalmasını sağlar.

<a id="architecture"></a>
## 2) Sistem Mimarisi (Architecture)
- Backend (Flask): Routes, stateflow agent, structured logging, in-memory durum (memory)
- Frontend (React + Vite + TS): Header, MainLayout, Log paneli, Geliştirici Modu
- Electron (opsiyonel): Masaüstü paketleme
- İlgili alt bileşenler: `llm_agent`, `license_llm`, `webbot`, `qt_browser`

<a id="components-overview"></a>
## 3) Bileşen Özeti (Components Overview)
- `backend/`: API uçları; TS1/TS2 akışını tetikler; log ve state yönetimi
- `react_ui/`: UI, developer mod butonları (Home, Ts1, Ts2), birleşik log paneli, sabit footer
- `scheduler/`: Basit job scheduler ve adım takibi (waiting → running → done → error)
- `llm_agent/`: OCR/LLM metinlerinden yapılandırılmış veri üretimi için yardımcı bileşen
- `license_llm/`: Ruhsat görüntüsünden LLM ile yapılandırılmış veri çıkarımı
- `webbot/`: HTML analiz ederek alanların doldurulmasını ve ilerlemeyi planlar
- `qt_browser/`: PyQt5 ile basit tarayıcı; HTML snapshot alma ve manuel giriş akışı
- `input_htmls/`: Test ve mapping akışları için HTML örnekleri

<a id="ts-flow"></a>
## 4) Veri Akışı ve Durum Makinesi (TS1/TS2)
Durumlar: başladı → devam ediyor (her job) → tamamlandı | hata
- TS1: JPEG → LLM → JSON (jpg2json’a yazılır; base adı JPG ile eşleşir)
- TS2: Web HTML (webbot) + LLM mapping → JSON (json2mapping’e yazılır)

<a id="tmpdata-policy"></a>
## 5) Geçici Veri Politikası (TmpData)
- Upload: `memory/TmpData/jpgDownload` yeni yükleme öncesi temizlenir → yalnızca son JPEG kalır.
- TS1: `/api/start-automation` öncesi `memory/TmpData/jpg2json` temizlenir → yalnızca son JSON kalır.
- TS2: `/api/test-state-2` öncesi `memory/TmpData/json2mapping` temizlenir → yalnızca son mapping JSON kalır (silinmez).
- Bellek: `memory` içinde son `ruhsat_json`, `html`, `mapping`, `latest_base` tutulur. TS2 gerekirse `jpg2json`’dan fallback ile JSON’u yükleyebilir.

<a id="api"></a>
## 6) API Tanımı (Flask Endpoints)
- POST `/api/upload`: JPEG yükler; `jpgDownload` temizlenir ve yeni dosya kaydedilir.
- POST `/api/start-automation`: TS1’i başlatır; `jpg2json` temizlenir; LLM JSON üretilir ve kaydedilir.
- POST `/api/test-state-2`: TS2’yi tetikler; `json2mapping` temizlenir; mapping JSON üretilir ve kaydedilir (kalıcı).
- GET `/api/state`: Bellekteki son durum döner.
- GET `/api/mapping`: Son mapping (memory) döner.
- GET `/api/logs`: Yapılandırılmış log halkası döner.
- GET `/health`: Sağlık kontrolü.

<a id="frontend"></a>
## 7) Frontend (React UI)
- Header: App adı, arama, upload, otomasyon; Geliştirici Mod butonları (Home, Ts1, Ts2). İnce dikey ayraçlar kaldırılmıştır; sade görünüm.
- MainLayout: Sağdan açılan birleşik log paneli (frontend + backend), footer için compact özet üretir.
- Footer: Sabit 60px yükseklik; tek satır truncation. Türkçe tek tip format: `[BİLGİ|UYARI|HATA|DEBUG] KOD: kısa_metin (klasör/dosya)`; hover’da tam metin `title` ile görülebilir.

<a id="scheduler"></a>
## 8) Zamanlayıcı (Scheduler)
Basit JobScheduler: her adım (llm_extract, wait_for_file, webbot, memory, llm) sırayla çalışır. Her job “waiting → running → done | error” durumlarını raporlar. Hata durumunda akış durdurulur ve kullanıcıya bildirilir.

<a id="llm-components"></a>
## 9) LLM Bileşenleri (llm_agent, license_llm)
- `llm_agent`: OCR metninden yapılandırılmış veri üretimine yardımcı işlevler; örnek kullanım testlerde.
- `license_llm`: Ruhsat görüntüsünden LLM ile alan çıkarımı; `extract_vehicle_info_from_image` ana fonksiyondur.

<a id="webbot"></a>
## 10) WebBot Bileşeni (webbot)
HTML arayüzleri analiz ederek hangi alanların doldurulacağını belirler; LLM ile birlikte form doldurma otomasyonunda kullanılır.

<a id="qt-electron"></a>
## 11) Qt Browser ve Electron
- `qt_browser`: PyQt5 tabanlı basit tarayıcı; manuel giriş sonrası HTML snapshot alır; otomasyon user story’si test dokümanında.
- `electron_app`: React UI build’in masaüstüne gömülmesi için temel yapı (örnek entegrasyon komutları ileride).

<a id="input-htmls"></a>
## 12) Girdi HTML’leri (input_htmls)
Testler ve mapping akışları için örnek HTML’ler (ör. `traffic-insurance.html`, `vehicle-details.html`). WebBot/LLM mapping için kullanılır.

<a id="tests-traceability"></a>
## 13) Test ve İzlenebilirlik
- Test stratejisi ve dosya yolu standartları: `docs/08_test_strategy.md`, `docs/09_test_files_and_paths.md`
- İzlenebilirlik matrisi: `docs/traceability_matrix.md`
- Tüm testler ve PDF özet: `python run_all_tests.py`

<a id="logging-errors"></a>
## 14) Loglama ve Hata Kodları
- Yapılandırılmış log alanları: level, code, component, message, time, extra
- FE/BE kod aralıkları: `docs/error_codes.md`
- Log paneli: sağdan açılır; footer’da compact Türkçe özet gösterilir.

<a id="setup-run"></a>
## 15) Kurulum ve Çalıştırma
Önkoşullar: Python 3.12+, Node.js 18+, pnpm
```
# Backend
pip install -r requirements.txt
python backend/app.py  # http://localhost:5001

# React UI
cd react_ui
pnpm install
pnpm dev

# Electron (opsiyonel)
cd electron_app
pnpm install
pnpm start
```

<a id="troubleshooting"></a>
## 16) Sorun Giderme ve Destek
- Backend başlatma sorunları: bağımlılıkları ve portu (5001) kontrol edin; konsol traceback’ine bakın.
- UI derleme sorunları: Node 18+, pnpm; temiz kuruluma `pnpm install` sonrası `pnpm dev`.
- Destek: azizhanazizoglu@gmail.com

<a id="docs-index"></a>
## 17) Belgeler Dizini (docs/ Index)
- [01_project_overview.md](docs/01_project_overview.md)
- [02_vmodel_and_methodology.md](docs/02_vmodel_and_methodology.md)
- [03_user_stories.md](docs/03_user_stories.md)
- [04_software_requirements.md](docs/04_software_requirements.md)
- [05_architecture_and_components.md](docs/05_architecture_and_components.md)
- [06_data_interfaces_and_variables.md](docs/06_data_interfaces_and_variables.md)
- [07_technologies_and_methods.md](docs/07_technologies_and_methods.md)
- [08_test_strategy.md](docs/08_test_strategy.md)
- [09_test_files_and_paths.md](docs/09_test_files_and_paths.md)
- [10_electron_react_desktop_user_story.md](docs/10_electron_react_desktop_user_story.md)
- [10_qt_browser_user_story.md](docs/10_qt_browser_user_story.md)
- [11_scheduler_and_state_flow.md](docs/11_scheduler_and_state_flow.md)
- [12_llm_agent_integration.md](docs/12_llm_agent_integration.md)
- [12_react_components_and_hooks.md](docs/12_react_components_and_hooks.md)
- [error_codes.md](docs/error_codes.md)
- [FOLDER_STRUCTURE_AND_NAMING_CONVENTION.md](docs/FOLDER_STRUCTURE_AND_NAMING_CONVENTION.md)
- [traceability_matrix.md](docs/traceability_matrix.md)
- [SAFETY_ASSURANCE_AND_TRACEABILITY.md](docs/SAFETY_ASSURANCE_AND_TRACEABILITY.md)

<a id="features-updates"></a>
## Özellikler ve Güncellemeler
Tüm .txt dokümanlar .md’ye taşındı. Detaylar ve derinlemesine anlatımlar için `docs/` klasörüne bakın.

### Neler Yeni (2025-08-25)
- Yapılandırılmış backend loglama (level, code, component, message, time, extra); `/api/logs` ile FE panelde birleşik gösterim
- Ts1 (JPG → LLM → JSON) ve Ts2 (Webbot → Mapping) uçtan uca akışlar; mapping çıktıları `memory/TmpData/json2mapping` altında kalıcı
- Geçici klasör standardı ve temizlik politikası:
	- Upload: `jpgDownload` yeni yükleme öncesi temizlenir; yalnızca son JPEG saklanır.
	- TS1: `/api/start-automation` öncesi `jpg2json` temizlenir; yalnızca son JSON saklanır.
	- TS2: `/api/test-state-2` öncesi `json2mapping` temizlenir; yalnızca son mapping JSON saklanır (silinmez).
- Türkçe state makinesi: “başladı → devam ediyor → tamamlandı | hata”
- Developer Mode: Header’da Home/Ts1/Ts2, kompakt SearchBar, Toaster ve yapılandırılmış log paneli
- Footer: Sabit 60px yükseklik, tek satır compact Türkçe format: `[BİLGİ|UYARI|HATA|DEBUG] KOD: kısa_metin (klasör/dosya)`
- Backend route’ları: `/api/upload`, `/api/start-automation`, `/api/state`, `/api/mapping`, `/api/logs`, `/api/test-state-2`, `/health`

<a id="monorepo-components"></a>
## Monorepo Yapısı ve Bileşenler
- Backend (Flask): `backend/` — Uygulama ve servisler, stateflow, yapılandırılmış loglama
- React UI (Vite + TS): `react_ui/` — Arayüz, geliştirici modu, log paneli
- Electron (opsiyonel): `electron_app/` — Masaüstü paketleme/başlatma
- LLM Agent: `llm_agent/` ve `license_llm/` — LLM/ocr entegrasyonu ve örnek çıkarımlar
- OCR Agent: `ocr_agent/` — OCR/LLM bağımlılıkları (requirements)
	- Gereksinimler: `ocr_agent/requirements.txt`
- Qt Browser (opsiyonel): `qt_browser/`
- Dokümantasyon: `docs/` — Proje genel dokümanları ve izlenebilirlik
	- Giriş: `docs/` dizinindeki ilgili başlıklar

<a id="quick-start"></a>
## Hızlı Başlangıç
Önkoşullar: Python 3.12+, Node.js 18+, pnpm.

1) Backend (Flask)
		- Bağımlılıklar: `pip install -r requirements.txt`
	- Çalıştırma: `python backend/app.py` (varsayılan: http://localhost:5001)

2) React UI
	 - `cd react_ui`
	 - `pnpm install`
	 - `pnpm dev`

3) Electron (opsiyonel)
	 - `cd electron_app`
	 - `pnpm install`
	 - `pnpm start`

Notlar ve troubleshooting için `docs/README.md` ve aşağıdaki Sorun Giderme bölümünü inceleyin.

<a id="api-summary-contracts"></a>
## API Özeti ve Sözleşmeler
- POST `/api/upload` → JPEG yükle
- POST `/api/start-automation` → Ts1 başlatır
- POST `/api/test-state-2` → Ts2 (webbot + mapping) test
- GET `/api/state` → state
- GET `/api/mapping` → son mapping
- GET `/api/logs` → yapılandırılmış loglar
- GET `/health` → sağlık kontrolü

Tam sözleşmeler ve akışlar: `docs/12_llm_agent_integration.md`.

## Test, Raporlama ve İzlenebilirlik
- Test stratejisi: `docs/08_test_strategy.md`
- Test dosyaları ve yolları: `docs/09_test_files_and_paths.md`
- İzlenebilirlik matrisi: `docs/traceability_matrix.md`
- Tüm testleri çalıştırma ve PDF özet: `python run_all_tests.py`

<a id="smoke-tests"></a>
## Smoke Tests (Hızlı Sağlık Kontrolü)
Smoke test, sistemin en kritik uçlarının “ayakta” olduğunu hızlıca doğrulayan, küçük ve uçtan uca mini testlerdir. Amaç; derin senaryolardan ziyade, temel servislerin kalkıp kalkmadığını ve basit bir akışın hata vermeden çalıştığını görmek. Bu proje için smoke testler:

- Konum: `tests/smokeTests/`
- Kapsam ve doğrulamalar:
	- GET `/health` → 200 ve `{ "status": "ok" }`
	- POST `/api/upload` → Basit bir JPEG yüklemesi kabul ediliyor mu? Dosya `memory/TmpData/jpgDownload` altına kaydoluyor mu?
	- POST `/api/start-automation` → TS1 akışı (JPEG→JSON) çalışıyor mu? `memory/TmpData/jpg2json` altında JSON üretiliyor mu? (OpenAI çağrısı monkeypatch ile taklit edilir.)
	- POST `/api/test-state-2` → Basit bir HTML + JSON ile mapping üretilip `memory/TmpData/json2mapping` altına kaydediliyor mu? (LLM çağrısı monkeypatch ile taklit edilir; test, code-fenced JSON’dan sağlam parse’ı da doğrular.)
- Dış bağımlılıklar: OpenAI ve internet erişimi gerektirmez; testler LLM fonksiyonlarını monkeypatch ile taklit eder ve offline, deterministik çalışır.
- Disk etkileri: `memory/TmpData` altında küçük JSON dosyaları yazılır ve eski mapping’ler temizlenebilir (kalıcı veri etkisi yoktur).

Hedef sayfa (referans):
- https://preview--screen-to-data.lovable.app/traffic-insurance

TS2 Doğrulama kriterleri (acceptance):
- Mapping JSON içinde şu alanlar bulunmalı ve input seçicilerine eşlenmiş olmalı:
	- `tckimlik` → örn. `input#identity`
	- `dogum_tarihi` → örn. `input#birthDate`
	- `ad_soyad` → örn. `input#name`
	- `plaka_no` → örn. `input#plate`
- Actions içinde `click#DEVAM` olmalı.

Tek komut (Windows PowerShell) — tam JSON çıktısı terminale yazdırılır:
```
python -m pytest tests/smokeTests -s -vv
```

Koşum sonunda “Smoke Mapping Output” bölümünde son mapping dosya yolu ve pretty-printed JSON görüntülenir.

Örnek çıktı (özetlenmiş):
```
----------------------------- Smoke Mapping Output -----------------------------
Latest mapping file: memory/TmpData/json2mapping/<...>_mapping.json
Fields: ad_soyad, dogum_tarihi, plaka_no, tckimlik
Actions: ['click#DEVAM']
Full JSON:
{
	"field_mapping": {
		"tckimlik": "input#identity",
		"dogum_tarihi": "input#birthDate",
		"ad_soyad": "input#name",
		"plaka_no": "input#plate"
	},
	"actions": ["click#DEVAM"]
}
```

CI
- GitHub Actions, main dalına push/PR geldiğinde smoke testleri çalıştırır ve son mapping JSON’u bir artifact olarak yükler.
- Workflow: `.github/workflows/ci-smoke.yml`

Jenkins tecrübesi olanlar için GitHub Actions kullanım ipuçları
- Nerede göreceğim?
	- Repo sayfasında “Actions” sekmesinden tüm koşumları görebilirsin.
	- PR açarsan, PR üzerinde workflow sonucu ve eklenen otomatik yorum (mapping özeti) görünür.
- Nasıl tetiklerim?
	- Push veya Pull Request ile otomatik tetiklenir.
	- Manuel tetikleme için “Actions” → “CI - Smoke” → “Run workflow”.
- Sonuçları nasıl incelerim?
	- Job loglarında pytest çıktıları ve “Smoke Mapping Output” özeti var.
	- Artifacts bölümünden `json2mapping-<branch>-<sha>` paketini indir; içinde:

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

