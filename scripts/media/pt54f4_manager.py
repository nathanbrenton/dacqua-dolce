#!/usr/bin/env python3
"""PT54-F4 local-only Media Manager for reviewed, TEST-only product photographs.

Never connects to a production host, alters SQL, commits Git, or auto-publishes.
An intentional publish action invokes the verified F3 publication boundary.
"""
from __future__ import annotations

import argparse
import json
import os
import secrets
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from pt54f1_media import REPO_ROOT, default_asset_root, parse_asset_name, scan_inbox
from pt54f2_prepare import MAX_PIXELS, Rejected, inspect_candidate, prepare, verify as verify_batch
from pt54f3_publish import load_index, plan, publish
from pt54f5_library import current_library, library_image
from pt54f6_captions import load_captions, save_caption
from pt54f10m_theme import theme_options, theme_stylesheet, theme_logo

MAX_UPLOAD = 64 * 1024 * 1024
MAX_JSON = 8192
MAX_BATCHES = 200
ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'webp', 'tif', 'tiff'}
ALLOWED_ROLES = {'system', 'tank', 'valve', 'brine', 'pureline', 'cartridge',
                 'detail', 'angle', 'hookup', 'membrane', 'faucet'}
PAGE_PATH = Path(__file__).with_name('pt54f4_ui.html')
JS_PATH = Path(__file__).with_name('pt54f4_ui.js')


def safe_name(fields: dict[str, object]) -> str:
    """Build a canonical future-photo filename; never trust an uploaded filename."""
    family = fields.get('family')
    if family not in ('refine', 'essence', 'harmony', 'origin'):
        raise Rejected('Choose a supported product family')
    role, ext = fields.get('role'), fields.get('extension')
    if role not in ALLOWED_ROLES or ext not in ALLOWED_EXT:
        raise Rejected('Unsupported image role or file extension')
    try:
        sequence, version = int(fields['sequence']), int(fields['version'])
    except (KeyError, ValueError, TypeError) as exc:
        raise Rejected('Sequence and version must be whole numbers') from exc
    if (str(fields['sequence']) != str(sequence) or str(fields['version']) != str(version)
            or not (1 <= sequence <= 99 and 1 <= version <= 99)):
        raise Rejected('Sequence and version must be 1–99')
    if role == 'brine' and family != 'refine':
        raise Rejected('Brine role is Refine-only')
    if role in ('membrane', 'faucet') and family != 'origin':
        raise Rejected('Membrane and faucet roles are Origin-only')
    if family in ('refine', 'essence'):
        size, material, valve, style = (fields.get(k) for k in ('size', 'material', 'valve', 'style'))
        if (size not in ('1-5', '2-0') or material not in ('stainless', 'neoprene')
                or valve not in ('clack3', 'clack5', 'performance')
                or style not in ('archetype', 'realistic')):
            raise Rejected('Invalid tank, valve, or image-style combination')
        base = f'{family}_{size}_{material}_{valve}_{style}'
    elif family == 'harmony':
        size, material = fields.get('size'), fields.get('material')
        if size not in ('1-5', '2-0') or material not in ('stainless', 'neoprene'):
            raise Rejected('Invalid Harmony size or jacket selection')
        base = f'harmony_{size}_{material}'
    else:
        variant = fields.get('variant')
        if variant not in ('standard', 'remineralization'):
            raise Rejected('Invalid Origin variant')
        base = f'origin_{variant}'
    name = f'{base}_{role}_{sequence:02d}_v{version:02d}.{ext}'
    parse_asset_name(name)
    return name


def approved_dirs(repo: Path, root: Path) -> None:
    if repo.is_symlink() or root.is_symlink() or not repo.is_dir() or not root.is_dir():
        raise Rejected('Expected non-symlink local TEST repository and photo library')
    if not (repo / 'frontend/src/components/catalog/publishedPhotoIndex.json').is_file():
        raise Rejected('F3 publication index not installed')
    for child in ('ingest-drop', 'staging', 'masters', 'receipts'):
        dest = root / child
        if not dest.is_dir() or dest.is_symlink():
            raise Rejected('Missing or unsafe photo-library folder: ' + child)


