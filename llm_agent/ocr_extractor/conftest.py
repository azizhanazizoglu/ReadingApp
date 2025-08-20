# llm_agent/ocr_extractor/conftest.py
def pytest_addoption(parser):
    parser.addoption("--file", action="store", default="sample_ruhsat.jpg", help="Test edilecek ruhsat OCR metni dosyası veya resim yolu")
