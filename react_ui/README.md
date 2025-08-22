# Zirve Sigorta Frontend

Bu proje, modern bir React (Vite + TypeScript) arayüzüdür. Allianz temalı, gece/gündüz moduna duyarlı ve kullanıcıdan web sitesi adresi alıp iframe içinde gösteren bir frontend sunar.

## Kullanım

- Bu klasör **sadece frontend arayüzünü** içerir.
- Backend işlemleri (API, otomasyon, veri işleme vb.) senin VS Code agent’in veya başka bir backend tarafından sağlanmalıdır.
- Frontend ile backend arasında HTTP, websocket veya başka bir iletişim yöntemiyle bağlantı kurabilirsin.

## Kurulum

1. Bağımlılıkları yükle:
   ```
   npm install
   ```
2. Geliştirme sunucusunu başlat:
   ```
   npm run dev
   ```
3. Build almak için:
   ```
   npm run build
   ```
   Çıktı `dist/` klasörüne yazılır.

## Entegrasyon

- Build edilen dosyaları (`dist/` klasörü) Python, Qt, Electron veya başka bir masaüstü uygulamasına gömerek kullanabilirsin.
- Backend ile entegrasyon için, frontend’den API çağrıları veya mesajlaşma yapılabilir.

## Özellikler

- Allianz vektör logosu, gece/gündüz moduna göre otomatik renk değiştirir.
- Kullanıcıdan web sitesi adresi alır ve iframe’de gösterir.
- “Git” ve şimşek ikonlu otomasyon başlatma butonları üst menüde bulunur.
- Modern, responsive ve Apple tarzı bir tasarıma sahiptir.
- JPEG ruhsat fotoğrafı yükleme (upload butonu)
- Web sitesi adresi girip gömme (iframe)
- Otomasyon başlatma ve sonuçları görme

## Build ve Çalıştırma
1. `npm install`
2. `npm run build`
3. Electron ile masaüstü uygulamasında kullanmak için ana dizine dönüp `electron_app` klasöründe `npm start` çalıştırın.

## Geliştirici Notları
- Her React değişikliğinden sonra tekrar build alın.
- Upload edilen dosya backend'e `/api/upload` ile gönderilir.
- Tüm yeni UI fonksiyonları build sonrası Electron'da görünür.

## Not

- Backend işlemleri bu projede yer almamaktadır. Lütfen backend’i kendi agent’iniz ile sağlayınız.