#!/usr/bin/env python3
"""PT54-G2 TEST-only photo acceptance audit and optional local evidence receipt.

Reads existing G1/G1.1 source ledger, active media index, archival originals,
144 derivative images, and historical media folders. NEVER removes/renames images,
changes the Git index, or touches PROD. A visual acceptance receipt is not legal
or production-deployment authorization.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
G1 = Path(__file__).with_name('pt54g1_replace.py')
INDEX = ROOT / 'frontend/src/components/catalog/photoSetIndex.json'
MEDIA = ROOT / 'frontend/public/products/media'
OUT = ROOT.parent / 'dacqua-dolce_build-assets/product-photography/acceptance'
FAMILIES = ('refine','essence','harmony')


def stop(message: str):
    raise SystemExit('STOP: ' + message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def load_g1():
    if not G1.is_file() or G1.is_symlink(): stop('G1 processor missing or symlinked')
    spec = importlib.util.spec_from_file_location('pt54g1_replace', G1)
    if not spec or not spec.loader: stop('Unable to load installed G1 validator')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def inventory_legacy():
    """Historical directories are left in place, for rollback and other references."""
    totals = {}
    for family in FAMILIES:
        folder = MEDIA / family
        if not folder.is_dir() or folder.is_symlink(): stop(f'Missing historical media folder: {folder}')
        files = sorted(path for path in folder.rglob('*') if path.is_file())
        if any(path.is_symlink() for path in files):stop(f'Symlink in legacy media: {folder}')
        totals[family] = {'retained_files': len(files), 'retained_bytes': sum(p.stat().st_size for p in files)}
    return totals


def audit() -> dict:
    g1 = load_g1()
    ledger = g1.manifest()
    if len(ledger)!=36:stop('Expected exactly 36 G1 originals')
    g1.build_galleries(ledger)
    # This validates every G1/G1.1 original, staged output and published
    # derivative with its current checksum, including the two corrected names.
    g1.verify_published(ledger)
    index=json.loads(INDEX.read_text())
    if set(index.get('sets',{}))!={'ai-placeholder','product-photo'}:
        stop('Unexpected source selector index')
    ai=index['sets']['ai-placeholder']; product=index['sets']['product-photo']
    if not ai.get('active') or product != {'active':False,'entries':{}}:
        stop('Expected only AI placeholders to be active; real photos remain unavailable')
    galleries=ai['entries']
    if len(galleries)!=24:stop('Expected 24 fully mapped image galleries')
    count=0
    for key,photos in galleries.items():
        family=key.split(':')[0]
        if family not in FAMILIES:stop(f'Unexpected family in AI index: {key}')
        if not photos:stop(f'Empty gallery: {key}')
        for photo in photos:
            count+=1
            for variant in ('src','thumbnail'):
                url=photo['media'][variant]
                # Strictly forbid historical images in active galleries, and path traversal.
                if not url.startswith(f'/products/media/ai-placeholders/{family}/') or '..' in Path(url).parts:
                    stop(f'Legacy or foreign photo still actively selected: {key} {url}')
    receipt=g1.validate_batch(ledger)
    artifact_count=sum(map(len,receipt['artifacts'].values()))
    if artifact_count!=144:stop('Expected 144 independently verified derivatives')
    report={
        'schema_version':1,
        'milestone':'PT54-G2',
        'environment':'TEST',
        'sources':36,
        'derivatives_verified':144,
        'active_galleries':24,
        'active_gallery_entries':count,
        'active_photo_source':'ai-placeholder',
        'real_product_photography_available':False,
        'corrected_harmony_names':receipt.get('label_correction',{}).get('swapped',[]),
        'source_ledger_sha256':sha256(g1.LEDGER),
        'photo_set_index_sha256':sha256(INDEX),
        'historical_images_retained_not_selected':inventory_legacy(),
        'origin_and_fitting_images':'untouched; frontend regression suite separately validates continuity',
        'maintenance_notice_technical_and_legal_review':'pending before production publication',
        'production_approved':False,
    }
    if len(report['corrected_harmony_names']) != 2:
        stop('G1.1 Harmony filename correction evidence missing; review original batch')
    return report


def record(report: dict):
    if OUT.is_symlink():stop('Symlinked evidence folder')
    OUT.mkdir(parents=True,exist_ok=True)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    dest=OUT/f'pt54g2-test-visual-acceptance-{stamp}.json'
    report.update({'recorded_utc':datetime.now(timezone.utc).isoformat(),
                   'visual_approval':'Operator attests that the TEST image set was visually reviewed and accepted'})
    with dest.open('x',encoding='utf-8') as f:
        json.dump(report,f,indent=2,sort_keys=True,ensure_ascii=False)
        f.write('\n')
    print(f'PASS: TEST-only visual acceptance evidence saved: {dest}')
    print('NOTICE: Not a technical-claim, legal, Git, or production-release approval')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['audit','record'])
    parser.add_argument('--accept-visual-review',action='store_true',help='Required for recording human visual acceptance')
    args=parser.parse_args()
    if args.action=='record' and not args.accept_visual_review:
        stop('Recording requires explicit --accept-visual-review')
    report=audit()
    print(json.dumps(report,indent=2,sort_keys=True))
    print('PASS: G2 TEST photo acceptance audit; legacy images retained but unselected')
    if args.action=='record':record(report)


if __name__=='__main__': main()
