# React UI: Component ve Hook Dokümantasyonu

Bu doküman, `react_ui` klasöründeki ana bileşenlerin (component) ve özel hook'ların (custom hook) detaylı açıklamalarını içerir. Her bir dosyanın amacı, props'ları ve kullanım örnekleri özetlenmiştir.

---

## 1. Ana Sayfa: `Index.tsx`
- **Amaç:** Uygulamanın giriş noktasıdır. Tüm state yönetimi, ana layout ve handler fonksiyonlarının bir araya getirildiği yerdir.
- **Kısaca:**
  - State ve iş mantığı burada başlatılır.
  - Tüm ana bileşenler (Header, BrowserView, CommandPanel, Footer) ve layout burada birleştirilir.
  - Handler fonksiyonları ve otomasyon mantığı ayrı hook/component'lere taşınmıştır.

---

## 2. MainLayout Component (`components/MainLayout.tsx`)
- **Amaç:** Tüm ana sayfa düzenini (header, ana içerik, footer) kapsayan, sade ve tekrar kullanılabilir bir layout bileşeni sunar.
- **Props:**
  - Tüm state ve handler fonksiyonları props olarak alınır.
  - Header, BrowserView, CommandPanel ve Footer'ı içerir.
- **Kullanım:**
  - `Index.tsx` içinde tek satırda çağrılır.

---

## 3. useAutomation Custom Hook (`hooks/useAutomation.ts`)
- **Amaç:** Otomasyon ile ilgili tüm state'leri ve temel işlevleri yönetir.
- **Döndürdükleri:**
  - iframeUrl, status, loading, automation, result, uploading, commandLog, fileInputRef ve bunların set fonksiyonları.
- **Kullanım:**
  - `Index.tsx`'te ana state kaynağı olarak kullanılır.

---

## 4. useAutomationHandlers Custom Hook (`components/AutomationHandlers.tsx`)
- **Amaç:**
  - Tüm handler fonksiyonlarını (handleGo, handleIframeLoad, handleAutomation, handleUploadClick, handleFileChange) tek bir yerde toplar.
  - State setter'ları ve props'lar ile birlikte çalışır.
- **Kullanım:**
  - `Index.tsx`'te handler fonksiyonları bu hook'tan alınır.

---

## 5. Header Component (`components/Header.tsx`)
- **Amaç:**
  - Uygulama başlığı, arama çubuğu, tema değiştirici ve dosya yükleme butonlarını içerir.
- **Props:**
  - appName, darkMode, fontStack, address, setAddress, handleGo, loading, automation, handleAutomation, iframeUrl, uploading, handleUploadClick, fileInputRef, handleFileChange

---

## 6. BrowserView Component (`components/BrowserView.tsx`)
- **Amaç:**
  - Web sitesinin gömülü olarak gösterildiği ana alan.
- **Props:**
  - iframeUrl, loading, uploading, darkMode, fontStack, handleIframeLoad, result, style

---

## 7. CommandPanel Component (`components/CommandPanel.tsx`)
- **Amaç:**
  - Komut geçmişi ve otomasyon loglarının tek satırda gösterildiği panel.
- **Props:**
  - commandLog, fontStack, darkMode

---

## 8. Footer Component (`components/Footer.tsx`)
- **Amaç:**
  - Her zaman görünür olan, durum ve iletişim bilgisini gösteren alt bar.
- **Props:**
  - fontStack, status, darkMode

---

## 9. SearchBar Component (`components/SearchBar.tsx`)
- **Amaç:**
  - Google tarzı, modern ve geniş arama çubuğu.
- **Props:**
  - value, onChange, onEnter, loading, disabled, darkMode

---

# Kullanım Akışı ve Bağımlılıklar
- `Index.tsx` → `useAutomation` ile state yönetir, `useAutomationHandlers` ile handler fonksiyonlarını alır.
- Tüm state ve fonksiyonlar `MainLayout`a props olarak aktarılır.
- `MainLayout` → Header, BrowserView, CommandPanel, Footer'ı birleştirir.
- Her bir alt component sadece kendi işlevine odaklanır.

---

# Özet Bağımlılık Diyagramı

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

# Geliştiriciye Notlar
- Her yeni işlev için ayrı bir component veya hook açmak kodun okunabilirliğini ve bakımını kolaylaştırır.
- Tüm state ve handler'lar tek merkezde değil, ilgili component/hook içinde tutulmalıdır.
- Dosya ve fonksiyon isimleri sade ve açıklayıcı olmalıdır.

---

# Ek: Yeni Component veya Hook Eklerken
- `src/components/` veya `src/hooks/` altında yeni dosya açın.
- Props ve dönen değerleri mutlaka TypeScript ile tipleyin.
- Kısa açıklama ve örnek kullanım ekleyin.

---
