# ReadingApp Documentation

This documentation provides a professional overview of the ReadingApp architecture, requirements, components, data interfaces, and development methodology. The project is designed for robust, flexible, and maintainable web form automation using LLMs and modular Python components.

## Table of Contents
1. Project Overview
2. V-Model & Development Methodology
3. User Stories
4. Software Requirements
5. System Architecture & Components
6. Data Interfaces & Variable Definitions
7. Technologies & Methods Used
8. Test Strategy

---
## Masaüstü Otomasyon Uygulaması (Electron + React)

### Kullanılan Teknolojiler
- React: Modern kullanıcı arayüzü
- Electron: React uygulamasını masaüstü (.exe) olarak çalıştırır
- PowerShell Script: Tek komutla build ve başlatma

### Kurulum ve Çalıştırma
1. Node.js ve npm kurulu olmalı (https://nodejs.org/)
2. Terminalde aşağıdaki komutları çalıştırın:
   - React build ve Electron başlatma için:
     ```powershell
     cd electron_app
     ./start_all.ps1
     ```
   - Script otomatik olarak React UI'ı build eder, Electron bağımlılıklarını yükler ve masaüstü uygulamasını başlatır.

### Script Detayı
- `electron_app/start_all.ps1`: Tüm işlemleri otomatik yapar.
- React build çıktısı: `react_ui/dist` klasöründe oluşur.
- Electron ana dosyası: `electron_app/main.js`

### Notlar
- Ortam değişkenlerinde `C:\Program Files\nodejs` mutlaka Path'e eklenmiş olmalı.
- İlk çalıştırmada internet bağlantısı gerekebilir (npm install için).
- Hata alırsanız terminaldeki uyarıları kontrol edin.

---
## Electron + React Desktop App Geliştirme ve Çalıştırma

### Geliştirici Modunda Çalıştırma
1. React UI'da değişiklik yapmak için önce şu adımları izleyin:
   - `cd react_ui`
   - `npm run build` (Her değişiklikten sonra build alınmalı)
2. Electron masaüstü uygulamasını başlatmak için:
   - `cd ../electron_app`
   - `npm start`

### Notlar
- React UI'da yeni butonlar veya arayüz ekleyebilirsiniz. Her değişiklikten sonra tekrar build alın.
- Electron uygulaması otomatik olarak güncel React build'ini yükler.
- Terminalde görülen `[ERROR:CONSOLE(1)] "Request Autofill.enable failed..."` gibi uyarılar Chromium tabanlı Electron'da önemsizdir, uygulamanın çalışmasına engel değildir.
- Diğer Python backend/agent ve API bileşenleri ile entegrasyon için REST API kullanılmaya devam edilir.

---
## Masaüstü Uygulama (Electron + React) Özellikleri ve Build Adımları

### Özellikler
- Modern React tabanlı arayüz
- JPEG ruhsat fotoğrafı yükleme (upload butonu ile)
- Web sitesi adresi girip gömme (iframe)
- Otomasyon başlatma (backend ile entegrasyon)
- Sonuçları ve logları arayüzde görme

### Build ve Çalıştırma
1. React UI'da değişiklik yaptıktan sonra:
   - `cd react_ui`
   - `npm install` (ilk kurulumda veya güncellemede)
   - `npm run build`
2. Electron masaüstü uygulamasını başlatmak için:
   - `cd ../electron_app`
   - `npm install` (ilk kurulumda)
   - `npm start`

### Notlar
- Upload edilen JPEG dosyası backend'e (`/api/upload`) gönderilir.
- Tüm yeni React fonksiyonları ve butonlar build sonrası Electron'da görünür.
- Hatalar ve uyarılar terminalde veya Electron penceresinde görülebilir.
- Diğer tüm entegrasyonlar için REST API kullanılır.

---
