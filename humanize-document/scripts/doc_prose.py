"""Read a document's prose for the humanize-document skill. Never writes to the document.

Works with Word (.docx), Markdown (.md) and plain text (.txt).

Usage:
    python3 doc_prose.py <file> --list              # prose paragraphs: index, section, words, opening words
    python3 doc_prose.py <file> --codes "<prefix>"  # code-formatted pieces of one paragraph
    python3 doc_prose.py <file> --out prose.txt     # prose for the AI detector, blank line between paragraphs

Options:
    --skip-style PREFIX   (Word only, repeatable) also skip paragraphs whose style starts with PREFIX

Headings, titles, captions, tables of contents, code blocks and empty paragraphs are not prose.
In Word, code is any run whose character style contains "code" or whose font is monospaced.
In Markdown, code is `backticked` text and fenced blocks.
"""

import argparse
import re
import sys
from pathlib import Path

# Paragraph styles that are never scored prose. Anything else with text counts, including
# odd styles that pasting from a website or a humanizer can leave behind.
SKIP_PREFIXES = ("Heading", "Title", "Subtitle", "Caption", "TOC", "Table of Figures", "Figure")
MONOSPACE = (
    "consolas", "courier", "menlo", "monaco", "lucida console", "source code", "fira code",
    "fira mono", "jetbrains mono", "cascadia", "sf mono", "roboto mono", "ubuntu mono",
    "inconsolata", "dejavu sans mono", "liberation mono", "andale mono",
)


def style_name(item) -> str:
    return item.style.name if getattr(item, "style", None) is not None else ""


def run_font(run) -> str:
    """The run's font name, from the run itself or its character style."""
    if run.font.name:
        return run.font.name
    style = run.style
    while style is not None:
        if style.font is not None and style.font.name:
            return style.font.name
        style = style.base_style
    return ""


def is_code_run(run) -> bool:
    if "code" in style_name(run).lower():
        return True
    font = run_font(run).lower()
    return any(font.startswith(name) for name in MONOSPACE)


def is_code_paragraph(paragraph) -> bool:
    if "code" in style_name(paragraph).lower():
        return True
    runs = [r for r in paragraph.runs if r.text.strip()]
    return bool(runs) and all(is_code_run(r) for r in runs)


# ---------------------------------------------------------------- Word

class WordParagraph:
    def __init__(self, paragraph):
        self.paragraph = paragraph
        self.text = paragraph.text.strip()
        self.style = style_name(paragraph)

    def codes(self):
        return [r.text for r in self.paragraph.runs if r.text and is_code_run(r)]


def word_paragraphs(path, extra_skips: "list[str] | tuple[str, ...]" = ()):
    import docx  # python-docx

    skips: "tuple[str, ...]" = SKIP_PREFIXES + tuple(str(s) for s in extra_skips)
    section = "Start"
    for paragraph in docx.Document(str(path)).paragraphs:
        style = style_name(paragraph)
        text = paragraph.text.strip()
        if style.startswith(("Heading", "Title")):
            if text:
                section = text
            continue
        if not text or style.startswith(skips) or is_code_paragraph(paragraph):
            continue
        yield section, WordParagraph(paragraph)


# ---------------------------------------------------------------- Markdown and text

class TextParagraph:
    def __init__(self, text):
        self.text = text
        self.style = ""

    def codes(self):
        return re.findall(r"`([^`]+)`", self.text)


def text_paragraphs(path):
    markdown = path.suffix.lower() in (".md", ".markdown")
    section = "Start"
    in_fence = False
    block = []
    lines = path.read_text(encoding="utf-8").splitlines() + [""]

    def flush():
        text = " ".join(line.strip() for line in block).strip()
        block.clear()
        return text

    for line in lines:
        stripped = line.strip()
        if markdown and stripped.startswith(("```", "~~~")):
            if block:
                text = flush()
                if text:
                    yield section, TextParagraph(text)
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if markdown and re.match(r"#{1,6}\s", stripped):
            if block:
                text = flush()
                if text:
                    yield section, TextParagraph(text)
            section = stripped.lstrip("#").strip()
            continue
        if not stripped:
            text = flush()
            # In Markdown, skip tables, images, and list items (templated, often broken by humanizers).
            if text and not (markdown and re.match(r"(\||!\[|[-*+]\s|\d+[.)]\s|>?\s*<)", text)):
                yield section, TextParagraph(text)
            continue
        block.append(line)


# ---------------------------------------------------------------- main

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true")
    group.add_argument("--codes", metavar="PREFIX")
    group.add_argument("--out", metavar="TXT")
    parser.add_argument("--skip-style", action="append", default=[], metavar="PREFIX")
    args = parser.parse_args()

    path = Path(args.path)
    if path.suffix.lower() == ".docx":
        rows = list(word_paragraphs(path, args.skip_style))
    elif path.suffix.lower() in (".md", ".markdown", ".txt"):
        rows = list(text_paragraphs(path))
    else:
        sys.exit("Unsupported file type: use .docx, .md or .txt")

    if args.list:
        for index, (section, p) in enumerate(rows):
            words = len(p.text.split())
            flag = f"  [style: {p.style}]" if p.style and not p.style.startswith("Normal") else ""
            print(f"{index:3d} | {section[:34]:34} | {words:4d}w | {p.text[:60]}{flag}")
    elif args.codes:
        matches = [p for _, p in rows if p.text.startswith(args.codes)]
        if len(matches) != 1:
            sys.exit(f"{len(matches)} paragraphs start with {args.codes!r}; give a longer prefix")
        print(matches[0].codes())
    else:
        text = "\n\n".join(p.text for _, p in rows)
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"{sum(len(p.text.split()) for _, p in rows)} words in {len(rows)} paragraphs, "
              f"{len(text)} characters -> {args.out}")


if __name__ == "__main__":
    main()
