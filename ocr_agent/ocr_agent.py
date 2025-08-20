# ocr_agent/ocr_agent.py
# Türk araç ruhsatı fotoğrafından temel bilgileri çıkaran OCR agent
import os
import json
import re
from typing import Dict, Any
import pytesseract
from PIL import Image, ImageOps, ImageEnhance

# Ruhsattan çıkarılacak alanlar (bazıları default, bazıları OCR ile)
DEFAULT_OCR_RESULT = {
    "tckimlik": "35791182456",  # Ruhsatta yok, default
    "dogum_tarihi": "05.03.1994",  # Ruhsatta yok, default
    "ad_soyad": "Aziz Serdar",  # Ruhsatta yok, default
    "plaka_no": None,
    "marka": None,
    "model_yili": None,
    "tescil_tarihi": None,
    "belge_seri": "WF0DXXSKR8R2222222",  # Ruhsatta yok, default
    "sasi_no": None
}

def extract_ruhsat_info(image_path: str) -> Dict[str, Any]:
    """
    Türk araç ruhsatı fotoğrafından temel bilgileri OCR ile çıkarır.
    """
    # Görüntü ön işleme: gri ton, kontrast artırma, threshold
    img = Image.open(image_path)
    img = ImageOps.grayscale(img)
    img = ImageEnhance.Contrast(img).enhance(2.0)
    img = img.point(lambda x: 0 if x < 140 else 255, '1')

    # OCR parametreleri: Türkçe, psm 6 (satır satır okuma)
    text = pytesseract.image_to_string(img, lang='tur', config='--psm 6')
    print("OCR ham metin:\n", text)

    result = DEFAULT_OCR_RESULT.copy()
    lines = text.split('\n')
    # Plaka: ilk 12 satırda, harf ve rakam karışımı, 2 rakam + harf + rakam toleranslı regex
    for l in lines[:12]:
        # Türk plakası: 2 rakam, 1-3 harf, 2-4 rakam (aralarda boşluk olabilir)
        plaka_match = re.search(r'\b\d{2}\s*[A-ZÇĞİÖŞÜ]{1,3}\s*\d{2,4}\b', l.replace('|','I'))
        if plaka_match:
            result['plaka_no'] = plaka_match.group(0)
            break
        # Alternatif: satırda hem rakam hem harf varsa ve uzunluğu 6-10 arasıysa
        words = l.split()
        for word in words:
            if (sum(c.isdigit() for c in word) >= 2 and sum(c.isalpha() for c in word) >= 1 and 6 <= len(word) <= 10):
                result['plaka_no'] = word
                break

    # Marka: MARKA/MARKASI veya MODELİ satırında ve bir sonraki satırda yaygın marka isimlerini ara
    marka_list = ['RENAULT', 'FORD', 'FIAT', 'TOYOTA', 'VOLKSWAGEN', 'OPEL', 'PEUGEOT', 'CITROEN', 'HYUNDAI', 'HONDA', 'MERCEDES', 'BMW', 'NISSAN', 'KIA', 'SEAT', 'SKODA', 'DACIA', 'SUZUKI', 'MAZDA', 'MITSUBISHI']
    for i, l in enumerate(lines):
        if 'MARKA' in l or 'MODELİ' in l or 'MODELI' in l:
            # Satırda marka var mı bak
            for marka in marka_list:
                if marka in l:
                    result['marka'] = marka
                    break
            # Sonraki satırda marka var mı bak
            if i+1 < len(lines):
                for marka in marka_list:
                    if marka in lines[i+1]:
                        result['marka'] = marka
                        break
            break
    # Alternatif: metnin tamamında marka ara
    if not result['marka']:
        for marka in marka_list:
            if marka in text:
                result['marka'] = marka
                break

    # Model yılı: 4 haneli, 1980-2030 arası bir sayı
    model_match = re.search(r'\b(19\d{2}|20[0-2]\d|2030)\b', text)
    if model_match:
        result['model_yili'] = model_match.group(0)

    # Tescil tarihi: gg.aa.yyyy veya gg/aa/yyyy
    tescil_match = re.search(r'(\d{2}[./]\d{2}[./]\d{4})', text)
    if tescil_match:
        result['tescil_tarihi'] = tescil_match.group(1)

    # Şasi no: 17 karakterli, harf ve rakam karışık (ör: VF1LB240531754309)
    sasi_match = re.search(r'\b[A-HJ-NPR-Z0-9]{17}\b', text)
    if sasi_match:
        result['sasi_no'] = sasi_match.group(0)

    return result

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Kullanım: python ocr_agent.py <ruhsat_foto.jpg>")
        exit(1)
    image_path = sys.argv[1]
    ocr_result = extract_ruhsat_info(image_path)
    print(json.dumps(ocr_result, ensure_ascii=False, indent=2))
