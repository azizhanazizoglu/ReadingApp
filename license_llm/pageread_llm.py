
import os
import openai

def map_json_to_html_fields(html_string: str, ruhsat_json: dict, model="gpt-4o"):
  """
  Given an HTML form and a JSON object with data to fill, use the LLM to determine which JSON field should be filled into which input/select in the HTML, and which button(s) should be clicked. The LLM should analyze all clues (label, placeholder, id, name, type, etc.) and return a mapping as JSON.
  Optimized: Only form fields are sent to the LLM for better accuracy.
  """
  import re
  openai.api_key = os.getenv("OPENAI_API_KEY")
  # Sadece <form>...</form> veya input/select/label bloklarını çıkar
  form_match = re.search(r'<form[\s\S]*?</form>', html_string, re.IGNORECASE)
  if form_match:
    html_fields = form_match.group(0)
  else:
    # Fallback: sadece input/select/label bloklarını topla
    html_fields = '\n'.join(re.findall(r'<(input|select|label)[^>]*>', html_string, re.IGNORECASE))
  prompt = f"""
Aşağıda bir web formunun HTML alanları ve doldurulacak Türkçe JSON verisi var. Görevin: JSON anahtarlarını en uygun input/select alanına eşleştir (id, name, placeholder, label'a bak).

Örnek mapping formatı:
{{
  "field_mapping": {{
  "ad_soyad": "input#name",
  "kimlik_no": "input#identity",
  "dogum_tarihi": "input#birthDate",
  "plaka_no": "input#plateNo"
  }},
  "actions": ["click#DEVAM"]
}}

Sadece mapping JSON'u döndür. Açıklama ekleme.

HTML alanları:
{html_fields}

JSON veri:
{ruhsat_json}
"""
  response = openai.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": prompt}],
    temperature=0.1,
    max_tokens=512
  )
  return response.choices[0].message.content.strip()