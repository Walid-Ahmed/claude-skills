"""Helpers for writing a flashcard deck file (deck.py) and the engine that renders it.

A deck file imports from here:

    from flashcards import deck, topic, card, code, example, pair, n, a, row, rows, url, msg

and defines DECK = deck(...). See SKILL.md and references/components.md.
"""
from __future__ import annotations

import html as _html
import re as _re
from dataclasses import dataclass, field

# Topic colours: (main, dark). Bold enough for headers and outlines, and they still read in greyscale.
PALETTE = [
    ("#1d4ed8", "#1e3a8a"),  # blue
    ("#0f766e", "#115e59"),  # teal
    ("#6d28d9", "#4c1d95"),  # violet
    ("#a21caf", "#701a75"),  # magenta
    ("#b45309", "#78350f"),  # amber
    ("#0e7490", "#164e63"),  # cyan
    ("#15803d", "#14532d"),  # green
    ("#4f46e5", "#3730a3"),  # indigo
]


@dataclass
class Card:
    slug: str       # file name part, such as "jwt-in-the-header"
    question: str   # shown in the question band; plain text or inline HTML
    body: str       # the answer: HTML using the components in references/components.md
    footer: str = ""  # one short line to remember, at the bottom left
    tag: str = ""     # one or two words, at the bottom right
    source: str = ""  # where the card comes from in the user's material, such as "Ch. 3, p. 42" or "slide 12"


@dataclass
class Topic:
    title: str
    cards: list
    colour: tuple | None = None  # (main, dark); taken from PALETTE when left out
    hook: str = ""        # a few words for thumbnails, such as "OAuth2 · JWT · Hashing"


@dataclass
class Deck:
    title: str            # the subject, such as "FastAPI"; shown in every card header
    topics: list
    credit: str = ""      # optional line for the README, such as where the examples come from
    slug: str = ""        # file name prefix for videos and thumbnails; from the title when left out
    extra_css: str = field(default="")  # rarely needed: extra styles for this deck
    max_cards: int = 0    # the most cards the user wants; 0 means no limit


