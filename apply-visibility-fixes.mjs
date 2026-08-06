#!/usr/bin/env node
/**
 * Shea Business Solutions — visibility fixes 2026-08-06
 * Fixes three CSS-only bugs Ryan flagged on the 08-06 SEO check-in call. Pure
 * ADD (one injected <style> block per page); no content, llms.txt, or lead-page
 * copy is touched. Idempotent: skips any page already carrying the marker.
 *
 *  A) NAV OVERLAY (34 root money/city/service pages): the template styles the
 *     bare `nav` element type (position:fixed;height:80px;opaque bg), so the
 *     second <nav class="breadcrumb"> inherits full nav-bar chrome and paints
 *     ON TOP of #mainNav, hiding logo+menu. Fix: reset nav.breadcrumb to static.
 *  B) INVISIBLE TABLE (2 blogs): .sbs-blog tbody td inherits cream text while
 *     even rows get a near-white (#f7f9fc) zebra bg -> cream-on-white invisible.
 *     Fix: make it a light card (white table base + dark td text).
 *  C) DEFAULT-BLUE/PURPLE CONTENT LINKS (sitewide dark theme): unclassed content
 *     + footer anchors fall back to #0000EE / #551A8B. Fix: brand gold.
 */
import { readFileSync, writeFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';

const ROOT = new URL('.', import.meta.url).pathname;
const MARKER = 'SBS visibility fixes 2026-08-06';

const BLOCK = `<style>
/* ${MARKER} (nav overlay + blog table + content link color) — CSS only, additive */
nav.breadcrumb{position:static;height:auto;padding:0;background:none;backdrop-filter:none;border-bottom:none;z-index:auto;}
.sbs-blog table{background:#fff;}
.sbs-blog tbody td{color:#1a1a1a;}
.article-body a:not([class]),.sbs-blog a:not([class]),.sbs-related a:not([class]),footer a:not([class]){color:var(--gold,#C9A84C);}
.article-body a:not([class]),.sbs-blog a:not([class]){text-decoration:underline;text-underline-offset:2px;}
</style>`;

// Every production HTML page (root + Blog/), excluding the throwaway preview.
const files = [];
for (const f of readdirSync(ROOT)) if (f.endsWith('.html') && f !== 'preview-home.html') files.push(f);
for (const f of readdirSync(join(ROOT, 'Blog'))) if (f.endsWith('.html')) files.push(join('Blog', f));

let changed = 0, skipped = 0;
for (const rel of files) {
  const p = join(ROOT, rel);
  let html = readFileSync(p, 'utf8');
  if (html.includes(MARKER)) { skipped++; continue; }
  if (!html.includes('</head>')) { console.log(`!! no </head>: ${rel}`); continue; }
  html = html.replace('</head>', `${BLOCK}\n</head>`);
  writeFileSync(p, html);
  changed++;
}
console.log(`Injected into ${changed} pages, skipped ${skipped} (already had marker). Total scanned: ${files.length}`);
