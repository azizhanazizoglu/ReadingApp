import datetime

memory = {
    'ruhsat_json': None,
    'html': None,
    'mapping': None,
    'state': 'idle',
    'uploaded_file': None,
    'steps': []
}
backend_logs = []

def log_backend(msg):
    print(msg)
    backend_logs.append(msg)
    if len(backend_logs) > 100:
        backend_logs.pop(0)
    memory['steps'].append({
        'timestamp': datetime.datetime.now().isoformat(),
        'msg': msg,
        'state': memory.get('state')
    })
    if len(memory['steps']) > 100:
        memory['steps'].pop(0)
