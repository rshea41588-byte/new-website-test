"""Apply the site's consent categories without reformatting its HTML."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = re.compile(r'<script\b(?P<attrs>[^>]*)>(?P<body>.*?)</script\s*>', re.I | re.S)
INCLUDES = '''<link rel="stylesheet" href="/assets/vendor/cookieconsent/cookieconsent.css">
    <link rel="stylesheet" href="/assets/site-consent.css">
    <script defer src="/assets/vendor/cookieconsent/cookieconsent.umd.js"></script>
    <script defer src="/assets/site-consent.js"></script>'''


def replace_script(match):
    attrs, body = match['attrs'], match['body']
    if re.search(r'\bid=["\']Cookiebot["\']', attrs, re.I):
        return INCLUDES
    if 'application/ld+json' in attrs or 'data-category=' in attrs:
        return match.group()
    combined = (attrs + body).lower()
    category = None
    if any(marker in combined for marker in ('oaiq', 'callrail', 'phone-click.php', 'bv-attr.js')):
        category = 'marketing'
    elif 'googletagmanager.com' in combined or re.search(r'\bgtag\s*\(', body):
        category = 'marketing' if 'AW-' in attrs + body else 'analytics'
    if not category:
        return match.group()
    if 'new FormData' in body or 'fetch(' in body:
        raise ValueError('A tracking script also handles a form and needs separate review')
    # Preserve the consent aware Google queue instead of replacing its event guard.
    body = re.sub(r'function\s+gtag\s*\(\)\s*\{\s*dataLayer\.push\(arguments\);?\s*\}',
                  '', body)
    attrs = re.sub(r'\s+type=["\'][^"\']*["\']', '', attrs, flags=re.I)
    attrs = re.sub(r'(?<![\w-])src=', 'data-src=', attrs, flags=re.I)
    return f'<script type="text/plain" data-category="{category}"{attrs}>{body}</script>'


def main():
    files = list(ROOT.glob('*.html'))
    for folder in ('pages', 'Blog', 'thank-you', '_scheduled'):
        files.extend((ROOT / folder).rglob('*.html'))
    changed = 0
    for path in files:
        original = path.read_bytes()
        text = original.decode('utf-8')
        if 'id="Cookiebot"' not in text and '/assets/site-consent.js' not in text and not any(marker in text for marker in ('googletagmanager.com', 'oaiq.min.js', 'cdn.callrail.com')):
            continue
        if 'id="Cookiebot"' not in text and '/assets/site-consent.js' not in text:
            text = text.replace('<head>', '<head>\n    ' + INCLUDES, 1)
        text = re.sub(r'\s*<link\b[^>]*href="https://consent(?:cdn)?\.cookiebot\.com"[^>]*>', '', text)
        text = SCRIPTS.sub(replace_script, text)
        text = re.sub(r'(window\.dataLayer = window\.dataLayer \|\| \[\];\r?\n)[ \t]+(\r?\n)', r'\1\2', text)
        text = text.replace('hidden data-sbs-map-hidden data-sbs-map-src=', 'hidden data-sbs-map-src=')
        text = re.sub(r'<iframe\b[^>]*(?<![\w-])src="https://maps\.google\.com/[^>]*>',
                      lambda match: re.sub(r'(?<![\w-])src=', 'hidden data-sbs-map-src=', match.group(), count=1), text)
        if path == ROOT / 'index.html':
            text = text.replace('<li>Cookiebot (cookie consent management)</li>',
                                '<li>CookieConsent (cookie preferences hosted on this website)</li>')
            text = text.replace('>Cookiebot</td>', '>Website cookie preferences</td>')
            text = re.sub(r'\s*<li><a href="https://www\.cookiebot\.com/en/privacy-policy/".*?</li>',
                          '', text, flags=re.S)
        if path == ROOT / 'thank-you/index.html':
            text = re.sub(r'\s*<link\b[^>]*href="https://fonts\.(?:googleapis|gstatic)\.com[^>]*>', '', text)
            if 'sbs-local-confirmation-fonts' not in text:
                text = text.replace('</head>', '''<style id="sbs-local-confirmation-fonts">
@font-face{font-family:'Jost';font-style:normal;font-weight:300 600;font-display:swap;src:url('/fonts/jost-400-latin.woff2') format('woff2')}
@font-face{font-family:'Cormorant Garamond';font-style:normal;font-weight:400 700;font-display:swap;src:url('/fonts/cormorant-garamond-400-latin.woff2') format('woff2')}
</style>
</head>''')
            if 'window.sbsPendingLead = raw;' not in text:
                text = text.replace('sessionStorage.removeItem(\'bvg_lead_pending\');',
                                    'window.sbsPendingLead = raw;\n            sessionStorage.removeItem(\'bvg_lead_pending\');')
            text = text.replace('&& sessionStorage.getItem("bvg_lead_pending")) lead("form");',
                                '&& (sessionStorage.getItem("bvg_lead_pending") || window.sbsPendingLead)) lead("form");')
            text = text.replace("if (!sessionStorage.getItem('bvg_lead_pending')) return;",
                                "if (!(sessionStorage.getItem('bvg_lead_pending') || window.sbsPendingLead)) return;")
        result = text.encode('utf-8')
        if result != original:
            path.write_bytes(result)
            changed += 1
    print(f'Configured local consent controls on {changed} pages.')


if __name__ == '__main__':
    main()
