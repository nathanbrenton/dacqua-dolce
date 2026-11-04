#!/usr/bin/env python3
"""Local-only, non-deploying client-change register and export.

Approval records a human decision, not an authenticated authorization or a
production deployment. Files are intentionally outside the application repo.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = 1
CATEGORIES = frozenset({'photography', 'caption', 'copy', 'presentation', 'accessibility', 'other'})
FAMILIES = frozenset({'refine', 'essence', 'harmony', 'origin', 'sitewide', 'unspecified'})
STATES = frozenset({'draft', 'in_review', 'approved', 'deferred', 'rejected'})
NEXT = {
    'draft': {'in_review', 'deferred'},
    'in_review': {'draft', 'approved', 'deferred', 'rejected'},
    'approved': {'in_review'},
    'deferred': {'draft'},
    'rejected': {'draft'},
}
SIZES = {'title': 120, 'reference': 200, 'before': 2000, 'after': 2000,
         'notes': 4000, 'acceptance': 2000, 'reviewer': 80}
MAX_RECORDS = 1000
MAX_FILE = 5 * 1024 * 1024
ID_RE = re.compile(r'^CR-\d{5}$')


class Invalid(ValueError):
    """Client-request validation failure."""


def stamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def _trusted_macos_alias(node: Path) -> bool:
    """Allow only Apple's fixed /var and /tmp links to their /private targets.

    macOS TemporaryDirectory() typically lives below /var/folders; rejecting
    that OS-managed alias breaks tests even though the target is legitimate.
    Arbitrary user-owned symlinks remain forbidden, including nested parents.
    """
    if sys.platform != 'darwin':
        return False
    destinations = {'/var': '/private/var', '/tmp': '/private/tmp'}
    target = destinations.get(str(node))
    return bool(target and node.is_dir() and node.resolve() == Path(target))


def assert_safe_root(root: Path) -> None:
    """Reject untrusted symlinked ancestors, including canonical ancestors."""
    original = Path(os.path.abspath(os.fspath(root.expanduser())))
    for node in (original, *original.parents):
        if node.is_symlink() and not _trusted_macos_alias(node):
            raise Invalid(f'Symlinked change-library path: {node}')
    canonical = original.resolve(strict=False)
    for node in (canonical, *canonical.parents):
        if node.is_symlink():
            raise Invalid(f'Symlinked change-library path: {node}')
    if original.exists() and not original.is_dir():
        raise Invalid('Change-library root must be a directory')


def path_for(root: Path) -> Path:
    assert_safe_root(root)
    return root / 'requests.json'


def fresh() -> dict:
    return {'schema_version': SCHEMA_VERSION, 'revision': 0, 'requests': []}


def _text(data: dict, key: str, required: bool = False) -> str:
    value = data.get(key, '')
    if not isinstance(value, str) or len(value) > SIZES[key] or '\x00' in value:
        raise Invalid(f'Invalid {key}; maximum {SIZES[key]} characters')
    value = value.strip()
    if required and not value:
        raise Invalid(f'{key} is required')
    return value


def _choice(data: dict, key: str, options: frozenset[str]) -> str:
    value = data.get(key)
    if not isinstance(value, str) or value not in options:
        raise Invalid(f'Unsupported {key}')
    return value


def _valid_doc(doc: object) -> dict:
    if not isinstance(doc, dict) or doc.get('schema_version') != SCHEMA_VERSION:
        raise Invalid('Unsupported change register schema')
    if not isinstance(doc.get('revision'), int) or doc['revision'] < 0:
        raise Invalid('Invalid register revision')
    rows = doc.get('requests')
    if not isinstance(rows, list) or len(rows) > MAX_RECORDS:
        raise Invalid('Invalid request list')
    identifiers = set()
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get('id'), str) or not ID_RE.fullmatch(row['id']):
            raise Invalid('Invalid request ID')
        if row['id'] in identifiers:
            raise Invalid('Duplicate request ID')
        identifiers.add(row['id'])
        if row.get('status') not in STATES or not isinstance(row.get('version'), int) or row['version'] < 1:
            raise Invalid('Invalid request status/version')
        if not isinstance(row.get('history'), list):
            raise Invalid('Invalid request history')
        for key in ('title', 'reference', 'before', 'after', 'notes', 'acceptance'):
            _text(row, key, required=key == 'title')
    return doc


def load(root: Path) -> dict:
    p = path_for(root)
    if p.is_symlink():
        raise Invalid('Symlinked request database rejected')
    if not p.exists():
        return fresh()
    if p.stat().st_size > MAX_FILE:
        raise Invalid('Request register exceeds maximum size')
    return _valid_doc(json.loads(p.read_text('utf-8')))


def _atomic(path: Path, payload: bytes) -> None:
    if path.is_symlink():
        raise Invalid('Refusing symlink file')
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.pt54f9-', dir=path.parent)
    try:
        os.chmod(tmp, 0o600)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def write(root: Path, doc: dict) -> None:
    root = root.expanduser().absolute()
    _valid_doc(doc)
    p = path_for(root)
    payload = (json.dumps(doc, indent=2, ensure_ascii=False) + '\n').encode('utf-8')
    if len(payload) > MAX_FILE:
        raise Invalid('Change register too large')
    root.mkdir(parents=True, exist_ok=True)
    backups = root / 'backups'
    if backups.is_symlink():
        raise Invalid('Unsafe backups directory')
    if p.exists():
        backups.mkdir(exist_ok=True)
        name = f'requests-rev{doc["revision"] - 1:06d}-{datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")}.json'
        old = p.read_bytes()
        if len(old) > MAX_FILE:
            raise Invalid('Existing register too large')
        target = backups / name
        with target.open('xb') as f:
            f.write(old)
    _atomic(p, payload)


def _check_version(row: dict, expected: object) -> None:
    if not isinstance(expected, int) or isinstance(expected, bool) or expected != row['version']:
        raise Invalid('Request changed since you opened it. Refresh before editing.')


def _find(doc: dict, ident: object) -> dict:
    if not isinstance(ident, str) or not ID_RE.fullmatch(ident):
        raise Invalid('Unknown request ID')
    for row in doc['requests']:
        if row['id'] == ident:
            return row
    raise Invalid('Unknown request ID')


def create(doc: dict, payload: dict) -> dict:
    if len(doc['requests']) >= MAX_RECORDS:
        raise Invalid('Request limit reached')
    details = {key: _text(payload, key, required=key == 'title') for key in
               ('title', 'reference', 'before', 'after', 'notes', 'acceptance')}
    details['category'] = _choice(payload, 'category', CATEGORIES)
    details['family'] = _choice(payload, 'family', FAMILIES)
    numeric = max((int(r['id'][3:]) for r in doc['requests']), default=0) + 1
    if numeric > 99999:
        raise Invalid('Request ID limit reached')
    ident = f'CR-{numeric:05d}'
    now = stamp()
    row = {'id': ident, **details, 'status': 'draft', 'version': 1,
           'created_utc': now, 'updated_utc': now, 'reviewer': '',
           'approved_utc': None,
           'history': [{'at': now, 'action': 'created', 'actor': 'local editor'}]}
    doc['requests'].append(row)
    doc['revision'] += 1
    return row


def edit(doc: dict, payload: dict) -> dict:
    row = _find(doc, payload.get('id'))
    _check_version(row, payload.get('expected_version'))
    if row['status'] not in ('draft', 'in_review'):
        raise Invalid('Reopen this request before editing an approved/deferred/rejected item')
    fields = {key: _text(payload, key, required=key == 'title') for key in
              ('title', 'reference', 'before', 'after', 'notes', 'acceptance')}
    fields['category'] = _choice(payload, 'category', CATEGORIES)
    fields['family'] = _choice(payload, 'family', FAMILIES)
    if all(row.get(k) == v for k, v in fields.items()):
        raise Invalid('No changes to save')
    row.update(fields)
    now = stamp()
    row['updated_utc'] = now
    row['version'] += 1
    row['history'].append({'at': now, 'action': 'edited', 'actor': 'local editor'})
    doc['revision'] += 1
    return row


def transition(doc: dict, payload: dict) -> dict:
    row = _find(doc, payload.get('id'))
    _check_version(row, payload.get('expected_version'))
    target = payload.get('status')
    if target not in NEXT[row['status']]:
        raise Invalid(f'Invalid transition from {row["status"]} to {target}')
    actor = 'local editor'
    if target == 'approved':
        actor = _text(payload, 'reviewer', required=True)
        if payload.get('confirmation') != f'APPROVE {row["id"]}':
            raise Invalid(f'Approval requires typing APPROVE {row["id"]}')
        if not row['after']:
            raise Invalid('A proposed after-state is required before approval')
        row['reviewer'] = actor
        row['approved_utc'] = stamp()
    elif row['status'] == 'approved':
        row['approved_utc'] = None
        row['reviewer'] = ''
    now = stamp()
    prev = row['status']
    row['status'], row['updated_utc'] = target, now
    row['version'] += 1
    row['history'].append({'at': now, 'action': f'{prev} → {target}', 'actor': actor})
    doc['revision'] += 1
    return row


def export_approved(root: Path, doc: dict) -> dict:
    """Export review evidence, never executable commands or code changes."""
    root = root.expanduser().absolute()
    assert_safe_root(root)
    selected = [dict(r) for r in doc['requests'] if r['status'] == 'approved']
    if not selected:
        raise Invalid('No approved change requests to export')
    directory = root / 'exports'
    if directory.is_symlink():
        raise Invalid('Unsafe export directory')
    directory.mkdir(parents=True, exist_ok=True)
    output = {'schema_version': 1, 'source_register_revision': doc['revision'],
              'created_utc': stamp(), 'purpose': 'planning evidence; not production publication',
              'approved_requests': selected}
    payload = (json.dumps(output, indent=2, ensure_ascii=False) + '\n').encode('utf-8')
    filename = 'approved-requests-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '.json'
    path = directory / filename
    with path.open('xb') as file:
        file.write(payload)
    return {'file': str(path), 'sha256': hashlib.sha256(payload).hexdigest(),
            'count': len(selected), 'note': 'Evidence only. Does not modify TEST or PROD source.'}
