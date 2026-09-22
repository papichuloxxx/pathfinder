# Pathfinder Driveways & Construction: static site

A plain HTML/CSS/JS rebuild of pathdriveway.co.zw. It has no framework, no database and no plugins. Upload the files and it runs.

```text
static-site/                  (this is the GitHub repository)
├── .github/workflows/pages.yml   publishes to GitHub Pages
├── site/        ← the website. Upload the contents of this folder to cPanel.
└── src/         ← source used to rebuild site/ (not uploaded)
    ├── pages/           one file per page (index, about, services, projects, products, contact, 404)
    ├── partials/        shared blocks: header, footer, contact block + form, CTA band, product grid, icons
    ├── data/projects.json   every project on the Projects page
    ├── layout.html      the <head> and page shell
    ├── build.py         assembles site/ from the above
    ├── logo.py          makes the navy/gold web logo and favicons from source/Mainlogo.jpeg
    └── images.py        crops, colour-corrects and exports all photos from the WordPress backup (not in the repo)
```

## Preview

The normal build uses clean links like `/about/`, which need a web server. To preview it: `cd site`, run `python -m http.server 8000`, and open <http://localhost:8000>.

To preview by double-clicking `site/index.html` instead, build with `python src/build.py --local`. Run a normal build again before uploading.

## Pages

| Page | Contents |
| --- | --- |
| Home | Hero → trust bar → 4 services → 4 featured projects → Why Pathfinder → paver range → about → testimonials → CTA → contact + enquiry form |
| About | Story, vision and mission, values |
| Services | Paving, Tarmac, Building & Renovations, Paver Manufacturing. Each has a quote button and a link to the matching projects |
| Projects | 13 real projects, filterable by All / Paving / Tarmac / Construction / Renovations. "View Project" opens a larger view |
| Products | Supply only vs supply and fix, 6 paver types with *Enquire Now*, common bricks, FAQ |
| Contact | WhatsApp (main line), office phone, email, address and directions, enquiry form |
| Privacy | Short privacy notice, linked from the form and the footer |
| Thank you | Shown after sending the form in a browser without JavaScript (not indexed) |

The page URLs match the old site (`/about/`, `/products/`, `/contact/`), so existing Google results keep working. `site/.htaccess` redirects the other old WordPress URLs (FAQ, blog posts, cart and checkout) to the right new pages.

## Deploying to the current host (cPanel / LiteSpeed)

