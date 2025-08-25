

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
from backend.stateflow_agent import stateflow_agent

@app.route('/api/upload', methods=['POST'])
def upload_file():
    return handle_file_upload()

@app.route('/api/start-automation', methods=['POST'])
def start_automation():
    try:
        log_backend("[INFO] /api/start-automation endpointine istek geldi.", memory)
        memory['state'] = 'automation_started'
        thread = threading.Thread(target=stateflow_agent)
        thread.start()
        return jsonify({"result": "Otomasyon başlatıldı, stateflow agent çalışıyor."})
    except Exception as e:
        log_backend(f"[ERROR] Otomasyon başlatılırken hata: {e}", memory)
        return jsonify({"error": str(e)}), 500

@app.route('/api/automation', methods=['POST'])
def automation_alias():
    return start_automation()

@app.route('/api/state', methods=['GET'])
def get_state():
    log_backend("[INFO] /api/state endpointine istek geldi.", memory)
    return jsonify(memory)

@app.route('/api/mapping', methods=['GET'])
def get_mapping():
    return jsonify({'mapping': memory.get('mapping')})

@app.route('/api/logs', methods=['GET'])
def get_logs():
    return jsonify({'logs': backend_logs})

if __name__ == "__main__":
    print('[INFO] Flask backend başlatılıyor (host=0.0.0.0, port=5001)')
    app.run(host='0.0.0.0', port=5001, debug=True)
