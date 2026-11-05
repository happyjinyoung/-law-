"""원본 파일을 수정하지 않고 원본 UI와 추가 서버 기능을 함께 제공한다."""
import hashlib
import json
import mimetypes
import os
import sys
from pathlib import Path
from http.server import ThreadingHTTPServer
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parent
SERVICE=ROOT/'extensions'/'server-assistant'
sys.path.insert(0,str(SERVICE))
import server as service
from backend import storage


def verify_originals():
    manifest=json.loads((ROOT/'ORIGINAL_FILES.json').read_text(encoding='utf-8'))
    for item in manifest['files']:
        path=ROOT/item['path']
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:
            raise RuntimeError('원본 파일 변경 감지: '+item['path'])
    return len(manifest['files'])


class Handler(service.Handler):
    def handle_request(self):
        path=urlparse(self.path).path
        allowed={f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'}
        if self.headers.get('Host','') not in allowed:
            return self.respond(403,{'error':'로컬 호스트 접속만 허용합니다.'})
        static={
            '/':ROOT/'extensions'/'launcher.html',
            '/launcher.js':ROOT/'extensions'/'launcher.js',
            '/launcher.css':ROOT/'extensions'/'launcher.css',
            '/original-bridge.js':ROOT/'extensions'/'original-bridge.js',
            '/service-bridge.js':ROOT/'extensions'/'service-bridge.js',
            '/index.html':ROOT/'index.html',
            '/css/style.css':ROOT/'css'/'style.css',
            '/js/app.js':ROOT/'js'/'app.js',
            '/js/analyzer.js':ROOT/'js'/'analyzer.js',
            '/js/rules.js':ROOT/'js'/'rules.js',
        }
        if self.command=='GET' and path in static:
            target=static[path]
            # 원본은 인라인 이벤트·CDN·웹 OCR을 사용한다. 그 문서의 기존 동작을 보존한다.
            original=path=='/index.html'
            body=target.read_bytes();self.send_response(200)
            self.send_header('Content-Type',(mimetypes.guess_type(target)[0] or 'application/octet-stream')+'; charset=utf-8')
            self.send_header('Content-Length',str(len(body)))
            self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
            if not original:
                self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; frame-src 'self'; frame-ancestors 'self'; base-uri 'none'")
            else:
                self.send_header('Content-Security-Policy',"frame-ancestors 'self'")
            self.end_headers();self.wfile.write(body);return
        if path=='/added/' and self.command=='GET':
            previous=self.path;self.path='/'
            try:return super().handle_request()
            finally:self.path=previous
        return super().handle_request()

    def respond(self,status,body,content_type='application/json; charset=utf-8'):
        # 추가 화면을 같은 로컬 실행 창에 넣을 수 있게 상위 프레임을 동일 출처로 제한한다.
        if not isinstance(body,bytes):body=json.dumps(body,ensure_ascii=False).encode('utf-8')
        self.send_response(status);self.send_header('Content-Type',content_type)
        self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'self'; base-uri 'none'; form-action 'self'")
        self.end_headers();self.wfile.write(body)

    do_GET=do_POST=do_PATCH=do_DELETE=do_PUT=handle_request


if __name__=='__main__':
    count=verify_originals();service.load_env();storage.init_db()
    port=int(os.getenv('PORT','8766'))
    print(f'배포 파일 {count}개 SHA-256 일치. 실행: http://127.0.0.1:{port}',flush=True)
    ThreadingHTTPServer(('127.0.0.1',port),Handler).serve_forever()
