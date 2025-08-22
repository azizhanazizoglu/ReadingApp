# Yeni Bir PC'de ReadingApp Kurulum ve Çalıştırma Rehberi

Bu doküman, ReadingApp projesini temiz bir bilgisayara klonladıktan sonra eksiksiz şekilde çalıştırmak için gereken adımları özetler.

---

## 1. Gerekli Yazılımlar
- **Python 3.12+** (https://www.python.org/downloads/)
- **Node.js ve npm** (https://nodejs.org/)
- **Git** (https://git-scm.com/)

## 2. Repoyu Klonla
```sh
git clone https://github.com/azizhanazizoglu/ReadingApp.git
cd ReadingApp
```

## 3. Python Bağımlılıklarını Kur
```sh
pip install -r requirements.txt
```

## 4. React UI ve Electron Bağımlılıklarını Kur
```sh
cd react_ui
npm install
cd ../electron_app
npm install
cd ..
```

## 5. Ortam Değişkenleri (.env)
- Proje kök dizininde `.env` dosyası oluştur.
- API anahtarları ve diğer gizli bilgileri buraya ekle.
- Örnek için `.env.example` dosyasına bakabilirsin (varsa).

## 6. React UI Build ve Electron Masaüstü Uygulamasını Başlat
```sh
cd electron_app
./start_all.ps1
```
- Bu script, React UI'ı build eder ve Electron uygulamasını başlatır.
- Windows dışı sistemlerde React UI'ı elle build edip Electron'u elle başlatabilirsin.

## 7. Testleri Çalıştırmak (Opsiyonel)
```sh
pytest
```

## 8. Notlar
- `node_modules`, `dist`, `__pycache__`, `.env`, test raporları gibi dosyalar git'te yoktur, otomatik oluşur.
- Herkes kendi .env dosyasını oluşturmalı.
- PDF test raporları `tdsp/test_reports/` klasöründe oluşur.

---

Herhangi bir hata veya eksik durumda README.md ve docs klasöründeki diğer dökümanlara bakabilirsin.
