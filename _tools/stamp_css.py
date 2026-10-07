"""stamp_css.py -- put a content fingerprint on the stylesheet link: style.css -> style.css?v=1a2b3c4d.

Where it sits: run after every edit to style.css, before committing (check_site.mjs fails if you forget).
Input:  style.css (its bytes), index.html and 404.html (their <link rel="stylesheet"> lines).
Output: both HTML files rewritten in place with the new ?v= value; prints old -> new.
Why: browsers keep style.css for 10 minutes (GitHub Pages sends max-age=600). A new page with an old
cached stylesheet breaks the layout (durations overlapping titles, 7 Oct 2026). A new ?v= is a new URL,
so the browser must download the matching stylesheet.
Run: python3 _tools/stamp_css.py
"""
import hashlib                                                             # [L] hashlib/pathlib/re: stdlib only, no install
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent                       # [L] repo root = parent of _tools/, so it works from any folder
PAGES = ["index.html", "404.html"]                                         # [L] every page that loads style.css
LINK = re.compile(r'(href="/?style\.css)(\?v=[0-9a-f]*)?(")')              # [L] matches href="style.css", "/style.css" and an existing ?v=..., nothing else


def css_version(css_path=ROOT / "style.css", n=8):
    """Return the first n hex digits of the SHA-256 of the stylesheet's bytes.

    css_path: pathlib.Path to style.css. n: int, digits kept; 8 hex = 32 bits, so two different
    versions of this file colliding is about 1 in 4 billion -- plenty for one site.
    Method: content hash, not a date or counter: it changes exactly when the CSS changes, and
    the checker can recompute it to prove the stamp is current.
    Alternatives: a date (?v=2026-10-07; two edits on one day collide), a counter (must remember to bump),
    or renaming the file (style.1a2b.css; old names pile up without a build tool).
    """
    return hashlib.sha256(css_path.read_bytes()).hexdigest()[:n]           # [L] same bytes -> same stamp; one changed character -> a new stamp


def main():
    """Rewrite the stylesheet link in each page to carry the current fingerprint."""
    v = css_version()
    updates = []                                                           # [L] check every page first, write only if all pass: never a half-stamped site
    for name in PAGES:
        html = (ROOT / name).read_text(encoding="utf-8")
        new, count = LINK.subn(lambda m: f"{m.group(1)}?v={v}{m.group(3)}", html)  # [L] lambda, not a "\1" template: no backslash surprises (see LEARNED.md, re.sub)
        if count != 1:                                                     # [L] exactly one stylesheet link per page; anything else means the HTML changed shape
            raise SystemExit(f"{name}: expected 1 stylesheet link, found {count}; nothing written")
        updates.append((name, new, LINK.search(html).group(2) or "(none)"))
    for name, new, old in updates:
        (ROOT / name).write_text(new, encoding="utf-8")
        print(f"{name}: style.css {old} -> ?v={v}")


if __name__ == "__main__":
    main()
