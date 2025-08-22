from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

def fetch_html_with_selenium(url, wait_time=3):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    driver = webdriver.Chrome(options=options)
    try:
        driver.get(url)
        time.sleep(wait_time)  # Sayfanın tam yüklenmesi için bekle
        html = driver.page_source
    finally:
        driver.quit()
    return html

if __name__ == "__main__":
    test_url = "https://www.example.com"
    html = fetch_html_with_selenium(test_url)
    with open("selenium_snapshot.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("HTML snapshot kaydedildi.")
