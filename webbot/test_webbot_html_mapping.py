# webbot'un ilk fonksiyonu: readWebPage


import os
import traceback
import requests
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

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


def get_requirement():
    """docs/09_test_files_and_paths.txt içinden requirement'ı çek"""
    docs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'docs', '09_test_files_and_paths.txt'))
    if os.path.exists(docs_path):
        with open(docs_path, encoding="utf-8") as f:
            content = f.read()
        import re
        m = re.search(r"## webbot.*?Requirement: (.*?)\n", content, re.DOTALL)
        if m:
            return m.group(1).strip()
    return "Download HTML from a real web page, print first 2000 chars, and assert HTML is non-empty."

def test_readWebPage():
    requirement = get_requirement()
    html = None
    test_result = "FAIL"
    error_msg = ""
    try:
        html = readWebPage()
        print("\n[TEST] Requirement:", requirement)
        print("Expected Output: HTML string, length > 0")
        print("Actual Output (first 2000 chars):\n", html[:2000])
        if html and len(html) > 0:
            test_result = "PASS"
        else:
            error_msg = "HTML is empty."
    except Exception as e:
        error_msg = str(e) + "\n" + traceback.format_exc()
        print("[ERROR]", error_msg)
    finally:
        if REPORTLAB_AVAILABLE:
            from textwrap import wrap
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            report_dir = os.path.join(project_root, 'tdsp', 'test_reports')
            os.makedirs(report_dir, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            pdf_path = os.path.join(report_dir, f'webbot_test_report_{timestamp}.pdf')
            c = canvas.Canvas(pdf_path, pagesize=letter)
            c.setFont("Helvetica", 10)
            y = 750
            def draw_wrapped(text, y, max_width=100):
                for line in wrap(str(text), max_width):
                    c.drawString(30, y, line)
                    y -= 15
                return y
            y = draw_wrapped("[webbot Test Report]", y)
            y -= 5
            y = draw_wrapped(f"Requirement: {requirement}", y)
            y -= 5
            y = draw_wrapped(f"Expected Output: HTML string, length > 0", y)
            y -= 5
            if html:
                y = draw_wrapped(f"Actual Output (truncated): {html[:1000].replace(chr(10), ' ')}", y)
            if error_msg:
                y = draw_wrapped(f"Error: {error_msg}", y)
            y -= 10
            y = draw_wrapped(f"Test Result: {test_result}", y)
            c.save()
            print(f"[PDF REPORT] Test report saved to: {pdf_path}")
        if test_result != "PASS":
            assert False, error_msg or "Test failed."

if __name__ == "__main__":
    test_readWebPage()
