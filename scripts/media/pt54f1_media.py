#!/usr/bin/env python3
"""PT54-F1: safe intake scanner for future D'Acqua Dolce photo release pipeline.

No image transformations, publishing, catalog/database edits, Git actions, or network.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

FAMILIES = ('refine', 'essence', 'harmony', 'origin')
RASTER_EXT = {'.png', '.jpg', '.jpeg', '.webp', '.tif', '.tiff'}
ROLE = r'(?:system|tank|valve|brine|pureline|cartridge|detail|angle|hookup|membrane|faucet)'
PATTERNS = (
    re.compile(rf'^(?P<family>refine|essence)_(?P<size>1-5|2-0)_(?P<material>stainless|neoprene)_(?P<valve>clack3|clack5|performance)_(?P<style>archetype|realistic)_(?P<role>{ROLE})_(?P<sequence>\d{{2}})_v(?P<version>\d{{2}})$'),
    re.compile(rf'^(?P<family>harmony)_(?P<size>1-5|2-0)_(?P<material>stainless|neoprene)_(?P<role>{ROLE})_(?P<sequence>\d{{2}})_v(?P<version>\d{{2}})$'),
    re.compile(rf'^(?P<family>origin)_(?P<variant>standard|remineralization)_(?P<role>{ROLE})_(?P<sequence>\d{{2}})_v(?P<version>\d{{2}})$'),
)
MAX_INBOX_FILES = 5000
# The repository and the build-assets library sit side by side in one workspace
# folder. Both are located from this file, so moving the workspace moves them too.
REPO_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE_ROOT = REPO_ROOT.parent
BUILD_ASSETS = WORKSPACE_ROOT / 'dacqua-dolce_build-assets'
MAX_SOURCE_BYTES = 256 * 1024 * 1024  # Flag large files for human review, do not process.


def parse_asset_name(name: str) -> dict[str, Any]:
    """Parse prospective filenames only. Historical names are not required to conform."""
    path = Path(name)
    if path.name != name or path.suffix.lower() not in RASTER_EXT:
        raise ValueError('Expected a standalone image filename with png/jpg/jpeg/webp/tif/tiff extension')
    if path.suffix != path.suffix.lower() or name != name.lower():
        raise ValueError('New image filenames must be lowercase')
    for regex in PATTERNS:
        match = regex.fullmatch(path.stem)
        if match:
            data = {k: v for k, v in match.groupdict().items() if v is not None}
            data['sequence'] = int(data['sequence'])
            data['version'] = int(data['version'])
            if data['sequence'] == 0 or data['version'] == 0:
                raise ValueError('Sequence and revision numbers start at 01')
            data['extension'] = path.suffix[1:]
            return data
    raise ValueError('Filename does not match the family-specific PT54-F1 grammar')


def checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_image(path: Path) -> dict[str, Any]:
    """Inspect with ImageMagick if installed; no writes or rendering."""
    magick = shutil.which('magick')
    if not magick:
        return {'status': 'unavailable', 'reason': 'ImageMagick not on PATH'}
    try:
        result = subprocess.run(
            [magick, 'identify', '-ping', '-format', '%m %w %h', str(path)],
            capture_output=True, text=True, timeout=20, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {'status': 'error', 'reason': type(exc).__name__}
    if result.returncode != 0:
        return {'status': 'error', 'reason': 'ImageMagick rejected the image'}
    fields = result.stdout.strip().split()
    if len(fields) != 3 or not all(item.isdigit() for item in fields[1:]):
        return {'status': 'error', 'reason': 'Unexpected ImageMagick metadata'}
    return {'status': 'ok', 'format': fields[0], 'width': int(fields[1]), 'height': int(fields[2])}


def within_root(path: Path, root: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(root.resolve(strict=False))
        return True
    except ValueError:
        return False


def safe_relative_path(raw: Any) -> bool:
    if not isinstance(raw, str) or not raw or '\\' in raw:
        return False
    p = Path(raw)
    return not p.is_absolute() and all(p_part not in ('', '.', '..') for p_part in p.parts)


def read_legacy_manifests(repo: Path) -> dict[str, Any]:
    """Audit old six-artifact manifests without changing their schema or names."""
    base = repo / 'frontend/public/products/media'
    summary: dict[str, Any] = {'count': 0, 'families': {}, 'asset_paths_checked': 0,
                                'missing_paths': [], 'unsafe_paths': [], 'invalid_json': [],
                                'duplicate_configs': []}
    seen: dict[tuple[str, str], str] = {}
    counts: Counter[str] = Counter()
    if not base.is_dir():
        summary['note'] = 'Website media root is absent'
        return summary
    for family in FAMILIES:
        directory = base / family / 'manifests'
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob('*.json')):
            summary['count'] += 1
            counts[family] += 1
            rel_manifest = path.relative_to(repo).as_posix()
            if path.is_symlink() or not within_root(path, repo):
                summary['unsafe_paths'].append(rel_manifest)
                continue
            try:
                data = json.loads(path.read_text(encoding='utf-8'))
                if not isinstance(data, dict):
                    raise ValueError('Expected JSON object')
            except (OSError, UnicodeError, ValueError) as exc:
                summary['invalid_json'].append({'manifest': rel_manifest, 'error': type(exc).__name__})
                continue
            config = data.get('configuration')
            if isinstance(config, str):
                key = (family, config)
                if key in seen:
                    summary['duplicate_configs'].append([seen[key], rel_manifest])
                seen[key] = rel_manifest
            assets = data.get('assets', {})
            if not isinstance(assets, dict):
                summary['invalid_json'].append({'manifest': rel_manifest, 'error': 'assets is not an object'})
                continue
            for role, value in assets.items():
                if not isinstance(value, dict) or 'path' not in value:
                    summary['invalid_json'].append({'manifest': rel_manifest, 'error': f'bad asset: {role}'})
                    continue
                raw = value['path']
                if not safe_relative_path(raw):
                    summary['unsafe_paths'].append({'manifest': rel_manifest, 'path': str(raw)[:200]})
                    continue
                media_path = repo / raw
                if not within_root(media_path, repo) or media_path.is_symlink():
                    summary['unsafe_paths'].append({'manifest': rel_manifest, 'path': raw})
                else:
                    summary['asset_paths_checked'] += 1
                    if not media_path.is_file():
                        summary['missing_paths'].append({'manifest': rel_manifest, 'path': raw})
    summary['families'] = dict(sorted(counts.items()))
    return summary


def scan_inbox(inbox: Path) -> dict[str, Any]:
    result: dict[str, Any] = {'exists': inbox.is_dir(), 'file_count': 0, 'candidates': [],
                              'rejected': [], 'duplicate_content': [], 'multiple_revisions': [],
                              'unsafe_items': []}
    if not inbox.exists():
        result['note'] = 'Inbox not created; use init to create external directories'
        return result
    if inbox.is_symlink() or not inbox.is_dir():
        result['unsafe_items'].append('Inbox is a symbolic link or not a directory')
        return result
    entries = sorted(inbox.iterdir(), key=lambda p: p.name)
    if len(entries) > MAX_INBOX_FILES:
        result['unsafe_items'].append('Too many inbox entries to scan in one batch')
        return result
    by_identity: dict[tuple[Any, ...], list[str]] = defaultdict(list)
    by_hash: dict[str, list[str]] = defaultdict(list)
    for path in entries:
        if path.is_symlink() or not path.is_file():
            result['unsafe_items'].append(path.name)
            continue
        result['file_count'] += 1
        try:
            parsed = parse_asset_name(path.name)
        except ValueError as exc:
            result['rejected'].append({'filename': path.name, 'reason': str(exc)})
            continue
        size_bytes = path.stat().st_size
        candidate = {'filename': path.name, 'identity': parsed, 'bytes': size_bytes}
        if size_bytes == 0 or size_bytes > MAX_SOURCE_BYTES:
            candidate['status'] = 'review_required'
            candidate['reason'] = 'Zero length or exceeds 256 MiB scanning limit'
        else:
            candidate['sha256'] = checksum(path)
            candidate['image'] = inspect_image(path)
            candidate['status'] = 'candidate' if candidate['image']['status'] == 'ok' else 'review_required'
            by_hash[candidate['sha256']].append(path.name)
        identity = tuple(parsed[k] for k in ('family', 'size', 'material', 'valve', 'style', 'variant', 'role', 'sequence') if k in parsed)
        by_identity[identity].append(path.name)
        result['candidates'].append(candidate)
    result['duplicate_content'] = [names for names in by_hash.values() if len(names) > 1]
    result['multiple_revisions'] = [names for names in by_identity.values() if len(names) > 1]
    return result


def default_asset_root() -> Path:
    return BUILD_ASSETS / 'product-photography'


def initialize(asset_root: Path) -> None:
    expected_parent = BUILD_ASSETS
    if asset_root != expected_parent / 'product-photography':
        raise ValueError('init is restricted to the existing D\'Acqua Dolce build-assets location')
    if not expected_parent.is_dir() or expected_parent.is_symlink():
        raise ValueError('Existing build-assets directory is required and must not be a symlink')
    folders = ('ingest-drop', 'staging', 'masters', 'receipts')
    if asset_root.is_symlink():
        raise ValueError('Product-photography root must not be a symlink')
    asset_root.mkdir(exist_ok=True)
    for folder in folders:
        path = asset_root / folder
        if path.is_symlink() or (path.exists() and not path.is_dir()):
            raise ValueError(f'Unsafe existing path: {folder}')
        path.mkdir(exist_ok=True)
        print(f'OK: {path}')


def build_report(repo: Path, asset_root: Path) -> dict[str, Any]:
    if not repo.is_dir():
        raise ValueError(f'Repository not found: {repo}')
    if not (repo / 'frontend/src/components/catalog/productMediaRegistry.ts').is_file():
        raise ValueError('Not a D\'Acqua Dolce repository')
    return {
        'schema_version': 1,
        'mode': 'inspection_only',
        'timestamp_utc': datetime.now(timezone.utc).isoformat(),
        'repo': str(repo),
        'asset_root': str(asset_root),
        'legacy': read_legacy_manifests(repo),
        'intake': scan_inbox(asset_root / 'ingest-drop'),
        'notes': [
            'No files were transcoded, published, renamed or deleted.',
            'Legacy Clack is not automatically categorized as Clack3 or Clack5.',
            'A manifest records approved media; scanner candidates are not public assets.',
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['init', 'scan', 'parse'])
    parser.add_argument('--repo', type=Path, default=REPO_ROOT)
    parser.add_argument('--asset-root', type=Path, default=default_asset_root())
    parser.add_argument('--filename', help='For parse action only')
    parser.add_argument('--no-write', action='store_true', help='Do not write a report file')
    parser.add_argument('--summary-only', action='store_true', help='With --no-write, print only brief findings')
    parser.add_argument('--report', type=Path, help='Explicit report output path (creates file exclusively)')
    args = parser.parse_args(argv)
    try:
        if args.action == 'parse':
            if not args.filename:
                parser.error('parse requires --filename')
            print(json.dumps(parse_asset_name(args.filename), indent=2, sort_keys=True))
        elif args.action == 'init':
            initialize(args.asset_root.expanduser())
        else:
            report = build_report(args.repo.expanduser(), args.asset_root.expanduser())
            legacy, intake = report['legacy'], report['intake']
            print(f"Legacy manifests: {legacy['count']} | referenced assets: {legacy['asset_paths_checked']}")
            print(f"Missing old asset refs: {len(legacy['missing_paths'])} | invalid old manifests: {len(legacy['invalid_json'])}")
            print(f"Intake images: {intake['file_count']} | valid names: {len(intake['candidates'])} | rejected: {len(intake['rejected'])}")
            if args.no_write:
                if not args.summary_only:
                    print(json.dumps(report, indent=2, sort_keys=True))
            else:
                stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
                out = args.report.expanduser() if args.report else WORKSPACE_ROOT / f'dacqua-dolce-pt54f1-scan-{stamp}.json'
                if not out.parent.is_dir() or out.parent.is_symlink():
                    raise ValueError('Report destination directory must exist and not be a symlink')
                with out.open('x', encoding='utf-8') as stream:
                    json.dump(report, stream, indent=2, sort_keys=True)
                    stream.write('\n')
                print(f'Report: {out}')
        return 0
    except (OSError, ValueError) as exc:
        print(f'STOP: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
