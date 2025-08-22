
import os
import pytest
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))
from datetime import datetime
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

def test_extract_vehicle_info_from_image(request):
    requirement = "Extract ruhsat info from image, output dict with keys like 'plaka_no', 'ad_soyad', etc."
    file_path = request.config.getoption("--jpg")
    if not os.path.exists(file_path):
        pytest.skip(f"{file_path} bulunamadı.")
    from license_llm.license_llm_extractor import extract_vehicle_info_from_image
    result = extract_vehicle_info_from_image(file_path)
    print("\n[TEST] Requirement:", requirement)
    print("Input file_path:", file_path)
    print("Expected Output: dict with ruhsat fields")
    print("Actual Output:", result)
    test_result = "PASS" if isinstance(result, dict) and ("plaka_no" in result or "raw_response" in result) else "FAIL"
    print("Test Result:", test_result)
    if REPORTLAB_AVAILABLE:
        from textwrap import wrap
        import glob
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        report_dir = os.path.join(project_root, 'tdsp', 'test_reports')
        os.makedirs(report_dir, exist_ok=True)
        # Eski raporları sil
        for old in glob.glob(os.path.join(report_dir, 'LICENSELLM_EXTRACTION_*.pdf')):
            try:
                os.remove(old)
            except Exception:
                pass
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        pdf_name = f'LICENSELLM_EXTRACTION_{timestamp}.pdf'
        pdf_path = os.path.join(report_dir, pdf_name)
        c = canvas.Canvas(pdf_path, pagesize=letter)
        c.setFont("Helvetica", 10)
        y = 750
        def draw_wrapped(text, y, max_width=100):
            for line in wrap(str(text), max_width):
                c.drawString(30, y, line)
                y -= 15
            return y
        y = draw_wrapped("[license_llm Test Report]", y)
        y -= 5
        y = draw_wrapped(f"Requirement: {requirement}", y)
        y -= 5
        y = draw_wrapped(f"Input file_path: {file_path}", y)
        y -= 5
        y = draw_wrapped(f"Expected Output: dict with ruhsat fields", y)
        y -= 5
        y = draw_wrapped(f"Actual Output: {str(result)}", y)
        y -= 10
        y = draw_wrapped(f"Test Result: {test_result}", y)
        c.save()
        print(f"[PDF REPORT] Test report saved to: {pdf_path}")
    assert isinstance(result, dict)
    assert "plaka_no" in result or "raw_response" in result
