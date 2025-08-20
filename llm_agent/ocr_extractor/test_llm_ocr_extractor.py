# Kök dizini sys.path'e ekle (her terminalde modül bulunur)
import sys
sys.path.insert(0, r'C:\Users\azizogla\Documents\Playground\Monitoring\ReadingApp')

# test_llm_ocr_extractor.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
import pytest
from llm_agent.ocr_extractor.llm_ocr_extractor import extract_vehicle_info_from_text

def test_extract_vehicle_info_from_text(pytestconfig):
    file_path = pytestconfig.getoption("--file")
    if not os.path.exists(file_path):
        pytest.skip(f"{file_path} bulunamadı.")
    # Dosya yolunu doğrudan LLM fonksiyonuna gönder
    result = extract_vehicle_info_from_text(file_path)
    print("LLM Agent output:", result)
    assert isinstance(result, dict)
