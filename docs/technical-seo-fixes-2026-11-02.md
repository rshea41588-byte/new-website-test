# Technical SEO repairs

The November 2 audit identified a malformed homepage schema block, an internal link to an unpublished article, copied language annotations on the contact page, and an unavailable Cookiebot configuration.

The repairs close the homepage schema before the Google Ads scripts, point the article link to the published monthly bookkeeping service page, and remove the unrelated contact language annotations. The existing service translation pairs remain intact.

## Consent controls

CookieConsent 3.2.1 is hosted in `assets/vendor/cookieconsent/` under its MIT license. Its license and source checksums are included. No Cookiebot subscription or remote consent service is needed.

`assets/site-consent.js` configures necessary storage, analytics, advertising, and external maps. Optional scripts use `type="text/plain"` with a `data-category`. Google Maps uses `data-sbs-map-src`. Google consent defaults to denied. The footer settings button allows changes, and withdrawal reloads the page to unload optional scripts. The preference cookie lasts 182 days.

Forms remain available without optional consent. The confirmation page keeps its existing lead receipt in memory so enabled conversion scripts can read it after consent initializes, while direct visits and refreshes do not create a new receipt.

Run `python tooling/apply-consent.py` after applying existing tracking templates to a page. It is idempotent and stops if a script combines optional tracking with a form submission handler that needs individual review. When adding a new tracking service or iframe provider, classify it explicitly and update the verification rules. The library does not automatically classify new integrations.

## Routing and headers

The homepage file alias and blog directory aliases redirect to their canonical public URLs. Existing public page rewrites are preserved.

The content security policy restricts base URLs, embedded objects, and framing, and upgrades insecure subresources. It intentionally does not add a script source allowlist that could break existing integrations. Frame restrictions, content type protection, and a referrer policy are also configured.

Vercel's mandatory HTTP to HTTPS redirect precedes the domain redirect. The two steps from the HTTP apex address are expected hosting behavior. Collapsing that path is not a repository repair and does not justify changing hosting or the preferred domain.

## Verification

1. Run `node tooling/verify-site-layout.mjs`.
2. Run `python tooling/verify-technical-seo.py`.
3. Run `node --check assets/site-consent.js`.
4. In a browser, check necessary only, each optional category, saved choices, withdrawal, maps, and the consultation form. Use intercepted submissions for tests so they do not create real leads.

The structural check covers all sitemap URLs, schema parsing, canonical tags, internal destinations, language alternates, consent script boundaries including the confirmation page, and the required headers. Real user Core Web Vitals and actual index coverage require their own data sources.
