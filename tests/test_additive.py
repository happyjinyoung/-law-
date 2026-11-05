import hashlib
import json
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
import run


class AdditiveTests(unittest.TestCase):
    def test_preserved_five_originals(self):
        self.assertEqual(run.verify_originals(),5)

    def test_original_routes_send_exact_bytes(self):
        server=ThreadingHTTPServer(('127.0.0.1',0),run.Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            for item in json.loads((run.ROOT/'ORIGINAL_FILES.json').read_text(encoding='utf-8'))['files']:
                with urllib.request.urlopen(f'http://127.0.0.1:{server.server_port}/'+item['path']) as response:
                    self.assertEqual(hashlib.sha256(response.read()).hexdigest(),item['sha256'])
            with urllib.request.urlopen(f'http://127.0.0.1:{server.server_port}/added/') as response:
                self.assertIn("frame-ancestors 'self'",response.headers['Content-Security-Policy'])
                self.assertIn('내손을 java',response.read().decode())
        finally:server.shutdown();server.server_close();thread.join()


if __name__=='__main__':unittest.main()
