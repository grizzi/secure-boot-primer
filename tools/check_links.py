#!/usr/bin/env python3
"""Check the built site: every internal link must point at an existing page and heading.

Usage: python3 tools/check_links.py public [BASE_PATH]

BASE_PATH is the path the site is served under, for example /secure-boot-primer/
on GitHub Pages (default: /). Hugo already stops on links to missing pages; this
also checks the #heading part, which Hugo does not.
"""
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.links = set(), []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "a" and "href" in a:
            self.links.append(a["href"])


def main(root, base="/"):
    root = Path(root)
    pages = {}
    for f in root.rglob("*.html"):
        p = Page()
        p.feed(f.read_text())
        url = "/" + str(f.relative_to(root).parent).strip(".") + "/"
        pages[url.replace("//", "/")] = p

    errors = 0
    for url, page in sorted(pages.items()):
        for href in page.links:
            parts = urlsplit(href)
            if parts.scheme or parts.netloc or href.startswith("mailto:"):
                continue
            path = parts.path or url
            if path.startswith(base):
                path = "/" + path[len(base):]
            target = pages.get(path if path.endswith("/") else path + "/")
            if target is None:
                if not (root / path.lstrip("/")).exists():
                    print(f"{url}: missing page {href}")
                    errors += 1
                continue
            if parts.fragment and unquote(parts.fragment) not in target.ids:
                print(f"{url}: missing heading {href}")
                errors += 1
    print(f"{len(pages)} pages checked, {errors} broken links")
    return 1 if errors else 0


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        raise SystemExit(__doc__)
    sys.exit(main(*sys.argv[1:]))
