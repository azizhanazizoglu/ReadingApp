import datetime
import re
import inspect

# In-memory ring buffer for backend logs (structured)
backend_logs = []  # list[dict]
_auto_inc = 1000

def _parse_level(msg: str) -> str:
    m = re.match(r"^\[(DEBUG|INFO|WARN|ERROR)\]\s*(.*)$", msg)
    return m.group(1) if m else "INFO"

def _strip_level(msg: str) -> str:
    m = re.match(r"^\[(DEBUG|INFO|WARN|ERROR)\]\s*(.*)$", msg)
    return m.group(2) if m else msg

def _parse_code(msg: str) -> str | None:
    # Accept inline code like [BE-1234] after level or at start
    m = re.search(r"\[(BE-\d{4})\]", msg)
    return m.group(1) if m else None

def _caller_component() -> str:
    # Try to infer component (module) from call stack
    try:
        frame = inspect.stack()[3]
        module = inspect.getmodule(frame.frame)
        if module and module.__name__:
            return module.__name__.split('.')[-1]
    except Exception:
        pass
    return 'backend'

def log_backend(msg: str, memory=None, *, level: str | None = None, code: str | None = None, component: str | None = None, extra: dict | None = None):
    """Record a structured backend log entry.

    Backwards compatible: existing calls can keep passing only msg and memory.
    Optional fields:
      - level: DEBUG|INFO|WARN|ERROR (parsed from [LEVEL] prefix if omitted)
      - code: e.g., BE-1234 (parsed from [BE-1234] if omitted; otherwise auto-increment)
      - component: logical component/module name (auto-inferred from caller if omitted)
      - extra: arbitrary dict for additional context
    """
    global _auto_inc
    # Derive level, code, component
    _level = (level or _parse_level(msg)).upper()
    inline_code = _parse_code(msg)
    _code = code or inline_code
    if not _code:
        _auto_inc += 1
        _code = f"BE-{_auto_inc}"
    _component = component or _caller_component()
    clean_message = _strip_level(msg)
    # Print a concise line for terminal
    print(f"[{_level}] {_code} {_component}: {clean_message}")

    entry = {
        'time': datetime.datetime.now().isoformat(),
        'level': _level,
        'code': _code,
        'component': _component,
        'message': clean_message,
    }
    if extra:
        entry['extra'] = extra

    backend_logs.append(entry)
    if len(backend_logs) > 300:
        backend_logs.pop(0)

    if memory is not None:
        memory.setdefault('steps', [])
        memory['steps'].append({
            'timestamp': entry['time'],
            'msg': entry['message'],
            'level': entry['level'],
            'code': entry['code'],
            'component': entry['component'],
            'state': memory.get('state')
        })
        if len(memory['steps']) > 300:
            memory['steps'].pop(0)
