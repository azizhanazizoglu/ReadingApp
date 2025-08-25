from flask import request, jsonify
from backend.memory import memory, log_backend, backend_logs
from backend.stateflow import stateflow_agent
from backend.stateflow_agent import stateflow_agent as full_stateflow_agent
from backend.memory_store import memory as new_memory
from license_llm.pageread_llm import map_json_to_html_fields
from webbot.test_webbot_html_mapping import readWebPage
import os
import time

def register_routes(app):
    @app.route('/api/upload', methods=['POST'])
    def upload_file():
        try:
            log_backend("[INFO] /api/upload endpointine istek geldi.")
            file = request.files['file']
            log_backend(f"[INFO] Yüklenen dosya: {file.filename}")
            tmp_dir = os.path.join('memory', 'TmpData')
            os.makedirs(tmp_dir, exist_ok=True)
            timestamp = int(time.time())
            filename = f"download_{timestamp}.jpg"
            filepath = os.path.join(tmp_dir, filename)
            file.save(filepath)
            log_backend(f"[INFO] Dosya kaydedildi: {filepath}")
            memory['uploaded_file'] = filepath
            memory['state'] = 'file_uploaded'
            return jsonify({"result": "JPEG yüklendi ve kaydedildi.", "file_path": filepath})
        except Exception as e:
            log_backend(f"[ERROR] Upload sırasında hata: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/start-automation', methods=['POST'])
    def start_automation():
        try:
            print("[INFO] /api/start-automation endpointine istek geldi.")
            memory['state'] = 'automation_started'
            import threading
            thread = threading.Thread(target=stateflow_agent)
            thread.start()
            return jsonify({"result": "Otomasyon başlatıldı, stateflow agent çalışıyor."})
        except Exception as e:
            print(f"[ERROR] Otomasyon başlatılırken hata: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/logs', methods=['GET'])
    def get_logs():
        return jsonify({"logs": backend_logs})

    @app.route('/api/mapping', methods=['GET'])
    def get_mapping():
        return jsonify({"mapping": memory.get('mapping')})

    @app.route('/api/test-state-2', methods=['POST'])
    def test_state_2():
        try:
            log_backend('[INFO] /api/test-state-2 çağrıldı (Webbot -> Mapping).')
            # HTML hazır değilse webbot ile al
            if not memory.get('html'):
                html = readWebPage()
                memory['html'] = html
            # Ruhsat JSON yoksa hata
            ruhsat_json = memory.get('ruhsat_json')
            if not ruhsat_json:
                return jsonify({"error": "Önce TestSt1 ile LLM JSON üretmelisiniz (ruhsat_json yok)."}), 400
            # Mapping
            mapping = map_json_to_html_fields(memory['html'], ruhsat_json)
            memory['mapping'] = mapping
            # Kaydetme: stateflow_agent içindeki logic zaten json2mapping'e kaydediyor; burada da benzerini yapıyoruz
            import json, time
            import os as _os
            json2mapping_dir = _os.path.join('memory', 'TmpData', 'json2mapping')
            _os.makedirs(json2mapping_dir, exist_ok=True)
            base = memory.get('latest_base') or f'mapping_{int(time.time())}'
            mapping_path = _os.path.join(json2mapping_dir, f'{base}_mapping.json')
            with open(mapping_path, 'w', encoding='utf-8') as f:
                json.dump(mapping, f, ensure_ascii=False, indent=2)
            log_backend(f"[INFO] /api/test-state-2 mapping kaydedildi: {mapping_path}")
            return jsonify({"result": "Mapping kaydedildi", "path": mapping_path})
        except Exception as e:
            log_backend(f"[ERROR] /api/test-state-2 hata: {e}")
            return jsonify({"error": str(e)}), 500
