# Data dictionary for component interfaces
# Her bir component arası veri alışverişi için ortak veri yapıları

from enum import Enum
from typing import Any, Dict

class AutomationStatus(str, Enum):
    NotStarted = 'NotStarted'
    Running = 'Running'
    Error = 'Error'
    Completed = 'Completed'

class SessionStatus(str, Enum):
    LoggedOut = 'LoggedOut'
    LoggedIn = 'LoggedIn'

class ProcessStatus(str, Enum):
    Idle = 'Idle'
    Processing = 'Processing'
    Completed = 'Completed'

# Ortak veri yapıları

data_dictionary = {
    'user_id': str,
    'document_image': Any,  # genellikle dosya yolu veya bytes
    'ocr_result': Dict,
    'form_field_map': Dict,
    'automation_status': AutomationStatus,
    'page_state': Dict,
    'retry_count': int,
    'session_status': SessionStatus,
    'process_status': ProcessStatus,
}
