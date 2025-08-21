import os
import pytest

def test_extract_vehicle_info_from_image(request):
    file_path = request.config.getoption("--jpg")
    if not os.path.exists(file_path):
        pytest.skip(f"{file_path} bulunamadı.")
    from license_llm.license_llm_extractor import extract_vehicle_info_from_image
    result = extract_vehicle_info_from_image(file_path)
    print("LLM output:", result)
    assert isinstance(result, dict)
    assert "plaka_no" in result or "raw_response" in result
