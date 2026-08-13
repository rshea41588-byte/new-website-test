#!/usr/bin/env node
/**
 * Shea Business Solutions — mobile tap-target fix, 2026-08-12
 * CSS-only, additive, mobile-scoped (<=768px). No content, no llms.txt, no
 * lead-page copy touched. Idempotent: replaces its own prior injected block.
 *
 * Measured live at 375x812 on 2026-08-12 before the fix:
 *   - footer link lists      311 x 23.1 px at a 35.1 px pitch (12 px dead gap)
 *   - footer contact links   311 x 23.1 px
 *   - footer social icons     18 x 18 px
 *   - mobile hamburger        32 x 24 px
 *   - breadcrumb "Home"     33.6 x 21.2 px
 * Every one of those is a standalone control under the 40 px floor. Inline links
 * inside sentences are deliberately NOT touched: WCAG 2.5.8 exempts them and
 * padding them would break the line box of Ryan's prose.
 *
 * Desktop is untouched on purpose - the rule the checklist scores is the 375 px
 * browser check, and widening desktop footers is a layout change nobody asked for.
 */
import { readFileSync, writeFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';

const ROOT = new URL('.', import.meta.url).pathname;
const MARKER = 'SBS tap targets 2026-08-12';
// \r? on both breaks: these files carry MIXED CRLF/LF endings, and an LF-only
// pattern silently fails to strip the prior block, which duplicates it on re-run.
const BLOCK_RE = new RegExp(`\\r?\\n?<style>\\r?\\n\\/\\* ${MARKER}[\\s\\S]*?<\\/style>`, 'g');

const BLOCK = `<style>
/* ${MARKER} — 40px minimum tap targets on mobile, CSS only, additive */
@media (max-width:768px){
.footer-col ul{gap:0;}
.footer-col ul li a{display:block;padding:9px 0;}
.footer-col a{padding:9px 0;margin-bottom:0;}
.footer-social a{display:inline-flex;align-items:center;justify-content:center;min-width:40px;min-height:40px;}
nav.breadcrumb a{display:inline-block;padding:10px 0;min-width:40px;}
.back-to-blog a{padding:10px 0;}
.hamburger{min-width:44px;min-height:44px;align-items:center;justify-content:center;padding:10px;}
}
</style>`;

const files = [];
for (const f of readdirSync(ROOT)) if (f.endsWith('.html') && f !== 'preview-home.html') files.push(f);
for (const f of readdirSync(join(ROOT, 'Blog'))) if (f.endsWith('.html')) files.push(join('Blog', f));

let changed = 0, skipped = 0;
for (const rel of files) {
  const p = join(ROOT, rel);
  let html = readFileSync(p, 'utf8');
  if (!html.includes('</head>')) { console.log(`!! no </head>: ${rel}`); skipped++; continue; }
  html = html.replace(BLOCK_RE, '');
  html = html.replace('</head>', `${BLOCK}\n</head>`);
  writeFileSync(p, html);
  changed++;
}
console.log(`Injected tap-target block on ${changed} pages (skipped ${skipped}). Total scanned: ${files.length}`);
