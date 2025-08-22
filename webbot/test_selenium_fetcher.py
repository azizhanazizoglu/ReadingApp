from webbot.selenium_fetcher import fetch_html_with_selenium

def test_fetch_html():
    url = "https://www.example.com"
    html = fetch_html_with_selenium(url)
    assert "<html" in html.lower()
    assert len(html) > 1000