def save_upload(repo: Path, root: Path, fields: dict[str, object], content: bytes) -> dict:
    """Exclusive intake write, verified by the same F2 candidate gate used later."""
    approved_dirs(repo, root)
    name = safe_name(fields)
    if not content or len(content) > MAX_UPLOAD:
        raise Rejected('Upload must be between 1 byte and 64 MiB')
    intake = root / 'ingest-drop'
    dest = intake / name
    if dest.exists() or dest.is_symlink():
        raise Rejected('Intake filename already exists; choose a new version or slot')
    fd = None
    created = False
    try:
        fd = os.open(dest, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0), 0o600)
        created = True
        with os.fdopen(fd, 'wb') as out:
            fd = None
            out.write(content)
            out.flush()
            os.fsync(out.fileno())
        report = inspect_candidate(dest, intake)
        if report['image']['width'] * report['image']['height'] > MAX_PIXELS:
            raise Rejected('Source exceeds pixel safety limit')
        return {'name': name, 'bytes': len(content), 'image': report['image'],
                'sha256': report['sha256'], 'status': 'intake_only'}
    except Exception:
        if created and dest.is_file() and not dest.is_symlink():
            dest.unlink()
        raise
    finally:
        if fd is not None:
            os.close(fd)


def batch_dir(root: Path, name: str) -> Path:
    if not isinstance(name, str) or len(name) > 100 or not name.startswith('batch-') \
            or not all(c.isascii() and (c.isalnum() or c == '-') for c in name):
        raise Rejected('Invalid batch ID')
    path = root / 'staging' / name
    if path.is_symlink() or not path.is_dir() or path.parent != root / 'staging':
        raise Rejected('Unknown or unsafe batch')
    return path


def batch_summary(root: Path, name: str) -> dict:
    path = batch_dir(root, name)
    verify_batch(path)
    data = json.loads((path / 'batch.json').read_text('utf-8'))
    items = []
    for index, entry in enumerate(data['items']):
        items.append({'name': entry['name'], 'conflicts': entry['conflicts'],
                      'preview': f'/preview/{name}/{index}',
                      'manifest': entry['manifest']})
    return {'name': name, 'count': len(items), 'items': items, 'created_utc': data['created_utc'],
            'status': 'review_pending'}


def current_state(repo: Path, root: Path) -> dict:
    approved_dirs(repo, root)
    found = scan_inbox(root / 'ingest-drop')
    index = load_index(repo, check_assets=True)
    staging = root / 'staging'
    batches = []
    for path in sorted(staging.glob('batch-*'), key=lambda p: p.name, reverse=True):
        if path.is_dir() and not path.is_symlink() and len(batches) < MAX_BATCHES:
            batches.append({'name': path.name, 'published':
                            (root / 'receipts' / (path.name + '.json')).is_file()})
    return {'intake': found, 'batches': batches, 'published_count': len(index['entries']),
            'root': str(root), 'repo': str(repo), 'mode': 'TEST only — local browser'}


class MediaManagerServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False

    def __init__(self, address: tuple[str, int], repo: Path, root: Path):
        if address[0] != '127.0.0.1':
            raise Rejected('Media Manager may bind only to 127.0.0.1')
        self.repo, self.asset_root = repo, root
        self.csrf = secrets.token_urlsafe(32)
        self.change_lock = threading.Lock()
        approved_dirs(repo, root)
        super().__init__(address, MediaManagerHandler)


