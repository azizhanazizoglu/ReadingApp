def pytest_addoption(parser):
    parser.addoption(
        "--jpg", action="store", default="ocr_agent/sample_ruhsat.jpg", help="Test edilecek ruhsat jpg dosyasının pathi"
    )