#!/usr/bin/env node
// BLOCKING section-order gate. Run: node tooling/section-order-gate.mjs
// Fails (exit 1) if any published page is missing data-section names or emits
// the canonical stack out of order. Blog/ is a protected legacy surface and is skipped.
import fs from 'node:fs';
import path from 'node:path';

const RANK = {
  'hero': 10, 'trust': 20, 'services': 30, 'offer': 40, 'how-it-works': 50,
  'article': 55, 'reviews': 60, 'case-studies': 65, 'who-we-are': 70,
  'about-business': 75, 'service-areas': 80, 'directions': 85,
  'related-services': 88, 'local-resources': 90, 'faq': 95,
  'tax-crosslink': 97, 'contact': 99
};

const files = fs.readdirSync('.').filter(f => f.endsWith('.html'))
  .filter(f => !['preview-home.html', 'google6fb6dbc31d8bbc9a.html'].includes(f));

let failures = [];
for (const f of files) {
  const src = fs.readFileSync(f, 'utf8');
  const tags = src.match(/<section\b[^>]*>/g) || [];
  if (!tags.length) continue;
  const names = [];
  for (const t of tags) {
    const m = t.match(/data-section="([^"]+)"/);
    if (!m) { failures.push(`${f}: <section> without data-section: ${t.slice(0, 80)}`); continue; }
    if (!(m[1] in RANK)) { failures.push(`${f}: unknown section name "${m[1]}"`); continue; }
    names.push(m[1]);
  }
  if (names.length && names[0] !== 'hero') failures.push(`${f}: first section is "${names[0]}", expected "hero"`);
  for (let i = 1; i < names.length; i++) {
    if (RANK[names[i]] < RANK[names[i - 1]]) {
      failures.push(`${f}: "${names[i]}" renders after "${names[i - 1]}" - canonical order violated`);
    }
  }
}

if (failures.length) {
  console.error(`SECTION ORDER GATE FAILED (${failures.length}):`);
  failures.forEach(l => console.error('  ' + l));
  process.exit(1);
}
console.log(`Section order gate PASSED across ${files.length} pages.`);
