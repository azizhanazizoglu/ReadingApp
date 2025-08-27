

from flask import Flask, request, jsonify
from flask_cors import CORS
import threading

import sys
import os
import json
import time
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
            tmp_dir = os.path.join(PROJECT_ROOT, 'memory', 'TmpData', 'jpg2json')
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
        try:
            _len = len(html) if isinstance(html, str) else 0
            log_backend(f"[INFO] TS2 payload alındı: url={url or ''} html_present={bool(html)} html_len={_len}", memory, code="BE-3001P")
        except Exception:
            pass
        if not html:
            if url:
                # Avoid keyword args for compatibility with monkeypatched test stub
                html = readWebPage(url)
            elif memory.get('html'):
                html = memory['html']
            else:
                html = readWebPage()
        else:
            # HTML webview'den geldi; doğrudan kullan (normalize etmeye gerek yok)
            pass
        memory['html'] = html

        # Save iframe HTML to webbot2html (clear previous, keep only latest)
        html_path = None
        try:
            import time as _time
            html_dir = os.path.join(PROJECT_ROOT, 'memory', 'TmpData', 'webbot2html')
            os.makedirs(html_dir, exist_ok=True)
            # Clear old files
            for name in os.listdir(html_dir):
                p = os.path.join(html_dir, name)
                try:
                    if os.path.isfile(p) or os.path.islink(p):
                        os.remove(p)
                    elif os.path.isdir(p):
                        import shutil
                        shutil.rmtree(p)
                except Exception:
                    pass
            ts = int(_time.time())
            html_path = os.path.join(html_dir, 'page.html')
            with open(html_path, 'w', encoding='utf-8') as _hf:
                _hf.write(html)
            # Extract first <form> and save as form.html (optional, for token economy)
            try:
                from bs4 import BeautifulSoup as _BSF
                _soup = _BSF(html, 'html.parser')
                _form = _soup.find('form')
                if _form is not None:
                    form_path = os.path.join(html_dir, 'form.html')
                    with open(form_path, 'w', encoding='utf-8') as _ff:
                        _ff.write(str(_form))
                    # Build a tiny form meta
                    inputs = len(_form.find_all(['input']))
                    selects = len(_form.find_all(['select']))
                    textareas = len(_form.find_all(['textarea']))
                    buttons = len(_form.find_all(['button']))
                    form_meta = {
                        'inputs': inputs,
                        'selects': selects,
                        'textareas': textareas,
                        'buttons': buttons
                    }
                    with open(os.path.join(html_dir, 'form_meta.json'), 'w', encoding='utf-8') as _mf:
                        import json as _json
                        _json.dump(form_meta, _mf, ensure_ascii=False, indent=2)
            except Exception:
                # Non-fatal form extraction error
                log_backend("[WARN] form.html çıkarma başarısız (devam ediliyor)", memory, code="BE-3001W-FORM")
            # Optional metadata JSON for traceability
            try:
                meta = {
                    "url": url or memory.get('iframe_url') or '',
                    "timestamp": ts,
                    "length": len(html)
                }
                with open(os.path.join(html_dir, 'page.json'), 'w', encoding='utf-8') as _jf:
                    import json as _json
                    _json.dump(meta, _jf, ensure_ascii=False, indent=2)
            except Exception:
                log_backend("[WARN] page.json meta yazılamadı (devam)", memory, code="BE-3001W-META")
            log_backend(f"[INFO] HTML kaydedildi: {html_path}", memory, code="BE-3001W", extra={"html_path": html_path})
        except Exception as _ex:
            # Log the error explicitly so it surfaces in UI
            try:
                log_backend(f"[WARN] HTML kaydetme başarısız: {_ex}", memory, code="BE-3001W-FAIL")
            except Exception:
                pass

        try:
            from bs4 import BeautifulSoup as _BS
            _s = _BS(html, "html.parser")
            _inputs = len(_s.find_all("input"))
            _selects = len(_s.find_all("select"))
            _textareas = len(_s.find_all("textarea"))
            _field_cnt = _inputs + _selects + _textareas
            # Küçük bir snippet göster (güvenli, tek satır)
            _snippet = (html[:140].replace("\n", " ").replace("\r", " ") + ("..." if len(html) > 140 else "")) if isinstance(html, str) else ""
            log_backend(f"[INFO] HTML yüklendi, alan sayısı: {_field_cnt} (input={_inputs}, select={_selects}, textarea={_textareas})", memory, code="BE-3001A", extra={"snippet": _snippet})
        except Exception:
            pass

        # LLM JSON: body.ruhsat_json > memory.ruhsat_json > jpg2json fallback
        ruhsat_json = body.get('ruhsat_json') or memory.get('ruhsat_json')
        if not ruhsat_json:
            # jpg2json fallback: en son .json dosyasını yükle
            try:
                jpg2json_dir = os.path.join(PROJECT_ROOT, 'memory', 'TmpData', 'jpg2json')
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
        try:
            json_block = _extract_json_block(raw_mapping)
            mapping = json.loads(json_block)
            log_backend("[INFO] LLM mapping JSON parse OK.", memory, code="BE-3001B", extra={"len": len(json_block)})
        except Exception as _e:
            log_backend(f"[WARN] LLM mapping JSON parse FAILED: {_e}", memory, code="BE-3001C")
            mapping = {"field_mapping": {}, "actions": []}

        memory['mapping'] = mapping
        # Diske kaydet: memory/TmpData/json2mapping/<base>_mapping.json
        json2mapping_dir = os.path.join(PROJECT_ROOT, 'memory', 'TmpData', 'json2mapping')
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
        resp = {"result": "Mapping kaydedildi", "path": mapping_path}
        if html_path:
            resp["html_saved_to"] = html_path
        return jsonify(resp)
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
