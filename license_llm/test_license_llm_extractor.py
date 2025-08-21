
import os
import pytest
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
        report_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'tdsp', 'test_reports'))
        os.makedirs(report_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        pdf_path = os.path.join(report_dir, f'license_llm_test_report_{timestamp}.pdf')
        c = canvas.Canvas(pdf_path, pagesize=letter)
        c.setFont("Helvetica", 10)
        y = 750
        c.drawString(30, y, "[license_llm Test Report]")
        y -= 20
        c.drawString(30, y, f"Requirement: {requirement}")
        y -= 20
        c.drawString(30, y, f"Input file_path: {file_path}")
        y -= 20
        c.drawString(30, y, f"Expected Output: dict with ruhsat fields")
        y -= 20
        c.drawString(30, y, f"Actual Output: {str(result)[:1000]}")
        y -= 40
        c.drawString(30, y, f"Test Result: {test_result}")
        c.save()
        print(f"[PDF REPORT] Test report saved to: {pdf_path}")
    assert isinstance(result, dict)
    assert "plaka_no" in result or "raw_response" in result
