#!/usr/bin/env python3
"""Import the primer from the Obsidian vault note into this site.

Usage: python3 tools/import_from_vault.py PATH/TO/security-primer.md PATH/TO/Imgs/security-primer

Splits the single note into one file per chapter (one per `## ` heading), converts
Obsidian links to standard Markdown links, and copies the figures that are used.
Standard Markdown links work in both Obsidian and Hugo, so after the switchover
this repository is the only copy and this script is no longer needed.
"""
import html
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
FIGURES = ROOT / "assets" / "figures"
IMAGES = ROOT / "assets" / "img"

# Chapters after these headings are shown as appendices in the navigation.
APPENDIX_FROM = "Reference"

HOME_INTRO = """\
# {title}

This primer explains how a Linux computer protects its disk and its boot software, and why each protection exists. The example computer is an NVIDIA Jetson Orin, but most of the ideas apply to any Linux computer.

It tells one story. Sam builds robots, and each chapter starts with an attack on one of them. Sam then invents the protection that stops it, step by step, before the chapter reveals the standard name of what Sam has built and shows how the Jetson does it. Each chapter ends with what is still missing, which is where the next chapter starts.

Concepts are explained in boxes the first time they appear, and small runnable examples show each step. The [glossary](12-glossary.md) collects every term.
"""


def slugify(text):
    text = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[\s_]+", "-", text).strip("-")


def frag(heading):
    """Obsidian's form of a heading in a Markdown link: spaces as %20, colons dropped."""
    return quote(heading.replace(":", ""), safe="()'")


def svg_title(path):
    """The figure's heading text (class "h"), used as alt text."""
    m = re.search(r'<text class="h"[^>]*>(.*?)</text>', path.read_text())
    if not m:
        return path.stem.replace("-", " ")
    return html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).replace("[", "(").replace("]", ")")


def main(note, imgdir):
    lines = note.read_text().splitlines()
    title = lines[0].strip().strip("`").lstrip("# ").strip()

    # Split into chapters at each `## ` heading (outside code fences).
    chapters, cur, fence = [], None, False
    for ln in lines[1:]:
        if re.match(r"^\s*(> )*```", ln):
            fence = not fence
        if not fence and ln.startswith("## "):
            cur = {"title": ln[3:].strip(), "lines": []}
            chapters.append(cur)
        elif cur is not None:
            cur["lines"].append(ln)

    appendix = False
    for i, ch in enumerate(chapters, 1):
        appendix = appendix or ch["title"] == APPENDIX_FROM
        ch["appendix"] = appendix
        ch["slug"] = slugify(ch["title"])
        ch["file"] = f"{i:02d}-{ch['slug']}.md"

    # Where every heading lives: chapter titles and their subheadings.
    where = {}
    for ch in chapters:
        where[ch["title"]] = (ch, None)
        fence = False
        for ln in ch["lines"]:
            if re.match(r"^\s*(> )*```", ln):
                fence = not fence
            m = None if fence else re.match(r"^(#{3,6}) (.+)$", ln)
            if m:
                where.setdefault(m.group(2).strip(), (ch, m.group(2).strip()))

    used = set()

    def convert(text, here):
        def link(m):
            target, alias = m.group(1), m.group(2)
            if not target.startswith("#"):
                raise SystemExit(f"unexpected link [[{target}]] in {here['title']}")
            heading = target[1:].strip()
            if heading not in where:
                raise SystemExit(f"broken link [[{target}]] in {here['title']}")
            ch, sub = where[heading]
            label = alias or heading
            if ch is here:
                return f"[{label}](#{frag(sub or ch['title'])})"
            return f"[{label}]({ch['file']}" + (f"#{frag(sub)}" if sub else "") + ")"

        def embed(m):
            name = m.group(1)
            used.add(name)
            if name.endswith(".svg"):
                return f"![{svg_title(imgdir / name)}](../assets/figures/{name})"
            return f"![](../assets/img/{name})"

        text = re.sub(r"!\[\[([^\]|]+)\]\]", embed, text)
        return re.sub(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]", link, text)

    CONTENT.mkdir(exist_ok=True)
    for old in CONTENT.glob("*.md"):
        old.unlink()
    for ch in chapters:
        body, fence = [], False
        for ln in ch["lines"]:
            if re.match(r"^\s*(> )*```", ln):
                fence = not fence
            if not fence and re.match(r"^#{3,6} ", ln):
                ln = ln[1:]  # the chapter title is now the page's h1, so subheadings move up one level
            body.append(ln)
        text = convert("\n".join(body).strip("\n"), ch)
        front = f"---\nslug: {ch['slug']}\n" + ("appendix: true\n" if ch["appendix"] else "") + "---\n"
        (CONTENT / ch["file"]).write_text(f"{front}# {ch['title']}\n\n{text}\n")

    (CONTENT / "_index.md").write_text(HOME_INTRO.format(title=title))

    for d in (FIGURES, IMAGES):
        d.mkdir(parents=True, exist_ok=True)
    for name in sorted(used):
        shutil.copy2(imgdir / name, (FIGURES if name.endswith(".svg") else IMAGES) / name)

    print(f"{len(chapters)} chapters, {len(used)} figures and images")
    for ch in chapters:
        print(f"  {ch['file']}" + ("  (appendix)" if ch["appendix"] else ""))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(Path(sys.argv[1]), Path(sys.argv[2]))
