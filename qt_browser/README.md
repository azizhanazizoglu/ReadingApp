# qt_browser

PyQt5 tabanlı basit bir web browser arayüzü. Kullanıcı adres çubuğuna URL girer, sayfa ekranda görünür. 'HTML Snapshot Al' butonuyla o anki sayfanın tam HTML'i dosyaya kaydedilir.

- `main.py`: Ana Qt browser uygulaması
- `qt_browser_snapshot.html`: Kaydedilen HTML snapshot (otomatik oluşur)

## Otomasyon User Story
- Kullanıcı browser ile manuel olarak giriş yapar, ana sayfaya kadar ilerler.
- 'Otomasyona Başla' butonuna basınca, ekrandaki HTML LLM'e gönderilir ve mapping sonucu alınır.
- Sonuçlar dosyaya ve terminale yazılır.

## Test
- `test_qt_browser.md` dosyasında manuel test adımları ve senaryoları yer alır.
