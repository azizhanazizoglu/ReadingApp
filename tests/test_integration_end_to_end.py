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
    html = None
    mapping_json = {}
    has_field_mapping = False
    has_actions = False
    # --- Fill HTML with mapping and save snapshot ---
    from bs4 import BeautifulSoup
    def fill_html_with_mapping(html, mapping_json, ruhsat_json):
        soup = BeautifulSoup(html, 'html.parser')
        field_mapping = mapping_json.get('field_mapping', {})
        for json_field, selector in field_mapping.items():
            value = ruhsat_json.get(json_field, "")
            # Try to parse selector: input#id, input[name=], label text, etc.
            el = None
            if selector.startswith('input#'):
                el = soup.find('input', id=selector.split('#',1)[1])
            elif 'input[name=' in selector:
                name = selector.split('input[name=',1)[1].split(']',1)[0].replace('"','').replace("'","")
                el = soup.find('input', attrs={'name': name})
            elif selector.startswith('label:'):
                label_text = selector.split(':',1)[1].strip().lower()
                label = soup.find('label', string=lambda s: s and label_text in s.lower())
                if label and label.get('for'):
                    el = soup.find(id=label['for'])
            # fallback: try by id or name
            if not el:
                el = soup.find(id=selector) or soup.find('input', attrs={'name': selector})
            if el:
                el['value'] = value
        return str(soup)

    # Always save a filled HTML snapshot for debugging, even if mapping is missing
    if html is not None:
        try:
            filled_html = fill_html_with_mapping(html, mapping_json if has_field_mapping else {}, ruhsat_json)
        except Exception as e:
            print(f"[DEBUG] fill_html_with_mapping failed: {e}")
            filled_html = html
        snapshot_dir = os.path.join(project_root, 'tdsp', 'test_reports', 'html_snapshots')
        os.makedirs(snapshot_dir, exist_ok=True)
        snapshot_path = os.path.join(snapshot_dir, f'filled_html_snapshot_{datetime.now().strftime("%Y%m%d_%H%M")}.html')
        with open(snapshot_path, 'w', encoding='utf-8') as f:
            f.write(filled_html)
        print(f"[DEBUG] mapping_json: {mapping_json if has_field_mapping else 'NO MAPPING'}")
        print(f"[HTML SNAPSHOT] Filled HTML saved to: {snapshot_path}")
    else:
        print("[DEBUG] No HTML available to save snapshot.")
    """Integration: webbot fetches HTML, LLM maps ruhsat JSON to HTML fields."""
    # --- Test Requirement ---
    requirement = (
        "End-to-end: Fetch HTML, map ruhsat JSON to HTML fields with LLM, output valid mapping JSON. "
        "Input: ruhsat_json, live HTML. Output: mapping JSON with 'field_mapping' and 'actions'."
    )
    print("\n=== [INTEGRATION TEST] End-to-End HTML to LLM Mapping ===")
    print(f"Requirement: {requirement}")

    # --- Test Input ---
    memory = MemoryDB()
    html = readWebPage()
    memory.save_html("page1", html)
    ruhsat_json = {
        "ad_soyad": "AZIZHAN AZIZOGLU",
        "kimlik_no": "35791182062",
        "dogum_tarihi": "05.03.1994",
        "plaka_no": "06 YK 1234"
    }
    print("Input ruhsat_json:", ruhsat_json)
    print(f"Fetched HTML length: {len(html)}")

    # --- Expected Output ---
    expected_output = "mapping JSON string with 'field_mapping' and 'actions' keys, valid JSON parseable."
    print("Expected Output:", expected_output)

    # --- Actual Behavior ---
    html = memory.get_html("page1")
    assert html and len(html) > 1000, "HTML content is too short or missing."
    mapping = map_json_to_html_fields(html, ruhsat_json)
    print("\n[Actual Output] LLM Mapping Output (raw string):\n", mapping)
    import json
    # --- Normalize LLM output: strip markdown code block wrappers if present ---
    def extract_json_from_markdown(text):
        import re
        # Remove triple backtick code block wrappers (```json ... ``` or ``` ... ```)
        pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
        match = re.search(pattern, text.strip(), re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return text.strip()
    mapping_clean = extract_json_from_markdown(mapping)
    has_field_mapping = False
    has_actions = False
    try:
        mapping_json = json.loads(mapping_clean)
        print("\n[Actual Output] Parsed Mapping JSON:")
        print(json.dumps(mapping_json, indent=2, ensure_ascii=False))
        has_field_mapping = "field_mapping" in mapping_json
        has_actions = "actions" in mapping_json
    except Exception as e:
        print("[FAIL] Could not parse mapping as JSON:", e)
        has_field_mapping = has_actions = False

    # --- Pass/Fail Comparison ---
    if isinstance(mapping, str) and has_field_mapping and has_actions:
        print("\n[PASS] Output contains both 'field_mapping' and 'actions' as required.")
        test_result = "PASS"
    else:
        print("\n[FAIL] Output missing required keys or not valid JSON.")
        test_result = "FAIL"
    assert isinstance(mapping, str), "LLM output should be a string."
    assert has_field_mapping, "Output missing 'field_mapping'."
    assert has_actions, "Output missing 'actions'."

    # --- PDF Report Generation ---
    if REPORTLAB_AVAILABLE:
        report_dir = os.path.join(project_root, 'tdsp', 'test_reports')
        os.makedirs(report_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        pdf_path = os.path.join(report_dir, f'integration_test_report_{timestamp}.pdf')
        c = canvas.Canvas(pdf_path, pagesize=letter)
        c.setFont("Helvetica", 10)
        y = 750
        c.drawString(30, y, "[Integration Test Report]")
        y -= 20
        c.drawString(30, y, f"Requirement: {requirement}")
        y -= 20
        c.drawString(30, y, f"Input ruhsat_json: {ruhsat_json}")
        y -= 20
        c.drawString(30, y, f"Fetched HTML length: {len(html)}")
        y -= 20
        c.drawString(30, y, f"Expected Output: {expected_output}")
        y -= 20
        c.drawString(30, y, f"Actual Output: (truncated)")
        y -= 20
        c.drawString(30, y, mapping[:1000].replace('\n', ' ') if isinstance(mapping, str) else str(mapping)[:1000])
        y -= 40
        c.drawString(30, y, f"Test Result: {test_result}")
        c.save()
        print(f"[PDF REPORT] Test report saved to: {pdf_path}")
    else:
        print("[INFO] reportlab not installed, PDF report not generated.")