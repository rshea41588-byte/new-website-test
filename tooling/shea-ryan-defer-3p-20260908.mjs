#!/usr/bin/env node
// perf-defer-3p-2026-09-08 — Shea Business Solutions (Ryan) / rshea41588-byte:new-website-test
// Pull the two eager third-party scripts (GA gtag ~170KB, OpenAI oaiq ~27KB) OFF the critical
// path so the LCP hero-text font swap is not starved for bandwidth on throttled mobile.
// SAFE: both keep their inline queue shims (dataLayer / window.oaiq.q), which buffer every event
// until the real SDK loads on first interaction or idle — zero conversion/analytics loss.
// Verified live 2026-09-08: gtag & oaiq already fire ungated (Cookiebot auto-block does not gate
// them), so deferring changes no consent posture. Idempotent, exact-string, line-endings preserved.
import fs from 'node:fs';
import path from 'node:path';

const ROOT = path.resolve(process.argv[2] || '.');
const DRY = process.argv.includes('--dry');
const MARK = 'perf-defer-3p-2026-09-08';

const GTAG_TAG = '<script async src="https://www.googletagmanager.com/gtag/js?id=G-LYDBN7KGBN"></script>';
const OAIQ_TAG = '<script async src="https://bzrcdn.openai.com/sdk/oaiq.min.js"></script>';

const loader = (label, url) =>
`<script>/* ${MARK}: load ${label} off the critical path (first interaction or idle); inline queue shim buffers events until it loads — no loss */
(function(){var d=0;function L(){if(d)return;d=1;var e=document.createElement('script');e.src='${url}';e.async=1;document.head.appendChild(e);}var ev=['pointerdown','keydown','touchstart','scroll','mousemove'];function H(){L();ev.forEach(function(x){removeEventListener(x,H,{passive:true});});}ev.forEach(function(x){addEventListener(x,H,{passive:true});});if('requestIdleCallback'in window){requestIdleCallback(L,{timeout:4000});}else{setTimeout(L,4000);}})();</script>`;

const GTAG_LOADER = loader('GA (gtag.js)', 'https://www.googletagmanager.com/gtag/js?id=G-LYDBN7KGBN');
const OAIQ_LOADER = loader('OpenAI pixel (oaiq)', 'https://bzrcdn.openai.com/sdk/oaiq.min.js');

const files = [];
for (const dir of [ROOT, path.join(ROOT, 'Blog')]) {
  if (!fs.existsSync(dir)) continue;
  for (const f of fs.readdirSync(dir)) if (f.endsWith('.html')) files.push(path.join(dir, f));
}

let changed = 0, gtagN = 0, oaiqN = 0, skipMarked = 0;
const report = [];
for (const fp of files) {
  let src = fs.readFileSync(fp, 'utf8');
  if (src.includes(MARK)) { skipMarked++; continue; }
  const before = src;
  let g = 0, o = 0;
  if (src.includes(GTAG_TAG)) { src = src.replace(GTAG_TAG, GTAG_LOADER); g = 1; gtagN++; }
  if (src.includes(OAIQ_TAG)) { src = src.replace(OAIQ_TAG, OAIQ_LOADER); o = 1; oaiqN++; }
  if (src !== before) {
    changed++;
    report.push(`${g?'G':'-'}${o?'O':'-'} ${path.relative(ROOT, fp)}`);
    if (!DRY) fs.writeFileSync(fp, src);
  }
}
console.log(`${DRY ? 'DRY-RUN' : 'APPLIED'} root=${ROOT}`);
console.log(`files scanned: ${files.length} | changed: ${changed} | gtag replaced: ${gtagN} | oaiq replaced: ${oaiqN} | already-marked(skipped): ${skipMarked}`);
for (const r of report) console.log('  ' + r);
