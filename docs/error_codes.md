# Error Code Listesi ve Kaynak Linkleri

Her bir component ve handler için hata kodları, açıklamaları ve ilgili kaynak dosya linkleri burada tutulur. Bu sayede hata loglarında görülen kodun anlamı ve kaynağı kolayca bulunabilir.

| Kod        | Açıklama                                 | Component/Function      | Kaynak Dosya                                      |
|------------|------------------------------------------|------------------------|---------------------------------------------------|
| BV-1001    | BrowserView loading state aktif          | BrowserView            | [BrowserView.tsx](../react_ui/src/components/BrowserView.tsx) |
| BV-1002    | BrowserView uploading state aktif        | BrowserView            | [BrowserView.tsx](../react_ui/src/components/BrowserView.tsx) |
| BV-9001    | BrowserView içinde yakalanan hata        | BrowserView            | [BrowserView.tsx](../react_ui/src/components/BrowserView.tsx) |
| BV-9003    | BrowserView loading state 10sn timeout! Kullanıcıya overlay gösterildi. | BrowserView | [BrowserView.tsx](../react_ui/src/components/BrowserView.tsx) |
| HD-1001    | Go butonuna tıklandı                     | Header                 | [Header.tsx](../react_ui/src/components/Header.tsx)           |
| HD-1002    | Otomasyon başlat butonuna tıklandı       | Header                 | [Header.tsx](../react_ui/src/components/Header.tsx)           |
| HD-1003    | Upload butonuna tıklandı                 | Header                 | [Header.tsx](../react_ui/src/components/Header.tsx)           |
| CP-1001    | CommandPanel render edildi               | CommandPanel           | [CommandPanel.tsx](../react_ui/src/components/CommandPanel.tsx) |
| FT-1001    | Footer render edildi                     | Footer                 | [Footer.tsx](../react_ui/src/components/Footer.tsx)             |
| SB-1001    | SearchBar render edildi                  | SearchBar              | [SearchBar.tsx](../react_ui/src/components/SearchBar.tsx)       |
| SB-1002    | Enter ile arama yapıldı                  | SearchBar              | [SearchBar.tsx](../react_ui/src/components/SearchBar.tsx)       |
| UA-1001    | useAutomation: handleGo çağrıldı         | useAutomation          | [useAutomation.ts](../react_ui/src/hooks/useAutomation.ts)       |
| UA-1002    | useAutomation: handleIframeLoad çağrıldı | useAutomation          | [useAutomation.ts](../react_ui/src/hooks/useAutomation.ts)       |
| UA-1003    | useAutomation: handleAutomation çağrıldı | useAutomation          | [useAutomation.ts](../react_ui/src/hooks/useAutomation.ts)       |
| UA-9001    | useAutomation: Otomasyon başlatılamadı (backend response not ok) | useAutomation | [useAutomation.ts](../react_ui/src/hooks/useAutomation.ts)       |
| UA-9002    | useAutomation: Otomasyon sırasında hata  | useAutomation          | [useAutomation.ts](../react_ui/src/hooks/useAutomation.ts)       |
| UA-9003    | useAutomation: JPEG yükleme başarısız (backend response not ok) | useAutomation | [useAutomation.ts](../react_ui/src/hooks/useAutomation.ts)       |
| UA-9004    | useAutomation: JPEG yüklenirken hata      | useAutomation          | [useAutomation.ts](../react_ui/src/hooks/useAutomation.ts)       |
| UAH-1101   | handleGo: çağrıldı (ana event) | useAutomationHandlers.handleGo | [handleGo.ts](../react_ui/src/hooks/useAutomationHandlers/handleGo.ts) |
| UAH-1110   | handleGo: Aynı URL tekrar girildi, iframe reload için boş string atanıyor (debug) | useAutomationHandlers.handleGo | [handleGo.ts](../react_ui/src/hooks/useAutomationHandlers/handleGo.ts) |
| UAH-1111   | handleGo: Aynı URL tekrar atanarak iframe reload tetiklendi (debug) | useAutomationHandlers.handleGo | [handleGo.ts](../react_ui/src/hooks/useAutomationHandlers/handleGo.ts) |
| UAH-1112   | handleGo: setIframeUrl çağrıldı (debug) | useAutomationHandlers.handleGo | [handleGo.ts](../react_ui/src/hooks/useAutomationHandlers/handleGo.ts) |
| UAH-9101   | handleGo: Adres boş veya geçersiz     | useAutomationHandlers.handleGo | [handleGo.ts](../react_ui/src/hooks/useAutomationHandlers/handleGo.ts) |
| UAH-9102   | handleGo: Beklenmeyen hata           | useAutomationHandlers.handleGo | [handleGo.ts](../react_ui/src/hooks/useAutomationHandlers/handleGo.ts) |
| UAH-1201   | handleIframeLoad: çağrıldı (başarılı event) | useAutomationHandlers.handleIframeLoad | [handleIframeLoad.ts](../react_ui/src/hooks/useAutomationHandlers/handleIframeLoad.ts) |
| UAH-9201   | handleIframeLoad: Beklenmeyen hata   | useAutomationHandlers.handleIframeLoad | [handleIframeLoad.ts](../react_ui/src/hooks/useAutomationHandlers/handleIframeLoad.ts) |
| UAH-1301   | handleAutomation: çağrıldı (başarılı event) | useAutomationHandlers.handleAutomation | [handleAutomation.ts](../react_ui/src/hooks/useAutomationHandlers/handleAutomation.ts) |
| UAH-9301   | handleAutomation: iframeUrl boş       | useAutomationHandlers.handleAutomation | [handleAutomation.ts](../react_ui/src/hooks/useAutomationHandlers/handleAutomation.ts) |
| UAH-9302   | handleAutomation: Ruhsat fotoğrafı yüklenmedi! | useAutomationHandlers.handleAutomation | [handleAutomation.ts](../react_ui/src/hooks/useAutomationHandlers/handleAutomation.ts) |
| UAH-9303   | handleAutomation: Otomasyon başlatılamadı (backend response not ok) | useAutomationHandlers.handleAutomation | [handleAutomation.ts](../react_ui/src/hooks/useAutomationHandlers/handleAutomation.ts) |
| UAH-9304   | handleAutomation: Otomasyon sırasında hata | useAutomationHandlers.handleAutomation | [handleAutomation.ts](../react_ui/src/hooks/useAutomationHandlers/handleAutomation.ts) |
| UAH-1401   | handleUploadClick: çağrıldı (başarılı event) | useAutomationHandlers.handleUploadClick | [handleUploadClick.ts](../react_ui/src/hooks/useAutomationHandlers/handleUploadClick.ts) |
| UAH-9401   | handleUploadClick: Beklenmeyen hata   | useAutomationHandlers.handleUploadClick | [handleUploadClick.ts](../react_ui/src/hooks/useAutomationHandlers/handleUploadClick.ts) |
| UAH-1501   | handleFileChange: Dosya seçilmedi     | useAutomationHandlers.handleFileChange | [handleFileChange.ts](../react_ui/src/hooks/useAutomationHandlers/handleFileChange.ts) |
| UAH-9502   | handleFileChange: JPEG yükleme başarısız (backend response not ok) | useAutomationHandlers.handleFileChange | [handleFileChange.ts](../react_ui/src/hooks/useAutomationHandlers/handleFileChange.ts) |
| UAH-9503   | handleFileChange: JPEG yüklenirken hata | useAutomationHandlers.handleFileChange | [handleFileChange.ts](../react_ui/src/hooks/useAutomationHandlers/handleFileChange.ts) |

> Diğer component ve handler'lar için de aynı şekilde kodlar eklenecek.
