# ocr_agent/test_ocr_agent.py
# Basit birim testi: örnek ruhsat fotoğrafı ile OCR sonucu kontrolü
import os
import pytest
from ocr_agent.ocr_agent import extract_ruhsat_info


def test_extract_ruhsat_info_file(pytestconfig):
    file_name = pytestconfig.getoption("file")
    image_path = os.path.join(os.path.dirname(__file__), file_name)
    if not os.path.exists(image_path):
        pytest.skip(f"{file_name} fotoğrafı yok, test atlandı.")
    result = extract_ruhsat_info(image_path)
    print(f"OCR Çıktısı ({file_name}):", result)
    assert isinstance(result, dict)
    assert any([result.get('plaka_no'), result.get('marka'), result.get('model_yili')])

#pytest ocr_agent/test_ocr_agent.py -s --file=sample_ruhsat.jpg
#pytest ocr_agent/test_ocr_agent.py -s --file=sample_ruhsat_modern.jpg