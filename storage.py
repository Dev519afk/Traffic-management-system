"""Local SQLite storage for manual incident records and completed analyses."""
from datetime import datetime
from pathlib import Path
import sqlite3
from contextlib import contextmanager

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs"
DB_PATH = OUT / "traffic_violations.db"
EVIDENCE = OUT / "violation_evidence"


@contextmanager
def db_connection():
    """Commit/rollback transactions and always release the SQLite handle."""
    conn = sqlite3.connect(DB_PATH)
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def initialize_database() -> None:
    OUT.mkdir(exist_ok=True, parents=True)
    EVIDENCE.mkdir(exist_ok=True, parents=True)
    with db_connection() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS violations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            vehicle_id TEXT,
            vehicle_class TEXT NOT NULL,
            violation_type TEXT NOT NULL,
            location TEXT DEFAULT 'Demo camera',
            notes TEXT DEFAULT '',
            status TEXT DEFAULT 'Manually recorded - not automatically verified',
            evidence_path TEXT DEFAULT ''
        )""")
        # Preserve and extend the existing database if one is copied into outputs.
        fields = {r[1] for r in conn.execute('PRAGMA table_info(violations)')}
        if 'evidence_path' not in fields:
            conn.execute("ALTER TABLE violations ADD COLUMN evidence_path TEXT DEFAULT ''")
        conn.execute("""CREATE TABLE IF NOT EXISTS traffic_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            video_name TEXT NOT NULL,
            duration_processed REAL NOT NULL,
            processed_frames INTEGER NOT NULL,
            unique_track_ids INTEGER NOT NULL,
            output_dir TEXT NOT NULL
        )""")


def add_run(video_name: str, duration: float, frames: int, ids: int, folder: Path) -> None:
    with db_connection() as conn:
        conn.execute("""INSERT INTO traffic_runs
            (created_at, video_name, duration_processed, processed_frames, unique_track_ids, output_dir)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (datetime.now().isoformat(timespec='seconds'), video_name, duration, frames, ids, str(folder)))


def get_runs():
    import pandas as pd
    with db_connection() as conn:
        return pd.read_sql_query('SELECT * FROM traffic_runs ORDER BY id DESC', conn)


def get_events():
    import pandas as pd
    with db_connection() as conn:
        return pd.read_sql_query('SELECT * FROM violations ORDER BY id DESC', conn)


def add_event(vehicle_id: str, vehicle_class: str, event_type: str,
              location: str, notes: str, uploaded=None) -> None:
    evidence_path = ''
    if uploaded is not None:
        suffix = Path(uploaded.name).suffix.lower()
        if suffix not in ('.png', '.jpg', '.jpeg'):
            raise ValueError('Only PNG or JPEG evidence is accepted')
        name = datetime.now().strftime('%Y%m%d_%H%M%S_%f') + suffix
        dest = EVIDENCE / name
        dest.write_bytes(uploaded.getvalue())
        evidence_path = str(dest)
    with db_connection() as conn:
        conn.execute("""INSERT INTO violations
            (timestamp, vehicle_id, vehicle_class, violation_type, location, notes, status, evidence_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), vehicle_id.strip() or 'Not specified',
             vehicle_class, event_type, location.strip() or 'Demo camera', notes.strip(),
             'Manually recorded - not automatically verified', evidence_path))
