
import os
import openai

def map_json_to_html_fields(html_string: str, ruhsat_json: dict, model="gpt-4o"):
  """
  TS2 (LLM-only): Analyze current page HTML and decide if it is a fillable form page or the final activation page.
  If a form page, return a mapping of keys -> CSS selectors plus ordered actions.
  If final, return empty mapping and final actions (e.g., click#Poliçeyi Aktifleştir).
  Output MUST be code-fenced JSON matching the required schema.
  """
  import re
  from bs4 import BeautifulSoup
  openai.api_key = os.getenv("OPENAI_API_KEY")
  # Önce <form>...</form> varsa onu kullan, yoksa input/select/label/button özetini çıkar
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
  # URL-agnostic TS2 prompt: decide fill_form vs final_activation and produce strict JSON
  prompt_header = (
    "Görev/Task:\n"
    "- Bu sayfanın HTML’ini analiz ederek şu kararı ver:\n"
    "  1) Doldurulacak bir form sayfası mı?\n"
    "  2) Nihai sayfa mı (yalnızca ‘Poliçeyi Aktifleştir’ benzeri CTA ile bitirme)?\n"
    "- Yalnız DOM/HTML; URL’e güvenme. Değer üretme yok. ÇIKTI SADECE code-fenced JSON.\n\n"
    "Anahtar Alanlar (anlam bazlı, lower_snake_case): plaka_no, tckimlik, dogum_tarihi, ad_soyad; opsiyonel: telefon, email, adres, motor_no, sasi_no, ruhsat_seri_no.\n"
    "Eşanlam/Synonyms (örnek):\n"
    "- plaka_no ≈ plaka, plaka no, araç plaka, plate, plate number, registration number\n"
    "- tckimlik ≈ tc, tc kimlik, kimlik no, national id, identity number\n"
    "- dogum_tarihi ≈ doğum tarihi, birth date, dob\n"
    "- ad_soyad ≈ ad soyad, isim, full name, name\n\n"
    "Final Sayfa Sinyalleri: ‘Poliçeyi Aktifleştir/Policeyi Aktiflestir’, ‘Poliçe(yi) üret/oluştur/yazdır’, ‘PDF’, ‘Teklifi Onayla’, ‘Satın Al’.\n"
    "Form Sayfası: input/textarea/select alanları net şekilde mevcut.\n\n"
    "Kurallar:\n"
    "- Final ise: is_final_page=true, field_mapping={}, actions=['click#Poliçeyi Aktifleştir', 'click#Policeyi Aktiflestir', 'click#Poliçeyi üret', 'click#Poliçeyi yazdır'] (güvenilir metinlerle).\n"
    "- Final değilse: is_final_page=false, field_mapping={key: tekil CSS selector}, actions=['click#DEVAM','click#İLERİ','click#Next'] (sayfadaki gerçek buton metinleriyle).\n"
  "- CSS selector önceliği: #id > [name=\"...\"] > sade tekil selector; olmayan alanı yazma; uydurma yok.\n"
    "- Yalnız JSON üret; açıklama yok.\n\n"
    "Çıktı Şeması:\n"
    "{\n"
    "  \"version\": \"ts2.v3\",\n"
    "  \"page_kind\": \"fill_form\" | \"final_activation\" | \"unknown\",\n"
    "  \"is_final_page\": boolean,\n"
    "  \"final_reason\": string,\n"
    "  \"evidence\": string[],\n"
    "  \"field_mapping\": { },\n"
    "  \"actions\": string[]\n"
    "}\n"
  )
  prompt = f"{prompt_header}\n\nHTML alanları:\n{html_fields}\n\nJSON veri (örnek amaçlı, değer uydurma yok):\n{ruhsat_json}"
  response = openai.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": prompt}],
    temperature=0.1,
    max_tokens=512
  )
  return response.choices[0].message.content.strip()