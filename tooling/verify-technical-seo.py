"""Check published HTML, discovery, and consent boundaries without network requests."""
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parent.parent
ORIGIN = 'https://www.sheabusinesssolutions.com'
CONFIG = json.loads((ROOT / 'vercel.json').read_text(encoding='utf-8'))
REWRITES = {rule['source']: rule['destination'] for rule in CONFIG['rewrites']}
REDIRECTS = {rule['source']: rule['destination'] for rule in CONFIG['redirects'] if ':' not in rule['source']}
EXCLUDED = [line.strip() for line in (ROOT / '.vercelignore').read_text().splitlines() if line.strip()]


def source_file(address):
    path = unquote(urlparse(address).path)
    seen = set()
    while path in REDIRECTS:
        assert path not in seen, f'Redirect loop at {address}'
        seen.add(path)
        path = REDIRECTS[path]
    relative = REWRITES.get(path, path).lstrip('/')
    if not relative or relative.endswith('/'):
        relative += 'index.html'
    assert not any(relative == item or (item.endswith('/') and relative.startswith(item)) for item in EXCLUDED), f'Excluded destination {address}'
    result = ROOT / relative
    assert result.is_file(), f'Missing destination {address}'
    return result


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.canonical = []
        self.alternates = []
        self.links = []
        self.scripts = []
        self.robots = []
        self.current = None
        self.feed(text)

    def handle_starttag(self, tag, items):
        attrs = dict(items)
        if tag == 'link' and attrs.get('rel') == 'canonical':
            self.canonical.append(attrs.get('href'))
        if tag == 'link' and 'hreflang' in attrs:
            self.alternates.append(attrs['href'])
        if tag == 'a' and 'href' in attrs:
            self.links.append(attrs['href'])
        if tag == 'meta' and attrs.get('name') in ('robots', 'googlebot'):
            self.robots.append(attrs.get('content', ''))
        if tag == 'script':
            self.current = {'attrs': attrs, 'text': ''}
            self.scripts.append(self.current)

    def handle_data(self, text):
        if self.current is not None:
            self.current['text'] += text

    def handle_endtag(self, tag):
        if tag == 'script':
            self.current = None


def main():
    xml = ElementTree.parse(ROOT / 'sitemap.xml')
    addresses = [node.text for node in xml.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
    pages = {}
    schema_count = 0
    link_count = 0
    for address in addresses:
        text = source_file(address).read_text(encoding='utf-8')
        page = Page(text)
        assert page.canonical == [address], f'Canonical conflict on {address}'
        assert not any('noindex' in value.lower() for value in page.robots), f'Noindex on {address}'
        assert 'cookiebot.com' not in text, f'Obsolete consent dependency on {address}'
        schemas = [script for script in page.scripts if script['attrs'].get('type') == 'application/ld+json']
        assert schemas, f'No schema on {address}'
        for schema in schemas:
            json.loads(schema['text'])
            schema_count += 1
        assert any(script['attrs'].get('src') == '/assets/site-consent.js' for script in page.scripts), f'No consent control on {address}'
        for script in page.scripts:
            attrs = script['attrs']
            combined = script['text'] + str(attrs.get('src', '')) + str(attrs.get('data-src', ''))
            tracker = any(marker in combined.lower() for marker in ('googletagmanager.com', 'oaiq', 'callrail', 'phone-click.php', 'bv-attr.js'))
            if attrs.get('type') == 'application/ld+json':
                continue
            if tracker:
                assert attrs.get('type') == 'text/plain' and attrs.get('data-category') in ('analytics', 'marketing'), f'Ungated tracker on {address}'
        pages[address] = page
    for address, page in pages.items():
        if page.alternates:
            assert address in page.alternates, f'Missing language self reference on {address}'
            for alternate in page.alternates:
                assert address in pages[alternate].alternates, f'Missing language return reference on {address}'
        for link in set(page.links):
            destination = urljoin(address, link)
            parsed = urlparse(destination)
            if parsed.scheme in ('http', 'https') and parsed.hostname in ('www.sheabusinesssolutions.com', 'sheabusinesssolutions.com'):
                source_file(destination)
                link_count += 1
    headers = {item['key'].lower(): item['value'] for group in CONFIG['headers'] for item in group['headers']}
    for name in ('content-security-policy', 'x-frame-options', 'x-content-type-options', 'referrer-policy'):
        assert headers.get(name), f'Missing security header {name}'
    assert REDIRECTS['/index.html'] == '/'
    assert REDIRECTS['/Blog'] == REDIRECTS['/Blog/index.html'] == '/Blog/'
    confirmation = Page((ROOT / 'thank-you/index.html').read_text(encoding='utf-8'))
    assert any(script['attrs'].get('src') == '/assets/site-consent.js' for script in confirmation.scripts)
    for script in confirmation.scripts:
        attrs = script['attrs']
        combined = script['text'] + str(attrs.get('src', '')) + str(attrs.get('data-src', ''))
        if any(marker in combined.lower() for marker in ('googletagmanager.com', 'oaiq', 'callrail', 'phone-click.php')):
            assert attrs.get('type') == 'text/plain', 'Ungated tracking on confirmation page'
    print(f'Verified {len(pages)} public pages, {schema_count} schema blocks, {link_count} internal links, language alternates, consent gates including confirmation, and security headers.')


if __name__ == '__main__':
    main()
