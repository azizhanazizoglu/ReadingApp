import datetime

backend_logs = []

def log_backend(msg, memory=None):
    print(msg)
    backend_logs.append(msg)
    if len(backend_logs) > 100:
        backend_logs.pop(0)
    if memory is not None:
        memory.setdefault('steps', [])
        memory['steps'].append({
            'timestamp': datetime.datetime.now().isoformat(),
            'msg': msg,
            'state': memory.get('state')
        })
        if len(memory['steps']) > 100:
            memory['steps'].pop(0)
