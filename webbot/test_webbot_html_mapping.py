# webbot'un ilk fonksiyonu: readWebPage
import requests

DEFAULT_URL = "https://preview--screen-to-data.lovable.app/traffic-insurance"

def readWebPage(url: str = None) -> str:
    """
    Verilen url'den (veya parametre verilmezse default url'den) HTML içeriğini indirir ve döndürür.
    """
    if url is None:
        url = DEFAULT_URL
    response = requests.get(url)
    response.raise_for_status()
    return response.text

def test_readWebPage():
    html = readWebPage()
    print("--- HTML BAŞLANGIÇ ---\n")
    print(html[:2000])  # İlk 2000 karakteri göster
    print("\n--- HTML SONU ---")

if __name__ == "__main__":
    test_readWebPage()
