import os
import time
from flask import request, jsonify
from backend.logging_utils import log_backend
from backend.memory_store import memory

def handle_file_upload():
    try:
        log_backend("[INFO] /api/upload endpointine istek geldi.", memory, code="BE-1001")
        # Clear jpgDownload folder before new upload
        jpg_download_dir = os.path.join('memory', 'TmpData', 'jpgDownload')
        os.makedirs(jpg_download_dir, exist_ok=True)
        for f in os.listdir(jpg_download_dir):
            if f.lower().endswith('.jpg'):
                try:
                    os.remove(os.path.join(jpg_download_dir, f))
                except Exception:
                    pass
        file = request.files['file']
        log_backend(f"[INFO] Yüklenen dosya: {file.filename}", memory, code="BE-1002", extra={"filename": file.filename})
        timestamp = int(time.time())
        filename = f"download_{timestamp}.jpg"
        filepath = os.path.join(jpg_download_dir, filename)
        file.save(filepath)
        log_backend(f"[INFO] Dosya kaydedildi: {filepath}", memory, code="BE-1003", extra={"path": filepath})
        memory['uploaded_file'] = filepath
        memory['state'] = 'file_uploaded'
        return jsonify({"result": "JPEG yüklendi ve kaydedildi.", "file_path": filepath})
    except Exception as e:
        log_backend(f"[ERROR] Upload sırasında hata: {e}", memory, code="BE-9001")
        return jsonify({"error": str(e)}), 500
