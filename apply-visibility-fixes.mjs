#!/usr/bin/env node
/**
 * Shea Business Solutions — visibility fixes 2026-08-06 (rev 2)
 * CSS-only, additive presentation fixes for bugs Ryan flagged on the 08-06 call
 * plus adjacent items caught in the verification sweep. No content, llms.txt, or
 * lead-page copy is touched. Idempotent: replaces its own prior injected block.
 *
 *  A) NAV OVERLAY (34 root pages): bare `nav` type rule made <nav.breadcrumb>
 *     overlay #mainNav. Reset nav.breadcrumb to static.
 *  B) INVISIBLE ZEBRA TABLE (2 blogs): cream td text on #f7f9fc even rows.
 *     Light-card fix (white table base + dark td text).
 *  C) INVISIBLE CAPTION (2 blogs: setup-timeline, cleanup-involve): leftover
 *     light-theme rule `.sbs-blog p.cap{color:#1a1a1a}` = dark-on-dark on the
 *     dark body. Restore to bright cream so the lead caption shows.
 *  D) DEFAULT-BLUE/PURPLE content + footer links (sitewide dark theme): unclassed
 *     anchors fell back to #0000EE/#551A8B. Brand gold. Broadened to `main` so
 *     content sections like .tax-crosslink are covered (not just .article-body).
 */
import { readFileSync, writeFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';

const ROOT = new URL('.', import.meta.url).pathname;
const MARKER = 'SBS visibility fixes 2026-08-06';
// Matches the whole injected <style>…marker…</style> block for clean replacement.
const BLOCK_RE = new RegExp(`\\n?<style>\\n\\/\\* ${MARKER}[\\s\\S]*?<\\/style>`, 'g');

const BLOCK = `<style>
/* ${MARKER} (rev2: nav overlay + blog table + blog caption + content link color) — CSS only, additive */
nav.breadcrumb{position:static;height:auto;padding:0;background:none;backdrop-filter:none;border-bottom:none;z-index:auto;}
.sbs-blog table{background:#fff;}
.sbs-blog tbody td{color:#1a1a1a;}
body .sbs-blog p.cap{color:#f5f2ec;}
main a:not([class]),.article-body a:not([class]),.sbs-blog a:not([class]),.sbs-related a:not([class]),footer a:not([class]){color:var(--gold,#C9A84C);}
.article-body a:not([class]),.sbs-blog a:not([class]),main .tax-crosslink a:not([class]){text-decoration:underline;text-underline-offset:2px;}
</style>`;

const files = [];
for (const f of readdirSync(ROOT)) if (f.endsWith('.html') && f !== 'preview-home.html') files.push(f);
for (const f of readdirSync(join(ROOT, 'Blog'))) if (f.endsWith('.html')) files.push(join('Blog', f));

let changed = 0;
for (const rel of files) {
  const p = join(ROOT, rel);
  let html = readFileSync(p, 'utf8');
  if (!html.includes('</head>')) { console.log(`!! no </head>: ${rel}`); continue; }
  html = html.replace(BLOCK_RE, '');                 // strip any prior injected block
  html = html.replace('</head>', `${BLOCK}\n</head>`); // inject fresh
  writeFileSync(p, html);
  changed++;
}
console.log(`Rewrote injected block on ${changed} pages. Total scanned: ${files.length}`);
