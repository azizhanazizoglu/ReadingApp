# How to Start: ReadingApp Kurulum ve Çalıştırma Rehberi

Bu rehber, ReadingApp projesini temiz bir bilgisayara indirip, React/Electron arayüzü ve Python backend ile eksiksiz çalıştırmak için gereken adımları içerir.

---

## 1. Github Reposunu Klonla
```sh
git clone https://github.com/azizhanazizoglu/ReadingApp.git
cd ReadingApp
```

## 2. Python Ortamı ve Bağımlılıkları
```sh
# (Opsiyonel) Conda ortamı oluştur
conda create -n sigorta python=3.12 -y
conda activate sigorta

# Gerekli Python paketlerini yükle
pip install -r requirements.txt
```

## 3. .env Dosyası Oluştur
- Proje kök dizininde `.env` dosyası oluştur.
- OpenAI API anahtarını ve diğer gizli bilgileri buraya ekle:
```env
OPENAI_API_KEY=senin_anahtarın
```

## 4. React UI Kurulumu ve Build
```sh
cd react_ui
npm install
npm run build
cd ..
```

## 5. Electron Masaüstü Uygulamasını Başlat
```sh
cd electron_app
./start_all.ps1
```
- Script otomatik olarak React UI'ı build eder ve Electron uygulamasını başlatır.

## 6. Testleri Çalıştırmak (Opsiyonel)
```sh
pytest
```

## 7. Notlar
- `node_modules`, `dist`, `__pycache__`, `.env`, test raporları gibi dosyalar git'te yoktur, otomatik oluşur.
- Herkes kendi .env dosyasını oluşturmalı.
- PDF test raporları `tdsp/test_reports/` klasöründe oluşur.

---

Daha fazla bilgi için `README.md` ve `docs/` klasörüne bakabilirsin.
