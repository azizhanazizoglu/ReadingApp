
import os
import openai

def map_json_to_html_fields(html_string: str, ruhsat_json: dict, model="gpt-4o"):
  """
  Given an HTML form and a JSON object with data to fill, use the LLM to determine which JSON field should be filled into which input/select in the HTML, and which button(s) should be clicked. The LLM should analyze all clues (label, placeholder, id, name, type, etc.) and return a mapping as JSON.
  Optimized: Only form fields are sent to the LLM for better accuracy.
  """
  import re
  from bs4 import BeautifulSoup
  openai.api_key = os.getenv("OPENAI_API_KEY")
  # Önce <form>...</form> varsa onu kullan, yoksa tüm input/select/label alanlarını parser ile çıkar
  form_match = re.search(r'<form[\s\S]*?</form>', html_string, re.IGNORECASE)
  if form_match:
    html_fields = form_match.group(0)
  else:
    soup = BeautifulSoup(html_string, "html.parser")
    fields = []
    for tag in soup.find_all(["input", "select", "label"]):
      # input/select için id, name, placeholder, type, value
      if tag.name in ["input", "select"]:
        desc = f"<{tag.name}"
        for attr in ["id", "name", "placeholder", "type", "value"]:
          if tag.has_attr(attr):
            desc += f' {attr}="{tag[attr]}"'
        desc += ">"
        # label ile eşleştir
        label_text = ""
        if tag.has_attr("id"):
          label = soup.find("label", attrs={"for": tag["id"]})
          if label:
            label_text = label.get_text(strip=True)
        if label_text:
          desc += f" [label: {label_text}]"
        fields.append(desc)
      elif tag.name == "label":
        fields.append(str(tag))
    html_fields = '\n'.join(fields)
  prompt = f"""
  - Aşağıda bir web formunun HTML alanları (formun tam içeriği veya input/select/label ve çevresi) ve doldurulacak Türkçe JSON verisi var. Görevin:
   - JSON anahtarlarını en uygun input/select alanına eşleştir (id, name, placeholder, label'a bak).
   - Sadece HTML'de GERÇEKTEN bulunan alanlara mapping yap. HTML'de olmayan alanları mapping'e ekleme.
   - Her sayfa için uygun field_mapping ve actions üret.
   - Sadece mapping JSON'u döndür. Açıklama ekleme.

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