# test_ocr_to_memory.py
# OCR Agent'ın memory (db) ile entegrasyonunu test eder.
import os
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

def test_ocr_result_to_memory(tmp_path):
    # Test için geçici bir veritabanı oluştur
    db_path = os.path.join(tmp_path, 'test_insurance.db')
    db = Database(db_path=db_path)

    # 1. Doküman ekle (kullanıcı id'si olmadan, örnek id: 1)
    document_id = db.save_document(user_id=1, file_path="tdsp/ruhsat/Ruhsat.jpg")
    assert document_id > 0

    # 2. LLM ile ruhsat görselinden veri çıkar
    from llm_agent.llm_ocr_extractor import extract_vehicle_info_from_image
    llm_result = extract_vehicle_info_from_image("tdsp/ruhsat/Ruhsat.jpg")
    ocr_sample = fill_ocr_sample(llm_result)
    ocr_json = json.dumps(ocr_sample, ensure_ascii=False)
    ocr_id = db.save_ocr_result(document_id=document_id, result_json=ocr_json)
    assert ocr_id > 0

    # 3. OCR sonucunu DB'den kontrol et
    with db._get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT result_json FROM ocr_results WHERE id = ?", (ocr_id,))
        row = cur.fetchone()
        assert row is not None
        result = json.loads(row[0])
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
