def pytest_addoption(parser):
    parser.addoption("--file", action="store", default="sample_ruhsat.jpg", help="Test edilecek ruhsat dosyası (örn: sample_ruhsat_modern.jpg)")