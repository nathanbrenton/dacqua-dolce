#!/usr/bin/env python3
"""PT54-F2: prepare and verify review-only, non-destructive photo batches.

The tool never modifies drop-folder originals, the Git repository, production,
archival masters, or existing approved manifests. Staging is not publication.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pt54f1_media import (
    MAX_SOURCE_BYTES,
    checksum,
    default_asset_root,
    inspect_image,
    parse_asset_name,
    safe_relative_path,
    within_root,
)

MAX_PIXELS = 50_000_000
MAX_BATCH_FILES = 250
WEB_MAX = '1122x1402>'
THUMB_MAX = '384x480>'
FORMAT_BY_EXTENSION = {'png': 'PNG', 'jpg': 'JPEG', 'jpeg': 'JPEG',
                       'webp': 'WEBP', 'tif': 'TIFF', 'tiff': 'TIFF'}
ROLES = ('master', 'website_png', 'website_webp', 'thumbnail_png', 'thumbnail_webp')


class Rejected(ValueError):
    """The candidate cannot be prepared safely."""


def ensure_directory(path: Path, label: str) -> None:
    if not path.is_dir() or path.is_symlink():
        raise Rejected(f'{label} must exist as a regular directory: {path}')


def inspect_candidate(path: Path, root: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file() or path.parent != root:
        raise Rejected(f'Unsafe or non-file intake item: {path.name}')
    fields = parse_asset_name(path.name)
    size = path.stat().st_size
    if not (0 < size <= MAX_SOURCE_BYTES):
        raise Rejected(f'Invalid source byte count: {path.name}')
    image = inspect_image(path)
    if image.get('status') != 'ok':
        raise Rejected(f'Cannot identify image: {path.name}: {image.get("reason", "unknown")}')
    if image.get('format', '').upper() != FORMAT_BY_EXTENSION[fields['extension']]:
        raise Rejected(f'Image format differs from its extension: {path.name}')
    w, h = image['width'], image['height']
    if w < 16 or h < 16 or w * h > MAX_PIXELS:
        raise Rejected(f'Unsupported source dimensions: {path.name}: {w}x{h}')
    # The pre-transform hash is a durable guard against concurrent source edits.
    return {'name': path.name, 'identity': fields, 'sha256': checksum(path),
            'bytes': size, 'image': image}


def identity_key(item: dict[str, Any]) -> tuple[Any, ...]:
    fields = item['identity']
    return tuple((k, fields.get(k)) for k in
                 ('family', 'size', 'material', 'valve', 'style', 'variant', 'role', 'sequence'))


def collect_candidates(root: Path, filename: str | None = None) -> list[dict[str, Any]]:
    intake = root / 'ingest-drop'
    ensure_directory(intake, 'Ingest folder')
    entries = list(intake.iterdir())
    if not filename and len(entries) > MAX_BATCH_FILES:
        raise Rejected(f'Ingest folder exceeds per-batch limit of {MAX_BATCH_FILES}')
    if filename:
        if Path(filename).name != filename or '/' in filename or '\\' in filename:
            raise Rejected('Select a single flat intake filename')
        entries = [intake / filename]
    if not entries:
        raise Rejected('Ingest folder is empty. Add approved source images first.')
    items = [inspect_candidate(p, intake) for p in sorted(entries)]
    by_sha: dict[str, list[str]] = defaultdict(list)
    by_identity: dict[tuple[Any, ...], list[str]] = defaultdict(list)
    for item in items:
        by_sha[item['sha256']].append(item['name'])
        by_identity[identity_key(item)].append(item['name'])
    dup_content = [v for v in by_sha.values() if len(v) > 1]
    multiple_versions = [v for v in by_identity.values() if len(v) > 1]
    if dup_content:
        raise Rejected('Duplicate content in selected batch: ' + repr(dup_content))
    if multiple_versions:
        raise Rejected('Multiple revisions for same photo slot in batch: ' + repr(multiple_versions))
    return items


def targets_for(item: dict[str, Any]) -> dict[str, str]:
    """A review-only placement proposal. These paths are never written by F2."""
    fields = item['identity']
    family, stem = fields['family'], Path(item['name']).stem
    base = f'frontend/public/products/media/{family}/generated'
    return {
        'master': f'masters/{family}/{item["name"]}',
        'website_png': f'{base}/{stem}.png',
        'website_webp': f'{base}/{stem}.webp',
        'thumbnail_png': f'{base}/thumbnails/{stem}.png',
        'thumbnail_webp': f'{base}/thumbnails/{stem}.webp',
        'manifest': f'{base}/manifests/{stem}.json',
    }


def collision_report(item: dict[str, Any], repo: Path, root: Path) -> list[str]:
    conflicts = []
    for kind, relative in targets_for(item).items():
        check_root = root if kind == 'master' else repo
        path = check_root / relative
        if not within_root(path, check_root):
            raise Rejected('Publication proposal escapes destination root')
        if path.exists() or path.is_symlink():
            conflicts.append(f'{kind}: {relative}')
    return conflicts


def output_info(path: Path, batch: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise Rejected('Missing output: ' + str(path))
    return {'path': path.relative_to(batch).as_posix(), 'sha256': checksum(path),
            'bytes': path.stat().st_size, 'image': inspect_image(path)}


def magick_run(command: list[str]) -> None:
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=180, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise Rejected('ImageMagick failed: ' + type(exc).__name__) from exc
    if result.returncode:
        raise Rejected('ImageMagick rejected the candidate: ' + result.stderr[:500])


def generate_derivative(magick: str, source: Path, output: Path, geometry: str, webp: bool) -> None:
    command = [magick, str(source), '-auto-orient', '-resize', geometry,
               # Privacy: remove embedded EXIF/IPTC/XMP from public derivatives.
               '+profile', 'exif', '+profile', 'iptc', '+profile', 'xmp']
    if webp:
        command += ['-define', 'webp:lossless=true', '-define', 'webp:method=6']
    command.append(str(output))
    magick_run(command)
    result = inspect_image(output)
    if result.get('status') != 'ok':
        raise Rejected('Failed to verify generated image')
    max_w, max_h = (1122, 1402) if geometry == WEB_MAX else (384, 480)
    if not 1 <= result['width'] <= max_w or not 1 <= result['height'] <= max_h:
        raise Rejected('Generated derivative dimensions exceed their limits')
    if result['format'] != ('WEBP' if webp else 'PNG'):
        raise Rejected('Generated derivative format mismatch')


def write_exclusive(path: Path, data: str) -> None:
    with path.open('x', encoding='utf-8') as out:
        out.write(data)


def prepare_one(magick: str, batch: Path, root: Path, repo: Path, item: dict[str, Any]) -> dict[str, Any]:
    name = item['name']
    source = root / 'ingest-drop' / name
    slot = batch / 'items' / Path(name).stem
    slot.mkdir(parents=True, exist_ok=False)
    master_dir = slot / 'master'
    web_dir = slot / 'website'
    thumb_dir = slot / 'thumbnails'
    for folder in (master_dir, web_dir, thumb_dir):
        folder.mkdir()
    master = master_dir / name
    # Exclusive copy, preserving every byte. The drop-folder original stays untouched.
    with source.open('rb') as stream, master.open('xb') as out:
        shutil.copyfileobj(stream, out)
    if checksum(master) != item['sha256'] or checksum(source) != item['sha256']:
        raise Rejected('Source changed during ingestion: ' + name)
    stem = Path(name).stem
    outputs = {'master': master,
               'website_png': web_dir / f'{stem}.png',
               'website_webp': web_dir / f'{stem}.webp',
               'thumbnail_png': thumb_dir / f'{stem}.png',
               'thumbnail_webp': thumb_dir / f'{stem}.webp'}
    for key, geometry, webp in [('website_png', WEB_MAX, False),
                                 ('website_webp', WEB_MAX, True),
                                 ('thumbnail_png', THUMB_MAX, False),
                                 ('thumbnail_webp', THUMB_MAX, True)]:
        generate_derivative(magick, master, outputs[key], geometry, webp)
    data = {'schema_version': 2, 'status': 'review_pending',
            'source': item, 'files': {key: output_info(value, batch)
                                     for key, value in outputs.items()},
            'proposed_destinations': targets_for(item),
            'existing_destination_conflicts': collision_report(item, repo, root),
            'notes': ['Not approved for publication', 'No catalog, Git, or database changes']}
    write_exclusive(slot / 'manifest.json', json.dumps(data, indent=2, sort_keys=True) + '\n')
    return {'name': name, 'manifest': (slot / 'manifest.json').relative_to(batch).as_posix(),
            'thumbnail': outputs['thumbnail_webp'].relative_to(batch).as_posix(),
            'conflicts': data['existing_destination_conflicts']}


def html_review(batch: Path, items: list[dict[str, Any]]) -> str:
    cards = []
    for item in items:
        escaped_name = html.escape(item['name'])
        img = html.escape(item['thumbnail'], quote=True)
        manifest = html.escape(item['manifest'], quote=True)
        warning = ('<p class="alert">Destination collision: manual approval required</p>'
                   if item['conflicts'] else '')
        cards.append(f'<article><img src="{img}" alt="{escaped_name}">'
                     f'<h2>{escaped_name}</h2><a href="{manifest}">Inspect metadata</a>{warning}</article>')
    body = '\n'.join(cards)
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>D’Acqua Dolce — Unpublished Photo Review</title>'
            '<style>body{font:16px system-ui;margin:2rem auto;max-width:1100px;padding:0 1rem;}'
            'header{border-bottom:2px solid #444;margin-bottom:2rem;}main{display:grid;'
            'grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:1rem;}'
            'article{border:1px solid #ddd;border-radius:10px;padding:1rem;overflow-wrap:anywhere;}'
            'img{width:100%;height:280px;object-fit:contain;background:#f6f6f6;}'
            'h2{font-size:0.9rem;}.alert{color:#ad3b1a;font-weight:bold}</style></head><body>'
            '<header><h1>Unpublished photo batch</h1><p>Review only — never served on the website. '
            'No approval, catalog change, or deployment was performed.</p></header>'
            f'<main>{body}</main></body></html>')


def prepare(root: Path, repo: Path, filename: str | None = None) -> Path:
    if root.is_symlink() or repo.is_symlink():
        raise Rejected('Asset root and repository cannot be symlinks')
    ensure_directory(root, 'Photography asset root')
    ensure_directory(root / 'staging', 'Staging folder')
    ensure_directory(repo, 'Repository')
    if not (repo / 'frontend/public/products/media').is_dir():
        raise Rejected('Expected website media root missing')
    magick = shutil.which('magick')
    if not magick:
        raise Rejected('ImageMagick 7 command "magick" must be installed')
    items = collect_candidates(root, filename)
    staging = root / 'staging'
    # Unique, exclusive creation; failures remove only files created inside our scratch batch.
    temporary = Path(tempfile.mkdtemp(prefix='.preparing-', dir=staging))
    try:
        (temporary / 'items').mkdir()
        entries = [prepare_one(magick, temporary, root, repo, item) for item in items]
        planned = {'schema_version': 2, 'status': 'review_pending',
                   'created_utc': datetime.now(timezone.utc).isoformat(),
                   'items': entries, 'count': len(entries),
                   'source_root': str(root / 'ingest-drop'),
                   'never_published': True,
                   'requires_separate_approval': True}
        write_exclusive(temporary / 'batch.json', json.dumps(planned, indent=2, sort_keys=True) + '\n')
        write_exclusive(temporary / 'review.html', html_review(temporary, entries))
        final_name = f'batch-{datetime.now(timezone.utc):%Y%m%dT%H%M%S}-{uuid.uuid4().hex[:10]}'
        final = staging / final_name
        if final.exists() or final.is_symlink():
            raise Rejected('Unanticipated staging batch collision')
        temporary.rename(final)
        print('PASS: staged ' + str(len(entries)) + ' photo(s) for review only')
        print('Batch: ' + str(final))
        print('Review page: ' + str(final / 'review.html'))
        print('No drop-folder, master-library, website, Git, or database changes')
        return final
    except Exception:
        # Only remove exclusively created scratch files, never a user asset or reviewed batch.
        shutil.rmtree(temporary)
        raise


def verify(batch: Path) -> None:
    if not batch.is_dir() or batch.is_symlink():
        raise Rejected('Batch must be a real directory')
    data = json.loads((batch / 'batch.json').read_text(encoding='utf-8'))
    if data.get('schema_version') != 2 or data.get('status') != 'review_pending':
        raise Rejected('Unexpected or modified batch schema/status')
    if not isinstance(data.get('items'), list) or len(data['items']) != data.get('count'):
        raise Rejected('Invalid batch item count')
    all_expected = {'batch.json', 'review.html'}
    if (batch / 'review.html').is_symlink() or not (batch / 'review.html').is_file():
        raise Rejected('Review page missing or unsafe')
    for entry in data['items']:
        relative = entry.get('manifest')
        if not safe_relative_path(relative):
            raise Rejected('Unsafe manifest path')
        manifest = batch / relative
        if manifest.is_symlink() or not manifest.is_file() or not within_root(manifest, batch):
            raise Rejected('Manifest missing or unsafe')
        all_expected.add(relative)
        item = json.loads(manifest.read_text(encoding='utf-8'))
        if item.get('status') != 'review_pending' or set(item.get('files', {})) != set(ROLES):
            raise Rejected('Invalid item schema')
        if entry.get('name') != item['source'].get('name'):
            raise Rejected('Item name mismatch')
        fields = parse_asset_name(entry['name'])
        if fields != item['source']['identity']:
            raise Rejected('Item identity mismatch')
        if targets_for(item['source']) != item['proposed_destinations']:
            raise Rejected('Destination mapping mismatch')
        for role, descriptor in item['files'].items():
            relative = descriptor.get('path')
            if not safe_relative_path(relative):
                raise Rejected('Unsafe output path')
            path = batch / relative
            if not within_root(path, batch) or path.is_symlink() or not path.is_file():
                raise Rejected('Missing or unsafe output: ' + str(relative))
            if checksum(path) != descriptor.get('sha256') or path.stat().st_size != descriptor.get('bytes'):
                raise Rejected('Output differs from recorded checksum: ' + str(relative))
            all_expected.add(relative)
        master_path = batch / item['files']['master']['path']
        if checksum(master_path) != item['source']['sha256']:
            raise Rejected('Master is not byte-identical to its source')
    # Reject extra files anywhere in batch tree; directory symlinks also rejected.
    for path in batch.rglob('*'):
        if path.is_symlink():
            raise Rejected('Symlink inside staging batch')
        if path.is_file() and path.relative_to(batch).as_posix() not in all_expected:
            raise Rejected('Unexpected staged file: ' + str(path))
    print(f'PASS: {len(data["items"])} staged photo(s); master and derivative checksums verified')
    print('Status: review_pending — not published')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('plan', 'prepare', 'verify', 'verify-latest'))
    parser.add_argument('--repo', type=Path, default=Path.home() / 'Desktop/dacqua-dolce')
    parser.add_argument('--asset-root', type=Path, default=default_asset_root())
    parser.add_argument('--filename', help='Prepare exactly one source instead of the whole drop folder')
    parser.add_argument('--batch', type=Path, help='Explicit staged batch for verify action')
    args = parser.parse_args(argv)
    root, repo = args.asset_root.expanduser(), args.repo.expanduser()
    try:
        if args.action == 'plan':
            items = collect_candidates(root, args.filename)
            for item in items:
                conflicts = collision_report(item, repo, root)
                print(f'PLAN: {item["name"]} ({item["image"]["width"]}x{item["image"]["height"]})')
                for kind, relative in targets_for(item).items():
                    print(f'  {kind}: {relative}')
                for conflict in conflicts:
                    print('  WARNING: destination already exists — ' + conflict)
            print(f'PASS: {len(items)} intake photo(s) ready to prepare (no writes)')
        elif args.action == 'prepare':
            new = prepare(root, repo, args.filename)
            verify(new)
        elif args.action == 'verify':
            if not args.batch:
                raise Rejected('--batch is required for verify')
            batch = args.batch.expanduser()
            if not within_root(batch, root / 'staging') or batch.parent != root / 'staging':
                raise Rejected('Batch must be directly inside the configured staging directory')
            verify(batch)
        else:
            staging = root / 'staging'
            ensure_directory(staging, 'Staging folder')
            batches = sorted((p for p in staging.glob('batch-*') if p.is_dir() and not p.is_symlink()),
                             key=lambda p: p.name, reverse=True)
            if not batches:
                raise Rejected('No prepared batches found')
            print('Batch: ' + str(batches[0]))
            verify(batches[0])
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError, KeyError, TypeError) as exc:
        print('STOP: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
