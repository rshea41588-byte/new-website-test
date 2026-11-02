# Shea Business Solutions Website

These are the source files for the [Shea Business Solutions website](https://www.sheabusinesssolutions.com/). Vercel publishes the site from the production branch, `main`.

## Where to edit

| Folder or file | Contents |
| --- | --- |
| `index.html` | Homepage |
| `pages/services/` | Bookkeeping, payroll, QuickBooks and tax services |
| `pages/service-areas/` | City and neighborhood pages |
| `pages/industries/` | Industry specific service pages |
| `pages/guides/` | Pricing and service selection guides |
| `pages/general/` | Contact, FAQ, reviews and navigation hubs |
| `Blog/` | Published articles and the blog listing |
| `_scheduled/` | Article publishing queue and its publisher |
| `images/`, `fonts/`, `assets/` | Website media, fonts and shared JavaScript |
| `api/` | Lead logging endpoint |
| `thank-you/` | Form confirmation page |
| `tooling/` | Maintenance scripts and layout verification |
| `docs/` | Organization guide, notes, reference files and homepage preview |

## Public addresses

Folder names organize the source files. Each page under `pages/` has a rewrite in `vercel.json` that serves its existing public address. For example, `pages/services/bookkeeping-services-orlando.html` is served at `/bookkeeping-services-orlando.html`.

Commit page moves and their routing rules together. See [the organization guide](docs/file-organization.md) for the file map and publishing instructions.

## Local checks

Run these commands from the repository folder with Node.js 20 or later and Python 3.12.

```powershell
node tooling/verify-site-layout.mjs
python _scheduled/publish_due.py --dry-run
```

For a browser preview that applies `vercel.json`, use Vercel's local development command, `vercel dev`, after installing its CLI and linking this project. Requests to the existing public paths need those routing rules. The [Vercel CLI guide](https://vercel.com/docs/cli/dev) describes local setup.

## Publishing

Review changes on a working branch and test a Vercel preview before merging into `main`. Publishing requires the moved files and `vercel.json` in the same commit. The GitHub workflow also checks approved queued articles daily and commits articles whose publication date has arrived.
