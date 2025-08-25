# Smoke Tests

Smoke test, sistemin en kritik uçlarının “ayakta” olduğunu hızlıca doğrulayan, küçük ve uçtan uca mini testlerdir. Amaç; derin senaryoları kapsamaktan çok, temel servislerin kalkıp kalkmadığını, basit bir akışın hata vermeden çalıştığını görmek.

Bu klasördeki smoke testler:
- Flask backend’in çalıştığını ve önemli endpoint’lerin yanıt verdiğini doğrular.
- Dış servislere (OpenAI, internet) bağımlılığı KALDIRMAK için LLM fonksiyonlarını monkeypatch ile taklit eder.
- Hızlı, offline ve deterministik çalışır.

Neleri test ediyoruz?
- GET /health → 200 ve {"status": "ok"}
- POST /api/upload → Basit bir JPEG yüklemesi kabul ediliyor mu?
- POST /api/start-automation → TS1 akışı monkeypatch ile “başarılı” simüle ediliyor mu?
- POST /api/test-state-2 → Basit bir HTML + JSON ile mapping üretilip diske kaydediliyor mu? (LLM çağrısı taklit edilir)

Nasıl çalıştırılır?
- Windows PowerShell için örnek:

```
python -m pytest tests/smokeTests -q
```

Notlar:
- Bu smoke testler, OpenAI API anahtarına ihtiyaç duymaz (LLM çağrıları taklit edilmiştir).
- Testler diske `memory/TmpData` altında küçük JSON dosyaları yazabilir ve eski mapping’leri temizleyebilir.
