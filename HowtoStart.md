# How to Start: ReadingApp Kurulum ve Çalıştırma Rehberi

Bu rehber, ReadingApp’i Windows PowerShell ortamında uçtan uca çalıştırmak, hızlı test etmek ve CI sonuçlarını görmek için gereken komutları tek sayfada sunar.

---

## 0) Önkoşullar
- Windows 10/11, PowerShell
- Python 3.12+
- Node.js 18+
- Git (ve isteğe bağlı pnpm)

## 1) Reponun İndirilmesi
```powershell
# Klasörü seç ve klonla
git clone https://github.com/azizhanazizoglu/ReadingApp.git
cd ReadingApp
```

## 2) Python Ortamı ve Bağımlılıklar
```powershell
# (Opsiyonel) Conda ile izole ortam
# conda create -n readingapp python=3.12 -y; conda activate readingapp

# Proje bağımlılıkları
pip install -r requirements.txt
```

## 3) .env (İsteğe Bağlı ama TS1 için Gerekli)
- Kök dizinde `.env` oluşturun.
- TS1 (JPEG→LLM→JSON) için OpenAI anahtarı gereklidir; Smoke testlerde gerekmez.
```powershell
# .env içeriği örnek
# OPENAI_API_KEY=senin_anahtarin
```

## 4) Backend’i Başlat (Flask)
```powershell
python backend/app.py  # http://localhost:5001
```

## 5) React UI’ı Başlat (Geliştirme)
```powershell
cd react_ui
# pnpm önerilir ama npm de olur
# pnpm install; pnpm dev
npm install; npm run dev
```
- Varsayılan dev adresi: http://localhost:5173
- UI kapatmak için Ctrl+C, sonra `cd ..` ile proje köküne dönebilirsiniz.

## 6) Electron (İsteğe Bağlı Masaüstü)
- Tek komut (build + electron):
```powershell
./electron_app/start_all.ps1
```
- Manuel (React build + Electron):
```powershell
# React build
cd react_ui; npm run build; cd ..
# Electron
cd electron_app; npm install; npm start
```

## 7) Hızlı Sağlık & Smoke Testleri
- Backend açıkken, aşağıdaki komut map JSON’unu terminale yazar:
```powershell
python -m pytest tests/smokeTests -s -vv
```
- En sonda “Smoke Mapping Output” bölümünde:
	- Son json2mapping dosya yolu
	- Fields & Actions
	- Pretty-printed full JSON

Ek yardımcı:
```powershell
python scripts/show_latest_mapping.py  # Son mapping’i yazdırır
```

## 8) Uçtan Uca Mini Akış (API ile)
- Aşağıdaki örneklerde PowerShell kullanılır. Backend: http://localhost:5001

1) JPEG Yükle (jpgDownload temizlenir ve dosya kaydedilir)
```powershell
# Windows’ta curl mevcuttur; multipart için uygundur
curl -F "file=@C:\\tam\_yol\_resim.jpg" http://localhost:5001/api/upload
```

2) TS1 Başlat (JPEG→JSON, jpg2json’a yazar)
```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:5001/api/start-automation
```

3) TS2 Çalıştır (HTML+JSON→mapping, json2mapping’e yazar)
```powershell
# TS2, body'deki url'den HTML indirir; ruhsat_json yoksa bellektekini ya da jpg2json’daki son JSON’u kullanır
Invoke-RestMethod -Method Post -Uri http://localhost:5001/api/test-state-2 -ContentType "application/json" -Body '{"url":"https://preview--screen-to-data.lovable.app/traffic-insurance"}'
```
- Dönen yanıtta `path` alanında mapping JSON dosya yolunu görürsünüz.

4) Durum/Log görüntüleme
```powershell
Invoke-RestMethod http://localhost:5001/health
Invoke-RestMethod http://localhost:5001/api/state
Invoke-RestMethod http://localhost:5001/api/mapping
Invoke-RestMethod http://localhost:5001/api/logs
```

## 9) Klasör Politikası (TmpData)
- memory/TmpData/jpgDownload: Upload öncesi temizlenir, sadece son JPEG kalır.
- memory/TmpData/jpg2json: TS1 öncesi temizlenir, sadece son JSON kalır.
- memory/TmpData/json2mapping: TS2 öncesi temizlenir, sadece son mapping kalır (silinmez, kalıcı saklanır).

## 10) CI (GitHub Actions) ve Jenkins Benzeri Çalıştırma
- GitHub Actions otomatik tetikleme: push/PR/workflow_dispatch
- Workflow: `.github/workflows/ci-smoke.yml`
- Neler yapar:
	- Smoke testleri çalıştırır, mapping özetini (fields/actions/full JSON) job summary ve PR yorumuna ekler.
	- `json2mapping-<branch>-<sha>` artifact olarak mapping JSON ve özet dosyalarını yükler.
- Nerede görürüm?
	- Repo → Actions → “CI - Smoke” koşumları
	- PR sayfasında otomatik yorum/özet
- Jenkins gibi çalıştırmak istersen:
	- Adımlar: `pip install -r requirements-ci.txt` ve `python -m pytest tests/smokeTests -s -vv`
	- Artifact arşivi: `memory/TmpData/json2mapping/*.json` ve `ci_artifacts/*`
	- Secrets: Jenkins Credentials ya da GitHub Secrets (OPENAI_API_KEY vs.)

## 11) Sık Karşılaşılan Sorunlar
- Backend hemen kapanıyor / hata veriyor:
	- Eksik paket: `pip install -r requirements.txt`
	- Port çakışması 5001 → farklı portla çalıştırmak için `backend/app.py` içinden `app.run(..., port=5001)` değerini değiştirin.
- TS1 hata veriyor: `.env` içinde `OPENAI_API_KEY` yok; Smoke testler için gerekmiyor ama gerçek TS1 için zorunlu.
- TS2 boş mapping üretiyor:
	- Smoke test ile doğrulayın (`-s -vv`), real LLM yerine stub kullanır.
	- Gerçek akışta mapping JSON code-fence çıkarımı yapılır; yine de boşsa HTML’i ve LLM çıktısını kontrol edin.

---

Daha derin dokümantasyon için `README.md` ve `docs/` klasörünü inceleyin. Küçük bileşenlere gitmek için README’deki “Hızlı Link Rehberi (Deep Links)” bölümünü kullanın.
