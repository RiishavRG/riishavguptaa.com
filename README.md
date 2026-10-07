# riishavguptaa.com

Personal academic website for Rishav Gupta, a Ph.D. student in Computer Science at the
University of Maryland, Baltimore County (UMBC), researching smartphone-based cardiovascular
health sensing. Plain HTML5 and CSS3 — no framework, no build step — hosted on GitHub Pages at
[riishavguptaa.com](https://riishavguptaa.com). Pushing to `main` redeploys in about a minute.

The design follows the CMSC 601 lecture "Self-Promotion: Web Pages" (10-second test, conventional
navigation, research identity statement, citable publications, accessibility, mobile-first testing).

## Files

| File | What it is |
|---|---|
| `index.html` | The whole site (one page, sections linked from the top menu) |
| `style.css` | All styling; colours and spacing are variables at the top |
| `404.html` | Page shown for any broken link |
| `Rishav_Gupta_CV.pdf` | The CV the "CV (PDF)" links serve — **keep this file name** so old links keep working |
| `images/` | Photos and research figures (`*-256.jpg`, `*-512.jpg`, `*-1000.jpg` are generated copies) |
| `favicon.svg`, `favicon-32.png`, `apple-touch-icon.png` | Browser-tab and home-screen icons |
| `images/og-card.png` | Preview image shown when the link is shared (LinkedIn, Slack, iMessage) |
| `sitemap.xml`, `robots.txt` | Help search engines find the site |
| `_tools/make_assets.py` | Regenerates the resized images, icons and preview card (not published: Jekyll skips `_` folders) |
| `_tools/check_site.mjs` | Automated pre-deploy test: widths and zoom, accessibility (axe), keyboard focus, links, preview tags |
| `_tools/site-check-reminders.ics` | Double-click to add the 15-minute check to your calendar (first Monday of Jan, May, Aug, Dec) |

## How to update

- **New paper:** in `index.html`, copy one `<li class="pub">` block in the Publications section, put
  it at the top (newest first), and change the title, authors, venue, links, abstract and BibTeX.
  Give it a new `id` (e.g. `pub-name`) and a new `data-copy`/`<pre id>` pair, and change the hidden
  name in both `<summary>` lines (`<span class="sr-only">: Short name, Venue Year</span>`) so screen
  readers can tell the Abstract and BibTeX buttons apart.
- **After a conference:** remove the `To appear` tag and add the DOI link (copy the MobiSys entry).
- **News:** add a `<li>` at the top of the News list; keep about 5 items, delete the oldest.
- **Press coverage:** add a `<li>` at the top of "In the media" (under News), with the headline as the link text.
- **CV:** replace `Rishav_Gupta_CV.pdf` with the new PDF, same file name.
- **New headshot:** replace `images/headshot.png`, then run `python3 _tools/make_assets.py`.
- **ORCID:** once you have an iD, uncomment the two ORCID lines in `index.html` (hero and Contact).
- **Always:** change "Last updated" in the footer and `<lastmod>` in `sitemap.xml`.

## 15-minute check, 2–4 times a year (January, May, August, December)

Calendar reminder: open `_tools/site-check-reminders.ics` once to import it.

- [ ] Nothing stale: no "N-th year" claims, News has something from the last ~6 months, footer date is current
- [ ] The CV PDF and the site agree (publications, positions, dates)
- [ ] Email and every profile link still work; no dead demo or project links
- [ ] "To appear" papers that have now appeared get their DOI link
- [ ] Contact details are current

## Test before deploying

- [ ] Search your name in a private/incognito window
- [ ] Open the site on your phone, and zoom to 200%
- [ ] Tab through every link and button with the keyboard — the focus ring must always be visible
- [ ] Run an accessibility checker: [WAVE](https://wave.webaim.org/) on https://riishavguptaa.com
- [ ] Click every important link
- [ ] Check the page title, tab icon, and link preview (paste the URL into a LinkedIn or Slack message)
- [ ] Ask someone to explain what you work on after 10 seconds on the page
