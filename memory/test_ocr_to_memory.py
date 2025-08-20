# test_ocr_to_memory.py
# OCR Agent'ın memory (db) ile entegrasyonunu test eder.
import os
import sqlite3
import json
import pytest
from memory.db import Database

# Test için kullanılacak örnek OCR sonucu (gerçekten gelen JSON)
OCR_SAMPLE = {
    "tckimlik": "35791182456",
    "dogum_tarihi": "05.03.1994",
    "ad_soyad": "Aziz Serdar",
    "plaka_no": "06AZ1055",
    "belge_seri": "WF0DXXSKR8R2222222",
    "sasi_no": "WF0DXXSKR8R2222222",
    "model_yili": "2022",
    "tescil_tarihi": "10.10.2022"
}

def test_ocr_result_to_memory(tmp_path):
    # Test için geçici bir veritabanı oluştur
    db_path = os.path.join(tmp_path, 'test_insurance.db')
    db = Database(db_path=db_path)

    # 1. Doküman ekle (kullanıcı id'si olmadan, örnek id: 1)
    document_id = db.save_document(user_id=1, file_path="/tmp/ruhsat.jpg")
    assert document_id > 0

    # 2. OCR sonucu kaydet
    ocr_json = json.dumps(OCR_SAMPLE, ensure_ascii=False)
    ocr_id = db.save_ocr_result(document_id=document_id, result_json=ocr_json)
    assert ocr_id > 0

    # 3. OCR sonucunu DB'den kontrol et
    with db._get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT result_json FROM ocr_results WHERE id = ?", (ocr_id,))
        row = cur.fetchone()
        assert row is not None
        result = json.loads(row[0])
        for key in OCR_SAMPLE:
            assert result[key] == OCR_SAMPLE[key]

# Database class'ına test için connection döndüren yardımcı fonksiyon ekle
# (testte private method olarak kullanılır, production'da kullanılmaz)
def _get_connection(self):
    return sqlite3.connect(self.db_path)
Database._get_connection = _get_connection

#run commands
#pytest memory/test_ocr_to_memory.py
#Coverage report
#pytest --cov=memory memory/test_ocr_to_memory.py
