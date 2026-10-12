"""Render the project's existing methods note as a standalone readable web page.

Only the Markdown constructs used in docs/data-quality.md are supported.
All source text is escaped; source changes remain in that Markdown file.
"""
from html import escape
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def inline(text):
    text = escape(text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    return re.sub(r"\[([^]]+)\]\((https://[^\s)]+)\)", r'<a href="\2">\1</a>', text)


def render(markdown):
    blocks, contents = [], []
    for block in markdown.strip().split("\n\n"):
        lines = block.splitlines()
        if block.startswith("# "):
            continue
        if block.startswith("## "):
            title = block[3:]
            anchor = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
            contents.append(f'<a href="#{anchor}">{escape(title)}</a>')
            blocks.append(f'<h2 id="{anchor}">{escape(title)}</h2>')
        elif block.startswith("| "):
            rows = [[inline(cell.strip()) for cell in line.strip("|").split("|")] for line in lines]
            head = "".join(f'<th scope="col">{cell}</th>' for cell in rows[0])
            body = "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows[2:])
            blocks.append('<div class="methods-table" role="region" aria-label="Location matching table" tabindex="0"><table><caption>Review listing to historical CLUE location crosswalk</caption><thead><tr>' + head + "</tr></thead><tbody>" + body + "</tbody></table></div>")
        elif block.startswith("- "):
            blocks.append("<ul>" + "".join(f"<li>{inline(line[2:])}</li>" for line in lines) + "</ul>")
        else:
            blocks.append(f'<p>{inline(block)}</p>')
    return "\n".join(blocks), "\n".join(contents)


def main():
    body, contents = render((ROOT / "docs/data-quality.md").read_text(encoding="utf-8"))
    page = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Data methods · Beyond the Stars</title><meta name="description" content="Sources, cleaning, geography and limitations behind the Melbourne restaurant data story.">
<link rel="stylesheet" href="../styles.css"><link rel="stylesheet" href="methods.css"></head>
<body class="methods-page"><a class="skip" href="#main">Skip to the methods</a>
<header class="masthead"><a class="wordmark" href="../index.html#sources">← BACK TO THE STORY</a><span>BEYOND THE STARS / DATA METHODS</span></header>
<main id="main"><p class="eyebrow">BEHIND THE NUMBERS</p><h1>Data methods.</h1>
<p class="methods-intro">How the source records became the maps and charts. Review snapshot accessed 6 October 2026; a limited follow-up audit was completed on 11 October 2026.</p>
<p><a href="../data.html?dataset=reviews">Browse the data and download CSV tables →</a></p>
<nav class="methods-contents" aria-label="On this page">{contents}</nav>
<article>{body}</article>
<p class="methods-back"><a href="../index.html#sources">← Back to the story</a> · <a href="data-quality.md" download>Download the original methods note (Markdown)</a></p>
</main><footer><span>MELBOURNE / AT THE TABLE</span><a href="#main">Back to the top ↑</a></footer></body></html>
'''
    (ROOT / "docs/data-methods.html").write_text(page, encoding="utf-8")
    print("Built docs/data-methods.html from docs/data-quality.md")


if __name__ == "__main__":
    main()
