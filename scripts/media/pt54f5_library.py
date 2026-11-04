#!/usr/bin/env python3
"""Read-only preview of the active PT54-G4 AI photos and retained Origin galleries.

The retired Archetype/Realistic registry is intentionally unsupported. Original
catalog photos are chosen by the storefront separately and are not generated
from unused legacy public assets here. Paths come from audited local metadata,
never from browser requests.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import quote

from pt54f2_prepare import Rejected
from pt54f3_publish import load_index
from pt54f6_captions import load_captions, caption_metadata

REGISTRY = Path('frontend/src/components/catalog/productMediaRegistry.ts')
PHOTO_SETS = Path('frontend/src/components/catalog/photoSetIndex.json')
PUBLIC = Path('frontend/public')
LABELS = {'system': 'Complete system', 'tank': 'Tank detail', 'brine': 'Brine tank',
          'pureline': 'Pureline assembly', 'valve': 'Control valve detail',
          'cartridge': 'Replacement cartridge', 'detail': 'Product detail',
          'angle': 'Additional view', 'hookup': 'Connection fitting',
          'membrane': 'RO membrane', 'faucet': 'RO faucet'}
ALLOWED_IMAGES = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp'}
MAX_VIEW_BYTES = 25 * 1024 * 1024
MAX_INDEX_BYTES = 512 * 1024
CONFIG = re.compile(r'^(?:refine|essence):(?:1\.5|2\.0):(?:stainless|neoprene)$|^harmony:(?:1\.5|2\.0):(?:stainless|neoprene):pass-through:[0-3]$')
PHOTO_ID = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')


def _local_file(repo: Path, relative: Path) -> Path:
    if not repo.is_dir() or repo.is_symlink():
        raise Rejected('Unsafe TEST repository')
    source = repo / relative
    node = source
    while node != repo:
        if node.is_symlink():
            raise Rejected('Symlinked gallery metadata is forbidden')
        node = node.parent
    if not source.is_file() or not source.resolve().is_relative_to(repo.resolve()):
        raise Rejected('Required gallery metadata missing or unsafe')
    return source


def selected_file(repo: Path, url: str) -> Path:
    """Resolve only an authorized, non-symlinked local public media file."""
    if not isinstance(url, str) or not url.startswith('/products/media/') or '\\' in url or '?' in url or '#' in url:
        raise Rejected('Unsupported published media URL')
    parts = url.lstrip('/').split('/')
    if any(p in ('', '.', '..') or p.startswith('.') for p in parts):
        raise Rejected('Unsafe media URL')
    if Path(url).suffix.lower() not in ALLOWED_IMAGES:
        raise Rejected('Unsupported image file type')
    root = repo / PUBLIC
    source = root.joinpath(*parts)
    cursor = source
    while cursor != root:
        if cursor.is_symlink():
            raise Rejected('Symlink media file is not previewable')
        cursor = cursor.parent
    if not source.is_file() or not source.resolve().is_relative_to(root.resolve()):
        raise Rejected('Selected image missing or unsafe')
    if source.stat().st_size > MAX_VIEW_BYTES:
        raise Rejected('Selected image exceeds preview limit')
    return source


def _origin_galleries(ts: str) -> dict[str, list[dict]]:
    """Read the unchanged literal Origin gallery declarations (not executable TS)."""
    start = ts.find('const ORIGIN_GALLERIES:')
    end = ts.find('const PUBLISHED_PHOTOS', start)
    if start < 0 or end < start:
        raise Rejected('Origin gallery declaration missing')
    section = ts[start:end]
    galleries = {}
    for match in re.finditer(r'^\s*(DD5RO|DD6ROAE): \[(.*?)^\s*\],', section, re.S | re.M):
        gallery = []
        for line in match.group(2).splitlines():
            line = line.strip().removesuffix(',')
            if line:
                try:
                    gallery.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise Rejected('Origin gallery contains unexpected media') from exc
        galleries['origin:' + match.group(1)] = gallery
    if set(galleries) != {'origin:DD5RO', 'origin:DD6ROAE'}:
        raise Rejected('Expected two Origin galleries')
    for photos in galleries.values():
        for photo in photos:
            _valid_photo(photo, 'origin')
    return galleries


def _valid_photo(photo: Any, family: str) -> None:
    if not isinstance(photo, dict) or set(photo) != {'id', 'label', 'alt', 'media'}:
        raise Rejected('Invalid photo index entry')
    if not isinstance(photo['id'], str) or not PHOTO_ID.fullmatch(photo['id']):
        raise Rejected('Invalid gallery photo identifier')
    if not all(isinstance(photo[k], str) and 0 < len(photo[k]) <= 200 for k in ('label', 'alt')):
        raise Rejected('Invalid gallery photo description')
    media = photo['media']
    if not isinstance(media, dict) or set(media) != {'src', 'thumbnail'}:
        raise Rejected('Invalid gallery image mapping')
    for url in media.values():
        if not isinstance(url, str) or not url.startswith('/products/media/') or \
                '\\' in url or '?' in url or '#' in url or \
                any(p in ('', '.', '..') or p.startswith('.') for p in url.lstrip('/').split('/')) or \
                Path(url).suffix.lower() not in ALLOWED_IMAGES:
            raise Rejected('Unsafe gallery image URL')
        if family != 'origin' and not url.startswith('/products/media/ai-placeholders/' + family + '/'):
            raise Rejected('AI gallery must not reference retired/legacy photography')


def _ai_galleries(repo: Path) -> dict[str, list[dict]]:
    source = _local_file(repo, PHOTO_SETS)
    if source.stat().st_size > MAX_INDEX_BYTES:
        raise Rejected('Photo set index too large')
    try:
        doc = json.loads(source.read_bytes())
    except (ValueError, UnicodeError) as exc:
        raise Rejected('Invalid current photo set JSON') from exc
    if not isinstance(doc, dict) or set(doc) != {'schema_version', 'sets'} or doc['schema_version'] != 1:
        raise Rejected('Unexpected photo set schema')
    sets = doc['sets']
    if not isinstance(sets, dict) or set(sets) != {'ai-placeholder', 'product-photo'}:
        raise Rejected('Unexpected photo source keys')
    if sets['product-photo'].get('active') is not False:
        raise Rejected('Unreviewed real-product photography is not supported by this reader')
    selected = sets.get('ai-placeholder')
    if not isinstance(selected, dict) or set(selected) != {'active', 'entries'} or selected['active'] is not True:
        raise Rejected('AI photo gallery is not active')
    entries = selected['entries']
    if not isinstance(entries, dict) or not entries or len(entries) > 64:
        raise Rejected('Invalid AI photo configuration index')
    for key, gallery in entries.items():
        if not isinstance(key, str) or not CONFIG.fullmatch(key) or not isinstance(gallery, list) or not 1 <= len(gallery) <= 15:
            raise Rejected('Unexpected current photo configuration')
        seen = set()
        for photo in gallery:
            _valid_photo(photo, key.split(':')[0])
            if photo['id'] in seen:
                raise Rejected('Duplicate gallery photo identifier')
            seen.add(photo['id'])
    return entries


def _origin_published(repo: Path, key: str, photos: list[dict]) -> list[dict]:
    """Mirror frontend's F3 overlay for Origin only; retired G4 paths never enter AI sets."""
    entries = load_index(repo, check_assets=False)['entries']
    selected = {}
    for entry in entries:
        if entry['configuration'] == key:
            slot = (entry['role'], entry['sequence'])
            if slot not in selected or entry['version'] > selected[slot]['version']:
                selected[slot] = entry
    result = list(photos)
    additions = []
    for (role, sequence), entry in selected.items():
        replace_id = role if sequence == 1 and role in ('system', 'tank', 'brine', 'pureline') else None
        label = LABELS.get(role, 'Additional product photograph') + (f' {sequence}' if sequence > 1 else '')
        photo = {'id': f'published-{role}-{sequence:02d}', 'label': label,
                 'media': {'src': entry['src'], 'thumbnail': entry['thumbnail']},
                 'source': f'approved v{entry["version"]:02d}'}
        if replace_id is not None:
            idx = next((i for i, old in enumerate(result) if old['id'] == replace_id), -1)
            if idx >= 0:
                photo['id'] = replace_id
                result[idx] = photo
                continue
        additions.append((role, sequence, photo))
    result.extend(item[2] for item in sorted(additions))
    return result


