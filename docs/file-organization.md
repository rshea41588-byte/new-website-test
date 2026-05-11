# File Organization

This site is organized as a static GitHub Pages website. Some files should stay at the top level of the repository so the live website keeps working.

## Keep At The Root

Keep these files in the repository root unless all links and site settings are updated at the same time:

- `index.html`
- `blog.html`
- `_config.yml`
- `manifest.json`
- `favicon.ico`
- `apple-icon.png`
- `icon0.svg`
- `icon1.png`
- `web-app-manifest-192x192.png`
- `web-app-manifest-512x512.png`
- `robots.txt`
- `sitemap.xml`
- `logo.png`

## Blog Posts

Blog posts belong in `_posts/`.

Use this naming format:

```text
YYYY-MM-DD-post-title.md
```

## Future Safe Folders

These folders are safe to add later if the site is updated to reference them:

- `assets/images/` for general images.
- `assets/css/` for stylesheet files.
- `assets/js/` for script files.
- `docs/` for planning notes and repo documentation.

## Before Moving Files

Before moving a file, search for its filename in `index.html`, `blog.html`, `manifest.json`, `sitemap.xml`, and `robots.txt`. If a file is referenced there, update the reference at the same time.
