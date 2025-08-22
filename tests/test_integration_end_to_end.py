"""
Integration test: Fetch HTML with webbot, map with LLM, print mapping result.
Extend this file for more integration/coverage tests.
"""

import sys
import os
import pytest
from dotenv import load_dotenv
# PDF reporting
from datetime import datetime
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# Force load .env from project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(dotenv_path=os.path.join(project_root, '.env'))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from webbot.test_webbot_html_mapping import readWebPage
from license_llm.pageread_llm import map_json_to_html_fields

class MemoryDB:
    def __init__(self):
        self.data = {}
    def save_html(self, key: str, html: str):
        self.data[key] = html
    def get_html(self, key: str) -> str:
        return self.data.get(key, "")

def test_end_to_end_html_to_llm_mapping():
    # input_htmls/vehicle-details.html ve input_htmls/traffic-insurance.html dosyalarındaki URL'leri oku
    url_files = [
        ("traffic-insurance", os.path.join(project_root, "input_htmls", "traffic-insurance.html")),
        ("vehicle-details", os.path.join(project_root, "input_htmls", "vehicle-details.html"))
    ]
    urls = []
    for label, file_path in url_files:
        if os.path.exists(file_path):
            with open(file_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("<!--"):
                        urls.append((label, line))

    # Her bir URL için ruhsat_json'u dinamik belirle (örnek: label'a göre farklı alanlar eklenebilir)
    mapping_results = []
    for label, url in urls:
        if label == "traffic-insurance":
            ruhsat_json = {
                "ad_soyad": "AZIZHAN AZIZOGLU",
                "kimlik_no": "35791182062",
                "dogum_tarihi": "05.03.1994",
                "plaka_no": "06 YK 1234"
            }
        else:
            ruhsat_json = {
                "ad_soyad": "AZIZHAN AZIZOGLU",
                "kimlik_no": "35791182062",
                "dogum_tarihi": "05.03.1994",
                "plaka_no": "06 YK 1234",
                "tescil_tarihi": "24.08.2004",
                "sasi_no": "VF1LB240531754309"
            }
        html = readWebPage(url)
    print(f"[DEBUG] HTML snapshot for {label} ({url}):\n" + html[:1000])
    mapping = map_json_to_html_fields(html, ruhsat_json)
    def extract_json_from_markdown(text):
        import re
        pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
        match = re.search(pattern, text.strip(), re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return text.strip()
        mapping_clean = extract_json_from_markdown(mapping)
        import json
        try:
            mapping_json = json.loads(mapping_clean)
        except Exception as e:
            print(f"[FAIL] Could not parse mapping as JSON for {label} ({url}):", e)
            mapping_json = {}
        # Sadece önemli kısımları yazdır
        print(f"\nWebpage: {label} ({url})")
        if isinstance(mapping_json, dict):
            if 'field_mapping' in mapping_json:
                print("field_mapping:")
                print(json.dumps(mapping_json['field_mapping'], indent=2, ensure_ascii=False))
            else:
                print("field_mapping: [YOK]")
            if 'actions' in mapping_json:
                print("actions:")
                print(json.dumps(mapping_json['actions'], indent=2, ensure_ascii=False))
            else:
                print("actions: [YOK]")
        else:
            print("field_mapping: [YOK]")
            print("actions: [YOK]")
        mapping_results.append((label, url, ruhsat_json, mapping_json, mapping))

    # PDF raporu oluştur
    if REPORTLAB_AVAILABLE:
        report_dir = os.path.join(project_root, 'tdsp', 'test_reports')
        os.makedirs(report_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        pdf_path = os.path.join(report_dir, f'integration_test_multi_report_{timestamp}.pdf')
        c = canvas.Canvas(pdf_path, pagesize=letter)
        c.setFont("Helvetica", 10)
        y = 750
        c.drawString(30, y, "[Integration Test Report: Multi-Page Mapping]")
        y -= 20
        for label, url, ruhsat_json, mapping_json, mapping_raw in mapping_results:
            c.drawString(30, y, f"Page: {label} ({url})")
            y -= 15
            c.drawString(30, y, f"Input ruhsat_json: {str(ruhsat_json)}")
            y -= 15
            c.drawString(30, y, f"Mapping Output:")
            y -= 15
            mapping_str = json.dumps(mapping_json, ensure_ascii=False, indent=2) if mapping_json else mapping_raw[:500]
            for line in mapping_str.splitlines():
                c.drawString(40, y, line)
                y -= 12
                if y < 50:
                    c.showPage()
                    c.setFont("Helvetica", 10)
                    y = 750
            y -= 10
        c.save()
        print(f"[PDF REPORT] Multi-page test report saved to: {pdf_path}")
