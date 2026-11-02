import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

export const SITE_ROOT = fileURLToPath(new URL('../', import.meta.url));

export function listMainPages(root = SITE_ROOT) {
  const files = fs.readdirSync(root).filter(file => file.endsWith('.html'));
  const pages = path.join(root, 'pages');
  if (fs.existsSync(pages)) {
    files.push(...fs.readdirSync(pages, { recursive: true })
      .filter(file => file.endsWith('.html'))
      .map(file => path.join('pages', file)));
  }
  return files.sort().map(file => path.join(root, file));
}
