import sqlite3
from contextlib import closing
from typing import Optional, Dict, Any, List
from .data_dictionary import AutomationStatus, SessionStatus, ProcessStatus

class Database:
    def __init__(self, db_path: str = 'insurance.db'):
        self.db_path = db_path
        self._create_tables()

    def _create_tables(self):
        schema = '''
        CREATE TABLE IF NOT EXISTS users (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT,
          email TEXT,
          phone TEXT
        );
        CREATE TABLE IF NOT EXISTS documents (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id INTEGER,
          file_path TEXT,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS ocr_results (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          document_id INTEGER,
          result_json TEXT,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS runs (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id INTEGER,
          status TEXT,
          attempt_count INTEGER,
          last_error TEXT,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS form_maps (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          run_id INTEGER,
          page_state TEXT,
          map_json TEXT,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS notifications (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          run_id INTEGER,
          type TEXT,
          message TEXT,
          screenshot_path TEXT,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        '''
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(schema)

    # Kullanıcı ekle
    def add_user(self, name: str, email: str, phone: str) -> int:
        with sqlite3.connect(self.db_path) as conn:
            with closing(conn.cursor()) as cur:
                cur.execute(
                    'INSERT INTO users (name, email, phone) VALUES (?, ?, ?)',
                    (name, email, phone)
                )
                conn.commit()
                return cur.lastrowid

    # Doküman kaydet
    def save_document(self, user_id: int, file_path: str) -> int:
        with sqlite3.connect(self.db_path) as conn:
            with closing(conn.cursor()) as cur:
                cur.execute(
                    'INSERT INTO documents (user_id, file_path) VALUES (?, ?)',
                    (user_id, file_path)
                )
                conn.commit()
                return cur.lastrowid

    # OCR sonucu kaydet
    def save_ocr_result(self, document_id: int, result_json: str) -> int:
        with sqlite3.connect(self.db_path) as conn:
            with closing(conn.cursor()) as cur:
                cur.execute(
                    'INSERT INTO ocr_results (document_id, result_json) VALUES (?, ?)',
                    (document_id, result_json)
                )
                conn.commit()
                return cur.lastrowid

    # Run başlat
    def start_run(self, user_id: int) -> int:
        with sqlite3.connect(self.db_path) as conn:
            with closing(conn.cursor()) as cur:
                cur.execute(
                    'INSERT INTO runs (user_id, status, attempt_count) VALUES (?, ?, ?)',
                    (user_id, AutomationStatus.NotStarted.value, 1)
                )
                conn.commit()
                return cur.lastrowid

    # Run durumunu güncelle
    def update_run_status(self, run_id: int, status: AutomationStatus, last_error: Optional[str] = None, attempt_count: Optional[int] = None):
        with sqlite3.connect(self.db_path) as conn:
            with closing(conn.cursor()) as cur:
                if attempt_count is not None:
                    cur.execute(
                        'UPDATE runs SET status = ?, last_error = ?, attempt_count = ? WHERE id = ?',
                        (status.value, last_error, attempt_count, run_id)
                    )
                else:
                    cur.execute(
                        'UPDATE runs SET status = ?, last_error = ? WHERE id = ?',
                        (status.value, last_error, run_id)
                    )
                conn.commit()

    # Form map kaydet
    def save_form_map(self, run_id: int, page_state: str, map_json: str) -> int:
        with sqlite3.connect(self.db_path) as conn:
            with closing(conn.cursor()) as cur:
                cur.execute(
                    'INSERT INTO form_maps (run_id, page_state, map_json) VALUES (?, ?, ?)',
                    (run_id, page_state, map_json)
                )
                conn.commit()
                return cur.lastrowid

    # Bildirim logla
    def log_notification(self, run_id: int, type_: str, message: str, screenshot_path: Optional[str] = None) -> int:
        with sqlite3.connect(self.db_path) as conn:
            with closing(conn.cursor()) as cur:
                cur.execute(
                    'INSERT INTO notifications (run_id, type, message, screenshot_path) VALUES (?, ?, ?, ?)',
                    (run_id, type_, message, screenshot_path)
                )
                conn.commit()
                return cur.lastrowid

    # Son run'ı getir
    def get_last_run(self, user_id: int) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            with closing(conn.cursor()) as cur:
                cur.execute(
                    'SELECT * FROM runs WHERE user_id = ? ORDER BY created_at DESC LIMIT 1',
                    (user_id,)
                )
                row = cur.fetchone()
                return dict(row) if row else None

    # Kullanıcıya ait dokümanları getir
    def get_documents_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            with closing(conn.cursor()) as cur:
                cur.execute(
                    'SELECT * FROM documents WHERE user_id = ?', (user_id,))
                return [dict(row) for row in cur.fetchall()]

    # Run detaylarını getir
    def get_run_details(self, run_id: int) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            with closing(conn.cursor()) as cur:
                cur.execute('SELECT * FROM runs WHERE id = ?', (run_id,))
                row = cur.fetchone()
                return dict(row) if row else None