class MediaManagerHandler(BaseHTTPRequestHandler):
    server: MediaManagerServer

    def log_message(self, fmt: str, *args: object) -> None:
        # Keep the local server log free of raw image bytes and secrets.
        print('Media Manager:', fmt % args, file=sys.stderr)

    def send_data(self, body: bytes, kind: str, status: int = 200) -> None:
        self.send_response(status)
        self.send_header('Content-Type', kind)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Content-Security-Policy',
                         "default-src 'none'; script-src 'self'; style-src 'unsafe-inline'; "
                         "img-src 'self'; connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)

    def respond(self, obj: dict, status: int = 200) -> None:
        self.send_data(json.dumps(obj, ensure_ascii=True).encode('utf-8'),
                       'application/json; charset=utf-8', status)

    def trusted_host(self) -> bool:
        host = self.headers.get('Host', '')
        return host == f'127.0.0.1:{self.server.server_port}'

    def deny_host(self) -> bool:
        if not self.trusted_host():
            self.respond({'error': 'Invalid host: use http://127.0.0.1 locally'}, 403)
            return True
        return False

    def do_GET(self) -> None:
        if self.deny_host():
            return
        url = urlsplit(self.path)
        try:
            if url.path == '/':
                return self.send_data(PAGE_PATH.read_bytes(), 'text/html; charset=utf-8')
            if url.path == '/media-manager.js':
                return self.send_data(JS_PATH.read_bytes(), 'text/javascript; charset=utf-8')
            if url.path == '/media-theme.js':
                return self.send_data(Path(__file__).with_name('pt54f10m_theme.js').read_bytes(),
                                      'text/javascript; charset=utf-8')
            if url.path == '/media-theme.css':
                return self.send_data(Path(__file__).with_name('pt54f10m_theme.css').read_bytes(),
                                      'text/css; charset=utf-8')
            if url.path == '/site-theme-tokens.css':
                return self.send_data(theme_stylesheet(self.server.repo), 'text/css; charset=utf-8')
            if url.path == '/api/theme-options':
                return self.respond(theme_options(self.server.repo))
            if url.path == '/site-logo':
                fields = parse_qs(url.query)
                if set(fields) != {'id'} or len(fields['id']) != 1:
                    raise Rejected('Choose a valid logo')
                return self.send_data(theme_logo(self.server.repo, fields['id'][0]), 'image/webp')
            if url.path == '/api/state':
                result = current_state(self.server.repo, self.server.asset_root)
                result['csrf'] = self.server.csrf
                return self.respond(result)
            if url.path == '/api/library':
                rows = current_library(self.server.repo)
                _, caption_etag = load_captions(self.server.repo)
                return self.respond({'source': 'local TEST registry, not live PROD',
                                     'count': len(rows), 'configurations': rows,
                                     'caption_etag': caption_etag})
            if url.path == '/api/library-image':
                query = parse_qs(url.query)
                if any(len(query.get(k, [])) != 1 for k in ('key', 'photo', 'size')):
                    raise Rejected('Image preview requires one key, photo, and size')
                content, kind = library_image(self.server.repo, query['key'][0],
                                              query['photo'][0], query['size'][0])
                return self.send_data(content, kind)
            if url.path == '/api/batch':
                name = parse_qs(url.query).get('name', [''])[0]
                return self.respond(batch_summary(self.server.asset_root, name))
            if url.path.startswith('/preview/'):
                parts = url.path.split('/')
                if len(parts) != 4 or not parts[3].isdigit():
                    raise Rejected('Unsupported preview')
                batch = batch_dir(self.server.asset_root, parts[2])
                data = json.loads((batch / 'batch.json').read_text('utf-8'))
                index = int(parts[3])
                if index < 0 or index >= len(data['items']):
                    raise Rejected('Unknown preview index')
                entry = data['items'][index]
                # Only F2-verified derivative thumbnails, never arbitrary filesystem paths.
                from pt54f1_media import safe_relative_path, within_root
                rel = entry['thumbnail']
                if not safe_relative_path(rel) or not rel.endswith('.webp'):
                    raise Rejected('Invalid thumbnail path')
                source = batch / rel
                if not within_root(source, batch) or source.is_symlink() or not source.is_file():
                    raise Rejected('Missing or unsafe thumbnail')
                return self.send_data(source.read_bytes(), 'image/webp')
            return self.respond({'error': 'Not found'}, 404)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            return self.respond({'error': str(exc)}, 400)

    def read_json(self) -> dict:
        length = self.request_length(MAX_JSON)
        if self.headers.get('Content-Type', '').split(';')[0].strip() != 'application/json':
            raise Rejected('Expected application/json')
        data = json.loads(self.rfile.read(length).decode('utf-8'))
        if not isinstance(data, dict):
            raise Rejected('Expected JSON object')
        return data

    def request_length(self, maximum: int) -> int:
        raw = self.headers.get('Content-Length', '')
        if not raw.isdigit():
            raise Rejected('Content-Length required')
        length = int(raw)
        if not 0 < length <= maximum:
            raise Rejected('Request size exceeds allowed limit')
        return length

    def do_POST(self) -> None:
        if self.deny_host():
            return
        origin = self.headers.get('Origin', '')
        if origin != f'http://127.0.0.1:{self.server.server_port}' or \
                self.headers.get('X-PT54-CSRF') != self.server.csrf:
            return self.respond({'error': 'Rejected cross-origin or missing CSRF token'}, 403)
        url = urlsplit(self.path)
        try:
            with self.server.change_lock:
                repo, root = self.server.repo, self.server.asset_root
                if url.path == '/api/upload':
                    if self.headers.get('Content-Type', '').split(';')[0] != 'application/octet-stream':
                        raise Rejected('Upload must be a raw image stream')
                    length = self.request_length(MAX_UPLOAD)
                    fields = {key: val[0] for key, val in parse_qs(url.query).items() if len(val) == 1}
                    result = save_upload(repo, root, fields, self.rfile.read(length))
                    return self.respond({'ok': True, 'upload': result})
                payload = self.read_json()
                if url.path == '/api/caption':
                    result = save_caption(repo, root, payload.get('key'), payload.get('photo_id'),
                                          payload.get('scope'), payload.get('caption'),
                                          payload.get('expected_etag'))
                    return self.respond({'ok': True, **result, 'note': 'TEST JSON only; not Git/PROD'})
                if url.path == '/api/prepare':
                    filename = payload.get('filename')
                    if filename is not None and (not isinstance(filename, str) or \
                            filename != Path(filename).name or '\\' in filename):
                        raise Rejected('Invalid intake filename')
                    new_batch = prepare(root, repo, filename)
                    verify_batch(new_batch)
                    return self.respond({'ok': True, 'batch': batch_summary(root, new_batch.name)})
                if url.path == '/api/plan':
                    batch = batch_dir(root, payload.get('batch', ''))
                    items, _ = plan(root, repo, batch)
                    rows = []
                    for item in items:
                        info = item['source']['source']
                        rows.append({'name': info['name'], 'configuration': item['configuration'],
                                     'role': info['identity']['role'], 'sequence': info['identity']['sequence'],
                                     'version': info['identity']['version']})
                    return self.respond({'ok': True, 'batch': batch.name, 'items': rows,
                                         'note': 'Plan only; nothing published'})
                if url.path == '/api/publish':
                    name = payload.get('batch', '')
                    if payload.get('approval') != name or payload.get('confirmed') is not True:
                        raise Rejected('Publication requires exact batch name and affirmative confirmation')
                    batch = batch_dir(root, name)
                    if (root / 'receipts' / (name + '.json')).exists():
                        raise Rejected('Batch already published')
                    receipt = publish(root, repo, batch, name)
                    return self.respond({'ok': True, 'batch': name, 'receipt': str(receipt),
                                         'note': 'Published to local TEST source only; not Git/PROD'})
                return self.respond({'error': 'Not found'}, 404)
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
            return self.respond({'error': str(exc)}, 400)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=REPO_ROOT)
    parser.add_argument('--asset-root', type=Path, default=default_asset_root())
    parser.add_argument('--port', type=int, default=18174)
    args = parser.parse_args(argv)
    if not (1024 <= args.port <= 65535):
        parser.error('Port must be between 1024 and 65535')
    try:
        server = MediaManagerServer(('127.0.0.1', args.port), args.repo.expanduser(),
                                    args.asset_root.expanduser())
    except (OSError, ValueError) as exc:
        print('STOP:', exc, file=sys.stderr)
        return 2
    print('PT54-F4 TEST Media Manager: http://127.0.0.1:' + str(args.port), flush=True)
    print('Local browser only; no production connection or automatic publication', flush=True)
    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
