import os
import time
import requests
import glob
import json

def test_flask_automation_e2e():
    # 1. Upload a sample JPEG
    backend_url = "http://localhost:5001"
    tmp_dir = os.path.join("memory", "TmpData")
    sample_jpg = os.path.join(tmp_dir, "sample_ruhsat.jpg")
    # Use an existing sample JPEG from ocr_agent if available
    if not os.path.exists(sample_jpg):
        sample_jpg = os.path.join("ocr_agent", "sample_ruhsat.jpg")
    assert os.path.exists(sample_jpg), f"Sample JPEG not found: {sample_jpg}"
    with open(sample_jpg, "rb") as f:
        files = {"file": ("sample.jpg", f, "image/jpeg")}
        r = requests.post(f"{backend_url}/api/upload", files=files)
        assert r.status_code == 200, f"Upload failed: {r.text}"
        print("[TEST] Upload response:", r.json())

    # 2. Start automation
    r = requests.post(f"{backend_url}/api/start-automation")
    assert r.status_code == 200, f"Automation start failed: {r.text}"
    print("[TEST] Automation start response:", r.json())

    # 3. Poll /api/state until done
    for _ in range(60):
        r = requests.get(f"{backend_url}/api/state")
        assert r.status_code == 200
        state = r.json().get("state")
        print(f"[TEST] Current state: {state}")
        if state == "done":
            break
        time.sleep(1)
    else:
        assert False, "Automation did not complete in time"

    # 4. Check for JSON output in TmpData
    json_files = glob.glob(os.path.join(tmp_dir, "ruhsat_*.json"))
    assert json_files, "No JSON output found in TmpData after automation"
    with open(json_files[-1], "r", encoding="utf-8") as jf:
        ruhsat_json = json.load(jf)
        print("[TEST] ruhsat_json output:", ruhsat_json)
        assert isinstance(ruhsat_json, dict)

    # 5. Optionally, fetch mapping result
    r = requests.get(f"{backend_url}/api/mapping")
    assert r.status_code == 200
    mapping = r.json().get("mapping")
    print("[TEST] Mapping result:", mapping)
    assert mapping is not None
