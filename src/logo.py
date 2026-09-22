"""Make the website version of the main logo from src/source/Mainlogo.jpeg (supplied orange-on-black) in the site's colours.

    python src/logo.py

The website keeps the approved proposal palette (navy and gold), so the logo is adapted to it:
  - the logo's orange (rule, diamond, road roller) becomes the site gold #C9A03C, keeping all its shading;
  - the black background becomes the header/footer navy #10152A, so the logo sits on it with no edge;
  - the navy company name (invisible on a dark background) becomes white.
Grey and black parts of the roller (drum, tyres) are kept, just warmed towards the navy.
The original file is not changed.

Output: site/assets/logo-{128,192}.webp (2x/3x for a 64-72px-tall logo) and logo-192.png, plus favicons made from
the logo's road roller: site/favicon.ico and site/assets/favicon-{16,32}.png, icon-192.png, apple-touch-icon.png.
"""
import colorsys
import os

from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'source', 'Mainlogo.jpeg')  # the logo exactly as supplied
OUT = os.path.normpath(os.path.join(HERE, '..', 'site', 'assets'))

NAVY_BG = (0x10, 0x15, 0x2A)     # --color-dark-950: header and footer background
GOLD = (0xC9, 0xA0, 0x3C)        # --color-accent-500
ORANGE = (0xF4, 0x8C, 0x08)      # the logo's orange, measured from the file
TEXT_RIGHT = 800                 # the company name and rule sit left of this x; the roller is to the right
NAVY_BLUE = 56                   # blue value of the solid navy lettering in the source
NOISE = 8                        # JPEG noise in the black background

_gh, _gs, _gv = colorsys.rgb_to_hsv(*(c / 255 for c in GOLD))
_oh, _os, _ov = colorsys.rgb_to_hsv(*(c / 255 for c in ORANGE))


def to_gold(r, g, b):
    """Map an orange-family pixel to the same shade of the site gold (hue swapped, saturation and brightness scaled)."""
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    if not (15 / 360 <= h <= 50 / 360 and s > 0.3):
        return r, g, b
    nr, ng, nb = colorsys.hsv_to_rgb(_gh, min(1.0, s * _gs / _os), min(1.0, v * _gv / _ov))
    return round(nr * 255), round(ng * 255), round(nb * 255)


def recolour():
    """The whole logo in site colours, at the source's full size."""
    im = Image.open(SRC).convert('RGB')
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            in_text = x < TEXT_RIGHT and not (x > 700 and y > 178)  # the roller's drum starts below the end of "Construction"
            if in_text and b > r + 6 and b >= g:                     # navy lettering -> white (anti-aliasing kept)
                v = round(255 * max(0.0, min(1.0, (b - NOISE) / (NAVY_BLUE - NOISE))))
                r, g, b = v, v, v
            elif max(r, g, b) <= NOISE:
                r, g, b = 0, 0, 0
            else:
                r, g, b = to_gold(r, g, b)
            # Treat black as transparent and lay the artwork over the navy:
            # dark pixels take on the navy, bright ones keep their own colour.
            k = 1 - max(r, g, b) / 255
            px[x, y] = tuple(min(255, round(c + bgc * k)) for c, bgc in zip((r, g, b), NAVY_BG))
    return im


def trim(im, pad=0):
    """Crop away the plain navy margin, leaving `pad` px of navy around the artwork."""
    box = ImageChops.difference(im, Image.new('RGB', im.size, NAVY_BG)).convert('L').point(lambda v: 255 if v > 10 else 0).getbbox()
    return im.crop((max(box[0] - pad, 0), max(box[1] - pad, 0), min(box[2] + pad, im.width), min(box[3] + pad, im.height)))


def icon(roller, size, rounded):
    """The gold road roller from the logo, centred on the logo navy. Rounded corners for browser tabs."""
    art_w = round(size * (0.94 if size <= 32 else 0.8))  # small icons use more of the square so the roller stays readable
    art = roller.resize((art_w, round(roller.height * art_w / roller.width)), Image.LANCZOS)
    if size <= 48:
        art = art.filter(ImageFilter.UnsharpMask(radius=0.6, percent=80, threshold=1))
    canvas = Image.new('RGB', (size, size), NAVY_BG)
    canvas.paste(art, ((size - art.width) // 2, (size - art.height) // 2))
    if not rounded:
        return canvas
    mask = Image.new('L', (size * 4, size * 4), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size * 4 - 1, size * 4 - 1], radius=round(size * 4 * 0.2), fill=255)
    out = canvas.convert('RGBA')
    out.putalpha(mask.resize((size, size), Image.LANCZOS))
    return out


def build():
    full = recolour()
    logo = trim(full, pad=10)
    for height in (128, 192):
        out = logo.resize((round(logo.width * height / logo.height), height), Image.LANCZOS)
        out.save(os.path.join(OUT, f'logo-{height}.webp'), 'WEBP', quality=90, method=6)
        print(f'logo-{height}.webp', out.size, os.path.getsize(os.path.join(OUT, f'logo-{height}.webp')), 'bytes')
    out.save(os.path.join(OUT, 'logo-192.png'), optimize=True)

    # Favicons: the logo's road roller (its text is unreadable at tab size).
    art = full.copy()
    ImageDraw.Draw(art).rectangle([0, 0, 800, 178], fill=NAVY_BG)    # blank out the end of "Construction" above the drum
    ImageDraw.Draw(art).rectangle([0, 179, 740, art.height], fill=NAVY_BG)  # and the rule to the left of the roller
    roller = trim(art.crop((700, 0, art.width, art.height)))
    icon(roller, 32, True).save(os.path.join(OUT, 'favicon-32.png'), optimize=True)
    icon(roller, 192, True).save(os.path.join(OUT, 'icon-192.png'), optimize=True)
    icon(roller, 180, False).save(os.path.join(OUT, 'apple-touch-icon.png'), optimize=True)  # iOS rounds the corners itself
    master = icon(roller, 256, True)
    master.save(os.path.normpath(os.path.join(OUT, '..', 'favicon.ico')), sizes=[(16, 16), (32, 32), (48, 48)])
    small16 = icon(roller, 16, True)
    small16.save(os.path.join(OUT, 'favicon-16.png'), optimize=True)
    stale = os.path.join(OUT, 'favicon.svg')  # the old "P" monogram
    if os.path.exists(stale):
        os.remove(stale)
    print('favicons: favicon.ico (16/32/48), favicon-16.png, favicon-32.png, icon-192.png, apple-touch-icon.png')


if __name__ == '__main__':
    build()
