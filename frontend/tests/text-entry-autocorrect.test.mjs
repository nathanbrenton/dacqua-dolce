/**
 * Every typed field turns off mobile autocorrect (iPhone rewrites names,
 * addresses and codes otherwise). Each text <input> and <textarea> in the
 * frontend must spread exactEntryProps or proseEntryProps from
 * src/components/forms/textEntry.ts.
 */
import assert from 'node:assert/strict';
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  exactEntryProps,
  proseEntryProps,
} from '../src/components/forms/textEntry.ts';

assert.deepEqual(exactEntryProps, { autoCorrect: 'off', spellCheck: false });
assert.deepEqual(proseEntryProps, { autoCorrect: 'off' });

const srcRoot = fileURLToPath(new URL('../src', import.meta.url));

// Input types with no typed text, where autocorrect never applies.
const NON_TEXT_TYPES = new Set([
  'button', 'checkbox', 'color', 'date', 'datetime-local', 'file', 'hidden',
  'image', 'month', 'radio', 'range', 'reset', 'submit', 'time', 'week',
]);

function tsxFiles(dir, out = []) {
  for (const name of readdirSync(dir)) {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) tsxFiles(path, out);
    else if (path.endsWith('.tsx')) out.push(path);
  }
  return out;
}

/** The opening JSX tag starting at `start`, skipping `>` inside `{…}`. */
function openingTag(src, start) {
  let depth = 0;
  for (let i = start; i < src.length; i += 1) {
    const c = src[i];
    if (c === '{') depth += 1;
    else if (c === '}') depth -= 1;
    else if (c === '>' && depth === 0) return src.slice(start, i + 1);
  }
  throw new Error(`Unclosed tag at ${start}`);
}

const missing = [];
let checked = 0;

for (const file of tsxFiles(srcRoot)) {
  const src = readFileSync(file, 'utf8');
  for (const match of src.matchAll(/<(input|textarea)\b/g)) {
    const tag = openingTag(src, match.index);
    const staticType = tag.match(/\btype="([^"]+)"/)?.[1];
    if (match[1] === 'input' && staticType && NON_TEXT_TYPES.has(staticType)) {
      continue;
    }
    checked += 1;
    if (!/\{\.\.\.(exactEntryProps|proseEntryProps)\}/.test(tag)) {
      const line = src.slice(0, match.index).split('\n').length;
      missing.push(`${relative(srcRoot, file)}:${line}`);
    }
  }
}

assert.ok(checked > 50, `expected to find the text fields, found ${checked}`);
assert.deepEqual(
  missing,
  [],
  'These fields need {...exactEntryProps} or {...proseEntryProps}',
);
