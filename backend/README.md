# Backend (Flask)

Python Flask tabanlı API sunucusu. Upload, otomasyon (TS1), mapping (TS2), state ve log uçları içerir.

## Uçlar
- POST `/api/upload` → JPEG yükle (jpgDownload temizlenir → yeni dosya kaydedilir)
- POST `/api/start-automation` → TS1 başlat (jpg2json temizlenir → LLM JSON kaydedilir)
- POST `/api/test-state-2` → TS2 çalıştır (json2mapping temizlenir → mapping JSON kaydedilir ve saklanır)
- GET `/api/state` → Bellekteki durum ve veriler
- GET `/api/mapping` → Son mapping (memory)
- GET `/api/logs` → Yapılandırılmış log halkası
- GET `/health` → Sağlık kontrolü

## TmpData Temizlik Politikası
- Upload: `memory/TmpData/jpgDownload` klasörü yeni yükleme öncesi temizlenir; yalnızca son JPEG tutulur.
- TS1: `/api/start-automation` öncesi `memory/TmpData/jpg2json` temizlenir; yalnızca son LLM JSON tutulur.
- TS2: `/api/test-state-2` öncesi `memory/TmpData/json2mapping` temizlenir; yalnızca son mapping JSON tutulur (silinmez).

## TS2 Akışı (LLM-only, Heuristik kapalı)
- Frontend (Electron webview) sayfanın DOM’unu alır ve `/api/test-state-2` body’sinde gönderir: `{ url, html, ruhsat_json? }`.
- Backend HTML’i diske kaydeder ve görünür log üretir:
	- `memory/TmpData/webbot2html/page.html`
	- (Varsa) `memory/TmpData/webbot2html/form.html`
	- `memory/TmpData/webbot2html/form_meta.json` (input/select/textarea/button sayıları)
	- `memory/TmpData/webbot2html/page.json` (url, timestamp, length)
- LLM yanıtı code-fence içindeki JSON’dan parse edilir. Heuristik kapalıdır; yalnızca LLM çıktısı kullanılır.
- Mapping sonucu `memory/TmpData/json2mapping/<base>_mapping.json` olarak kaydedilir ve response’ta `path` döner.
- Response, HTML kaydının konumunu da içerir: `html_saved_to`.

Örnek başarılı response:
```
{
	"result": "Mapping kaydedildi",
	"path": ".../memory/TmpData/json2mapping/<base>_mapping.json",
	"html_saved_to": ".../memory/TmpData/webbot2html/page.html"
}
```

Notlar:
- HTML body’de yoksa, backend `readWebPage(url)` ile yalnızca fallback olarak indirir.
- TS2, `ruhsat_json` alanını body’de bulamazsa en son TS1 çıktısını `memory/TmpData/jpg2json` klasöründen otomatik yüklemeyi dener.
- Select/datalist seçenekleri LLM’e gönderilirken `MAX_SELECT_OPTIONS` ile sınırlandırılır.

## Loglama
- Her olay yapılandırılmış olarak loglanır: `level`, `code`, `component`, `message`, `time`, `extra`.
- `GET /api/logs` endpoint’i FE tarafından periyodik çekilir.

Başlıca TS2 log kodları:
- `BE-3001` TS2 çağrısı
- `BE-3001P` payload özeti (url/html uzunluğu)
- `BE-3001A` alan sayımı (input/select/textarea)
- `BE-3001W` HTML diske yazıldı
- `BE-3001W-FORM` form çıkarma uyarısı (opsiyonel hata, devam edilir)
- `BE-3001W-META` meta yazma uyarısı (opsiyonel)
- `BE-3001W-FAIL` HTML kaydı başarısız (yol ve hata mesajı loglanır)
- `BE-3001B` LLM mapping JSON parse OK
- `BE-3001C` LLM mapping JSON parse FAILED (fallback boş mapping)
- `BE-3002` mapping dosyası kaydedildi

## Çalıştırma
```
pip install -r requirements.txt
python backend/app.py  # 0.0.0.0:5001
```

## Ortam Değişkenleri
- `OPENAI_API_KEY`: LLM çağrıları için zorunlu.
- `MAX_SELECT_OPTIONS` (opsiyonel, varsayılan 20): select/datalist seçeneklerinin özetlenmesindeki üst sınır.

## Bilinen Dizinyapısı (absolute path)
- Uygulama, proje kökünü (`PROJECT_ROOT`) baz alır ve tüm TmpData yollarını absolute olarak kullanır. Böylece çalışma dizini değişse bile kayıtlar güvenilirdir.
