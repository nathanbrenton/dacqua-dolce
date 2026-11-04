"""Local Media Manager theme parity with the canonical storefront Aesthetic Lab.

Read only. Source definitions remain in frontend/src/theme, not a forked list.
"""
from __future__ import annotations

import re
from pathlib import Path

MAX_STYLESHEET_BYTES = 256_000
MAIN_THEME_ROOT = Path('frontend/src/theme')


def _local_file(repo: Path, relative: str) -> Path:
    """Allow only known in-repository paths; reject symlinked components."""
    if repo.is_symlink() or not repo.is_dir():
        raise ValueError('Unsafe TEST repository')
    path = repo
    for part in Path(relative).parts:
        if part in ('', '.', '..'):
            raise ValueError('Unsafe relative path')
        path = path / part
        if path.is_symlink():
            raise ValueError('Theme file symlink rejected')
    if not path.is_file():
        raise ValueError('Theme file not found')
    if not path.resolve().is_relative_to(repo.resolve()):
        raise ValueError('Theme file outside TEST repository')
    return path


def _text(repo: Path, relative: str) -> str:
    path = _local_file(repo, relative)
    if path.stat().st_size > MAX_STYLESHEET_BYTES:
        raise ValueError('Theme source too large')
    return path.read_text(encoding='utf-8')


def _object_array(text: str, name: str) -> list[dict[str, str]]:
    match = re.search(r'export const ' + re.escape(name) + r'\s*=\s*\[([\s\S]*?)\] as const;', text)
    if match is None:
        raise ValueError('Missing storefront theme definition: ' + name)
    items = []
    for block in re.findall(r'\{([^{}]*)\}', match.group(1)):
        obj = dict(re.findall(r'\b(id|label|detail|path)\s*:\s*"([^"]+)"', block))
        if 'id' in obj and 'label' in obj:
            if not re.fullmatch(r'[a-z0-9-]+', obj['id']):
                raise ValueError('Unsafe theme identifier')
            items.append(obj)
    if not items or len(items) > 20 or len({x['id'] for x in items}) != len(items):
        raise ValueError('Unexpected storefront theme definitions')
    return items


def _default(text: str, name: str) -> str:
    match = re.search(r'export const ' + re.escape(name) + r'[\s\S]{0,140}?=\s*"([a-z0-9-]+)"', text)
    if not match:
        raise ValueError('Missing storefront theme default: ' + name)
    return match.group(1)


def theme_options(repo: Path) -> dict:
    themes_src = _text(repo, str(MAIN_THEME_ROOT/'themes.ts'))
    typo_src = _text(repo, str(MAIN_THEME_ROOT/'typography.ts'))
    logo_src = _text(repo, str(MAIN_THEME_ROOT/'branding.ts'))
    appearance_src = _text(repo, str(MAIN_THEME_ROOT/'appearance.ts'))
    themes = _object_array(themes_src, 'THEMES')
    typography = _object_array(typo_src, 'TYPOGRAPHY_SCHEMES')
    logos = _object_array(logo_src, 'LOGO_VARIANTS')
    appearances = re.findall(r'"(light|dark)"', appearance_src.split('] as const')[0])
    if appearances != ['light', 'dark']:
        raise ValueError('Unexpected storefront appearance list')
    defaults = {'theme': _default(themes_src, 'DEFAULT_THEME'),
                'appearance': _default(appearance_src, 'DEFAULT_APPEARANCE'),
                'typography': _default(typo_src, 'DEFAULT_TYPOGRAPHY_SCHEME'),
                'logo': _default(logo_src, 'DEFAULT_LOGO_VARIANT')}
    if (defaults['theme'] not in {x['id'] for x in themes}
            or defaults['typography'] not in {x['id'] for x in typography}
            or defaults['logo'] not in {x['id'] for x in logos}
            or defaults['appearance'] not in appearances):
        raise ValueError('Invalid storefront theme default')
    return {'themes': [{'id': x['id'], 'label': x['label']} for x in themes],
            'appearance': [{'id': x, 'label': x.title()} for x in appearances],
            'typography': [{k: x[k] for k in ('id', 'label', 'detail') if k in x}
                           for x in typography],
            'logos': [{'id': x['id'], 'label': x['label']} for x in logos],
            'defaults': defaults, 'source': 'frontend/src/theme (current TEST checkout)'}


def theme_stylesheet(repo: Path) -> bytes:
    return _text(repo, str(MAIN_THEME_ROOT/'tokens.css')).encode('utf-8')


def theme_logo(repo: Path, logo_id: str) -> bytes:
    logos = _object_array(_text(repo, str(MAIN_THEME_ROOT/'branding.ts')), 'LOGO_VARIANTS')
    selected = next((logo for logo in logos if logo['id'] == logo_id), None)
    if selected is None:
        raise ValueError('Unknown storefront logo')
    path = selected.get('path', '')
    if not re.fullmatch(r'/brand/logos/[a-z0-9-]+\.webp', path):
        raise ValueError('Unsupported storefront logo path')
    file = _local_file(repo, 'frontend/public' + path)
    if file.stat().st_size > 2_000_000:
        raise ValueError('Logo file too large')
    return file.read_bytes()
