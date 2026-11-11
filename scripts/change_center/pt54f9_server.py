#!/usr/bin/env python3
"""PT54-F9 local TEST Client Change Center. Never launches a deployment."""
from __future__ import annotations

import argparse
import json
import secrets
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from pt54f9_core import Invalid, assert_safe_root, create, edit, export_approved, load, transition, write
from pt54f10_settings import LABEL_SPECS, read as read_labels, save as save_labels

HERE = Path(__file__).resolve().parent
HTML = HERE / 'pt54f9_ui.html'
JS = HERE / 'pt54f9_ui.js'
MAX_JSON = 12000


class ChangeServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False

    def __init__(self, address: tuple[str, int], root: Path, repo: Path | None = None):
        if address[0] != '127.0.0.1':
            raise Invalid('Only loopback address 127.0.0.1 is permitted')
        root = root.expanduser().absolute()
        assert_safe_root(root)
        self.root = root
        self.repo = (repo if repo is not None else HERE.parents[1]).expanduser().absolute()
        self.csrf = secrets.token_urlsafe(32)
        self.write_lock = threading.Lock()
        super().__init__(address, ChangeHandler)


class ChangeHandler(BaseHTTPRequestHandler):
    server: ChangeServer

    def log_message(self, fmt: str, *args: object) -> None:
        print('Change Center:', fmt % args, file=sys.stderr)

    def send_bytes(self, payload: bytes, mime: str, status: int = 200) -> None:
        self.send_response(status)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(payload)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Content-Security-Policy',
                         "default-src 'none'; script-src 'self'; style-src 'unsafe-inline'; "
                         "connect-src 'self'; img-src 'self'; base-uri 'none'; "
                         "form-action 'none'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(payload)

    def respond(self, payload: dict, status: int = 200) -> None:
        self.send_bytes(json.dumps(payload, ensure_ascii=True).encode('utf-8'),
                        'application/json; charset=utf-8', status)

    def trusted_host(self) -> bool:
        return self.headers.get('Host', '') == f'127.0.0.1:{self.server.server_port}'

    def do_GET(self) -> None:
        if not self.trusted_host():
            return self.respond({'error': 'Use the 127.0.0.1 loopback URL'}, 403)
        path = urlsplit(self.path)
        if path.query:
            return self.respond({'error': 'Query parameters are not supported'}, 400)
        try:
            if path.path == '/':
                return self.send_bytes(HTML.read_bytes(), 'text/html; charset=utf-8')
            if path.path == '/change-center.js':
                return self.send_bytes(JS.read_bytes(), 'text/javascript; charset=utf-8')
            if path.path == '/api/presentation':
                with self.server.write_lock:
                    document = read_labels(self.server.repo)
                return self.respond({'document': document, 'specs': [
                    {'key': key, 'title': title, 'help': help_text}
                    for key, title, help_text in LABEL_SPECS]})
            if path.path == '/api/state':
                with self.server.write_lock:
                    current = load(self.server.root)
                return self.respond({'csrf': self.server.csrf, 'register': current,
                                     'root': str(self.server.root),
                                     'mode': 'Local TEST records; no site changes or deployment'})
            return self.respond({'error': 'Not found'}, 404)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            return self.respond({'error': str(exc)}, 400)

    def do_POST(self) -> None:
        if not self.trusted_host():
            return self.respond({'error': 'Use the 127.0.0.1 loopback URL'}, 403)
        if (self.headers.get('Origin') != f'http://127.0.0.1:{self.server.server_port}'
                or self.headers.get('X-PT54-CSRF') != self.server.csrf):
            return self.respond({'error': 'Cross-origin or missing CSRF token'}, 403)
        path = urlsplit(self.path)
        if path.query:
            return self.respond({'error': 'Query parameters are not supported'}, 400)
        if path.path not in ('/api/create', '/api/edit', '/api/status', '/api/export', '/api/presentation/save'):
            return self.respond({'error': 'Not found'}, 404)
        try:
            if self.headers.get('Content-Type', '').split(';')[0].strip() != 'application/json':
                raise Invalid('Expected application/json')
            length = self.headers.get('Content-Length', '')
            if not length.isdecimal() or not 0 < int(length) <= MAX_JSON:
                raise Invalid('Invalid JSON request size')
            payload = json.loads(self.rfile.read(int(length)).decode('utf-8'))
            if not isinstance(payload, dict):
                raise Invalid('Expected JSON object')
            with self.server.write_lock:
                if path.path == '/api/presentation/save':
                    receipt = save_labels(self.server.repo, self.server.root / 'presentation-backups', payload)
                    return self.respond({'ok': True, **receipt})
                doc = load(self.server.root)
                if path.path == '/api/create':
                    changed = create(doc, payload)
                elif path.path == '/api/edit':
                    changed = edit(doc, payload)
                elif path.path == '/api/status':
                    changed = transition(doc, payload)
                else:
                    receipt = export_approved(self.server.root, doc)
                    return self.respond({'ok': True, 'export': receipt})
                write(self.server.root, doc)
                return self.respond({'ok': True, 'request': changed, 'register_revision': doc['revision']})
        except (OSError, ValueError, KeyError, TypeError, UnicodeError, json.JSONDecodeError) as exc:
            return self.respond({'error': str(exc)}, 400)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=18175)
    parser.add_argument('--root', type=Path,
                        default=Path(__file__).resolve().parents[3] / 'dacqua-dolce_build-assets/change-center')
    args = parser.parse_args(argv)
    if not 1024 <= args.port <= 65535:
        parser.error('Port must be between 1024 and 65535')
    try:
        server = ChangeServer(('127.0.0.1', args.port), args.root)
    except (OSError, ValueError) as exc:
        print('STOP:', exc, file=sys.stderr)
        return 2
    print(f'PT54-F9 Client Change Center: http://127.0.0.1:{args.port}/', flush=True)
    print('Local TEST change tracking only; no automatic code, Git, or PROD changes', flush=True)
    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
