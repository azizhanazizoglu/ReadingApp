# qt_browser/test_qt_browser.md

## Manuel Test Adımları

1. `pip install PyQt5 PyQtWebEngine` komutları ile gerekli paketleri yükleyin.
2. `python qt_browser/main.py` komutunu çalıştırın.
3. Açılan pencerede adres çubuğuna bir URL girin ve Enter'a basın.
4. Sayfa yüklendikten sonra:
   - 'HTML Snapshot Al' butonuna basarsanız, o anki sayfanın HTML'i `qt_browser_snapshot.html` olarak kaydedilir.
   - 'Otomasyona Başla' butonuna basarsanız, o anki sayfanın HTML'i LLM mapping pipeline'ına gönderilir ve sonuç `qt_browser_llm_mapping.json` dosyasına kaydedilir.
5. Terminalde mapping sonucu ve hata mesajlarını görebilirsiniz.

## Otomasyon User Story
- Kullanıcı browser ile manuel olarak giriş yapar, ana sayfaya kadar ilerler.
- 'Otomasyona Başla' butonuna basınca, ekrandaki HTML LLM'e gönderilir ve mapping sonucu alınır.
- Sonuçlar dosyaya ve terminale yazılır.
