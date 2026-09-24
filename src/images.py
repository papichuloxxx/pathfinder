"""Build the site's images from the recovered WordPress uploads and the recent-work photos.

Every photo is cropped to one of the site's fixed aspect ratios, given the same light
colour correction, and exported as WebP at a few widths (never upscaled).

    python src/images.py
"""
import os
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
UPLOADS = os.path.normpath(os.path.join(HERE, '..', '..', 'wpress_extracted', 'uploads'))
# Recent-work photos sent by the client (unzipped into ../../recent-work/<project>/NN.jpg). Like the
# WordPress backup, they stay out of the public repo. Sources starting 'recent-work/' are read from there.
PROJECT_ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
OUT = os.path.normpath(os.path.join(HERE, '..', 'site', 'assets', 'img'))

HERO, CARD, PROJECT = 16 / 9, 4 / 3, 3 / 2

# name, source (relative to uploads), aspect, widths, focus (x, y), optional pre-crop box
# The PATHFINDER-*.png sources are the company's social graphics; the pre-crop keeps only
# the photo band between the logo header and the contact-details footer.
BAND = (0, 240, 1080, 740)
IMAGES = [
    ('hero', '2021/03/20171024_105750-e1524129740150.jpg', HERO, [800, 1280, 1920, 2560], (0.5, 0.58), None),

    ('svc-paving', '2022/07/40276475_162264497984402_7170547196020916224_n.jpg', CARD, [480, 800, 1200], (0.5, 0.6), None),
    ('svc-tarmac', '2025/04/IMG-20250415-WA0125.jpg', CARD, [480, 800, 1008], (0.5, 0.5), None),
    ('svc-construction', '2021/03/20180105_131935-e1524129849930.jpg', CARD, [480, 800, 1200], (0.55, 0.5), None),
    ('svc-manufacturing', '2025/04/IMG-20250415-WA0062.jpg', CARD, [480, 800, 1080], (0.5, 0.5), None),

    ('about', '2021/03/DSC01074.jpg', CARD, [480, 800, 1200], (0.42, 0.5), None),
    ('mfg-yard', '2025/04/IMG-20250405-WA0026.jpg', CARD, [480, 800, 1020], (0.5, 0.5), None),

    # Recent work (September 2026 photos). Each project's best photo comes first.
    ('proj-presbyterian-1', 'recent-work/presbyterian/01.jpg', PROJECT, [480, 756], (0.5, 0.42), None),
    ('proj-presbyterian-2', 'recent-work/presbyterian-more/05.jpg', PROJECT, [480, 1000], (0.5, 0.5), None),
    ('proj-presbyterian-3', 'recent-work/presbyterian/06.jpg', PROJECT, [480, 756], (0.5, 0.55), None),
    ('proj-presbyterian-4', 'recent-work/presbyterian/03.jpg', PROJECT, [480, 756], (0.5, 0.5), None),
    ('proj-presbyterian-5', 'recent-work/presbyterian/11.jpg', PROJECT, [480, 756], (0.5, 0.5), None),
    ('proj-presbyterian-6', 'recent-work/presbyterian-more/02.jpg', PROJECT, [480, 1000], (0.5, 0.5), None),
    ('proj-presbyterian-7', 'recent-work/presbyterian/05.jpg', PROJECT, [480, 756], (0.5, 0.6), None),
    ('proj-greystone-1', 'recent-work/greystone-park/02.jpg', PROJECT, [480, 1008], (0.5, 0.5), None),
    ('proj-greystone-2', 'recent-work/greystone-park/03.jpg', PROJECT, [480, 1008], (0.5, 0.5), None),
    ('proj-greystone-3', 'recent-work/greystone-park/01.jpg', PROJECT, [480, 1008], (0.5, 0.5), None),
    ('proj-cabs-1', 'recent-work/cabs/02.jpg', PROJECT, [480, 1000], (0.5, 0.42), None),
    ('proj-cabs-2', 'recent-work/cabs/01.jpg', PROJECT, [480, 1000], (0.5, 0.42), None),
    ('proj-cabs-3', 'recent-work/cabs/03.jpg', PROJECT, [480, 1000], (0.5, 0.42), None),
    ('proj-kamfinsa-1', 'recent-work/kamfinsa/01.jpg', PROJECT, [480, 756], (0.5, 0.55), None),
    ('proj-kamfinsa-2', 'recent-work/kamfinsa/08.jpg', PROJECT, [480, 756], (0.5, 0.42), None),
    ('proj-kamfinsa-3', 'recent-work/kamfinsa/07.jpg', PROJECT, [480, 1008], (0.5, 0.5), None),
    ('proj-kamfinsa-4', 'recent-work/kamfinsa/04.jpg', PROJECT, [480, 1008], (0.5, 0.5), None),
    ('proj-kingsmead-1', 'recent-work/kingsmead-road/02.jpg', PROJECT, [480, 706], (0.55, 0.5), None),
    ('proj-kingsmead-2', 'recent-work/kingsmead-road/03.jpg', PROJECT, [480, 706], (0.5, 0.5), None),
    ('proj-coronation-1', 'recent-work/coronation/02.jpg', PROJECT, [480, 706], (0.5, 0.5), None),
    ('proj-coronation-2', 'recent-work/coronation/11.jpg', PROJECT, [480, 706], (0.5, 0.5), None),
    ('proj-coronation-3', 'recent-work/coronation/16.jpg', PROJECT, [480, 706], (0.5, 0.5), None),
    ('proj-coronation-4', 'recent-work/coronation/07.jpg', PROJECT, [480, 706], (0.5, 0.5), None),
    ('proj-coronation-5', 'recent-work/coronation/15.jpg', PROJECT, [480, 706], (0.5, 0.5), None),
    ('proj-good-hope-1', 'recent-work/good-hope/05.jpg', PROJECT, [480, 706], (0.4, 0.5), None),
    ('proj-good-hope-2', 'recent-work/good-hope/02.jpg', PROJECT, [480, 861], (0.5, 0.5), None),
    ('proj-good-hope-3', 'recent-work/good-hope/07.jpg', PROJECT, [480, 861], (0.5, 0.5), None),
    ('proj-good-hope-4', 'recent-work/good-hope/10.jpg', PROJECT, [480, 706], (0.5, 0.5), None),

    ('proj-winston-park', '2025/05/PATHFINDER-4.png', PROJECT, [480, 750], (0.5, 0.5), BAND),
    ('proj-adelaide-park', '2025/04/PATHFINDER.png', PROJECT, [480, 750], (0.5, 0.5), BAND),
    ('proj-kambuzuma', '2025/04/IMG-20250410-WA0002.jpg', PROJECT, [480, 735], (0.5, 0.6), None),
    ('proj-presbyterian-paving', '2025/06/PATHFINDER-5.png', PROJECT, [480, 750], (0.5, 0.5), BAND),
    ('proj-car-park', '2025/04/WhatsApp-Image-2025-03-07-at-08.53.04_6e685c88-Copy.jpg', PROJECT, [480, 1000], (0.5, 0.5), None),
    ('proj-car-park-2', '2025/04/WhatsApp-Image-2025-01-29-at-04.55.44-Copy.jpg', PROJECT, [480, 750], (0.5, 0.55), None),
    ('proj-tarmac-driveway', '2025/04/IMG-20250415-WA0137.jpg', PROJECT, [480, 1008], (0.5, 0.5), None),
    ('proj-tarmac-driveway-2', '2025/04/IMG-20250415-WA0125.jpg', PROJECT, [480, 1008], (0.5, 0.5), None),
    ('proj-courtyard', '2022/07/49104179_220527595491425_2772733334705405952_n.jpg', PROJECT, [480, 1200], (0.5, 0.6), None),
    ('proj-walkway', '2025/04/WhatsApp-Image-2025-03-14-at-14.23.03_a2139cf4.jpg', PROJECT, [480, 1080], (0.5, 0.5), None),
    ('proj-herringbone', '2025/04/WhatsApp-Image-2025-04-10-at-10.28.45_acbdf83c.jpg', PROJECT, [480, 780], (0.5, 0.45), None),
    ('proj-geometric', '2025/05/IMG-20250226-WA0012.jpg', PROJECT, [480, 712], (0.5, 0.55), None),
    ('proj-diagonal', '2025/05/WhatsApp-Image-2025-03-12-at-09.52.22_8adc8c32.jpg', PROJECT, [480, 720], (0.5, 0.5), None),
    ('proj-site-works', '2021/03/20180105_131935-e1524129849930.jpg', PROJECT, [480, 1200], (0.55, 0.5), None),

    ('prod-interlocking', '2025/04/IMG-20250405-WA0007.jpg', CARD, [480, 765], (0.5, 0.62), None),
    ('prod-holland', '2025/04/IMG-20250415-WA0004.jpg', CARD, [480, 765], (0.5, 0.45), None),
    ('prod-3d-diamond', 'recent-work/pavers/3d-diamond.jpg', CARD, [480, 750], (0.5, 0.6), None),
    ('prod-hexagonal', '2025/04/IMG-20250405-WA0017.jpg', CARD, [480, 765], (0.5, 0.62), None),
    ('prod-bone', 'recent-work/pavers/bone.jpg', CARD, [480, 810], (0.5, 0.5), None),
    ('prod-star', '2025/04/IMG-20250405-WA0039.jpg', CARD, [480, 765], (0.5, 0.55), None),
]


