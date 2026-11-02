import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { SITE_ROOT, listMainPages } from './site-pages.mjs';

const config = JSON.parse(fs.readFileSync(path.join(SITE_ROOT, 'vercel.json'), 'utf8'));
const rewrites = new Map();
const destinations = new Set();

for (const rule of config.rewrites) {
  assert.match(rule.source, /^\/[a-z0-9-]+\.html$/);
  assert.match(rule.destination, /^\/pages\/[a-z-]+\/[a-z0-9-]+\.html$/);
  assert.equal(path.posix.basename(rule.destination), rule.source.slice(1));
  assert(!rewrites.has(rule.source), `Duplicate public address ${rule.source}`);
  assert(!destinations.has(rule.destination), `Duplicate file mapping ${rule.destination}`);
  assert(fs.statSync(path.join(SITE_ROOT, rule.destination.slice(1))).isFile());
  assert(!fs.existsSync(path.join(SITE_ROOT, rule.source.slice(1))),
    `A root file would override the rewrite for ${rule.source}`);
  rewrites.set(rule.source, rule.destination);
  destinations.add(rule.destination);

  const category = rule.destination.split('/')[2];
  assert(config.redirects.some(redirect =>
    redirect.source === `/pages/${category}/:file` &&
    redirect.destination === '/:file' && redirect.permanent === true),
    `Missing redirect from the folder address for ${rule.destination}`);
}

for (const file of listMainPages()) {
  const relative = path.relative(SITE_ROOT, file).split(path.sep).join('/');
  if (relative.startsWith('pages/')) {
    assert(destinations.has(`/${relative}`), `Missing public address for ${relative}`);
  }
}

const sitemap = fs.readFileSync(path.join(SITE_ROOT, 'sitemap.xml'), 'utf8');
const addresses = [...sitemap.matchAll(/<loc>(.*?)<\/loc>/g)].map(match => new URL(match[1]));
assert(addresses.length > 0, 'The sitemap must contain page addresses');
const seen = new Set();
const exclusions = fs.readFileSync(path.join(SITE_ROOT, '.vercelignore'), 'utf8')
  .split(/\r?\n/).map(line => line.trim()).filter(line => line && !line.startsWith('#'));

for (const address of addresses) {
  assert.equal(address.origin, 'https://www.sheabusinesssolutions.com');
  assert(!seen.has(address.href), `Duplicate sitemap address ${address.href}`);
  seen.add(address.href);
  let relative = (rewrites.get(address.pathname) || address.pathname).slice(1);
  if (!relative || relative.endsWith('/')) relative += 'index.html';
  assert(!exclusions.some(exclusion =>
    exclusion.endsWith('/') ? relative.startsWith(exclusion) : relative === exclusion),
    `Sitemap address points to an excluded file ${address.href}`);
  assert(fs.existsSync(path.join(SITE_ROOT, relative)),
    `Sitemap address has no file ${address.href}`);
}

console.log(`Verified ${rewrites.size} page rewrites and ${addresses.length} sitemap addresses.`);
