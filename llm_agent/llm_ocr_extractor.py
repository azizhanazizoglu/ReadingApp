import os
import base64
from dotenv import load_dotenv
import openai

load_dotenv()

def extract_vehicle_info_from_image(file_path: str) -> dict:
    """
    OpenAI API ile ruhsat görselinden araç bilgilerini çıkarır.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY .env dosyasında bulunamadı!")
    client = openai.OpenAI(api_key=api_key)
    prompt = """
The following image is a Turkish vehicle registration document (ruhsat). Please extract ONLY the following fields as a valid JSON object, using Turkish characters where appropriate:
- plaka_no (license plate, exactly as printed on the document, e.g. '06 AK 8886', with correct spacing and no extra characters)
- marka (brand)
- model_yili (model year)
- tescil_tarihi (registration date)
- sasi_no (chassis number)
If any of the following fields are missing, use these default values:
- tckimlik: "35791182456"
- dogum_tarihi: "05.03.1994"
- ad_soyad: "Aziz Serdar"
- belge_seri: use the same value as sasi_no
Your output must be a JSON object in the following format (example):
{
  "tckimlik": "35791182456",
  "dogum_tarihi": "05.03.1994",
  "ad_soyad": "Aziz Serdar",
  "plaka_no": "06 AK 8886",
  "belge_seri": "VF1LB240531754309",
  "sasi_no": "VF1LB240531754309",
  "model_yili": "2005",
  "tescil_tarihi": "24.08.2004"
}
Return ONLY the JSON object, with no explanation or extra text.
"""
    with open(file_path, "rb") as f:
        image_bytes = f.read()
    image_base64 = base64.b64encode(image_bytes).decode()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
            ]}
        ],
        max_tokens=512,
    )
    import json
    try:
        return json.loads(response.choices[0].message.content)
    except Exception:
        return {"raw_response": response.choices[0].message.content}
