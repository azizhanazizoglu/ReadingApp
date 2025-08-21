
import os
import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--jpg", action="store", default="ocr_agent/sample_ruhsat.jpg", help="Test edilecek ruhsat jpg dosyasının pathi"
    )

def test_extract_vehicle_info_from_image(request):
    file_path = request.config.getoption("--jpg")
    if not os.path.exists(file_path):
        pytest.skip(f"{file_path} bulunamadı.")
    from llm_agent.llm_ocr_extractor import extract_vehicle_info_from_image
    result = extract_vehicle_info_from_image(file_path)
    print("LLM output:", result)
    assert isinstance(result, dict)
    assert "plaka_no" in result or "raw_response" in result
