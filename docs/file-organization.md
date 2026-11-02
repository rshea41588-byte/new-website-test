# File Organization

## Hosting

Vercel serves the static HTML files and the endpoint in `api/`. The production deployment checked on November 2, 2026 uses `main` at commit `19b04f7067b33690a4e8e09b0bc70e39c3783df3`.

The organization work groups 61 existing public pages under `pages/`. Their HTML contents, public addresses, canonical tags and sitemap entries are preserved. Vercel rewrites each existing address to its new file location. Requests directly to the source folder addresses redirect to the existing public addresses.

## Page folders

| Location | Pages |
| --- | --- |
| `pages/services/` | 17 service pages, including the Spanish bookkeeping and payroll pages |
| `pages/service-areas/` | 23 city and neighborhood pages, including Spanish Kissimmee |
| `pages/industries/` | 10 pages for construction, restaurants, retail and other industries |
| `pages/guides/` | 6 pages about pricing and selecting a provider |
| `pages/general/` | Contact, FAQ, reviews, services hub and service areas hub |
| `Blog/` | Existing articles and `index.html`, the blog listing |

For example, edit `pages/service-areas/bookkeeping-windermere-fl.html` for the public page `/bookkeeping-windermere-fl.html`. Public links continue to use the existing address.

## Supporting folders

| Location | Purpose |
| --- | --- |
| `_scheduled/` | Queue metadata, draft articles awaiting their dates and `publish_due.py` |
| `tooling/` | Maintenance scripts, `site-pages.mjs` and `verify-site-layout.mjs` |
| `docs/reference/` | Previous sitemap snapshot, indexable URL list, font CSS reference and IndexNow key reference |
| `docs/previews/` | The previous homepage preview |
| `images/`, `fonts/`, `assets/` | Media and files used by the public site |
| `api/` | Lead logging endpoint |
| `thank-you/` | Form confirmation page |
| `.github/workflows/` | Automatic article publishing workflow |

Files in `docs/`, `tooling/` and `_scheduled/` are excluded from Vercel uploads through `.vercelignore`. Existing exclusions for two unpublished blog articles are retained. Moving the old homepage preview into `docs/previews/` keeps it excluded as well.

## Files at the top level

1. `index.html` and `404.html` serve the homepage and missing page response.
2. `robots.txt`, `sitemap.xml` and `llms.txt` provide discovery information.
3. `google6fb6dbc31d8bbc9a.html` and `6e2bb6923e0d1808deab92ba79f8cef4.txt` provide verification at their existing addresses.
4. `favicon.ico`, `favicon-32x32.png`, `apple-touch-icon.png` and `site.webmanifest` provide browser icons and manifest information.
5. `vercel.json` controls public routes and existing redirects.
6. `.vercelignore` controls deployment exclusions. `.gitignore` controls Git exclusions.
7. `_config.yml` is retained as the existing GitHub Pages configuration.
8. `README.md` provides the folder overview.

## Adding or moving a page

1. Create the HTML file in the appropriate page folder.
2. Add an explicit public address and destination to `vercel.json`. Every file in `pages/` needs one rewrite. Follow the existing naming pattern and keep public paths flat.
3. Update links and `sitemap.xml` when adding a new public page. When moving an existing page, retain its public address and relative asset references.
4. Run `node tooling/verify-site-layout.mjs` and `python _scheduled/publish_due.py --dry-run`.
5. Commit the file changes and routing changes together, check a Vercel preview, then merge the approved change into `main`.

For an article, use the existing `Blog/` format. To schedule publication, place the article in `_scheduled/` and add its metadata to `_scheduled/manifest.json`. The existing workflow publishes due articles, updates the blog listing and sitemap, and pushes the resulting commit.

The historical `tooling/section-order-gate.mjs` already reports 155 findings against the current production version. Its file discovery now includes the organized pages. Those findings concern the existing page sections and need their own review.
