"""Assemble the static site from src/ into site/.

    python src/build.py           # production build for the cPanel host (clean URLs, PHP form, writes .htaccess)
    python src/build.py --local   # preview build that opens by double-clicking
    python src/build.py --pages --base /pathfinder/ --site-url https://papichuloxxx.github.io/pathfinder/ --noindex
                                  # GitHub Pages build (run by .github/workflows/pages.yml): no PHP, no .htaccess

Pages live in src/pages/*.html. Each starts with an HTML comment holding JSON metadata
(title, description, path, nav). Shared blocks live in src/partials/ and are included
with {{> name}}. Project cards are generated from src/data/projects.json.
Images are referenced with {{img name="..." alt="..." sizes="..."}}; run images.py first.
"""
import hashlib
import html
import json
import os
import re
import argparse
import sys
from urllib.parse import quote

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.normpath(os.path.join(HERE, '..', 'site'))
IMG_DIR = os.path.join(SITE, 'assets', 'img')
SITE_URL = 'https://www.pathdriveway.co.zw/'

# The one main WhatsApp line. site.js swaps in a message naming the service being viewed.
WHATSAPP_NUMBER = '263789734406'
WHATSAPP_DISPLAY = '078 973 4406'
WHATSAPP_TEXT = 'Hello Pathfinder, I would like a quote for my project.'
ENQUIRY_EMAIL = 'admin@pathdriveway.co.zw'

SIZES = {
    'full': '100vw',
    'card4': '(min-width: 1140px) 17.5rem, (min-width: 640px) calc(50vw - 3rem), calc(100vw - 2rem)',
    'card3': '(min-width: 1000px) 23.5rem, (min-width: 640px) calc(50vw - 3rem), calc(100vw - 2rem)',
    'card2': '(min-width: 768px) calc(50vw - 3rem), calc(100vw - 2rem)',
    'half': '(min-width: 900px) calc(50vw - 4rem), calc(100vw - 2rem)',
}
CATEGORY_LABELS = {'paving': 'Paving', 'tarmac': 'Tarmac', 'construction': 'Construction', 'renovations': 'Renovations'}

def schema(site_url):
    return {
        '@context': 'https://schema.org',
        '@type': 'HomeAndConstructionBusiness',
        'name': 'Pathfinder Driveways & Construction',
        'url': site_url,
        'image': site_url + 'assets/img/og-image.jpg',
        'telephone': '+263242788113',
        'email': ENQUIRY_EMAIL,
        'foundingDate': '1998',
        'address': {
            '@type': 'PostalAddress',
            'streetAddress': 'No. 5 Partner House, Eastlea Shops',
            'addressLocality': 'Harare',
            'addressCountry': 'ZW',
        },
        'sameAs': [
            'https://www.facebook.com/pathdrive',
            'https://www.instagram.com/pathfinderdrivewayscon/',
            'https://www.linkedin.com/company/80231533/',
        ],
    }


def read(*parts):
    with open(os.path.join(HERE, *parts), encoding='utf-8') as f:
        return f.read()


