

from flask import Flask, request, jsonify
from flask_cors import CORS
import threading

import sys
import os
# Ensure project root is in sys.path for module imports
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


app = Flask(__name__)
CORS(app)
from license_llm.license_llm_extractor import extract_vehicle_info_from_image

@app.route('/api/test-llm-extract', methods=['POST'])
def test_llm_extract():
    """
    Test endpoint: POST JSON {"file_path": "absolute/path/to/jpg"}
    Calls extract_vehicle_info_from_image and returns the result.
    """
    data = request.get_json()
    file_path = data.get('file_path')
    if not file_path or not os.path.exists(file_path):
        return jsonify({"error": f"File not found: {file_path}"}), 400
    try:
        result = extract_vehicle_info_from_image(file_path)
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Import modular components
from backend.memory_store import memory
from backend.logging_utils import log_backend, backend_logs
from backend.file_upload import handle_file_upload
from backend.stateflow_agent import stateflow_agent, run_ts1_extract
from webbot.test_webbot_html_mapping import readWebPage
from license_llm.pageread_llm import map_json_to_html_fields

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

@app.route('/api/upload', methods=['POST'])
def upload_file():
    return handle_file_upload()

@app.route('/api/start-automation', methods=['POST'])
def start_automation():
    try:
        log_backend("[INFO] /api/start-automation endpointine istek geldi.", memory, code="BE-2001")
        # Cleanup: ensure TmpData/jpg2json is clean before a new TS1 run
        try:
            tmp_dir = os.path.join('memory', 'TmpData', 'jpg2json')
            if os.path.isdir(tmp_dir):
                for name in os.listdir(tmp_dir):
                    path = os.path.join(tmp_dir, name)
                    try:
                        if os.path.isfile(path) or os.path.islink(path):
                            os.remove(path)
                        elif os.path.isdir(path):
                            import shutil
                            shutil.rmtree(path)
                    except Exception:
                        pass
        except Exception:
            # non-fatal cleanup issue
            pass
        memory['state'] = 'automation_started'
        # TS1 sadece LLM JSON üretir; mapping TS2'ye bırakılır
        run_ts1_extract()
        log_backend("[INFO] TS1 tamamlandı (mapping yok).", memory, code="BE-2002")
        return jsonify({"result": "TS1 tamamlandı (JPEG→JSON)."})
    except Exception as e:
        log_backend(f"[ERROR] Otomasyon başlatılırken hata: {e}", memory, code="BE-9002")
        return jsonify({"error": str(e)}), 500

@app.route('/api/automation', methods=['POST'])
def automation_alias():
    return start_automation()

@app.route('/api/state', methods=['GET'])
def get_state():
    log_backend("[INFO] /api/state endpointine istek geldi.", memory, code="BE-2101")
    return jsonify(memory)

@app.route('/api/mapping', methods=['GET'])
def get_mapping():
    return jsonify({'mapping': memory.get('mapping')})

@app.route('/api/logs', methods=['GET'])
def get_logs():
    return jsonify({'logs': backend_logs})

@app.route('/api/test-state-2', methods=['POST'])
def test_state_2():
    try:
        log_backend('[INFO] /api/test-state-2 çağrıldı (Webbot -> Mapping).', memory, code="BE-3001")
        body = request.get_json(silent=True) or {}
        # HTML hazırla: body.html > body.url > memory.html > default URL
        html = body.get('html')
        url = body.get('url')
        if not html:
            if url:
                html = readWebPage(url)
            elif memory.get('html'):
                html = memory['html']
            else:
                html = readWebPage()
        memory['html'] = html
        # LLM JSON: body.ruhsat_json > memory.ruhsat_json > jpg2json fallback
        ruhsat_json = body.get('ruhsat_json') or memory.get('ruhsat_json')
        if not ruhsat_json:
            # jpg2json fallback: en son .json dosyasını yükle
            try:
                jpg2json_dir = os.path.join('memory', 'TmpData', 'jpg2json')
                if os.path.isdir(jpg2json_dir):
                    json_files = [f for f in os.listdir(jpg2json_dir) if f.lower().endswith('.json')]
                    if json_files:
                        latest = max(json_files, key=lambda f: os.path.getmtime(os.path.join(jpg2json_dir, f)))
                        with open(os.path.join(jpg2json_dir, latest), encoding='utf-8') as jf:
                            import json as _json
                            ruhsat_json = _json.load(jf)
                            memory['ruhsat_json'] = ruhsat_json
                            memory['latest_base'] = os.path.splitext(latest)[0]
            except Exception:
                pass
        if not ruhsat_json:
            return jsonify({"error": "LLM JSON bulunamadı. TS1 çalıştırın veya body.ruhsat_json sağlayın."}), 400
        # Mapping (LLM tabanlı fonksiyon) ve JSON olarak parse etme
        raw_mapping = map_json_to_html_fields(html, ruhsat_json)
        def _extract_json_block(text: str) -> str:
            import re
            pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
            m = re.search(pattern, text.strip(), re.IGNORECASE)
            return (m.group(1).strip() if m else text.strip())
        import json
        try:
            mapping = json.loads(_extract_json_block(raw_mapping))
        except Exception:
            # fallback: boş şablon döndürme yerine minimal yapı
            mapping = {"field_mapping": {}, "actions": []}
        memory['mapping'] = mapping
        # Diske kaydet: memory/TmpData/json2mapping/<base>_mapping.json
        import os, json, time
        json2mapping_dir = os.path.join('memory', 'TmpData', 'json2mapping')
        os.makedirs(json2mapping_dir, exist_ok=True)
        # Eski mapping dosyalarını temizle (yalnızca son işlem kalsın)
        try:
            for name in os.listdir(json2mapping_dir):
                path = os.path.join(json2mapping_dir, name)
                if os.path.isfile(path) or os.path.islink(path):
                    try:
                        os.remove(path)
                    except Exception:
                        pass
        except Exception:
            pass
        base = memory.get('latest_base') or f'mapping_{int(time.time())}'
        mapping_path = os.path.join(json2mapping_dir, f'{base}_mapping.json')
        with open(mapping_path, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, ensure_ascii=False, indent=2)
        log_backend(f"[INFO] /api/test-state-2 mapping kaydedildi: {mapping_path}", memory, code="BE-3002", extra={"path": mapping_path})
        return jsonify({"result": "Mapping kaydedildi", "path": mapping_path})
    except Exception as e:
        log_backend(f"[ERROR] /api/test-state-2 hata: {e}", memory, code="BE-9301")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print('[INFO] Flask backend başlatılıyor (host=0.0.0.0, port=5001)')
    try:
        # Debug: print URL map
        print('URL Map:', app.url_map)
    except Exception as _e:
        print('URL Map okunamadı:', _e)
    app.run(host='0.0.0.0', port=5001, debug=True)
