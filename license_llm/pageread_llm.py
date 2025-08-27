
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
    # Cap for select options
    try:
      max_select_opts = int(os.getenv("MAX_SELECT_OPTIONS", "20"))
    except Exception:
      max_select_opts = 20
  for tag in soup.find_all(["input", "select", "label", "textarea", "datalist", "button"]):
      # input/select/textarea için id, name, placeholder, type, value
      if tag.name in ["input", "select", "textarea"]:
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
        # select ise ilk N option'ı özetle
        if tag.name == "select":
          options = tag.find_all("option")
          if options:
            desc += f" [options_count: {len(options)}]"
            subset = options[:max_select_opts]
            opt_pairs = []
            for o in subset:
              txt = o.get_text(strip=True)
              val = o.get("value", "")
              if val and val != txt:
                opt_pairs.append(f"{txt}::{val}")
              else:
                opt_pairs.append(txt)
            desc += " [options: " + ", ".join(opt_pairs) + (" …" if len(options) > len(subset) else "") + "]"
        fields.append(desc)
      elif tag.name == "label":
        fields.append(str(tag))
      elif tag.name == "datalist":
        # Datalist destekliyse, seçenekleri özetle
        opts = tag.find_all("option")
        if opts:
          names = [o.get("value", o.get_text(strip=True)) for o in opts[:max_select_opts]]
          fields.append(f"<datalist id=\"{tag.get('id','')}\"> [options_count: {len(opts)}] [options: {', '.join(names)}{(' …' if len(opts) > max_select_opts else '')}]")
      elif tag.name == "button":
        # Butonları da özetle ki actions çıkabilsin
        desc = "<button"
        for attr in ["id", "name", "type", "value"]:
          if tag.has_attr(attr):
            desc += f' {attr}="{tag[attr]}"'
        text = tag.get_text(strip=True)
        if text:
          desc += f">{text}</button>"
        else:
          desc += ">...</button>"
        fields.append(desc)
  html_fields = '\n'.join(fields)
  prompt_header = """
Sen bir form eşleme yardımcısısın. Aşağıdaki HTML alanlarını (formun kendisi veya input/select/label özeti) ve doldurulacak Türkçe JSON verisini kullanarak, JSON anahtarlarını doğru input/select öğelerine eşle.

Kurallar:
- id, name, placeholder, label metinlerinden yararlan; semantik eşleşme yap.
- Dil-agnostik çalış: Label/placeholder metinleri Türkçe/İngilizce/Fransızca vb. dillerde olabilir; aksan/diakritik ve yazım/çoğul/ek varyasyonlarını normalize ederek anlamına göre eşleştir (yalnızca kelime eşleşmesine takılma).
- Eşanlamlıları anla ve normalle:
  - plaka_no ≈ ["plaka", "plaka no", "plaka numarası", "plate", "plate no", "plate number"].
  - sasi_no ≈ ["şasi", "şasi no", "şasi numarası", "vin", "chassis"].
  - tescil_tarihi ≈ ["tescil tarihi", "kayıt tarihi", "registration date"].
  - tckimlik ≈ ["tc", "tc kimlik", "kimlik no", "identity"].
  - dogum_tarihi ≈ ["doğum tarihi", "birth date", "birthdate"].
  - ad_soyad ≈ ["ad soyad", "ad/soyad", "isim", "name"].
- Sadece HTML’de GERÇEKTEN bulunan alanlara mapping yap (yoksa ekleme).
- Emin değilsen bir alanı eşleme; uydurma/hallucination yapma.
- CSS seçicide öncelik: id (input#id) > name (input[name='...']).
- Buton eylemleri için actions üret (örn. click#DEVAM, click#İLERİ, click#NEXT). HTML’de olmayan bir butonu yazma.
- Çıktıyı sadece JSON olarak ver; açıklama yazma. JSON’u üçlü tırnak çitleri içinde (```json ... ```) döndür.

Örnek format:
```json
{{
  "field_mapping": {{
    "ad_soyad": "input#name",
    "tckimlik": "input#identity",
    "dogum_tarihi": "input#birthDate",
    "plaka_no": "input#plateNo"
  }},
  "actions": ["click#DEVAM"]
}}
```
"""
  prompt = f"{prompt_header}\n\nHTML alanları:\n{html_fields}\n\nJSON veri:\n{ruhsat_json}"
  response = openai.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": prompt}],
    temperature=0.1,
    max_tokens=512
  )
  return response.choices[0].message.content.strip()