"""Loopback-only HTML form for saving agent-captured public DOM JSON on F:."""
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import csv
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'csl_2026_capture' / 'browser_dom'
FIXTURES = ROOT / 'data/csl/season_2026/guoan_fixtures_observed_2026.csv'
OUT.mkdir(parents=True, exist_ok=True)
PAGE = b'''<!doctype html><html><head><title>Local DOM archive</title></head><body>
<h1>Save captured public Sofascore DOM</h1>
<form method="POST"><label for="payload">DOM JSON</label><textarea id="payload" name="payload" rows="12" cols="90"></textarea>
<button type="submit">Save to F drive</button></form></body></html>'''

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/fixtures':
            with FIXTURES.open(encoding='utf-8-sig', newline='') as source:
                rows = list(csv.DictReader(source))
            body = json.dumps(rows, ensure_ascii=False).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path != '/':
            self.send_error(404)
            return
        with FIXTURES.open(encoding='utf-8-sig', newline='') as source:
            fixtures = list(csv.DictReader(source))
        fixture_json = json.dumps(fixtures, ensure_ascii=False).replace('<', '\\u003c')
        page = PAGE.replace(b'</body>',
                            ('<script id="fixtures" type="application/json">' + fixture_json + '</script></body>').encode('utf-8'))
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(page)))
        self.end_headers()
        self.wfile.write(page)

    def do_POST(self):
        from urllib.parse import parse_qs
        try:
            if self.headers.get('Host') != '127.0.0.1:8876':
                raise ValueError('Invalid host')
            if self.headers.get('Origin') != 'http://127.0.0.1:8876':
                raise ValueError('Only same-origin form submissions are supported')
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length < 8_000_000:
                raise ValueError('Invalid body size')
            payload = parse_qs(self.rfile.read(length).decode('utf-8'))['payload'][0]
            record = json.loads(payload)
            mid = str(record['match_id'])
            if not re.fullmatch(r'\d{6,12}', mid):
                raise ValueError('Invalid event ID')
            if not record['source_url'].startswith('https://www.sofascore.com/football/match/'):
                raise ValueError('Invalid source')
            digest = hashlib.sha256(payload.encode()).hexdigest()
            dest = OUT / f'{mid}_{digest[:12]}.json'
            # Content-addressed archive: no replacement of other observations.
            if not dest.exists():
                dest.write_text(payload, encoding='utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({'saved': str(dest), 'sha256': digest, 'match_id': mid}, ensure_ascii=False).encode())
        except Exception as exc:
            self.send_error(400, str(exc))

if __name__ == '__main__':
    print('Local archive form at http://127.0.0.1:8876 ; Ctrl+C to stop.', flush=True)
    HTTPServer(('127.0.0.1', 8876), Handler).serve_forever()