def deck(title, topics, credit="", slug="", extra_css="", max_cards=0):
    for i, t in enumerate(topics):
        if t.colour is None:
            t.colour = PALETTE[i % len(PALETTE)]
    slug = slug or (_re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") + "-flashcards")
    return Deck(title, topics, credit, slug, extra_css, max_cards)


def topic(title, cards, colour=None, hook=""):
    return Topic(title, cards, colour, hook)


def card(slug, question, body, footer="", tag="", source=""):
    return Card(slug, question, body, footer, tag, source)


# ---------------------------------------------------------------- code
_TOKENS = {
    "python": _re.compile(
        r"""(?P<c>\#[^\n]*)|(?P<s>"[^"\n]*"|'[^'\n]*')"""
        r"""|\b(?P<k>class|async|await|def|return|raise|for|while|in|if|elif|else|not|from|import|and|or|is|None|True|False|with|as|try|except|finally|yield|lambda)\b"""
        r"""|\b(?P<f>[A-Za-z_]\w*)(?=\()"""),
    "bash": _re.compile(r"""(?P<c>\#[^\n]*)|(?P<s>"[^"\n]*"|'[^'\n]*')"""),
    "json": _re.compile(r"""(?P<s>"[^"\n]*")|\b(?P<k>true|false|null)\b"""),
    "js": _re.compile(
        r"""(?P<c>//[^\n]*)|(?P<s>"[^"\n]*"|'[^'\n]*'|`[^`]*`)"""
        r"""|\b(?P<k>const|let|var|function|return|if|else|for|while|await|async|new|import|from|export|class|null|true|false)\b"""
        r"""|\b(?P<f>[A-Za-z_$][\w$]*)(?=\()"""),
    "dockerfile": _re.compile(
        r"""(?P<c>\#[^\n]*)|(?P<s>"[^"\n]*"|'[^'\n]*')"""
        r"""|^(?P<k>(?i:FROM|RUN|CMD|COPY|ADD|WORKDIR|ENV|ARG|EXPOSE|ENTRYPOINT|VOLUME|USER|LABEL|HEALTHCHECK|SHELL))\b""", _re.M),
    "yaml": _re.compile(r"""(?P<c>\#[^\n]*)|(?P<s>"[^"\n]*"|'[^'\n]*')|^(?P<f>\s*-?\s*[\w.-]+)(?=:)""", _re.M),
    "toml": _re.compile(r"""(?P<c>\#[^\n]*)|(?P<s>"[^"\n]*"|'[^'\n]*')|^(?P<k>\[[^\]\n]+\])|^(?P<f>[\w.-]+)(?=\s*=)""", _re.M),
    "sql": _re.compile(r"""(?P<c>--[^\n]*)|(?P<s>'[^'\n]*')|\b(?P<k>(?i:select|from|where|insert|into|values|update|set|delete|create|table|join|on|group|by|order|limit|and|or|not|null|primary|key))\b"""),
}


def code(src, lang="python"):
    """Escape code and colour comments, strings, keywords, and calls.

    lang: python, bash, json, js, sql, dockerfile, yaml, toml, or text (no colours).
    """
    src = src.strip("\n")
    pattern = _TOKENS.get(lang)
    if not pattern:
        return _html.escape(src, quote=False)
    out, end = [], 0
    for m in pattern.finditer(src):
        out.append(_html.escape(src[end:m.start()], quote=False))
        out.append(f'<span class="{m.lastgroup}">{_html.escape(m.group(), quote=False)}</span>')
        end = m.end()
    out.append(_html.escape(src[end:], quote=False))
    return "".join(out)


def example(caption, src, lang="python"):
    """A labelled code box. Start the caption with "Example:" so readers know it is one case, not the rule."""
    return f'<div class="snippet"><div class="cap">{caption}</div><pre>{code(src, lang)}</pre></div>'


def pair(left, right):
    """Two boxes side by side, such as two example() calls."""
    return f'<div class="pair">{left}{right}</div>'


# ---------------------------------------------------------------- diagrams
def n(title, sub="", kind="", fail=""):
    """One diagram box. kind: '' | 'dash' (data or the client) | 'good' | 'bad'. fail: a red outcome line, or a list of them."""
    sub_html = f"<span>{sub}</span>" if sub else ""
    fails = [fail] if isinstance(fail, str) and fail else (fail or [])
    return f'<div class="dn {kind}"><b>{title}</b>{sub_html}' + "".join(f"<em>{f}</em>" for f in fails) + "</div>"


def a(label="", left=False, ghost=False):
    """An arrow between boxes, with an optional small label under it."""
    label_html = f"<small>{label}</small>" if label else ""
    return f'<div class="da{" ghost" if ghost else ""}">{"←" if left else "→"}{label_html}</div>'


def row(*parts):
    """A left-to-right flow: row(n(...), a(...), n(...), ...)."""
    return '<div class="dg">' + "".join(parts) + "</div>"


def rows(*labelled):
    """Labelled rows that line up in columns: rows(("Label", [n(...), a(...), n(...)]), ...)."""
    longest = max(len(parts) for _, parts in labelled)
    out = []
    for label, parts in labelled:
        padded = list(parts)
        while len(padded) < longest:
            padded += [a(ghost=True), n("", kind="ghost")]
        out.append(f'<div class="lbl">{label}</div>' + row(*padded[:longest]))
    return '<div class="dgl">' + "".join(out) + "</div>"


def url(*segments):
    """A URL or command split into labelled parts: url(("/books/", ""), ("1", "Path value"), ...)."""
    parts = []
    for text, label in segments:
        parts.append(f'<div class="seg{" hi" if label else ""}"><div class="t">{_html.escape(text)}</div>'
                     + (f"<small>{label}</small>" if label else "") + "</div>")
    return '<div class="url">' + "".join(parts) + "</div>"


def msg(*lines):
    """A message (HTTP request, email, packet) with each part labelled on the right: msg((text, label), ...)."""
    return '<div class="msg">' + "".join(
        f'<div class="l">{_html.escape(t)}</div><div class="r">{label}</div>' for t, label in lines) + "</div>"
