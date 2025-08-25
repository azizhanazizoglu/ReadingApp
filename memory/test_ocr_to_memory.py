# test_ocr_to_memory.py
# OCR Agent'ın memory (db) ile entegrasyonunu test eder.
import os
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))
import sqlite3
import json
import pytest
from memory.db import Database

# Test için kullanılacak örnek OCR sonucu (gerçekten gelen JSON)

# LLM'den gelen sonucu OCR_SAMPLE formatına dönüştürür, eksik alanları default ile doldurur
def fill_ocr_sample(llm_result: dict) -> dict:
    return {
        "tckimlik": llm_result.get("tckimlik", "35791182456"),
        "dogum_tarihi": llm_result.get("dogum_tarihi", "05.03.1994"),
        "ad_soyad": llm_result.get("ad_soyad", "Aziz Serdar"),
        "plaka_no": llm_result.get("plaka_no", ""),
        "belge_seri": llm_result.get("belge_seri", llm_result.get("sasi_no", "WF0DXXSKR8R2222222")),
        "sasi_no": llm_result.get("sasi_no", "WF0DXXSKR8R2222222"),
        "model_yili": llm_result.get("model_yili", "2022"),
        "tescil_tarihi": llm_result.get("tescil_tarihi", "10.10.2022")
    }

from datetime import datetime
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

import traceback

def get_requirement():
    """docs/09_test_files_and_paths.md içinden requirement'ı çek (fallback: .txt)"""
    base_docs = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'docs'))
    candidates = [
        os.path.join(base_docs, '09_test_files_and_paths.md'),
        os.path.join(base_docs, '09_test_files_and_paths.txt'),
    ]
    for docs_path in candidates:
        if os.path.exists(docs_path):
            with open(docs_path, encoding="utf-8") as f:
                content = f.read()
            import re
            m = re.search(r"## memory.*?Requirement: (.*?)\n", content, re.DOTALL)
            if m:
                return m.group(1).strip()
            break
    return "Store and retrieve OCR/LLM results, check data integrity and correct storage."

def test_ocr_result_to_memory(tmp_path):
    requirement = get_requirement()
    document_id = ocr_id = None
    result = None
    test_result = "FAIL"
    error_msg = ""
    try:
        # Test için geçici bir veritabanı oluştur
        db_path = os.path.join(tmp_path, 'test_insurance.db')
        db = Database(db_path=db_path)
        document_id = db.save_document(user_id=1, file_path="tdsp/ruhsat/Ruhsat.jpg")
        from llm_agent.llm_ocr_extractor import extract_vehicle_info_from_image
        llm_result = extract_vehicle_info_from_image("tdsp/ruhsat/Ruhsat.jpg")
        ocr_sample = fill_ocr_sample(llm_result)
        ocr_json = json.dumps(ocr_sample, ensure_ascii=False)
        ocr_id = db.save_ocr_result(document_id=document_id, result_json=ocr_json)
        with db._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT result_json FROM ocr_results WHERE id = ?", (ocr_id,))
            row = cur.fetchone()
            result = json.loads(row[0]) if row else None
        if document_id > 0 and ocr_id > 0 and result and all(result[k] == ocr_sample[k] for k in ocr_sample):
            test_result = "PASS"
        else:
            error_msg = "Data mismatch or missing."
    except Exception as e:
        error_msg = str(e) + "\n" + traceback.format_exc()
        print("[ERROR]", error_msg)
    finally:
        if REPORTLAB_AVAILABLE:
            from textwrap import wrap
            import glob
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            report_dir = os.path.join(project_root, 'tdsp', 'test_reports')
            os.makedirs(report_dir, exist_ok=True)
            # Eski raporları sil
            for old in glob.glob(os.path.join(report_dir, 'MEMORY_OCR2MEMORY_*.pdf')):
                try:
                    os.remove(old)
                except Exception:
                    pass
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            pdf_name = f'MEMORY_OCR2MEMORY_{timestamp}.pdf'
            pdf_path = os.path.join(report_dir, pdf_name)
            c = canvas.Canvas(pdf_path, pagesize=letter)
            c.setFont("Helvetica", 10)
            y = 750
            def draw_wrapped(text, y, max_width=100):
                for line in wrap(str(text), max_width):
                    c.drawString(30, y, line)
                    y -= 15
                return y
            y = draw_wrapped("[memory Test Report]", y)
            y -= 5
            y = draw_wrapped(f"Requirement: {requirement}", y)
            y -= 5
            y = draw_wrapped(f"Input: Ruhsat image path: tdsp/ruhsat/Ruhsat.jpg", y)
            y -= 5
            y = draw_wrapped(f"Expected Output: OCR/LLM result stored and retrieved, all fields match.", y)
            y -= 5
            y = draw_wrapped(f"Actual Output (truncated): {str(result)}", y)
            if error_msg:
                y = draw_wrapped(f"Error: {error_msg}", y)
            y -= 10
            y = draw_wrapped(f"Test Result: {test_result}", y)
            c.save()
            print(f"[PDF REPORT] Test report saved to: {pdf_path}")
        if test_result != "PASS":
            assert False, error_msg or "Test failed."
    assert document_id > 0
    assert ocr_id > 0
    assert result is not None
    for key in ocr_sample:
        assert result[key] == ocr_sample[key]

# Database class'ına test için connection döndüren yardımcı fonksiyon ekle
# (testte private method olarak kullanılır, production'da kullanılmaz)
def _get_connection(self):
    return sqlite3.connect(self.db_path)
Database._get_connection = _get_connection

#run commands
#pytest memory/test_ocr_to_memory.py
#Coverage report
#pytest --cov=memory memory/test_ocr_to_memory.py
