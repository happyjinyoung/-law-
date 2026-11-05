"""SQLite를 계약·일정·알림의 단일 저장소로 사용한다."""
import json
import os
import sqlite3
from pathlib import Path
from contextlib import contextmanager

DEFAULTS = {'profile': '사용자', 'master': True, 'leads': [7,3,1,0], 'time': '09:00'}


@contextmanager
def connection():
    path = Path(os.getenv('APP_DB', str(Path(__file__).resolve().parents[1] / 'data' / 'app.sqlite3')))
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally: db.close()


def init_db():
    with connection() as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS drafts(id TEXT PRIMARY KEY, name TEXT NOT NULL, type TEXT NOT NULL,
          text TEXT NOT NULL, analysis TEXT NOT NULL, sample INTEGER NOT NULL, created TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS contracts(id TEXT PRIMARY KEY, name TEXT NOT NULL, type TEXT NOT NULL,
          text TEXT NOT NULL, analysis TEXT NOT NULL, sample INTEGER NOT NULL, created TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS events(id TEXT PRIMARY KEY, contract_id TEXT REFERENCES contracts(id) ON DELETE CASCADE,
          title TEXT NOT NULL, date TEXT NOT NULL, alarm INTEGER NOT NULL DEFAULT 1, source TEXT NOT NULL DEFAULT '');
        CREATE TABLE IF NOT EXISTS settings(id INTEGER PRIMARY KEY CHECK(id=1), value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS notifications(event_id TEXT REFERENCES events(id) ON DELETE CASCADE,
          day TEXT NOT NULL, PRIMARY KEY(event_id,day));
        ''')


def row_contract(row):
    value = dict(row)
    value['analysis'] = json.loads(value['analysis'])
    value['sample'] = bool(value['sample'])
    return value


def settings():
    with connection() as db:
        row = db.execute('SELECT value FROM settings WHERE id=1').fetchone()
        return json.loads(row[0]) if row else dict(DEFAULTS)


def state():
    with connection() as db:
        contracts = [row_contract(r) for r in db.execute('SELECT * FROM contracts ORDER BY created DESC, rowid DESC')]
        events = [dict(r) for r in db.execute('SELECT * FROM events ORDER BY date,title')]
    return {'contracts': contracts, 'events': events, 'settings': settings()}
