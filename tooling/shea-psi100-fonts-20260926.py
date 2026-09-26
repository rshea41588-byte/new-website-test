#!/usr/bin/env python3
"""PSI-100 pass 2026-09-26 (Bloomview). Perf only, no visible change.

1. FONT DEDUPE. Every weight file under /fonts/ is a byte-identical copy of ONE variable font per
   family+subset (md5-proven below: cormorant-garamond-{400,500,600,700}-latin.woff2 are the same bytes,
   likewise jost-{300..600}). The inline block declared 16 @font-face rules -> the browser fetched the
   same file up to 4x under 4 URLs (7 font requests, ~222 KB on the homepage). Collapsed to one
   @font-face per family+subset with a font-weight RANGE equal to the min..max of the old discrete
   weights, pointing at the 400 file. Rendering is identical: the old faces were the same variable file,
   and Chrome clamps a requested weight into the face range exactly as the old nearest-face match did
   (all weights used in page CSS are 100-multiples inside/at the ends of the old sets).
   Font preloads collapsed to the 2 canonical latin files.
2. HERO srcset (index.html only): ryan_hero.webp (900w, 86 KB) now offered with 480w/640w derivatives
   made from the original JPEG master, same crop.

Idempotent: a file already carrying the marker is skipped. Exact-string, asserts every anchor.
Only pages carrying the standard inline font block are touched (Blog/ is protected and excluded).
"""
import hashlib, re, sys, glob, os, collections

ROOT = sys.argv[1] if len(sys.argv) > 1 else '.'
MARK = '/*psi100-fonts-20260926*/'
CANON = {'Cormorant Garamond': 'cormorant-garamond-400', 'Jost': 'jost-400'}

def md5(p):
    return hashlib.md5(open(os.path.join(ROOT, p.lstrip('/')), 'rb').read()).hexdigest()

BLOCK_RE = re.compile(r"<style>(@font-face\{font-family:'Cormorant Garamond'[^<]*)</style>")
FACE_RE = re.compile(r"@font-face\{font-family:'([^']+)';font-style:(\w+);font-weight:(\d+);font-display:swap;src:url\((/fonts/[a-z0-9-]+\.woff2)\) format\('woff2'\);unicode-range:([^}]*)\}")
PRELOAD_RE = re.compile(r'[ \t]*<link rel="preload" as="font" type="font/woff2" href="/fonts/[a-z0-9-]+\.woff2" crossorigin>\n?')

def new_block(css):
    faces = FACE_RE.findall(css)
    rebuilt = ''.join(m.group(0) for m in FACE_RE.finditer(css))
    assert rebuilt == css, 'block has content outside the parsed @font-face rules'
    groups = collections.OrderedDict()
    for fam, style, wt, url, ur in faces:
        groups.setdefault((fam, style, ur), []).append((int(wt), url))
    out = []
    for (fam, style, ur), lst in groups.items():
        hashes = {md5(u) for _, u in lst}
        assert len(hashes) == 1, f'{fam} {ur[:20]}: files differ, cannot merge: {lst}'
        subset = 'latin-ext' if lst[0][1].endswith('-latin-ext.woff2') else 'latin'
        canon = f'/fonts/{CANON[fam]}-{subset}.woff2'
        assert md5(canon) in hashes
        lo, hi = min(w for w, _ in lst), max(w for w, _ in lst)
        out.append(f"@font-face{{font-family:'{fam}';font-style:{style};font-weight:{lo} {hi};font-display:swap;src:url({canon}) format('woff2');unicode-range:{ur}}}")
    return MARK + ''.join(out)

PRELOADS = ('<link rel="preload" as="font" type="font/woff2" href="/fonts/cormorant-garamond-400-latin.woff2" crossorigin>\n'
            '    <link rel="preload" as="font" type="font/woff2" href="/fonts/jost-400-latin.woff2" crossorigin>\n')

HERO_OLD = '<link rel="preload" as="image" href="images/ryan_hero.webp" type="image/webp" fetchpriority="high">'
HERO_NEW = ('<link rel="preload" as="image" href="images/ryan_hero.webp" imagesrcset="images/ryan_hero-480.webp 480w, images/ryan_hero-640.webp 640w, images/ryan_hero.webp 900w" '
            'imagesizes="(max-width:1024px) 260px, 340px" type="image/webp" fetchpriority="high">')
PIC1_OLD = '<div class="hero-img-frame"><picture style="display:block;width:100%;height:100%"><source type="image/webp" srcset="images/ryan_hero.webp">'
PIC1_NEW = ('<div class="hero-img-frame"><picture style="display:block;width:100%;height:100%"><source type="image/webp" '
            'srcset="images/ryan_hero-480.webp 480w, images/ryan_hero-640.webp 640w, images/ryan_hero.webp 900w" sizes="(max-width:1024px) 260px, 340px">')
PIC2_OLD = '<div class="about-img-border-2"></div><picture style="display:block"><source type="image/webp" srcset="images/ryan_hero.webp">'
PIC2_NEW = ('<div class="about-img-border-2"></div><picture style="display:block"><source type="image/webp" '
            'srcset="images/ryan_hero-480.webp 480w, images/ryan_hero-640.webp 640w, images/ryan_hero.webp 900w" sizes="(max-width:600px) calc(100vw - 40px), 470px">')

changed = []
for f in sorted(glob.glob(os.path.join(ROOT, '*.html'))):
    s = open(f, encoding='utf-8', newline='').read()
    if MARK in s:
        continue
    m = BLOCK_RE.search(s)
    if not m:
        continue
    assert len(BLOCK_RE.findall(s)) == 1, f
    t = s[:m.start(1)] + new_block(m.group(1)) + s[m.end(1):]
    pre = list(PRELOAD_RE.finditer(t))
    assert 1 <= len(pre) <= 4, (f, len(pre))
    first = pre[0]
    indent = re.match(r'[ \t]*', first.group(0)).group(0)
    parts, last = [], 0
    for i, p in enumerate(pre):
        parts.append(t[last:p.start()])
        if i == 0:
            parts.append(indent + PRELOADS)
        last = p.end()
    parts.append(t[last:])
    t = ''.join(parts)
    assert t.count('rel="preload" as="font"') == 2, f
    if os.path.basename(f) == 'index.html':
        for old, new in ((HERO_OLD, HERO_NEW), (PIC1_OLD, PIC1_NEW), (PIC2_OLD, PIC2_NEW)):
            assert t.count(old) == 1, (f, old[:60])
            t = t.replace(old, new)
    open(f, 'w', encoding='utf-8', newline='').write(t)
    changed.append(os.path.basename(f))
print(len(changed), 'files changed')
print('\n'.join(changed))
