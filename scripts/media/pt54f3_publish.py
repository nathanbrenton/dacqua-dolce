#!/usr/bin/env python3
"""PT54-F3: verify and explicitly publish reviewed F2 photo batches to TEST.

No automatic approval, network, database, Git, or production operation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pt54f1_media import default_asset_root, safe_relative_path, within_root
from pt54f2_prepare import Rejected, targets_for, verify as verify_f2

INDEX_REL = Path('frontend/src/components/catalog/publishedPhotoIndex.json')
MEDIA_ROOT = Path('frontend/public/products/media')
WEB_ROLES = ('website_png', 'website_webp', 'thumbnail_png', 'thumbnail_webp', 'manifest')
WEB_COPY_ROLES = ('website_png', 'website_webp', 'thumbnail_png', 'thumbnail_webp')
ALLOWED_ROLES = {'system', 'tank', 'valve', 'brine', 'pureline', 'cartridge',
                 'detail', 'angle', 'hookup', 'membrane', 'faucet'}
EXPECTED_KEYS = {'configuration', 'role', 'sequence', 'version',
                 'photographed_valve', 'src', 'thumbnail', 'source_sha256',
                 'source_name', 'published_utc'}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for blob in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(blob)
    return h.hexdigest()


def check_parents(path: Path, root: Path) -> None:
    if not within_root(path, root):
        raise Rejected(f'Destination escapes allowed root: {path}')
    if root.is_symlink():
        raise Rejected(f'Symlink root: {root}')
    current = path
    while current != root:
        if current.is_symlink():
            raise Rejected(f'Symlink component: {current}')
        current = current.parent


def assert_file(path: Path, root: Path) -> None:
    check_parents(path, root)
    if not path.is_file() or path.is_symlink():
        raise Rejected('Expected regular file: ' + str(path))


def configuration(identity: dict[str, Any]) -> str:
    family = identity['family']
    if family in ('refine', 'essence'):
        valve = identity['valve']
        if valve not in ('clack3', 'clack5', 'performance'):
            raise Rejected('Unsupported photographed valve')
        return f'{family}:{identity["size"].replace("-", ".")}:{identity["material"]}:' \
               f'{"clack" if valve.startswith("clack") else valve}:{identity["style"]}'
    if family == 'harmony':
        return f'harmony:{identity["size"].replace("-", ".")}:{identity["material"]}:pass-through:0'
    if family == 'origin':
        return 'origin:DD5RO' if identity['variant'] == 'standard' else 'origin:DD6ROAE'
    raise Rejected('Unknown photo family')


def validate_entry(entry: Any) -> None:
    if not isinstance(entry, dict) or set(entry) != EXPECTED_KEYS:
        raise Rejected('Unrecognized publication index entry')
    if not isinstance(entry['configuration'], str) or not entry['configuration']:
        raise Rejected('Invalid publication configuration')
    if entry['role'] not in ALLOWED_ROLES:
        raise Rejected('Invalid published photo role')
    if type(entry['sequence']) is not int or not 1 <= entry['sequence'] <= 99:
        raise Rejected('Invalid published photo sequence')
    if type(entry['version']) is not int or not 1 <= entry['version'] <= 99:
        raise Rejected('Invalid published photo revision')
    if entry['photographed_valve'] not in ('clack3', 'clack5', 'performance', None):
        raise Rejected('Invalid photographed valve')
    if entry['configuration'].startswith(('refine:', 'essence:')):
        suffix = entry['configuration'].split(':')
        if len(suffix) != 5 or suffix[1] not in ('1.5', '2.0') or suffix[2] not in ('stainless', 'neoprene') \
                or suffix[3] not in ('clack', 'performance') or suffix[4] not in ('archetype', 'realistic'):
            raise Rejected('Invalid Refine/Essence configuration')
        model = entry['photographed_valve']
        if model is None or ('clack' if model.startswith('clack') else 'performance') != suffix[3]:
            raise Rejected('Photographed valve does not match configuration')
    elif entry['configuration'].startswith('harmony:'):
        if entry['configuration'] not in {
            f'harmony:{s}:{m}:pass-through:0'
            for s in ('1.5', '2.0') for m in ('stainless', 'neoprene')
        } or entry['photographed_valve'] is not None:
            raise Rejected('Invalid Harmony configuration')
    elif entry['configuration'] not in ('origin:DD5RO', 'origin:DD6ROAE') or entry['photographed_valve'] is not None:
        raise Rejected('Invalid Origin configuration')
    for key in ('src', 'thumbnail'):
        value = entry[key]
        if not isinstance(value, str) or not value.startswith('/products/media/') \
                or not safe_relative_path(value.lstrip('/')) or '/generated/' not in value:
            raise Rejected('Invalid published public-media URL')
        if not value.startswith('/products/media/' + entry['configuration'].split(':')[0] + '/generated/'):
            raise Rejected('Cross-family published public-media URL')
        if not value.endswith('.webp'):
            raise Rejected('Published media must be WebP')
    if not isinstance(entry['source_sha256'], str) or len(entry['source_sha256']) != 64 \
            or any(x not in '0123456789abcdef' for x in entry['source_sha256']):
        raise Rejected('Invalid source digest')
    if not isinstance(entry['source_name'], str) or Path(entry['source_name']).name != entry['source_name']:
        raise Rejected('Invalid source filename')
    if not isinstance(entry['published_utc'], str) or not entry['published_utc']:
        raise Rejected('Missing publication timestamp')


def load_index(repo: Path, check_assets: bool = False) -> dict[str, Any]:
    index_path = repo / INDEX_REL
    assert_file(index_path, repo)
    index = json.loads(index_path.read_text(encoding='utf-8'))
    if not isinstance(index, dict) or set(index) != {'schema_version', 'entries'} \
            or index['schema_version'] != 1 or not isinstance(index['entries'], list):
        raise Rejected('Unexpected published photo index schema')
    seen = set()
    model_by_config: dict[str, str] = {}
    for entry in index['entries']:
        validate_entry(entry)
        key = (entry['configuration'], entry['role'], entry['sequence'], entry['version'])
        if key in seen:
            raise Rejected('Duplicate published photo revision slot')
        seen.add(key)
        if entry['photographed_valve'] in ('clack3', 'clack5'):
            previous = model_by_config.setdefault(entry['configuration'], entry['photographed_valve'])
            if previous != entry['photographed_valve']:
                raise Rejected('Clack3 and Clack5 mixed within one gallery configuration')
        if check_assets:
            stem = Path(entry['source_name']).stem
            family = entry['configuration'].split(':')[0]
            manifest = (repo / MEDIA_ROOT / family / 'generated/manifests' / (stem + '.json'))
            assert_file(manifest, repo)
            approved = json.loads(manifest.read_text(encoding='utf-8'))
            if approved.get('source', {}).get('sha256') != entry['source_sha256']:
                raise Rejected('Published source digest differs from its reviewed manifest')
            for key, role in (('src', 'website_webp'), ('thumbnail', 'thumbnail_webp')):
                relative = entry[key].lstrip('/')
                target = repo / 'frontend/public' / relative
                assert_file(target, repo)
                recorded = approved.get('files', {}).get(role, {}).get('sha256')
                if not isinstance(recorded, str) or sha(target) != recorded:
                    raise Rejected('Published WebP differs from reviewed checksum: ' + relative)
    return index


def read_batch(batch: Path, root: Path, repo: Path) -> list[dict[str, Any]]:
    staging = root / 'staging'
    if batch.parent != staging or not batch.name.startswith('batch-'):
        raise Rejected('Batch must be a direct child of the external staging directory')
    check_parents(batch, root)
    verify_f2(batch)
    data = json.loads((batch / 'batch.json').read_text(encoding='utf-8'))
    output = []
    for summary in data['items']:
        manifest_path = batch / summary['manifest']
        data_item = json.loads(manifest_path.read_text(encoding='utf-8'))
        identity = data_item['source']['identity']
        config = configuration(identity)
        if identity['role'] == 'brine' and identity['family'] != 'refine':
            raise Rejected('Brine photos are allowed only for Refine')
        if identity['role'] in ('membrane', 'faucet') and identity['family'] != 'origin':
            raise Rejected('RO-specific photos must belong to Origin')
        destinations = targets_for(data_item['source'])
        if destinations != data_item['proposed_destinations']:
            raise Rejected('Destination mapping mismatch')
        targets: dict[str, tuple[Path, Path]] = {}
        for role, relative in destinations.items():
            if not safe_relative_path(relative):
                raise Rejected('Unsafe proposed destination')
            target_root = root if role == 'master' else repo
            target = target_root / relative
            check_parents(target, target_root)
            if target.exists() or target.is_symlink():
                raise Rejected('Destination already exists; revisioned publication cannot overwrite: ' + relative)
            if role == 'manifest':
                source = manifest_path
            else:
                source = batch / data_item['files'][role]['path']
            assert_file(source, batch)
            targets[role] = (source, target)
        output.append({'source': data_item, 'configuration': config, 'targets': targets})
    return output


def entry_from_item(item: dict[str, Any], repo: Path, stamp: str) -> dict[str, Any]:
    info = item['source']['source']
    fields = info['identity']
    targets = item['targets']
    def url(role: str) -> str:
        relative = targets[role][1].relative_to(repo / 'frontend/public')
        return '/' + relative.as_posix()
    return {
        'configuration': item['configuration'], 'role': fields['role'],
        'sequence': fields['sequence'], 'version': fields['version'],
        'photographed_valve': fields.get('valve'),
        'src': url('website_webp'), 'thumbnail': url('thumbnail_webp'),
        'source_sha256': info['sha256'], 'source_name': info['name'],
        'published_utc': stamp,
    }


def plan(root: Path, repo: Path, batch: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if root.is_symlink() or repo.is_symlink() or not root.is_dir() or not repo.is_dir():
        raise Rejected('Invalid repository or photography library')
    index = load_index(repo, check_assets=True)
    items = read_batch(batch, root, repo)
    if not items:
        raise Rejected('Cannot publish an empty batch')
    existing = {(row['configuration'], row['role'], row['sequence'], row['version'])
                for row in index['entries']}
    current_models: dict[str, str] = {
        row['configuration']: row['photographed_valve']
        for row in index['entries'] if row['photographed_valve'] in ('clack3', 'clack5')
    }
    pending = set()
    for item in items:
        row = entry_from_item(item, repo, 'pending')
        key = row['configuration'], row['role'], row['sequence'], row['version']
        if key in existing or key in pending:
            raise Rejected('Photo revision slot already published or duplicated in batch: ' + str(key))
        pending.add(key)
        if row['photographed_valve'] in ('clack3', 'clack5'):
            earlier = current_models.setdefault(row['configuration'], row['photographed_valve'])
            if earlier != row['photographed_valve']:
                raise Rejected('Mixed Clack3/Clack5 source photos in one configuration: ' + row['configuration'])
        for earlier in index['entries']:
            if (earlier['configuration'], earlier['role'], earlier['sequence']) == key[:3] \
                    and earlier['version'] >= row['version']:
                raise Rejected('Photo replacement revision must increase: ' + str(key))
    for item in items:
        fields = item['source']['source']['identity']
        print('PLAN:', item['source']['source']['name'], '->', item['configuration'],
              f"slot {fields['role']}:{fields['sequence']:02d} revision {fields['version']:02d}")
        for kind, (_, destination) in item['targets'].items():
            print('  ', kind, destination)
    print(f'PASS: {len(items)} independently verified photo(s); zero destination collisions')
    print('No files published, no Git or database operations')
    return items, index


def exclusive_copy(source: Path, destination: Path, root: Path, created_files: list[Path]) -> None:
    check_parents(destination, root)
    if destination.exists() or destination.is_symlink():
        raise Rejected('Publication collision: ' + str(destination))
    destination.parent.mkdir(parents=True, exist_ok=True)
    check_parents(destination, root)
    with source.open('rb') as inp, destination.open('xb') as out:
        created_files.append(destination)
        shutil.copyfileobj(inp, out)
    if sha(source) != sha(destination):
        raise Rejected('Copy verification failed: ' + str(destination))


def write_atomic(path: Path, contents: bytes) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix='.photo-index-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(contents)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def publish(root: Path, repo: Path, batch: Path, approve: str) -> Path:
    if approve != batch.name or not batch.name.startswith('batch-'):
        raise Rejected('--approve must equal the exact reviewed batch directory name')
    items, index = plan(root, repo, batch)
    old_bytes = (repo / INDEX_REL).read_bytes()
    stamp = datetime.now(timezone.utc).isoformat()
    new_entries = [entry_from_item(item, repo, stamp) for item in items]
    next_index = {'schema_version': 1, 'entries': index['entries'] + new_entries}
    next_bytes = (json.dumps(next_index, indent=2, sort_keys=True) + '\n').encode('utf-8')
    receipt = root / 'receipts' / (batch.name + '.json')
    check_parents(receipt, root)
    if receipt.exists() or receipt.is_symlink():
        raise Rejected('Publication receipt already exists; batch cannot be republished')
    if not receipt.parent.is_dir() or receipt.parent.is_symlink():
        raise Rejected('Missing or unsafe receipts directory')
    created: list[Path] = []
    index_written = False
    try:
        for item in items:
            for kind, (source, target) in item['targets'].items():
                exclusive_copy(source, target, root if kind == 'master' else repo, created)
        # Recheck batch against the earlier F2 hashes immediately before index commit.
        verify_f2(batch)
        if (repo / INDEX_REL).read_bytes() != old_bytes:
            raise Rejected('Published index changed during preparation')
        write_atomic(repo / INDEX_REL, next_bytes)
        index_written = True
        load_index(repo, check_assets=True)
        receipt_content = {'schema_version': 1, 'batch': batch.name,
                           'published_utc': stamp, 'new_entries': new_entries,
                           'old_index_sha256': hashlib.sha256(old_bytes).hexdigest(),
                           'new_index_sha256': hashlib.sha256(next_bytes).hexdigest(),
                           'copied_paths': [str(p) for p in created],
                           'note': 'TEST only; not staged, committed, pushed, or deployed'}
        with receipt.open('x', encoding='utf-8') as out:
            json.dump(receipt_content, out, indent=2, sort_keys=True)
            out.write('\n')
    except Exception:
        if index_written:
            write_atomic(repo / INDEX_REL, old_bytes)
        for path in reversed(created):
            if path.is_file() and not path.is_symlink():
                path.unlink()
        raise
    print(f'PASS: locally published {len(items)} reviewed photographs')
    print('Receipt:', receipt)
    print('Index:', repo / INDEX_REL)
    print('Do not deploy or commit until you review the website in TEST')
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('plan', 'publish', 'verify'))
    parser.add_argument('--repo', type=Path, default=Path.home() / 'Desktop/dacqua-dolce')
    parser.add_argument('--asset-root', type=Path, default=default_asset_root())
    parser.add_argument('--batch', type=Path)
    parser.add_argument('--approve', help='Exact batch name; required for publication')
    args = parser.parse_args(argv)
    repo, root = args.repo.expanduser(), args.asset_root.expanduser()
    try:
        if args.action == 'verify':
            index = load_index(repo, check_assets=True)
            print(f'PASS: reviewed index with {len(index["entries"])} photo revision entries')
            return 0
        if args.batch is None:
            raise Rejected('--batch is required')
        batch = args.batch.expanduser()
        if args.action == 'plan':
            plan(root, repo, batch)
        else:
            if args.approve is None:
                raise Rejected('--approve exact-batch-name is required')
            publish(root, repo, batch, args.approve)
        return 0
    except (OSError, ValueError, RuntimeError, TypeError, KeyError, json.JSONDecodeError) as exc:
        print('STOP:', exc, file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
