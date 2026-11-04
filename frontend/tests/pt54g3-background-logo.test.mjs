import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import { test } from 'node:test';

const app = readFileSync('src/App.tsx', 'utf8');
const controls = readFileSync('src/components/developer/DeveloperControls.tsx', 'utf8');
const css = readFileSync('src/styles.css', 'utf8');
const state = readFileSync('src/theme/backgroundLogo.ts', 'utf8');
const svg = readFileSync('public/brand/logos/dacqua-dolce-background-black.svg', 'utf8');

test('G3: exact Aesthetic Lab checkbox, controlled state and local persistence', () => {
  assert.match(controls, /id="developer-background-logo-visible"/);
  assert.match(controls, /checked=\{backgroundLogoVisible\}/);
  assert.match(controls, /onBackgroundLogoChange\(event\.target\.checked\)/);
  assert.match(controls, /Background logo visible/);
  assert.match(app, /setBackgroundLogoVisible/);
  assert.match(app, /getInitialBackgroundLogoVisible/);
  assert.match(app, /saveBackgroundLogoVisible\(backgroundLogoVisible\)/);
  assert.match(state, /DEFAULT_BACKGROUND_LOGO_VISIBLE = true/);
  assert.match(state, /localStorage\.getItem\(BACKGROUND_LOGO_STORAGE_KEY\)/);
  assert.match(state, /localStorage\.setItem\(BACKGROUND_LOGO_STORAGE_KEY/);
});

test('G3: backdrop is excluded from operations and account workspaces', () => {
  assert.match(state, /operations\|account/);
  assert.match(app, /backgroundLogoVisible && isBackgroundLogoAllowedPath\(path\)/);
  assert.match(app, /showBackgroundLogo \? \(/);
  assert.match(app, /className="site-background-logo" aria-hidden="true"/);
  assert.match(app, /path === "\/operations"/);
  assert.match(app, /path === "\/account"/);
});

test('G3: one responsive, fixed, behind-content vector with pointer transparency', () => {
  assert.match(css, /#root \{\s*isolation: isolate/);
  assert.match(css, /\.site-background-logo \{[\s\S]*position: fixed/);
  assert.match(css, /z-index: -1/);
  assert.match(css, /pointer-events: none/);
  assert.match(css, /background-size: min\(74vw, 1060px\) auto/);
  assert.match(css, /max-width: 760px\) and \(orientation: portrait\)/);
  assert.match(css, /max-width: 950px\) and \(orientation: landscape\)/);
  assert.match(css, /\.site-background-logo ~ :is\(\.support-page-route, \.product-detail-route, \.detail-shell\)/);
  assert.match(css, /data-appearance="dark"/);
});

test('G3: SVG contains local black vector paths, no background image or external refs', () => {
  assert.match(svg, /<svg[^>]+viewBox=/);
  assert.match(svg, /<path d="/);
  assert.match(svg, /fill="#000000"/);
  assert.doesNotMatch(svg, /<image\b|<foreignObject\b|(?:href|xlink:href)="https?:\/\/|data:image\//);
  assert.equal((svg.match(/<svg\b/g) ?? []).length, 1);
});


test('G3.1: first visit defaults ON, explicit saved OFF persists, storage failure defaults ON', () => {
  // Execute the tiny display-preference module with mocked browser storage.
  // Only remove its TypeScript type annotations and export keywords.
  const javascript = state
    .replace(/\bexport\s+/g, '')
    .replace(/:\s*(?:string|boolean|void)\b/g, '');
  const key = 'dacqua-dolce-background-logo-visible-v1';
  const scenarios = [
    { saved: null, expected: true },
    { saved: 'true', expected: true },
    { saved: 'false', expected: false },
    { saved: 'invalid', expected: true },
  ];
  for (const { saved, expected } of scenarios) {
    const data = new Map();
    if (saved !== null) data.set(key, saved);
    const api = vm.runInNewContext(javascript + '\n({getInitialBackgroundLogoVisible,saveBackgroundLogoVisible})', {
      localStorage: {
        getItem(k) { return data.has(k) ? data.get(k) : null; },
        setItem(k, v) { data.set(k, v); },
      },
    });
    assert.equal(api.getInitialBackgroundLogoVisible(), expected, `stored=${saved}`);
    api.saveBackgroundLogoVisible(false);
    assert.equal(data.get(key), 'false');
    assert.equal(api.getInitialBackgroundLogoVisible(), false);
    api.saveBackgroundLogoVisible(true);
    assert.equal(data.get(key), 'true');
    assert.equal(api.getInitialBackgroundLogoVisible(), true);
  }
  const unavailable = vm.runInNewContext(javascript + '\ngetInitialBackgroundLogoVisible()', {
    localStorage: { getItem() { throw new Error('blocked storage'); } },
  });
  assert.equal(unavailable, true);
});
