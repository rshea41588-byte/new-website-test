# -*- coding: utf-8 -*-
# Runs in GitHub Actions from the repo root (see .github/workflows/publish-scheduled-posts.yml).
# Publishes any queued post whose publish_date has arrived: moves it from _scheduled/ into Blog/
# and inserts its sitemap.xml <url> and Blog/index.html card. Idempotent — a post already in
# Blog/ is skipped and its queue copy cleaned up, so re-runs never double-publish.
#
# Local testing: set PUBLISH_TODAY=YYYY-MM-DD to simulate a date; add --dry-run to only list.
import os, sys, io, json, datetime

DRY = "--dry-run" in sys.argv
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHED = os.path.join(ROOT, "_scheduled")
BASE = "https://www.sheabusinesssolutions.com"

def read(p): return io.open(p, encoding="utf-8", newline="").read()
def write(p, t): io.open(p, "w", encoding="utf-8", newline="").write(t)
def nl_of(t): return "\r\n" if "\r\n" in t else "\n"

def apply_sitemap(meta):
    p = os.path.join(ROOT, "sitemap.xml"); sm = read(p); NL = nl_of(sm)
    if meta["slug"] in sm: return
    block = (f"  <url>\n    <loc>{BASE}/Blog/{meta['slug']}</loc>\n"
             f"    <lastmod>{meta['publish_date']}</lastmod>\n"
             f"    <changefreq>monthly</changefreq>\n    <priority>0.7</priority>\n  </url>\n").replace("\n", NL)
    write(p, sm.replace("</urlset>", block + "</urlset>", 1))

def apply_index(meta):
    p = os.path.join(ROOT, "Blog", "index.html"); idx = read(p); NL = nl_of(idx)
    if meta["slug"] in idx: return
    card = (f'\n            <a href="{BASE}/Blog/{meta["slug"]}" class="blog-card fade-up">\n'
            f'                <div class="blog-card-body">\n'
            f'                    <div class="blog-card-tag">{meta["tag"]}</div>\n'
            f'                    <h2>{meta["card_title"]}</h2>\n'
            f'                    <p>{meta["card_desc"]}</p>\n'
            f'                    <div class="blog-card-meta">\n'
            f'                        <span class="blog-card-date">{meta["date_label"]} &nbsp;&bull;&nbsp; {meta["readtime"]}</span>\n'
            f'                        <span class="blog-card-read">Read More &rarr;</span>\n'
            f'                    </div>\n                </div>\n            </a>').replace("\n", NL)
    anchor = '<div class="blog-grid">'; i = idx.index(anchor) + len(anchor)
    write(p, idx[:i] + card + idx[i:])

def validate_schema(src_path, slug):
    """Schema-validation build gate: every JSON-LD block in a page must parse,
    and the page must carry the canonical Article + FAQPage + BreadcrumbList graph.
    A failure raises, which fails the Actions run and stops the publish."""
    import re as _re
    t = read(src_path)
    blocks = _re.findall(r'<script type="application/ld\+json">(.*?)</script>', t, _re.S)
    if not blocks:
        raise SystemExit(f"SCHEMA GATE FAIL [{slug}]: no JSON-LD found")
    types = set()
    for b in blocks:
        try:
            doc = json.loads(b)
        except Exception as e:
            raise SystemExit(f"SCHEMA GATE FAIL [{slug}]: invalid JSON-LD ({e})")
        for node in (doc.get("@graph", [doc]) if isinstance(doc, dict) else []):
            ntype = node.get("@type")
            if isinstance(ntype, list): types.update(ntype)
            elif ntype: types.add(ntype)
    missing = {"Article", "FAQPage", "BreadcrumbList"} - types
    if missing:
        raise SystemExit(f"SCHEMA GATE FAIL [{slug}]: missing schema types {sorted(missing)}")
    print(f"  schema gate OK [{slug}]: {sorted(types)}")

def regate_outputs(meta):
    """Post-transform gate: apply_sitemap()/apply_index() rewrite files AFTER validate_schema()
    ran, so their OUTPUT is re-checked here. Any failure raises, which fails the Actions step
    before the commit/push step runs, so nothing ships."""
    import re as _re, xml.etree.ElementTree as _ET
    slug = meta["slug"]
    try:
        root = _ET.fromstring(read(os.path.join(ROOT, "sitemap.xml")).encode("utf-8"))
    except Exception as e:
        raise SystemExit(f"POST-TRANSFORM GATE FAIL [{slug}]: sitemap.xml does not parse ({e})")
    locs = [el.text for el in root.iter() if el.tag.endswith("loc")]
    if locs.count(f"{BASE}/Blog/{slug}") != 1:
        raise SystemExit(f"POST-TRANSFORM GATE FAIL [{slug}]: sitemap <loc> count != 1")
    validate_schema(os.path.join(ROOT, "Blog", slug), slug)
    for p in (os.path.join(ROOT, "Blog", "index.html"), os.path.join(ROOT, "Blog", slug)):
        t = read(p)
        if len(_re.findall(r"<h1[\s>]", t)) != 1:
            raise SystemExit(f"POST-TRANSFORM GATE FAIL [{slug}]: {os.path.basename(p)} does not carry exactly one <h1>")
        for b in _re.findall(r'<script type="application/ld\+json">(.*?)</script>', t, _re.S):
            try: json.loads(b)
            except Exception as e:
                raise SystemExit(f"POST-TRANSFORM GATE FAIL [{slug}]: invalid JSON-LD in {os.path.basename(p)} ({e})")
    print(f"  post-transform gate OK [{slug}]")

def main():
    manifest = json.load(io.open(os.path.join(SCHED, "manifest.json"), encoding="utf-8"))
    today = (datetime.date.fromisoformat(os.environ["PUBLISH_TODAY"])
             if os.environ.get("PUBLISH_TODAY") else datetime.datetime.utcnow().date())
    published = []
    for meta in manifest.get("posts", []):
        slug = meta["slug"]
        dest = os.path.join(ROOT, "Blog", slug)
        src = os.path.join(SCHED, slug)
        if os.path.exists(dest):                      # already published earlier
            if os.path.exists(src) and not DRY: os.remove(src)
            continue
        if datetime.date.fromisoformat(meta["publish_date"]) > today:   # not due yet
            continue
        if not os.path.exists(src):
            print(f"WARN: due but queued file missing: {slug}"); continue
        print(("[DRY] would publish: " if DRY else "publishing: ") + f"{slug} (due {meta['publish_date']})")
        validate_schema(src, slug)                     # SCHEMA VALIDATION GATE (fails the build on invalid/missing JSON-LD)
        if DRY: continue
        os.replace(src, dest)                          # move out of queue into Blog/
        apply_sitemap(meta); apply_index(meta)
        regate_outputs(meta)                           # re-run the gates on the transformed output
        published.append(slug)
    if not DRY and not published:
        print(f"No posts due as of {today}.")

if __name__ == "__main__":
    main()
