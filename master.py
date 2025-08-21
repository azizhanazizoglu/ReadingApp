# Master entegrasyon: webbot, memory, pageread_llm
from webbot.test_webbot_html_mapping import readWebPage
from license_llm.pageread_llm import map_json_to_html_fields

# Basit memory (database) interface
default_html_key = "page1"
class MemoryDB:
    def __init__(self):
        self.data = {}
    def save_html(self, key: str, html: str):
        self.data[key] = html
    def get_html(self, key: str) -> str:
        return self.data.get(key, "")

# 1. Webbot'u çağırıp HTML'i memory'e kaydet
def fetch_and_store_html(memory: MemoryDB, url: str = None, key: str = default_html_key):
    html = readWebPage(url)
    memory.save_html(key, html)
    print(f"[INFO] HTML memory'e kaydedildi: {key}")

# 2. Memory'den HTML'i alıp pageread_llm'e ver
def analyze_html_with_llm(memory: MemoryDB, ruhsat_json: dict, key: str = default_html_key, **llm_kwargs):
    html = memory.get_html(key)
    if not html:
        print(f"[ERROR] Memory'de {key} için HTML yok!")
        return
    mapping = map_json_to_html_fields(html, ruhsat_json, **llm_kwargs)
    print("\n[LLM Mapping Çıktısı]:\n", mapping)

# Entegrasyon testi
def main():
    memory = MemoryDB()
    # 1. HTML'i indir ve kaydet
    fetch_and_store_html(memory)
    # 2. Ruhsat datası ile LLM mapping
    ruhsat_json = {
        "ad_soyad": "AZIZHAN AZIZOGLU",
        "kimlik_no": "35791182062",
        "dogum_tarihi": "05.03.1994",
        "plaka_no": "06 YK 1234"
    }
    analyze_html_with_llm(memory, ruhsat_json)

if __name__ == "__main__":
    main()
