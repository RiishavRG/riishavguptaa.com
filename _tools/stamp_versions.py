"""stamp_versions.py -- put a content fingerprint on links to files that change: style.css and the CV PDF.
    style.css -> style.css?v=1a2b3c4d      Rishav_Gupta_CV.pdf -> Rishav_Gupta_CV.pdf?v=5e6f7a8b

Where it sits: run after every edit to style.css or every new CV, before committing (check_site.mjs fails if you forget).
Input:  the bytes of each file below; index.html and 404.html (their links to those files).
Output: both HTML files rewritten in place with the new ?v= values; prints old -> new.
Why: browsers keep files for 10 minutes (GitHub Pages sends max-age=600). A new page with an old cached stylesheet
broke the layout (7 Oct 2026); a cached old CV hid a newly published one (2 Nov 2026). A new ?v= is a new URL,
so the browser must download the current file. The file itself keeps its name, so outside links still work.
Run: python3 _tools/stamp_versions.py
"""
import hashlib                                                             # [L] hashlib/pathlib/re: stdlib only, no install
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent                       # [L] repo root = parent of _tools/, so it works from any folder
PAGES = ["index.html", "404.html"]                                         # [L] every page that links to these files
ASSETS = ["style.css", "Rishav_Gupta_CV.pdf"]                              # [L] files that change while keeping their name; add others here


def link_pattern(asset):
    """Regex for href="asset", href="/asset", or either with an existing ?v=... (and nothing else).

    asset: str, file name at the site root. Returns a compiled pattern with groups (prefix, old ?v=, closing quote).
    Method: re.escape, so the "." in a file name matches only a dot. Alternatives: an HTML parser (heavier, and it
    would re-serialise the file and change unrelated formatting)."""
    return re.compile(r'(href="/?' + re.escape(asset) + r')(\?v=[0-9a-f]*)?(")')  # [L] escape, not a raw name: "style.css" would otherwise also match "styleXcss"


def version(asset, n=8):
    """First n hex digits of the SHA-256 of the file's bytes (8 hex = 32 bits; a chance collision is ~1 in 4 billion).

    Method: content hash, not a date or counter: it changes exactly when the file changes, and the checker can
    recompute it. Alternatives: a date (two updates on one day collide) or a counter (must remember to bump)."""
    return hashlib.sha256((ROOT / asset).read_bytes()).hexdigest()[:n]   # [L] same bytes -> same stamp; one changed byte -> a new stamp


def main():
    """Check every page has exactly one link per asset, then write all stamps (never a half-stamped site)."""
    stamps = {a: version(a) for a in ASSETS}
    updates = []
    for name in PAGES:
        html = (ROOT / name).read_text(encoding="utf-8")
        log = []
        for asset, v in stamps.items():
            pat = link_pattern(asset)
            old = pat.search(html)
            html, count = pat.subn(lambda m: f"{m.group(1)}?v={v}{m.group(3)}", html)  # [L] lambda, not a "\1" template: no backslash surprises (see LEARNED.md, re.sub)
            if count != 1:                                                 # [L] exactly one link per asset per page; anything else means the HTML changed shape
                raise SystemExit(f"{name}: expected 1 link to {asset}, found {count}; nothing written")
            log.append(f"{asset} {old.group(2) or '(none)'} -> ?v={v}")
        updates.append((name, html, log))
    for name, html, log in updates:                                        # [L] write only after every page passed the check
        (ROOT / name).write_text(html, encoding="utf-8")
        print(f"{name}: " + "; ".join(log))


if __name__ == "__main__":
    main()
