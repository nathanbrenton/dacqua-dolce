#!/usr/bin/env python3
"""PT54-F10: bounded, source-controlled presentation wording for local TEST.

Only known low-risk product-page labels; no pricing, purchase options,
product identifiers, legal text, or backend settings can be changed here.
"""
from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from pt54f9_core import Invalid, assert_safe_root

LABEL_SPECS = (
    ('overview_heading', 'Product overview heading', 'The section above the system description'),
    ('tank_size_label', 'Tank size selector', 'Refine, Essence and Harmony sizing label'),
    ('system_configuration_label', 'System configuration selector', 'Origin configuration selector label'),
    ('fitting_size_label', 'Fitting size selector', 'The connection-size control label'),
    ('fitting_type_label', 'Fitting type selector', 'The connection-type control label'),
    ('connection_size_prompt', 'Fitting size placeholder', 'Displayed until a size is selected'),
    ('pureline_configuration_label', 'Pureline configuration selector', 'Harmony Pureline option selector'),
    ('system_size_heading', 'System size heading', 'Additional product variant section'),
    ('media_volume_label', 'Media volume selector', 'Additional product variant label'),
)
DEFAULTS = dict(zip(
    (x[0] for x in LABEL_SPECS),
    ('System overview', 'TANK SIZE', 'SYSTEM CONFIGURATION', 'FITTING SIZE',
     'FITTING TYPE', 'Choose connection size', 'PURELINE CONFIGURATION',
     'Select system size', 'MEDIA VOLUME'),
))
RELATIVE = Path('frontend/src/components/catalog/presentationLabels.json')
MAX_LEN = 80
MAX_FILE = 16384


def target_file(repo: Path) -> Path:
    repo = repo.expanduser().absolute()
    assert_safe_root(repo)
    if not repo.is_dir():
        raise Invalid('Missing repository directory')
    dest = repo / RELATIVE
    assert_safe_root(dest.parent)
    if not dest.is_file() or dest.is_symlink():
        raise Invalid('Presentation settings file missing or symlinked')
    return dest


def valid(doc: object) -> dict:
    if not isinstance(doc, dict) or set(doc) != {'schema_version', 'revision', 'labels'} or doc['schema_version'] != 1:
        raise Invalid('Unsupported presentation settings schema')
    if type(doc['revision']) is not int or doc['revision'] < 0:
        raise Invalid('Invalid presentation settings revision')
    labels = doc['labels']
    if not isinstance(labels, dict) or set(labels) != set(DEFAULTS):
        raise Invalid('Unknown or missing presentation label')
    for key, value in labels.items():
        if (not isinstance(value, str) or not value.strip() or value != value.strip()
                or len(value) > MAX_LEN or any(ord(c) < 32 or ord(c) == 127 for c in value)
                or '<' in value or '>' in value):
            raise Invalid(f'Invalid {key} label: plain text, 1-{MAX_LEN} characters required')
    return doc


def read(repo: Path) -> dict:
    path = target_file(repo)
    if path.stat().st_size > MAX_FILE:
        raise Invalid('Presentation settings file too large')
    return valid(json.loads(path.read_text('utf-8')))


def save(repo: Path, backup_root: Path, payload: dict) -> dict:
    if not isinstance(payload, dict) or set(payload) != {'expected_revision', 'labels'}:
        raise Invalid('Unexpected presentation settings request fields')
    previous = read(repo)
    expected = payload['expected_revision']
    if type(expected) is not int or expected != previous['revision']:
        raise Invalid('Presentation settings changed. Refresh before saving.')
    new = {'schema_version': 1, 'revision': expected + 1, 'labels': payload['labels']}
    valid(new)
    if new['labels'] == previous['labels']:
        raise Invalid('No changes to save')

    # Never store executable or dynamic content. The only output is static JSON.
    dest = target_file(repo)
    backup_root = backup_root.expanduser().absolute()
    assert_safe_root(backup_root)
    if backup_root.is_symlink():
        raise Invalid('Symlinked backup directory')
    backup_root.mkdir(parents=True, exist_ok=True)
    name = 'presentation-r' + str(previous['revision']).zfill(4) + '-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '.json'
    previous_bytes = dest.read_bytes()
    with (backup_root / name).open('xb') as fh:
        fh.write(previous_bytes)
        fh.flush()
        os.fsync(fh.fileno())
    new_bytes = (json.dumps(new, indent=2, ensure_ascii=False) + '\n').encode('utf-8')
    fd, tmp = tempfile.mkstemp(prefix='.pt54f10-', dir=dest.parent)
    try:
        with os.fdopen(fd, 'wb') as fh:
            fh.write(new_bytes)
            fh.flush()
            os.fsync(fh.fileno())
        os.chmod(tmp, dest.stat().st_mode & 0o777)
        os.replace(tmp, dest)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    return {'document': new, 'backup': str(backup_root / name), 'changed': sorted(
        k for k in DEFAULTS if new['labels'][k] != previous['labels'][k])}
