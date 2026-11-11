#!/usr/bin/env python3
"""PT54-G1. TEST-only, checksum-locked new AI placeholder asset staging and activation.

No Git staging/commits/push, no database changes, and no writes to PROD.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = Path.home() / 'Desktop' / 'new-photos'
VAULT = ROOT.parent / 'dacqua-dolce_build-assets' / 'product-photography'
BATCH = VAULT / 'staging' / 'pt54g1-ai-placeholder-replacement'
MASTERS = VAULT / 'masters' / 'pt54g1-ai-placeholder-20261103'
MEDIA = ROOT / 'frontend/public/products/media/ai-placeholders'
INDEX = ROOT / 'frontend/src/components/catalog/photoSetIndex.json'
LEDGER = Path(__file__).with_name('pt54g1_sources.json')
ALLOWED_EXTRAS = {'.DS_Store'}


def fail(reason: str) -> None:
    raise SystemExit(f'STOP: {reason}')


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def check_regular(path: Path) -> None:
    if path.is_symlink() or not path.is_file():
        fail(f'Not a regular file: {path}')
    for ancestor in path.parents:
        if ancestor.is_symlink():
            fail(f'Symlinked directory: {ancestor}')


def manifest() -> dict:
    data = json.loads(LEDGER.read_text())
    if len(data) != 36:
        fail('Source ledger must contain exactly 36 files')
    return data


def expected_source_files(data: dict) -> dict[str, Path]:
    files: dict[str, Path] = {}
    for relative, metadata in data.items():
        pp = Path(relative)
        if pp.is_absolute() or len(pp.parts) != 2 or pp.parts[0] not in ('refine','essence','harmony') or pp.suffix != '.png':
            fail(f'Unexpected source ledger entry: {relative}')
        path = SOURCE_ROOT / pp
        check_regular(path)
        if path.stat().st_size != metadata['bytes'] or sha256(path) != metadata['sha256']:
            fail(f'Source image changed since context collection: {path}')
        files[relative] = path
    if not SOURCE_ROOT.is_dir() or SOURCE_ROOT.is_symlink():
        fail('new-photos folder is unavailable or symlinked')
    for path in SOURCE_ROOT.rglob('*'):
        if path.is_symlink(): fail(f'Unexpected symlink in new photos: {path}')
        if path.is_file():
            relative = path.relative_to(SOURCE_ROOT).as_posix()
            if path.name not in ALLOWED_EXTRAS and relative not in files:
                fail(f'Unexpected file in new-photos: {relative}')
    return files


def verify_magick(files: dict[str,Path], data: dict) -> None:
    exe = shutil.which('magick')
    if not exe: fail('ImageMagick 7 missing: install magick on TEST')
    for relative, path in files.items():
        result = subprocess.run([exe, 'identify', '-format', '%m %w %h', str(path)], capture_output=True, text=True, check=True)
        if result.stdout.strip() != f"PNG {data[relative]['width']} {data[relative]['height']}":
            fail(f'Incorrect dimensions/format: {path}: {result.stdout!r}')


def duplicates(data: dict) -> list[tuple[str,str]]:
    reverse: dict[str, list[str]] = {}
    for relative, meta in data.items(): reverse.setdefault(meta['sha256'], []).append(relative)
    return [(a,b) for names in reverse.values() if len(names)>1 for i,a in enumerate(names) for b in names[i+1:] if a.split('/')[0]!=b.split('/')[0]]


def paths(family: str, stem: str) -> tuple[str,str]:
    base = f'/products/media/ai-placeholders/{family}'
    return f'{base}/{stem}.webp', f'{base}/thumbnails/{stem}.webp'


def photo(family: str, stem: str, role: str, label: str) -> dict:
    url, thumbnail = paths(family, stem)
    return {'id':role, 'label':label, 'alt':f'{family.title()} — {label.lower()}', 'media':{'src':url,'thumbnail':thumbnail}}


def build_galleries(data: dict) -> dict[str,list[dict]]:
    """All 24 selected configurations must have complete deterministic galleries."""
    names = {Path(name).stem for name in data}
    entries: dict[str,list[dict]] = {}
    for size,unit in [('1-5','1.5'),('2-0','2.0')]:
        for material,finish in [('chrome','stainless'),('neoprene','neoprene')]:
            ref = f'refine_performance_{size}_{material}'
            with_brine = f'{ref}_with-brine-tank'
            key = f'refine:{unit}:{finish}'
            entries[key] = [photo('refine',with_brine,'system','Complete system'),
                photo('refine',ref,'tank','Treatment tank'),
                photo('refine','refine_brine-tank_front','brine','Brine tank · front'),
                photo('refine','refine_brine-tank_side','brine-side','Brine tank · side')]
            ess = f'essence_performance_{size}_{material}'
            entries[f'essence:{unit}:{finish}'] = [photo('essence',ess,'system','Complete system')]
            standalone = f'harmony_pass-through_{size}_{material}'
            for count,style in [(0,''),(1,'solo'),(2,'duo'),(3,'trio')]:
                key=f'harmony:{unit}:{finish}:pass-through:{count}'
                if count==0:
                    entries[key]=[photo('harmony',standalone,'system','Complete system')]
                    continue
                combo = f'{standalone}_pureline-{count}-{style}'
                prefix=f'harmony_pureline-{count}-{style}'
                entries[key] = [photo('harmony',combo,'system','Complete system'),
                    photo('harmony',standalone,'tank','Treatment tank'),
                    photo('harmony',f'{prefix}_front','pureline','Pureline assembly · front'),
                    photo('harmony',f'{prefix}_back','pureline-back','Pureline assembly · rear')]
    used={item['media']['src'].split('/')[-1].removesuffix('.webp') for photos in entries.values() for item in photos}
    if len(entries)!=24 or used!=names:
        fail(f'Incomplete or unmatched source mapping: {len(entries)} configurations; unused={sorted(names-used)}; missing={sorted(used-names)}')
    return entries


def expected_artifacts(relative: str) -> list[Path]:
    family=relative.split('/')[0]; stem=Path(relative).stem
    return [Path(family)/f'{stem}.png',Path(family)/f'{stem}.webp',Path(family)/'thumbnails'/f'{stem}.png',Path(family)/'thumbnails'/f'{stem}.webp']


def processing_batch(data:dict, files:dict[str,Path]) -> dict:
    receipt={'schema_version':1,'source_set':'ai-placeholder','source_count':36,'generated_utc':datetime.now(timezone.utc).isoformat(), 'source_sha256':{k:v['sha256'] for k,v in data.items()},'artifacts':{}}
    BATCH.parent.mkdir(parents=True,exist_ok=True)
    if BATCH.exists() or BATCH.is_symlink(): fail(f'Staging batch already exists; verify it before proceeding: {BATCH}')
    with tempfile.TemporaryDirectory(prefix='pt54g1-',dir=BATCH.parent) as temp:
        tmp=Path(temp)
        magick=shutil.which('magick')
        for n,(relative,source) in enumerate(sorted(files.items()),1):
            artifacts=expected_artifacts(relative)
            for artifact in artifacts: (tmp/artifact).parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(source,tmp/artifacts[0])
            subprocess.run([magick,str(source),'-strip','-define','webp:lossless=true','-quality','100',str(tmp/artifacts[1])],check=True)
            subprocess.run([magick,str(source),'-auto-orient','-resize','384x480>','-strip',str(tmp/artifacts[2])],check=True)
            subprocess.run([magick,str(tmp/artifacts[2]),'-define','webp:lossless=true','-quality','100',str(tmp/artifacts[3])],check=True)
            receipt['artifacts'][relative]={path.as_posix():sha256(tmp/path) for path in artifacts}
            print(f'  PREPARED {n}/36: {relative}',flush=True)
        (tmp/'pt54g1-receipt.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
        (tmp/'review.html').write_text('<!DOCTYPE html><meta charset="utf-8"><title>PT54-G1 photo review</title><style>body{font:16px system-ui;background:#f5f5f5;color:#222}figure{display:inline-block;width:230px;vertical-align:top;margin:14px;padding:10px;background:white}img{max-width:100%;height:260px;object-fit:contain}figcaption{overflow-wrap:anywhere;font-size:12px}</style><h1>PT54-G1 AI placeholder preview · TEST only</h1>'+''.join(f'<figure><img src="{expected_artifacts(name)[3].as_posix()}"><figcaption>{name}</figcaption></figure>' for name in sorted(files)))
        tmp.rename(BATCH)
    return receipt


def validate_batch(data:dict) -> dict:
    receiptpath=BATCH/'pt54g1-receipt.json'
    check_regular(receiptpath)
    receipt=json.loads(receiptpath.read_text())
    if receipt.get('source_count')!=36 or receipt.get('source_sha256')!={k:v['sha256'] for k,v in data.items()}:
        fail('Invalid batch source ledger')
    for relative, artifacts in receipt['artifacts'].items():
        if relative not in data or set(artifacts)!={p.as_posix() for p in expected_artifacts(relative)}:
            fail(f'Unexpected staged output set: {relative}')
        for name,sha in artifacts.items():
            p=BATCH/name;check_regular(p)
            if sha256(p)!=sha:fail(f'Prepared derivative tampered: {p}')
    if len(receipt['artifacts'])!=36:fail('Incomplete stage')
    return receipt


def copy_if_safe(source:Path,dest:Path,expected_hash:str) -> None:
    if dest.exists() or dest.is_symlink():
        check_regular(dest)
        if sha256(dest)!=expected_hash:fail(f'Destination conflicts with current file: {dest}')
        return
    dest.parent.mkdir(parents=True,exist_ok=True)
    if dest.parent.is_symlink():fail(f'Unsafe output folder: {dest.parent}')
    shutil.copyfile(source,dest)
    if sha256(dest)!=expected_hash:fail(f'Copy checksum failure: {dest}')


def activate(data:dict,receipt:dict) -> None:
    existing=json.loads(INDEX.read_text())
    if existing.get('schema_version')!=1 or set(existing['sets'])!={'ai-placeholder','product-photo'}:
        fail('Unexpected gallery-index schema')
    if existing['sets']['product-photo']['active']:
        fail('Actual product-photo set already active: do not overwrite it')
    galleries=build_galleries(data)
    new={'schema_version':1,'sets':{'ai-placeholder':{'active':True,'entries':galleries}, 'product-photo':existing['sets']['product-photo']}}
    if existing['sets']['ai-placeholder']['active']:
        if existing!=new:fail('Already activated with different media mapping')
        print('PASS: AI gallery index already activated; no changes')
        return
    # Preserve all input copies and master originals before touching the website.
    for relative,record in data.items():
        copy_if_safe(SOURCE_ROOT/relative, MASTERS/relative,record['sha256'])
    # All old Refine/Essence/Harmony image files remain recoverable; the new
    # active index completely supersedes them in the storefront.
    for relative,artifacts in receipt['artifacts'].items():
        for name,digest in artifacts.items():copy_if_safe(BATCH/name,MEDIA/name,digest)
    tmp=INDEX.with_suffix('.json.tmp')
    if tmp.exists() or tmp.is_symlink():fail('Temporary gallery index exists; refusing overwrite')
    tmp.write_text(json.dumps(new,indent=2,ensure_ascii=False,sort_keys=True)+'\n')
    tmp.replace(INDEX)
    print('PASS: 36 AI source files archived; 144 derivatives installed; 24 galleries activated. No old media deleted.')


def verify_published(data:dict) -> None:
    index=json.loads(INDEX.read_text());galleries=build_galleries(data)
    if not index['sets']['ai-placeholder']['active'] or index['sets']['ai-placeholder']['entries']!=galleries:
        fail('Published AI source index is incomplete or changed')
    receipt=validate_batch(data)
    for relative, artifacts in receipt['artifacts'].items():
        for name,digest in artifacts.items():
            path=MEDIA/name;check_regular(path)
            if sha256(path)!=digest:fail(f'Website derivative changed: {path}')
        master=MASTERS/relative;check_regular(master)
        if sha256(master)!=data[relative]['sha256']:fail(f'Archival master changed: {master}')
    print('PASS: 36 immutable masters; 144 website derivatives; 24 complete active galleries, all checksums verified')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['plan','prepare','activate','verify'])
    parser.add_argument('--acknowledge-cross-family-duplicates',action='store_true')
    args=parser.parse_args()
    data=manifest();galleries=build_galleries(data)
    pairs=duplicates(data)
    print(f'PT54-G1: {len(data)} source images; {len(galleries)} galleries; {len(pairs)} cross-family duplicate pairs')
    for a,b in pairs:print(f'  DUPLICATE: {a} = {b}')
    if args.action in ('plan','prepare'):
        files=expected_source_files(data)
        verify_magick(files,data)
        if args.action=='plan':
            print('PASS: input filenames, sizes, SHA-256, dimensions and mapping verified; no writes')
            return
        if pairs and not args.acknowledge_cross_family_duplicates:
            fail('Cross-family duplicates require explicit --acknowledge-cross-family-duplicates')
        processing_batch(data,files)
        print(f'PASS: batch prepared. Review images at {BATCH}/review.html before activation')
        return
    if args.action=='activate':
        if pairs and not args.acknowledge_cross_family_duplicates:
            fail('Cross-family duplicates require explicit --acknowledge-cross-family-duplicates')
        receipt=validate_batch(data)
        activate(data,receipt)
        return
    verify_published(data)


if __name__=='__main__':
    main()
