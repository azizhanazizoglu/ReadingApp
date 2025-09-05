import datetime
import re
import inspect
import json
from pathlib import Path

# Logging retention configuration.
# preserve_all=True means never trim automatically; only explicit clear endpoint will remove logs.
# max can be set (int) when preserve_all=False to cap buffer size.
log_config = {
    'preserve_all': True,  # default per user request: keep everything until explicit delete
    'max': None            # when None and preserve_all=True no trimming occurs
}

def _derive_color(level: str, message: str, extra: dict | None) -> str:
    lvl = (level or '').upper()
    msg_l = (message or '').lower()
    # Success / progress heuristics → green
    success_tokens = ["navigated_", "fill_progress", "fill_complete", "mapped", "success", "home candidates", "task/menu actions"]
    if any(tok in msg_l for tok in success_tokens):
        return 'green'
    if lvl == 'WARN' or 'fallback' in msg_l or 'nav_failed' in msg_l:
        return 'yellow'
    if lvl == 'ERROR':
        return 'yellow'  # degrade to yellow (only 3 colors requested)
    return 'blue'

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

    color = _derive_color(_level, clean_message, extra)
    entry = {
        'time': datetime.datetime.now().isoformat(),
        'level': _level,
        'code': _code,
        'component': _component,
        'message': clean_message,
        'color': color,
        'category': color  # backward compatibility for earlier UI expecting 'category'
    }
    if extra:
        entry['extra'] = extra

    backend_logs.append(entry)
    # Conditional trimming only if not preserving all and max specified
    try:
        if not log_config.get('preserve_all'):
            max_sz = log_config.get('max')
            if isinstance(max_sz, int) and max_sz > 0:
                while len(backend_logs) > max_sz:
                    backend_logs.pop(0)
    except Exception:
        # Fail-safe: never block logging on retention errors
        pass

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

def dump_json_debug(data: dict, name_prefix: str = 'debug', base_dir: str | None = None) -> str | None:
    try:
        ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        base = Path(base_dir or 'webbot2html') / 'tsx_debug'
        base.mkdir(parents=True, exist_ok=True)
        file = base / f"{name_prefix}_{ts}.json"
        file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        return str(file)
    except Exception:
        return None