def file_version(rel):
    with open(os.path.join(SITE, rel), 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()[:8]


_widths = {}


def image_widths(name):
    if name not in _widths:
        found = sorted(int(m.group(1)) for f in os.listdir(IMG_DIR)
                       if (m := re.fullmatch(re.escape(name) + r'-(\d+)\.webp', f)))
        if not found:
            sys.exit(f'No images found for "{name}" — run src/images.py first.')
        largest = Image.open(os.path.join(IMG_DIR, f'{name}-{found[-1]}.webp'))
        _widths[name] = (found, largest.size)
    return _widths[name]


def image_data(name, root):
    widths, (w, h) = image_widths(name)
    srcset = ', '.join(f'{root}assets/img/{name}-{x}.webp {x}w' for x in widths)
    fallback = next((x for x in widths if x >= 640), widths[-1])
    return {
        'src': f'{root}assets/img/{name}-{fallback}.webp',
        'large': f'{root}assets/img/{name}-{widths[-1]}.webp',
        'thumb': f'{root}assets/img/{name}-{widths[0]}.webp',
        'srcset': srcset, 'w': w, 'h': h,
    }


def render_img(attrs, root):
    d = image_data(attrs['name'], root)
    sizes = SIZES.get(attrs.get('sizes', 'full'), attrs.get('sizes', '100vw'))
    eager = 'eager' in attrs
    parts = [
        f'src="{d["src"]}"', f'srcset="{d["srcset"]}"', f'sizes="{sizes}"',
        f'width="{d["w"]}"', f'height="{d["h"]}"', f'alt="{html.escape(attrs.get("alt", ""), quote=True)}"',
        'loading="eager" fetchpriority="high"' if eager else 'loading="lazy"', 'decoding="async"',
    ]
    if attrs.get('class'):
        parts.insert(0, f'class="{attrs["class"]}"')
    return '<img ' + ' '.join(parts) + '>'


def expand_images(text, root):
    def repl(m):
        body = m.group(1)
        attrs = dict(re.findall(r'(\w+)="([^"]*)"', body))
        for flag in re.findall(r'(?:^|\s)(eager)(?=\s|$)', re.sub(r'"[^"]*"', '""', body)):
            attrs[flag] = True
        return render_img(attrs, root)
    return re.sub(r'\{\{img ([^}]*)\}\}', repl, text)


def render_projects(root):
    projects = json.loads(read('data', 'projects.json'))
    out = []
    for p in projects:
        first = p['images'][0]
        labels = ' · '.join(CATEGORY_LABELS[c] for c in p['categories'])
        dialog = {
            'title': p['title'], 'service': p['service'], 'location': p['location'],
            'tag': labels, 'description': p['description'], 'category': p['categories'][0],
            'images': [dict(image_data(i['name'], root), alt=i['alt']) for i in p['images']],
        }
        location = (f'\n                  <li><svg class="icon" aria-hidden="true"><use href="#i-pin"/></svg>'
                    f'{html.escape(p["location"])}</li>') if p['location'] else ''
        out.append(f'''          <li data-categories="{' '.join(p['categories'])}">
            <article class="card card--project" id="{p['id']}" data-project="{html.escape(json.dumps(dialog), quote=True)}">
              <div class="card__media">{{{{img name="{first['name']}" alt="{html.escape(first['alt'], quote=True)}" sizes="card3"}}}}</div>
              <div class="card__body">
                <p class="tag">{labels}</p>
                <h3>{html.escape(p['title'])}</h3>
                <ul class="card__meta">
                  <li class="card__service">{html.escape(p['service'][0].upper() + p['service'][1:])}</li>{location}
                </ul>
                <p>{html.escape(p['description'])}</p>
                <button class="text-link" type="button" data-open-project aria-haspopup="dialog">View Project <svg class="icon" aria-hidden="true"><use href="#i-arrow"/></svg><span class="visually-hidden">: {html.escape(p['title'])}</span></button>
              </div>
            </article>
          </li>''')
    return '\n'.join(out)


def minify_css(css):
    """Conservative minifier: drops comments and layout whitespace, never touches calc() operators
    or the space before ':' (which matters in selectors like `.on-dark :focus-visible`)."""
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    css = re.sub(r'\s+', ' ', css)
    css = re.sub(r'\s*([{};,])\s*', r'\1', css)
    css = re.sub(r':\s+', ':', css)
    return css.replace(';}', '}').strip()


def inline_css(font_base):
    with open(os.path.join(SITE, 'assets', 'css', 'tokens.css'), encoding='utf-8') as f:
        tokens = f.read()
    with open(os.path.join(SITE, 'assets', 'css', 'site.css'), encoding='utf-8') as f:
        site = f.read()
    return minify_css(tokens.replace('url("../fonts/', f'url("{font_base}') + site)


def clean_urls(page):
    """Link to /about/ rather than /about/index.html (production build only)."""
    # Works for relative links (about/index.html, ../index.html) and any base path (/pathfinder/about/index.html).
    return re.sub(r'href="([^"#?:]*?)index\.html([?#][^"]*)?"', lambda m: f'href="{m.group(1) or "./"}{m.group(2) or ""}"', page)


def build(local=False, pages=False, base='/', site_url=SITE_URL, noindex=False):
    """local: double-click preview. pages: GitHub Pages (no PHP, no .htaccess). base: URL path the site lives under."""
    layout = read('layout.html')
    partials = {os.path.splitext(f)[0]: read('partials', f) for f in os.listdir(os.path.join(HERE, 'partials'))}
    versions = {'v_js': file_version('assets/js/site.js')}
    prod_css = inline_css(base + 'assets/fonts/')
    sitemap = []
    for fname in sorted(os.listdir(os.path.join(HERE, 'pages'))):
        raw = read('pages', fname)
        m = re.match(r'\s*<!--(.*?)-->\s*\n', raw, re.S)
        meta, body = json.loads(m.group(1)), raw[m.end():]
        path = meta['path']
        root = base if meta.get('root') == '/' else '../' * path.count('/')
        clean = '' if path == 'index.html' else path.removesuffix('index.html')
        canonical = site_url + clean

        head = []
        if meta.get('preload'):
            d = image_data(meta['preload'], root)
            head.append(f'  <link rel="preload" as="image" href="{d["src"]}" imagesrcset="{d["srcset"]}" '
                        f'imagesizes="100vw" fetchpriority="high">')
        if meta.get('schema'):
            head.append('  <script type="application/ld+json">' + json.dumps(schema(site_url), ensure_ascii=False) + '</script>')
        if meta.get('noindex') or noindex:
            head.append('  <meta name="robots" content="noindex">')

        page = layout.replace('{{content}}', body.rstrip('\n'))
        for _ in range(3):
            page = re.sub(r'\{\{> ([\w-]+)\}\}', lambda mm: partials[mm.group(1)].rstrip('\n'), page)
        if '{{projects}}' in page:
            page = page.replace('{{projects}}', render_projects(root))
        page = expand_images(page, root)

        values = dict(versions, title=html.escape(meta['title']), description=html.escape(meta['description'], quote=True),
                      canonical=canonical, site_url=site_url, root=root, head_extra='\n'.join(head),
                      canonical_tag='' if meta.get('noindex') else f'  <link rel="canonical" href="{canonical}">\n',
                      inline_css=inline_css(f'{root}assets/fonts/') if local else prod_css,
                      quote_href='#enquiry' if meta['nav'] == 'home' else f'{root}contact/index.html#enquiry',
                      wa_link=f'https://wa.me/{WHATSAPP_NUMBER}?text={quote(WHATSAPP_TEXT)}',
                      wa_display=WHATSAPP_DISPLAY.replace(' ', '&nbsp;'),
                      wa_topic=html.escape(meta.get('wa_topic', ''), quote=True),
                      # The form sends through enquiry.php on the cPanel host. GitHub Pages can't run PHP,
                      # so there it hands the enquiry to the visitor's email app instead.
                      form_action=f'mailto:{ENQUIRY_EMAIL}' if pages else f'{root}enquiry.php',
                      form_endpoint='' if pages else f'{root}enquiry.php',
                      form_enctype=' enctype="text/plain"' if pages else '')
        page = re.sub(r'\{\{current:(\w+)\}\}', lambda mm: ' aria-current="page"' if mm.group(1) == meta['nav'] else '', page)
        page = re.sub(r'\{\{(\w+)\}\}', lambda mm: values[mm.group(1)], page)
        if '{{' in page:
            sys.exit(f'{fname}: unexpanded placeholder near: ' + page[page.index('{{'):][:80])
        if not local:
            page = clean_urls(page)

        out = os.path.join(SITE, path)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, 'w', encoding='utf-8', newline='\n') as f:
            f.write(page)
        if not (meta.get('noindex') or noindex):
            sitemap.append(canonical)
        print(f'built {path}')

    with open(os.path.join(SITE, 'sitemap.xml'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        f.writelines(f'  <url><loc>{u}</loc></url>\n' for u in sitemap)
        f.write('</urlset>\n')

    if noindex:
        with open(os.path.join(SITE, 'robots.txt'), 'w', encoding='utf-8', newline='\n') as f:
            f.write('User-agent: *\nDisallow: /\n')
    if local:
        print('\nLOCAL build: links use index.html so the site opens by double-clicking. Run a normal build before uploading.')
        return
    if pages:
        print('\nGITHUB PAGES build: the form uses the visitor\'s email app; .htaccess is not used there.')
        return
    # style-src allows inline styles (the CSS is inlined in each page) rather than pinning a hash, so a page and
    # .htaccess can never drift out of sync and leave the live site unstyled. Scripts stay locked to 'self'.
    csp = ("default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
           "font-src 'self'; connect-src 'self'; form-action 'self' mailto:; frame-ancestors 'self'; base-uri 'self'; "
           "object-src 'none'; upgrade-insecure-requests")
    with open(os.path.join(SITE, '.htaccess'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(read('htaccess.txt').replace('{{csp}}', csp))
    print(f'wrote .htaccess (inline CSS {len(prod_css):,} bytes)')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--local', action='store_true', help='preview build that opens by double-clicking index.html')
    ap.add_argument('--pages', action='store_true', help='GitHub Pages build (no PHP form, no .htaccess)')
    ap.add_argument('--base', default='/', help='URL path the site is served from, e.g. /pathfinder/ (default /)')
    ap.add_argument('--site-url', default=SITE_URL, help='full address of the site, for canonical and sharing links')
    ap.add_argument('--noindex', action='store_true', help='ask search engines not to index this copy')
    ap.add_argument('--site', help='build into this folder (it must already contain assets/) instead of site/')
    args = ap.parse_args()
    if args.site:
        SITE = os.path.abspath(args.site)
        IMG_DIR = os.path.join(SITE, 'assets', 'img')

    def with_slash(v):
        return v if v.endswith('/') else v + '/'
    if not args.base.startswith('/'):
        # Git Bash on Windows rewrites "/pathfinder/" into a Windows path; run with MSYS_NO_PATHCONV=1 there.
        sys.exit(f'--base must be a URL path starting with "/", got {args.base!r}')
    build(local=args.local, pages=args.pages, base=with_slash(args.base), site_url=with_slash(args.site_url), noindex=args.noindex)
