# Linux security primer

How a Linux computer protects its disk and its boot software, told as a story: each chapter starts with an attack, and Hari invents the protection that stops it. The ideas apply to any Linux computer; an NVIDIA Jetson Orin NX serves as the real-world running example.

**Read it:** the chapters are plain Markdown in [`content/`](content/), readable on GitHub or in any editor. The website is built from the same files.

## Writing

The repository is also an Obsidian vault: open this folder in Obsidian and edit the files in `content/`.

- Links are standard Markdown, which both Obsidian and the site understand: `[text](04-only-signed-software-may-run.md#Heading%20text)`. The shared Obsidian settings in `.obsidian/app.json` make Obsidian create links in this form.
- Callouts use Obsidian's syntax: `> [!info] Title`, `> [!example]`, `> [!warning]`. A `+` or `-` after the type (`> [!example]+`) makes the box foldable, open or closed.
- Each file starts with a `slug` (the page's address) and its title as a `# ` heading. Chapters are ordered by their file names; `appendix: true` puts a page under "Appendix".
- Figures are SVG files in `assets/figures/`, linked as `![description](../assets/figures/name.svg)`. Photos go in `assets/img/`.
- Each chapter ends with a "Test your knowledge" quiz. A question is a folded callout: `> [!quiz]- Question?`, then a task list whose `[x]` item is the right answer, then the explanation. The site turns the options into clickable answers and keeps a score; Obsidian keeps the answer folded.
- To animate a figure, wrap each part of the SVG in `<g data-step="N" data-caption="…">` (N from 1 to at most 9). The site then shows ▶ Play and step buttons above the figure and the current step's caption below it. Parts outside any group are always visible, and Obsidian shows the complete figure.

## Building

The site needs only [Hugo](https://gohugo.io/) (a single program, version 0.169 or newer). No Node, no JavaScript packages, and no JavaScript on the pages.

```sh
hugo server        # preview at http://localhost:1313, reloads on every save
hugo               # build into public/
python3 tools/check_links.py public    # check every link and #heading target
```

Pushing to `main` publishes the site through GitHub Actions (`.github/workflows/pages.yml`). One-time setup: in the repository's Settings → Pages, set Source to "GitHub Actions".

## How it works

| Part | File |
|---|---|
| Page frame, chapter list, previous/next | `layouts/baseof.html`, `page.html`, `home.html`, `layouts/_partials/` |
| Callouts and quizzes | `layouts/_markup/render-blockquote.html` (styles at the end of `assets/css/main.css`) |
| Figures: each SVG is placed into the page as code; step controls and captions for animated figures | `layouts/_markup/render-image.html` |
| Step animations (no JavaScript: radio buttons, `:has()` and a CSS custom property) | `assets/css/figures.css` |
| Links to other pages and headings | `layouts/_markup/render-link.html` |
| Styles | `assets/css/main.css` (text and layout), `figures.css`, `syntax.css` (code colours) |

Some figures are generated (Python, no packages): `python3 tools/figures/gen_e2e.py assets/figures` and `python3 tools/figures/gen_whole.py assets/figures`.

`tools/import_from_vault.py` converted the original single Obsidian note into these chapter files. It is kept for reference only.

## Licence

Text and figures: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Templates, styles and tools: MIT. See [LICENSE](LICENSE).
