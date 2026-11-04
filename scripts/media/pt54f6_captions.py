#!/usr/bin/env python3
"""PT54-F6 reviewed TEST photo subtitle overrides (metadata only; no image mutation)."""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from pt54f2_prepare import Rejected

CAPTION_PATH = Path('frontend/src/components/catalog/photoCaptionOverrides.json')
FAMILIES = frozenset({'refine', 'essence', 'harmony', 'origin'})
PHOTO_ID = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
MAX_CAPTION = 96


def caption_file(repo: Path) -> Path:
    source = repo / CAPTION_PATH
    if repo.is_symlink() or not repo.is_dir() or not source.is_file():
        raise Rejected('Missing approved TEST caption file')
    item = source
    while item != repo:
        if item.is_symlink():
            raise Rejected('Symlinked caption file/path is forbidden')
        item = item.parent
    return source


def load_captions(repo: Path) -> tuple[dict, str]:
    raw = caption_file(repo).read_bytes()
    if len(raw) > 512 * 1024:
        raise Rejected('Caption file exceeds safety limit')
    digest = hashlib.sha256(raw).hexdigest()
    try:
        doc = json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise Rejected('Invalid caption JSON') from exc
    if not isinstance(doc, dict) or set(doc) != {'schema_version', 'families', 'configurations'} \
            or doc['schema_version'] != 1:
        raise Rejected('Unknown caption schema')
    for scope in ('families', 'configurations'):
        mapping = doc[scope]
        if not isinstance(mapping, dict):
            raise Rejected('Malformed caption scope')
        for key, entries in mapping.items():
            if scope == 'families':
                valid = key in FAMILIES
            else:
                valid = isinstance(key, str) and len(key) < 130 and key.split(':')[0] in FAMILIES \
                    and all(re.fullmatch(r'[a-zA-Z0-9.\-]+', part) for part in key.split(':'))
            if not valid or not isinstance(entries, dict) or not entries:
                raise Rejected('Malformed caption key')
            for photo_id, caption in entries.items():
                if not isinstance(photo_id, str) or not PHOTO_ID.fullmatch(photo_id):
                    raise Rejected('Invalid photo identifier')
                _check_caption(caption, allow_empty=False)
    return doc, digest


def _check_caption(value: object, allow_empty: bool = True) -> str:
    if not isinstance(value, str) or len(value) > MAX_CAPTION or any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise Rejected('Caption must be plain text (96 characters maximum; no line breaks)')
    if value != value.strip():
        raise Rejected('Trim surrounding whitespace before saving')
    if not value and not allow_empty:
        raise Rejected('Saved caption cannot be empty')
    return value


def caption_metadata(doc: dict, family: str, configuration: str, photo_id: str, base: str) -> dict:
    inherited = doc['families'].get(family, {}).get(photo_id)
    specific = doc['configurations'].get(configuration, {}).get(photo_id)
    return {
        'base_label': base,
        'label': specific if specific is not None else (inherited if inherited is not None else base),
        'caption_source': 'configuration' if specific is not None else ('family' if inherited is not None else 'original'),
        'family_caption': inherited or '',
        'configuration_caption': specific or '',
    }


def save_caption(repo: Path, asset_root: Path, key: object, photo_id: object,
                 scope: object, caption: object, expected_etag: object) -> dict:
    """Protect against stale client edits, fake IDs and unexpected filesystem writes."""
    if scope not in ('family', 'configuration') or not isinstance(key, str) or \
            not isinstance(photo_id, str) or not PHOTO_ID.fullmatch(photo_id):
        raise Rejected('Invalid caption target')
    if not isinstance(expected_etag, str) or not re.fullmatch(r'[a-f0-9]{64}', expected_etag):
        raise Rejected('Missing valid caption file version; refresh first')
    caption = _check_caption(caption)
    from pt54f5_library import current_library
    row = next((r for r in current_library(repo) if r['key'] == key), None)
    if row is None or not any(p['id'] == photo_id for p in row['photos']):
        raise Rejected('Caption target is not in the selected TEST gallery')
    path = caption_file(repo)
    doc, digest = load_captions(repo)
    if digest != expected_etag:
        raise Rejected('Caption file changed; refresh library before saving')
    target = doc['families'] if scope == 'family' else doc['configurations']
    name = row['family'] if scope == 'family' else key
    entries = dict(target.get(name, {}))
    if caption:
        entries[photo_id] = caption
    else:
        entries.pop(photo_id, None)
    if entries:
        target[name] = entries
    else:
        target.pop(name, None)
    content = (json.dumps(doc, indent=2, ensure_ascii=False, sort_keys=True) + '\n').encode('utf-8')
    if content == path.read_bytes():
        return {'changed': False, 'etag': digest}
    # Verify new document meets the same strict schema before changing source.
    if len(content) > 512 * 1024:
        raise Rejected('Caption file exceeds safety limit')
    if asset_root.is_symlink() or not asset_root.is_dir():
        raise Rejected('Missing safe asset library')
    receipts = asset_root / 'receipts'
    if receipts.is_symlink() or not receipts.is_dir():
        raise Rejected('Missing safe receipt folder')
    backup_dir = receipts / 'caption-backups'
    backup_dir.mkdir(exist_ok=True)
    if backup_dir.is_symlink():
        raise Rejected('Unsafe caption backup directory')
    original = path.read_bytes()
    backup_name = f'caption-before-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}-{uuid4().hex[:12]}.json'
    with (backup_dir / backup_name).open('xb') as output:
        output.write(original)
    fd, temporary = tempfile.mkstemp(prefix='.pt54f6-', suffix='.json', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as output:
            output.write(content)
            output.flush()
            os.fsync(output.fileno())
        os.chmod(temporary, path.stat().st_mode & 0o777)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return {'changed': True, 'etag': hashlib.sha256(content).hexdigest(),
            'backup': str(backup_dir / backup_name)}
