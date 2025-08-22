"""
run_all_tests.py

- Tüm ana testleri çalıştırır.
- Her testin sonucunu (PASS/FAIL) ve PDF raporunu terminalde özetler.
- En sonda genel bir özet tablo ve toplam başarı oranı verir.
- Her testin requirement'ını docs/09_test_files_and_paths.txt dosyasından çeker ve PDF raporuna ekler.
- CI/CD (Jenkins) entegrasyonuna uygundur.
"""
import subprocess
import os
import re
from datetime import datetime

# Testler ve komutları
TESTS = [
    {
        "name": "LLM Extraction/Mapping",
        "script": "license_llm/test_license_llm_extractor.py",
        "cmd": ["pytest", "-s", "license_llm/test_license_llm_extractor.py", "--jpg", "tdsp/ruhsat/Ruhsat.jpg"],
        "requirement_key": "license_llm"
    },
    {
        "name": "Webbot HTML Download",
        "script": "webbot/test_webbot_html_mapping.py",
        "cmd": ["pytest", "-s", "webbot/test_webbot_html_mapping.py"],
        "requirement_key": "webbot"
    },
    {
        "name": "Memory Integration",
        "script": "memory/test_ocr_to_memory.py",
        "cmd": ["pytest", "-s", "memory/test_ocr_to_memory.py"],
        "requirement_key": "memory"
    },
    {
        "name": "End-to-End Integration",
        "script": "tests/test_integration_end_to_end.py",
        "cmd": ["pytest", "-s", "tests/test_integration_end_to_end.py"],
        "requirement_key": "integration"
    }
]

DOCS_PATH = os.path.join("docs", "09_test_files_and_paths.txt")

# Requirement'ları docs dosyasından çek
requirements = {}
if os.path.exists(DOCS_PATH):
    with open(DOCS_PATH, encoding="utf-8") as f:
        content = f.read()
    for key in ["license_llm", "webbot", "memory", "integration"]:
        m = re.search(rf"## {key}\n.*?Requirement: (.*?)\n", content, re.DOTALL)
        if m:
            requirements[key] = m.group(1).strip()

# Testleri sırayla çalıştır
results = []
print("\n=== RUNNING ALL TESTS ===\n")
for test in TESTS:
    print(f"[RUNNING] {test['name']}...")
    start = datetime.now()
    proc = subprocess.run(test["cmd"], capture_output=True, text=True)
    duration = (datetime.now() - start).total_seconds()
    output = proc.stdout + proc.stderr
    passed = "Test Result: PASS" in output or "[PASS]" in output or "1 passed" in output
    pdfs = []
    # PDF raporunu bul
    report_dir = os.path.join("tdsp", "test_reports")
    if os.path.exists(report_dir):
        for fname in os.listdir(report_dir):
            if fname.lower().startswith(test["name"].split()[0].lower()) and fname.endswith(".pdf"):
                pdfs.append(os.path.join(report_dir, fname))
    results.append({
        "name": test["name"],
        "passed": passed,
        "duration": duration,
        "pdfs": pdfs,
        "requirement": requirements.get(test["requirement_key"], "(not found)"),
        "output": output
    })
    print(f"[RESULT] {test['name']}: {'PASS' if passed else 'FAIL'} ({duration:.1f}s)")
    if pdfs:
        print(f"  PDF Report: {pdfs[-1]}")
    print()

# Genel özet tablo
print("\n=== TEST SUMMARY ===")
print(f"{'Test':35} | {'Result':6} | {'Duration(s)':11} | PDF Report")
print("-"*80)
for r in results:
    print(f"{r['name']:35} | {'PASS' if r['passed'] else 'FAIL':6} | {r['duration']:11.2f} | {r['pdfs'][-1] if r['pdfs'] else '-'}")

print("\n=== REQUIREMENTS ===")
for r in results:
    print(f"\n[{r['name']}]\nRequirement: {r['requirement']}\n")

# Toplam başarı oranı
total = len(results)
passed = sum(1 for r in results if r['passed'])
print(f"\nTOTAL: {passed}/{total} tests passed.")
if passed == total:
    print("\nALL TESTS PASSED ✅\n")
else:
    print("\nSOME TESTS FAILED ❌\n")