1. **Keep the WordPress backup.** Save `www-pathdriveway-co-zw-20260919-074451-1r14m4uwzd7n.wpress` somewhere safe. With the All-in-One WP Migration plugin it restores the old site exactly.
2. In cPanel File Manager, move the WordPress files out of `public_html` (or delete them once you're sure the backup is good).
3. Run a normal build (`python src/build.py`, without `--local`).
4. Upload **everything inside `site/`** into `public_html`, including the hidden `.htaccess` file. The build writes `.htaccess`, which holds the redirects, caching rules and security headers (Content-Security-Policy, HSTS and others).
5. Visit the site and **send a test enquiry**, then check it arrives in admin@pathdriveway.co.zw. Also check that an old URL such as `/faq-section/` redirects.
6. Run the live address through Google PageSpeed Insights (pagespeed.web.dev) to confirm the scores on real hosting.

## GitHub and GitHub Pages

The repository is <https://github.com/papichuloxxx/pathfinder> (public), and the site publishes to **<https://papichuloxxx.github.io/pathfinder/>**.

- **What's in the repo:** only this `static-site` folder (source, built site and README). The WordPress backup, its database and the reference-letter PDFs are **not** in the repo, because they contain personal details.
- **Publishing:** every push to `main` runs `.github/workflows/pages.yml`. It rebuilds the pages for the `/pathfinder/` address and deploys them. The first time, set **Settings → Pages → Source** to **GitHub Actions**.
- **How the GitHub Pages copy differs from the cPanel site:**
  - **The form:** GitHub Pages can't run PHP, so the form hands the enquiry to the visitor's email app, addressed to admin@pathdriveway.co.zw. WhatsApp and phone links work as normal.
  - **`.htaccess`:** GitHub ignores it, so the old-URL redirects and the extra security headers only apply on the cPanel host. GitHub Pages always serves over HTTPS.
  - **Search engines:** the github.io copy is marked "noindex", so it won't compete with the real domain in Google.
- **Using the real domain on GitHub Pages instead of cPanel:** add `www.pathdriveway.co.zw` under Settings → Pages → Custom domain and point the domain's DNS at GitHub. The workflow then builds for `/` and lets search engines index it. The form would still use the email-app handoff; for direct sending on GitHub Pages, connect a form service such as Formspree or Web3Forms and add its domain to the CSP.
- **Rebuilding locally:** `python src/build.py` makes the cPanel version in `site/`, which is what's committed. To preview the GitHub Pages version on Windows Git Bash, prefix the command with `MSYS_NO_PATHCONV=1` so `/pathfinder/` isn't rewritten into a Windows path.

## WhatsApp

A green **WhatsApp us** button floats at the bottom right of every page. The contact section, footer and mobile menu all use **078 973 4406** as the one main line.

The chat opens with a message already written, naming the service the visitor was looking at:

- **Services page:** whichever service section is on screen.
- **Products page:** pavers.
- **Contact form:** the service they chose.
- **Project pop-up:** that project's service, for example *"…a quote for 3D arrow paver installation (similar to your Winston Park project)"*.

To change the number, edit `WHATSAPP_NUMBER` and `WHATSAPP_DISPLAY` at the top of `src/build.py`, then rebuild. The other two mobile numbers still appear, as a smaller "Other lines" entry in the contact section.

## The enquiry form

The form follows the proposal:

- The heading is "Let's discuss your project".
- It asks for six things: full name, phone / WhatsApp number, email address, service required, project location and a brief description.
- The button reads **Request a Quote**.

**Enquiries go straight to admin@pathdriveway.co.zw.** `site/enquiry.php` is a small script that sends them through the host's own mail server, so no third-party form service is involved. The visitor sees "Thank you. Your enquiry has been sent." and the email's Reply-To is the visitor's address, so you can reply directly.

- **Requirements:** PHP 7.2 or newer, which the current cPanel host has (the old WordPress site ran on it). The host is still on PHP 7.2, which stopped receiving security updates in 2020, so switch it to PHP 8.x in cPanel under *MultiPHP Manager*. The script works on both.
- **If sending fails** (for example, the host's mail server is down), the visitor keeps what they typed and is offered a pre-filled email, WhatsApp, or a call. The enquiry isn't lost.
- **Spam protection:**
  - A hidden trap field catches bots.
  - There's a limit of 5 enquiries per visitor every 15 minutes and 40 per hour site-wide.
  - Messages over 3,000 characters are refused.
  - The recipient is fixed, and nothing a visitor types can add email headers or recipients.
  - The only thing stored is a hashed, 24-hour counter for the limits.
- **To change the recipient,** edit `ENQUIRY_TO` (and `ENQUIRY_FROM`, which must be an address on this domain) at the top of `site/enquiry.php`.
- **Testing without sending:** set the environment variable `PATHFINDER_MAIL_DRYRUN` to a file path, and the script writes each email to that file instead. For example: `PATHFINDER_MAIL_DRYRUN=mail.log php -S 127.0.0.1:8080 -t site`.

## Editing and rebuilding

You need Python 3 with Pillow installed (`pip install pillow`).

```sh
python src/images.py   # only when photos change: rebuilds site/assets/img/ from ../wpress_extracted/uploads/
python src/build.py    # always: rebuilds every page in site/ and writes site/.htaccess
```

The build inlines the CSS into every page, because that loads fastest on mobile data. After editing `tokens.css` or `site.css`, always rebuild. To change headers or redirects, edit `src/htaccess.txt`, not `site/.htaccess`.

- **Change text** in `src/pages/*.html`. Phone numbers, the address and the email appear in `src/partials/` (header, footer, contact block).
- **Add a project:**
  1. Add its photo to the `IMAGES` list in `src/images.py`, then run `images.py`.
  2. Add an entry to `src/data/projects.json` with the id, title, service, location, categories and description.
  3. Run `build.py`.
- **Testimonials** are in the testimonials section of `src/pages/index.html`. There are two, both word-for-word extracts from signed reference letters dated December 2024:
  - Kudakwashe Kainga, Zimbabwe Leaf Tobacco Company (Universal): tar resurfacing and construction.
  - Togara Mushonga, Finance Director, Aviation Ground Services: tar resurfacing.

  To add another, copy one `<li>` block and use the client's own words. Never publish a referee's phone number or signature.
- **Colours, fonts and spacing** are all defined in `site/assets/css/tokens.css`. Layout and components are in `site/assets/css/site.css`.

## Design system

- **Logo:** the header and footer use the main logo (`Mainlogo.jpeg`), adapted to the site's navy and gold. The logo's orange (rule, diamond and road roller) is recoloured to the site gold `#C9A03C`, keeping its shading. The black background becomes the header/footer navy `#10152A`, so it sits with no visible edge. The navy company name, which would be invisible on navy, is white. `python src/logo.py` makes this version (`site/assets/logo-128.webp`, `logo-192.webp`); the original file isn't modified.
- **Colours:** these come from the proposal deck. Navy `#1B2340` is the main colour, with a deeper navy `#10152A` for the header and footer, and gold `#C9A03C` is reserved for calls to action and accents. The background is off-white `#F6F4EE` and body text is charcoal `#2B2B2B`. Gold text on light backgrounds uses a darker `#7D6220` so it stays readable.
- **Type:** Manrope for headings, Inter for body text. Both are self-hosted in `site/assets/fonts/` (SIL Open Font License), so the site loads nothing from Google.
- **Buttons:** primary is gold with navy text; secondary is an outline (navy on light backgrounds, gold on dark). The header's **Get a Quote** button is visible at every screen size. On small phones it shortens to **Quote**.
- **Photos:** every photo is real Pathfinder work, cropped to fixed ratios (4:3 for services and products, 3:2 for projects, 16:9 for the hero) and given the same light colour correction. There's no stock photography.

## Removed from the old site

- The newsletter signup
- The 3-slide hero carousel
- The blog (2022 posts)
- Theme demo posts and the empty shop pages
- The "Add Your Curvy Text Here" placeholder
- The company-structure chart
- The shareholder and staff "promises"
- All iStock images
- The broken social links, which are now corrected

The FAQ moved to the Products page.

## Confirm with the client before launch

A checklist of facts and permissions to confirm with Pathfinder (project locations, claims from the old site, photo ownership, testimonial permission) is kept in `CLIENT-CHECKLIST.md`. It stays on your computer and is deliberately left out of the public GitHub repository.

## Quality audit (22 Sep 2026)

The audit ran against a local server that behaves like the live host: gzip compression and the same headers as `.htaccess`.

| Standard | Target | Result |
| --- | --- | --- |
| Lighthouse accessibility, best practices and SEO | 100 | **100** on all 6 pages, mobile and desktop |
| Lighthouse performance, desktop | ≥ 90 | **99–100** |
| Lighthouse performance, mobile (slow-4G simulation) | ≥ 90 | **84–97**: Home 84, Contact 89, the rest 94–97 (see note) |
| Largest Contentful Paint, mobile | ≤ 2.5 s | 1.5–2.5 s |
| Cumulative Layout Shift | ≤ 0.1 | **0.00** on every page |
| Homepage weight, mobile | ≤ 1.5 MB | **420 KB** (was 1.25 MB before the audit fixes) |
| WCAG 2.2 AA (axe-core) | 0 violations | **0**, covering 7 pages × 2 widths plus the open menu, project pop-up, form errors and empty filter |
| Keyboard | every stop visible and not hidden | Pass. With the menu open, the page behind it is unreachable |
| HTML validity (html-validate) | 0 errors | **0** |
| Security headers | CSP, HSTS, nosniff, referrer, permissions, frame | All set in `.htaccess`; scripts locked to the site itself |
| Old browsers | iOS 15+, Android Chrome 90+, Samsung Internet | Colours in hex, viewport-unit fallbacks, older-Safari-safe JS, `<dialog>` fallback |
| Honest content | no invented claims | Pass. Unconfirmed facts are listed above |

**Mobile performance note.** Lighthouse slows the CPU four times over on top of this laptop, which benchmarks low (1,040). Even the nearly empty 404 page spends ~220 ms on its first layout here. Scores on Google's own PageSpeed Insights servers are normally higher, so re-check once the site is live.

**Still open (needs the client):**

- **First real enquiry:** send one test enquiry after going live and confirm it arrives in admin@pathdriveway.co.zw. Check the spam folder too; mail sent from the site's own domain usually lands well.
- **Measurement:** there is no analytics. Adding Cloudflare Web Analytics (free, no cookies, and the domain already uses Cloudflare) would show enquiries, WhatsApp taps and calls. It needs `static.cloudflareinsights.com` added to the CSP.
- **Privacy notice approval:** the short notice is in place at `/privacy/`, but Pathfinder should approve its wording.
- **Better photography, and a third testimonial if one comes in:** see the list above.
