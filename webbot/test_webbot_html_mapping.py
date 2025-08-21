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

from datetime import datetime
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

def test_readWebPage():
    requirement = "Download HTML from a real web page, print first 2000 chars, and assert HTML is non-empty."
    html = readWebPage()
    print("\n[TEST] Requirement:", requirement)
    print("Expected Output: HTML string, length > 0")
    print("Actual Output (first 2000 chars):\n", html[:2000])
    test_result = "PASS" if html and len(html) > 0 else "FAIL"
    print("Test Result:", test_result)
    if REPORTLAB_AVAILABLE:
        report_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'tdsp', 'test_reports'))
        os.makedirs(report_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        pdf_path = os.path.join(report_dir, f'webbot_test_report_{timestamp}.pdf')
        c = canvas.Canvas(pdf_path, pagesize=letter)
        c.setFont("Helvetica", 10)
        y = 750
        c.drawString(30, y, "[webbot Test Report]")
        y -= 20
        c.drawString(30, y, f"Requirement: {requirement}")
        y -= 20
        c.drawString(30, y, f"Expected Output: HTML string, length > 0")
        y -= 20
        c.drawString(30, y, f"Actual Output (truncated): {html[:1000].replace(chr(10), ' ')}")
        y -= 40
        c.drawString(30, y, f"Test Result: {test_result}")
        c.save()
        print(f"[PDF REPORT] Test report saved to: {pdf_path}")
    assert html and len(html) > 0

if __name__ == "__main__":
    test_readWebPage()