def _selected_galleries(repo: Path) -> list[dict]:
    ts = _local_file(repo, REGISTRY).read_text('utf-8')
    ai, origins = _ai_galleries(repo), _origin_galleries(ts)
    rows = []
    for key, photos in sorted(ai.items()):
        rows.append({'key': key, 'family': key.split(':')[0], 'photos': [
            {'id': p['id'], 'label': p['label'], 'media': dict(p['media']),
             'source': 'G1 approved AI placeholder'} for p in photos]})
    for key, photos in sorted(origins.items()):
        base = [{'id': p['id'], 'label': p['label'], 'media': dict(p['media']),
                 'source': 'Origin approved legacy'} for p in photos]
        rows.append({'key': key, 'family': 'origin', 'photos': _origin_published(repo, key, base)})
    return sorted(rows, key=lambda r: r['key'])


def current_library(repo: Path) -> list[dict]:
    """Render only selected G4 AI/Origin galleries in the local-only library viewer."""
    captions, _ = load_captions(repo)
    rows = _selected_galleries(repo)
    for row in rows:
        for number, photo in enumerate(row['photos']):
            media = photo['media']
            try:
                selected_file(repo, media['src'])
                available = True
            except Rejected:
                available = False
            photo.update(caption_metadata(captions, row['family'], row['key'], photo['id'], photo['label']))
            photo['available'] = available
            photo['preview'] = '/api/library-image?key=' + quote(row['key'], safe='') + '&photo=' + str(number) + '&size=thumb'
            photo['full'] = '/api/library-image?key=' + quote(row['key'], safe='') + '&photo=' + str(number) + '&size=full'
            photo['filename'] = Path(media['src']).name
            del photo['media']
        row['count'] = len(row['photos'])
    return rows


def library_image(repo: Path, key: str, photo: str, size: str) -> tuple[bytes, str]:
    if size not in ('full', 'thumb') or not isinstance(photo, str) or not photo.isascii() or \
            not photo.isdecimal() or len(photo) > 3:
        raise Rejected('Invalid requested gallery image')
    rows = _selected_galleries(repo)
    row = next((r for r in rows if r['key'] == key), None)
    if row is None or int(photo) >= len(row['photos']):
        raise Rejected('Image not selected by the current TEST gallery')
    media = row['photos'][int(photo)]['media']
    try:
        source = selected_file(repo, media['src' if size == 'full' else 'thumbnail'])
    except Rejected:
        if size != 'thumb':
            raise
        source = selected_file(repo, media['src'])
    return source.read_bytes(), ALLOWED_IMAGES[source.suffix.lower()]
