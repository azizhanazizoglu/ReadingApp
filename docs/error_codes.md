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

## Backend Log Kodları

| Kod     | Açıklama                                             | Component/Function        | Kaynak Dosya                                 |
|---------|------------------------------------------------------|---------------------------|----------------------------------------------|
| BE-1001 | /api/upload isteği alındı                            | file_upload.handle_file_upload | [file_upload.py](../backend/file_upload.py) |
| BE-1002 | Yüklenen dosya adı                                   | file_upload.handle_file_upload | [file_upload.py](../backend/file_upload.py) |
| BE-1003 | Dosya jpgDownload klasörüne kaydedildi               | file_upload.handle_file_upload | [file_upload.py](../backend/file_upload.py) |
| BE-9001 | Upload sırasında beklenmeyen hata                    | file_upload.handle_file_upload | [file_upload.py](../backend/file_upload.py) |
| BE-2001 | /api/start-automation isteği alındı                  | app.start_automation       | [app.py](../backend/app.py)                 |
| BE-2002 | stateflow_agent thread başlatıldı                    | app.start_automation       | [app.py](../backend/app.py)                 |
| BE-9002 | Otomasyon başlatılırken hata                         | app.start_automation       | [app.py](../backend/app.py)                 |
| BE-2101 | /api/state isteği alındı                             | app.get_state              | [app.py](../backend/app.py)                 |
| BE-3001 | /api/test-state-2 çağrıldı (Webbot -> Mapping)       | app.test_state_2           | [app.py](../backend/app.py)                 |
| BE-3002 | Mapping kaydedildi                                   | app.test_state_2           | [app.py](../backend/app.py)                 |
| BE-9301 | /api/test-state-2 sırasında hata                     | app.test_state_2           | [app.py](../backend/app.py)                 |
| BE-4001 | stateflow_agent thread started                       | stateflow_agent            | [stateflow_agent.py](../backend/stateflow_agent.py) |
| BE-4002 | Scheduler'a işler eklendi                            | stateflow_agent            | [stateflow_agent.py](../backend/stateflow_agent.py) |
| BE-4003 | Scheduler tüm işleri çalıştırıyor                    | stateflow_agent            | [stateflow_agent.py](../backend/stateflow_agent.py) |
| BE-4004 | stateflow_agent tüm işleri tamamladı                 | stateflow_agent            | [stateflow_agent.py](../backend/stateflow_agent.py) |
| BE-4101 | LLM extract job başladı (JPEG aranıyor)              | stateflow_agent            | [stateflow_agent.py](../backend/stateflow_agent.py) |
| BE-4102 | Son JPEG bulundu                                     | stateflow_agent            | [stateflow_agent.py](../backend/stateflow_agent.py) |
| BE-4103 | LLM extractor çağrılıyor                             | stateflow_agent            | [stateflow_agent.py](../backend/stateflow_agent.py) |
| BE-4104 | LLM yanıtı alındı (debug)                            | stateflow_agent            | [stateflow_agent.py](../backend/stateflow_agent.py) |
| BE-4105 | LLM JSON çıktısı hazır                               | stateflow_agent            | [stateflow_agent.py](../backend/stateflow_agent.py) |
| BE-4106 | JSON dosyası jpg2json klasörüne kaydedildi           | stateflow_agent            | [stateflow_agent.py](../backend/stateflow_agent.py) |
| BE-4201 | Webbot HTML içerik alındı                            | stateflow_agent            | [stateflow_agent.py](../backend/stateflow_agent.py) |
| BE-4301 | Mapping JSON json2mapping klasörüne kaydedildi       | stateflow_agent            | [stateflow_agent.py](../backend/stateflow_agent.py) |
| BE-9101 | JSON kaydetme başarısız; raw txt olarak kaydedildi   | stateflow_agent            | [stateflow_agent.py](../backend/stateflow_agent.py) |
| BE-9102 | LLM extraction veya dosya kaydı sırasında hata       | stateflow_agent            | [stateflow_agent.py](../backend/stateflow_agent.py) |
| BE-9103 | Mapping JSON kaydedilemedi                           | stateflow_agent            | [stateflow_agent.py](../backend/stateflow_agent.py) |
| BE-9104 | stateflow_agent thread çöktü                         | stateflow_agent            | [stateflow_agent.py](../backend/stateflow_agent.py) |
| BE-9105 | stateflow_agent exception traceback                  | stateflow_agent            | [stateflow_agent.py](../backend/stateflow_agent.py) |

## Frontend Ek Kodlar

| Kod        | Açıklama                                | Component            |
|------------|-----------------------------------------|----------------------|
| IDX-TS2-200| Index: Ts2 başarılı, mapping kaydedildi | Index.tsx            |
| IDX-TS2-500| Index: Ts2 hata                         | Index.tsx            |
