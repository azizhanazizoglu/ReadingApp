# Webbot: HTML form mapping with LLM
import os
import openai

def map_json_to_html_fields(html_string: str, ruhsat_json: dict, model="gpt-4o"):
    """
    LLM'e html ve ruhsat jsonunu ver, hangi json alanı hangi input'a yazılacak ve hangi butona basılacak mappingini döndür.
    """
    openai.api_key = os.getenv("OPENAI_API_KEY")
    prompt = f"""
Sen bir web form doldurma asistanısın. Sana bir HTML formunun kodu ve doldurulacak bilgileri içeren bir JSON verilecek.

Görevlerin:
1. JSON'daki her alanı, HTML'deki uygun input veya select alanına eşleştir.
2. Hangi butona basılması gerektiğini belirt (ör: 'DEVAM').
3. Mapping'i aşağıdaki formatta, sadece JSON olarak döndür:
{
  "field_mapping": {
    "json_alan_adi": "input#id veya input[name=] veya label text"
  },
  "actions": ["click#button_id veya button text"]
}

Örnek mapping:
{
  "field_mapping": {
    "ad_soyad": "input#name",
    "kimlik_no": "input#identity",
    "dogum_tarihi": "input#birthDate",
    "plaka_no": "input#plateNo"
  },
  "actions": ["click#DEVAM"]
}

İşte HTML:
"""
    prompt += html_string[:8000]  # token sınırı için kısıtlıyoruz
    prompt += "\n\nDoldurulacak JSON:\n" + str(ruhsat_json)
    prompt += "\n\nSadece mapping JSON'unu döndür. Açıklama ekleme."

    response = openai.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=512
    )
    # Sadece JSON dönecek şekilde promptladık
    return response.choices[0].message.content.strip()
