# llm_agent/test_llm_agent.py
# Test for LLM agent (mocked, since no real LLM call)
import pytest
from llm_agent.llm_agent import extract_vehicle_info_from_text

def test_extract_vehicle_info_from_text():
    ocr_text = """
    PLAKA NO: 06 AK 8836
    MARKASI: RENAULT
    MODELİ: 2005
    TESCIL TARIHI: 24.08.2004
    ŞASİ NO: VF1LB240531754309
    """
    result = extract_vehicle_info_from_text(ocr_text)
    assert isinstance(result, dict)
    # In real test, check actual values after LLM integration
