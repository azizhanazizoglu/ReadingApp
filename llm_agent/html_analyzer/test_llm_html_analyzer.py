# test_llm_html_analyzer.py
import pytest
from llm_agent.html_analyzer.llm_html_analyzer import analyze_html_form

def test_analyze_html_form():
    html = "<input name='plaka' /> <input name='model_yili' />"
    ocr_json = {"plaka_no": "06 AK 8836", "model_yili": "2005"}
    result = analyze_html_form(html, ocr_json)
    assert isinstance(result, dict)
