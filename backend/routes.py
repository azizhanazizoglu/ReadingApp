from flask import request, jsonify
from backend.memory import memory, log_backend, backend_logs
from backend.stateflow import stateflow_agent
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
