
from flask import Flask, request, jsonify
from flask_cors import CORS
from scheduler.job_scheduler import JobScheduler, Job
from webbot.test_webbot_html_mapping import readWebPage
from license_llm.pageread_llm import map_json_to_html_fields
import threading
import time

app = Flask(__name__)
CORS(app)

# Basit memory (global dict)
memory = {
    'ruhsat_json': None,
    'html': None,
    'mapping': None,
    'state': 'idle',
}
backend_logs = []

def log_backend(msg):
    print(msg)
    backend_logs.append(msg)
    # Maksimum 100 log tut
    if len(backend_logs) > 100:
        backend_logs.pop(0)

# ...diğer route ve fonksiyonlar burada...
from flask import Flask, request, jsonify
from flask_cors import CORS
from scheduler.job_scheduler import JobScheduler, Job
from webbot.test_webbot_html_mapping import readWebPage
from license_llm.pageread_llm import map_json_to_html_fields
import threading
import time

app = Flask(__name__)
CORS(app)

# Basit memory (global dict)
memory = {
    'ruhsat_json': None,
    'html': None,
    'mapping': None,
    'state': 'idle',
}
backend_logs = []

def log_backend(msg):
    print(msg)
    backend_logs.append(msg)
    # Maksimum 100 log tut
    if len(backend_logs) > 100:
        backend_logs.pop(0)

# Stateflow zinciri (JobScheduler ile)
def stateflow_agent():
    scheduler = JobScheduler()
    def wait_for_file():
        while memory['ruhsat_json'] is None:
            time.sleep(0.2)
        return 'file_ready'
    def webbot_job():
        html = readWebPage()
        memory['html'] = html
        return 'html_ready'
    def memory_job():
        if memory['html']:
            memory['state'] = 'memory_ready'
            return 'memory_ready'
        raise Exception('HTML not in memory')
    def llm_job():
        mapping = map_json_to_html_fields(memory['html'], memory['ruhsat_json'])
        memory['mapping'] = mapping
        memory['state'] = 'llm_done'
        return 'llm_done'
    scheduler.add_job(Job('wait_for_file', wait_for_file))
    scheduler.add_job(Job('webbot', webbot_job))
    scheduler.add_job(Job('memory', memory_job))
    scheduler.add_job(Job('llm', llm_job))
    scheduler.run_all()
    memory['state'] = 'done'
    return scheduler.get_states()

@app.route('/api/upload', methods=['POST'])
def upload_file():
    import os
    import time
    try:
        log_backend("[INFO] /api/upload endpointine istek geldi.")
        file = request.files['file']
        log_backend(f"[INFO] Yüklenen dosya: {file.filename}")
        # Klasör oluştur
        tmp_dir = os.path.join('memory', 'TmpData')
        os.makedirs(tmp_dir, exist_ok=True)
        # Dosya adı oluştur
        timestamp = int(time.time())
        filename = f"download_{timestamp}.jpg"
        filepath = os.path.join(tmp_dir, filename)
        # Dosyayı kaydet
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
        thread = threading.Thread(target=stateflow_agent)
        thread.start()
        return jsonify({"result": "Otomasyon başlatıldı, stateflow agent çalışıyor."})
    except Exception as e:
        print(f"[ERROR] Otomasyon başlatılırken hata: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/state', methods=['GET'])
def get_state():

    print("[INFO] /api/state endpointine istek geldi.")
    return jsonify(memory)

# EN SONDA: Backend loglarını döndüren endpoint
@app.route('/api/logs', methods=['GET'])
def get_logs():
    return jsonify({'logs': backend_logs})

if __name__ == "__main__":
    print('[INFO] Flask backend başlatılıyor (host=0.0.0.0, port=5001)')
    app.run(host='0.0.0.0', port=5001, debug=True)
