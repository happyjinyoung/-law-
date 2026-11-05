"""로컬 단일 사용자 시연 서버. 외부 공개용 인증 서버가 아니다."""
import base64
import json
import mimetypes
import os
import re
import sqlite3
import uuid
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from backend import storage
from backend.analysis import analyze, search_contract
from backend.ai import call_ai, AIError
from backend.extraction import extract_file, validate_text

ROOT = Path(__file__).resolve().parent


def load_env():
    # .env는 Git에서 제외된다. 운영체제 환경변수를 우선한다.
    path = ROOT / '.env'
    if path.exists():
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            if '=' in line and not line.lstrip().startswith('#'):
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def short(value, label, limit=120):
    if not isinstance(value, str) or not value.strip() or len(value) > limit: raise ValueError(label+' 입력을 확인하세요.')
    return value.strip()


def iso_date(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value): raise ValueError('날짜 형식이 올바르지 않습니다.')
    date.fromisoformat(value)
    return value


def api(method, path, data):
    if method == 'GET' and path == '/api/state': return storage.state()
    if method == 'GET' and path == '/api/capabilities':
        from backend.extraction import ocr_status
        return {'ai_configured': bool(os.getenv('AI_API_KEY') and os.getenv('AI_MODEL')), 'ocr': ocr_status()}
    if method == 'GET' and path == '/api/sample':
        return {'text': (ROOT / 'samples' / 'fictional-rental.txt').read_text(encoding='utf-8')}
    if method == 'POST' and path == '/api/extract':
        try: content = base64.b64decode(data.get('content', ''), validate=True)
        except (ValueError, TypeError) as exc: raise ValueError('파일 데이터가 올바르지 않습니다.') from exc
        return extract_file(short(data.get('name'), '파일명', 250), content)
    if method == 'POST' and path == '/api/analyze':
        text = validate_text(data.get('text'))
        name, kind = short(data.get('name'), '계약 이름'), short(data.get('type'), '계약 유형', 40)
        result = analyze(text)
        if data.get('mode') not in ('demo', 'ai'): raise ValueError('분석 모드를 확인하세요.')
        if data['mode'] == 'ai':
            result['ai_notes'] = call_ai(text)
            result.update(mode='ai', mode_label='AI 설명 + 규칙 조건 추출')
        draft = str(uuid.uuid4())
        with storage.connection() as db:
            # 오래된 미저장 초안은 정리해 불필요한 원문 보관을 줄인다.
            db.execute("DELETE FROM drafts WHERE created < datetime('now','-1 day')")
            db.execute('INSERT INTO drafts(id,name,type,text,analysis,sample) VALUES(?,?,?,?,?,?)',
                       (draft, name, kind, text, json.dumps(result, ensure_ascii=False), int(data.get('sample') is True)))
        return {'draft_id': draft, 'name': name, 'type': kind, 'text': text, 'analysis': result, 'sample': data.get('sample') is True}
    if method == 'POST' and path == '/api/contracts':
        with storage.connection() as db:
            row = db.execute('SELECT * FROM drafts WHERE id=?', (data.get('draft_id'),)).fetchone()
            if not row: raise ValueError('분석 초안을 찾을 수 없습니다. 다시 분석하세요.')
            existing = db.execute('SELECT id FROM contracts WHERE id=?', (row['id'],)).fetchone()
            if not existing:
                db.execute('INSERT INTO contracts(id,name,type,text,analysis,sample) VALUES(?,?,?,?,?,?)', tuple(row[k] for k in ['id','name','type','text','analysis','sample']))
        return {'id': row['id']}
    if method in ('PATCH', 'DELETE') and path.startswith('/api/contracts/'):
        identifier = path.rsplit('/', 1)[-1]
        with storage.connection() as db:
            if not db.execute('SELECT id FROM contracts WHERE id=?', (identifier,)).fetchone(): raise ValueError('계약을 찾을 수 없습니다.')
            if method == 'DELETE':
                db.execute('DELETE FROM contracts WHERE id=?', (identifier,))
                db.execute('DELETE FROM drafts WHERE id=?', (identifier,))
            else:
                db.execute('UPDATE contracts SET name=?,type=? WHERE id=?', (short(data.get('name'), '계약 이름'), short(data.get('type'), '유형', 40), identifier))
        return {'ok': True}
    if path == '/api/events' and method == 'POST' or path.startswith('/api/events/') and method in ('PATCH','DELETE'):
        identifier = str(uuid.uuid4()) if method == 'POST' else path.rsplit('/', 1)[-1]
        with storage.connection() as db:
            if method != 'POST' and not db.execute('SELECT id FROM events WHERE id=?', (identifier,)).fetchone(): raise ValueError('일정을 찾을 수 없습니다.')
            if method == 'DELETE': db.execute('DELETE FROM events WHERE id=?', (identifier,))
            else:
                title, day = short(data.get('title'), '일정명'), iso_date(data.get('date'))
                contract_id, source = data.get('contract_id') or None, data.get('source', '')
                if not isinstance(source, str) or len(source) > 100_000: raise ValueError('일정 근거를 확인하세요.')
                if contract_id:
                    row = db.execute('SELECT text FROM contracts WHERE id=?', (contract_id,)).fetchone()
                    if not row: raise ValueError('연결할 계약이 없습니다.')
                    if source and source not in row['text']: raise ValueError('일정 근거가 계약 원문에 없습니다.')
                elif source: raise ValueError('원문 근거는 연결 계약이 필요합니다.')
                alarm = int(data.get('alarm') is True or data.get('alarm') == 1)
                if method == 'POST':
                    # 같은 후보를 반복 클릭해도 중복 일정을 생성하지 않는다.
                    same = db.execute('SELECT id FROM events WHERE contract_id IS ? AND title=? AND date=?', (contract_id,title,day)).fetchone()
                    if same: return {'id': same['id'], 'duplicate': True}
                    db.execute('INSERT INTO events VALUES(?,?,?,?,?,?)', (identifier,contract_id,title,day,alarm,source))
                else:
                    db.execute('UPDATE events SET contract_id=?, title=?, date=?, alarm=?, source=? WHERE id=?', (contract_id,title,day,alarm,source,identifier))
                    db.execute('DELETE FROM notifications WHERE event_id=?', (identifier,))
        return {'id': identifier}
    if path == '/api/settings' and method == 'PUT':
        value = {'profile': short(data.get('profile'), '프로필', 40), 'master': data.get('master') is True,
                 'time': data.get('time'), 'leads': data.get('leads')}
        if not isinstance(value['time'], str) or not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d', value['time']): raise ValueError('알림 시간을 확인하세요.')
        if not isinstance(value['leads'], list) or not all(type(n) is int and n in (0,1,3,7) for n in value['leads']): raise ValueError('알림 사전일을 확인하세요.')
        value['leads'] = sorted(set(value['leads']), reverse=True)
        with storage.connection() as db:
            db.execute('INSERT OR REPLACE INTO settings VALUES(1,?)', (json.dumps(value, ensure_ascii=False),))
        return value
    if path == '/api/notifications/claim' and method == 'POST':
        # DB 고유키로 여러 탭이 동시에 검사해도 같은 날 알림은 한 번만 표시한다.
        day, identifier = iso_date(data.get('day')), short(data.get('event_id'), '일정 ID')
        with storage.connection() as db:
            row = db.execute('SELECT date,alarm FROM events WHERE id=?', (identifier,)).fetchone()
            cfg = storage.settings()
            if not row or not row['alarm'] or not cfg['master'] or (date.fromisoformat(row['date'])-date.fromisoformat(day)).days not in cfg['leads']:
                return {'claimed': False}
            try: db.execute('INSERT INTO notifications VALUES(?,?)', (identifier,day)); claimed = True
            except sqlite3.IntegrityError: claimed = False
        return {'claimed': claimed}
    if path == '/api/consult' and method == 'POST':
        question = short(data.get('question'), '질문', 1000)
        with storage.connection() as db:
            row = db.execute('SELECT text FROM contracts WHERE id=?', (data.get('contract_id'),)).fetchone()
        if not row: raise ValueError('보관한 계약을 먼저 선택하세요.')
        if data.get('mode') == 'ai':
            notes = call_ai(row['text'], question)
            return {'mode':'ai', 'label':'선택 계약에 근거한 AI 설명', 'notes':notes, 'evidence':[],
                    'answer': '인용문과 설명을 함께 확인하세요.' if notes else '선택한 계약 원문에서 확인할 수 없습니다.', 'general':'일반 법률·제도 정보는 제공하지 않습니다.'}
        return search_contract(row['text'], question)
    raise LookupError('요청 경로를 찾을 수 없습니다.')


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_): pass  # 원문·질문·키가 접근 로그에 남지 않게 한다.

    def respond(self, status, body, content_type='application/json; charset=utf-8'):
        if not isinstance(body, bytes): body = json.dumps(body, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        self.end_headers(); self.wfile.write(body)

    def handle_request(self):
        try:
            host = self.headers.get('Host', '')
            allowed = {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}
            if host not in allowed: return self.respond(403, {'error':'로컬 호스트로만 접속할 수 있습니다.'})
            path = urlparse(self.path).path
            if path.startswith('/api/'):
                data = {}
                if self.command != 'GET':
                    if self.headers.get('X-Requested-With') != 'contract-app': return self.respond(403, {'error':'요청 출처를 확인할 수 없습니다.'})
                    origin = self.headers.get('Origin')
                    if origin and origin not in {'http://'+x for x in allowed}: return self.respond(403, {'error':'외부 출처 요청을 거부했습니다.'})
                    if not self.headers.get('Content-Type', '').startswith('application/json'): raise ValueError('JSON 요청이 필요합니다.')
                    size = int(self.headers.get('Content-Length','0'))
                    if size > 14*1024*1024: return self.respond(413, {'error':'요청이 너무 큽니다. 파일은 10MB 이하입니다.'})
                    if size < 0: raise ValueError('요청 길이를 확인하세요.')
                    data = {} if size == 0 and self.command == 'DELETE' else json.loads(self.rfile.read(size))
                    if not isinstance(data, dict): raise ValueError('JSON 객체가 필요합니다.')
                return self.respond(200, api(self.command, path, data))
            if self.command != 'GET': raise LookupError()
            target = ROOT/'frontend'/({'/':'index.html'}.get(path, path.lstrip('/')))
            if not target.resolve().is_relative_to((ROOT/'frontend').resolve()) or not target.is_file(): raise LookupError()
            return self.respond(200, target.read_bytes(), mimetypes.guess_type(target)[0] or 'application/octet-stream')
        except AIError as exc: self.respond(502, {'error':str(exc)})
        except (ValueError, TypeError, KeyError) as exc: self.respond(400, {'error':str(exc) or '입력을 확인하세요.'})
        except LookupError: self.respond(404, {'error':'찾을 수 없습니다.'})
        except Exception: self.respond(500, {'error':'서버 처리 오류입니다. 입력을 보존하고 다시 시도하세요.'})

    do_GET = do_POST = do_PATCH = do_DELETE = do_PUT = handle_request


if __name__ == '__main__':
    load_env(); storage.init_db()
    port = int(os.getenv('PORT','8765'))
    print(f'내손을 java: http://127.0.0.1:{port}', flush=True)
    ThreadingHTTPServer(('127.0.0.1', port), Handler).serve_forever()
