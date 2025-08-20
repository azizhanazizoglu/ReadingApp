# SSL sertifikası için certifi ile ortam değişkeni ayarla
import os
try:
    import certifi
    os.environ["SSL_CERT_FILE"] = certifi.where()
except ImportError:
    pass
# ocr_extractor/llm_ocr_extractor.py
"""
LLM agent for extracting structured info from OCR text of Turkish vehicle registration.
"""
from typing import Dict

#Aşağıdaki metin bir Türk araç ruhsatının OCR çıktısıdır. Lütfen aşağıdaki alanları JSON olarak çıkar:\n- plaka_no\n- marka\n- model_yili\n- tescil_tarihi\n- sasi_no\n\nMetin:\n{ocr_text}\n\nYanıt sadece JSON olsun.

def extract_vehicle_info_from_text(file_path_or_text: str) -> Dict:
    """
    Dosya yolu (resim veya metin) ya da doğrudan metin alır, OpenAI LLM ile ruhsat bilgisini çıkarır.
    """
    import os
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    try:
        import openai
        openai.api_key = os.getenv("OPENAI_API_KEY")
    except ImportError:
        openai = None

    if openai is None or not openai.api_key:
        print("OpenAI API anahtarı veya openai paketi eksik. Sadece örnek çıktı dönüyor.")
        return {}

    import mimetypes
    import json
    # Eğer dosya ise, uzantısına bak
    if os.path.exists(file_path_or_text):
        mime, _ = mimetypes.guess_type(file_path_or_text)
        if mime and mime.startswith("image"):
            # OpenAI Vision API ile resmi analiz et (base64 encoding ile)
            import base64
            with open(file_path_or_text, "rb") as img_file:
                img_bytes = img_file.read()
            img_b64 = base64.b64encode(img_bytes).decode("utf-8")
            prompt = "Aşağıdaki görsel bir Türk araç ruhsatıdır. Lütfen aşağıdaki alanları JSON olarak çıkar:\n- plaka_no\n- marka\n- model_yili\n- tescil_tarihi\n- sasi_no\nYanıt sadece JSON olsun."
            response = openai.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                    ]}
                ],
                max_tokens=1024
            )
            try:
                return json.loads(response.choices[0].message.content)
            except Exception:
                return {"raw": response.choices[0].message.content}
        else:
            # Düz metin dosyası ise oku
            with open(file_path_or_text, encoding='utf-8') as f:
                ocr_text = f.read()
    else:
        # Doğrudan metin verilmişse
        ocr_text = file_path_or_text

    prompt = f"Aşağıdaki metin bir Türk araç ruhsatının OCR çıktısıdır. Lütfen aşağıdaki alanları JSON olarak çıkar:\n- plaka_no\n- marka\n- model_yili\n- tescil_tarihi\n- sasi_no\n\nMetin:\n{ocr_text}\n\nYanıt sadece JSON olsun."
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1024
    )
    try:
        return json.loads(response.choices[0].message.content)
    except Exception:
        return {"raw": response.choices[0].message.content}
