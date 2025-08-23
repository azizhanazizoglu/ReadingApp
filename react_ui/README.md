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


---

# Teknik Mimarî ve Component/Hook Akışı

## Ana Component ve Hook Yapısı

- **Index.tsx**: Uygulamanın giriş noktası, tüm state ve handler yönetimi burada başlar.
- **useAutomation (hook)**: Otomasyon state ve temel işlevleri yönetir.
- **useAutomationHandlers (hook)**: Tüm handler fonksiyonlarını (go, upload, otomasyon, iframe load) tek yerde toplar.
- **MainLayout**: Header, BrowserView, CommandPanel, Footer gibi ana bileşenleri birleştirir.
- **Header**: Uygulama başlığı, arama çubuğu, tema değiştirici ve upload butonları.
- **BrowserView**: Web sitesinin gömülü olarak gösterildiği ana alan.
- **CommandPanel**: Komut geçmişi ve otomasyon loglarının tek satırda gösterildiği panel.
- **Footer**: Her zaman görünür olan, durum ve iletişim bilgisini gösteren alt bar.
- **SearchBar**: Google tarzı, modern ve geniş arama çubuğu.

### Akış Diyagramı
```
Index.tsx
   ├─ useAutomation (hook)
   ├─ useAutomationHandlers (hook)
   └─ MainLayout
            ├─ Header
            ├─ BrowserView
            ├─ CommandPanel
            └─ Footer
```

---

## Geliştiriciye Notlar
- Her yeni işlev için ayrı bir component veya hook açmak kodun okunabilirliğini ve bakımını kolaylaştırır.
- Tüm state ve handler'lar tek merkezde değil, ilgili component/hook içinde tutulmalıdır.
- Dosya ve fonksiyon isimleri sade ve açıklayıcı olmalıdır.
- Yeni component veya hook eklerken mutlaka TypeScript ile tipleyin ve kısa açıklama ekleyin.

---

## Detaylı Component ve Hook Açıklamaları

Daha fazla detay ve tüm props ile kullanım örnekleri için `src/COMPONENTS_AND_HOOKS.md` dosyasına bakınız.

---

- Backend işlemleri bu projede yer almamaktadır. Lütfen backend’i kendi agent’iniz ile sağlayınız.