def crop_to(im, aspect, focus):
    w, h = im.size
    if w / h > aspect:
        nw = round(h * aspect)
        left = min(max(round(focus[0] * w - nw / 2), 0), w - nw)
        return im.crop((left, 0, left + nw, h))
    nh = round(w / aspect)
    top = min(max(round(focus[1] * h - nh / 2), 0), h - nh)
    return im.crop((0, top, w, top + nh))


def grade(im):
    """Light, consistent correction: clip 0.5% highlights/shadows, a touch more colour."""
    im = ImageOps.autocontrast(im, cutoff=0.5, preserve_tone=True)
    im = ImageEnhance.Color(im).enhance(1.08)
    return ImageEnhance.Contrast(im).enhance(1.03)


def main():
    os.makedirs(OUT, exist_ok=True)
    report = []
    managed = {name for name, *_ in IMAGES}
    for f in os.listdir(OUT):  # clear old sizes so build.py never lists stale widths in srcset
        base, _, rest = f.rpartition('-')
        if base in managed and rest.endswith('.webp') and rest[:-5].isdigit():
            os.remove(os.path.join(OUT, f))
    for name, src, aspect, widths, focus, box in IMAGES:
        path = os.path.join(PROJECT_ROOT, src) if src.startswith('recent-work/') else os.path.join(UPLOADS, src)
        im = ImageOps.exif_transpose(Image.open(path)).convert('RGB')
        if box:
            im = im.crop(box)
        im = grade(crop_to(im, aspect, focus))
        made = []
        for w in sorted(set(min(w, im.width) for w in widths)):
            out = im.resize((w, round(w / aspect)), Image.LANCZOS)
            if im.width / w >= 1.5:  # only restore crispness lost to a real downscale
                out = out.filter(ImageFilter.UnsharpMask(radius=1, percent=45, threshold=2))
            out.save(os.path.join(OUT, f'{name}-{w}.webp'), 'WEBP', quality=72, method=6)
            made.append(w)
        report.append(f'{name:28} {im.width}x{im.height} -> {made}')
        if name == 'hero':
            og = crop_to(im, 1200 / 630, (0.5, 0.58)).resize((1200, 630), Image.LANCZOS)
            og.save(os.path.join(OUT, 'og-image.jpg'), 'JPEG', quality=82, optimize=True, progressive=True)
    print('\n'.join(report))


if __name__ == '__main__':
    main()
