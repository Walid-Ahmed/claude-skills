"""Load a deck file and render it: card pages, PNGs with a fit check, PDFs, and a README index."""
import contextlib
import html as htmllib
import importlib.util
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
CSS = (HERE / "card.css").read_text()
FONTS = '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">'

# A4 landscape: 1200 x 849 CSS px, rendered at 2x, so 2400 x 1698 px PNGs (about 205 dpi on A4).
WIDTH, HEIGHT, SCALE = 1200, 849, 2

# Hides the answer but keeps the layout, so the question sits where it does on the full card.
HIDE_ANSWER = """
  .answer { position: relative; }
  .answer > *:not(.think), .foot > span:first-child { visibility: hidden; }
  .think { position: absolute; left: 0; right: 0; top: 42%; text-align: center; font-size: 30px; font-weight: 700;
           color: var(--indigo-dark); visibility: visible; }
  .think small { display: block; font-size: 17px; font-weight: 500; color: var(--muted); margin-top: 8px; }
"""

# How far the answer runs past the space above the footer, or off the right edge. Above 0 means text is cut off.
FIT_CHECK = """(() => {
    const answer = document.querySelector('.answer');
    const wide = answer.scrollWidth - answer.clientWidth;
    if (wide > 0) return wide;
    const last = answer.lastElementChild.getBoundingClientRect().bottom;
    const pad = parseFloat(getComputedStyle(answer).paddingBottom);
    return Math.ceil(last + pad - document.querySelector('.foot').getBoundingClientRect().top);
})()"""


def load_deck(path):
    """Import a deck file and return its DECK. The deck file can `from flashcards import ...`."""
    path = pathlib.Path(path).resolve()
    sys.path.insert(0, str(HERE.parent))
    spec = importlib.util.spec_from_file_location("deck_file", path)
    if spec is None or spec.loader is None:
        sys.exit(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "DECK"):
        sys.exit(f"{path} must define DECK = deck(...)")
    return module.DECK


def folder(t, topic):
    return f"{t:02d}-" + re.sub(r"[^a-z0-9]+", "-", topic.title.lower()).strip("-")


def file_name(i, card):
    return f"{i:02d}-{card.slug}.png"


def page(deck, t, i, hide_answer=False, hint="The answer comes next"):
    """The HTML for card i (1-based) of topic t (1-based)."""
    topic = deck.topics[t - 1]
    card = topic.cards[i - 1]
    main, dark = topic.colour
    theme = f":root {{ --indigo: {main}; --indigo-dark: {dark}; --band: #fff; --chip: #fff; --chip-ink: {dark}; }}"
    style = CSS + deck.extra_css + theme + (HIDE_ANSWER if hide_answer else "")
    think = f'<div class="think">Think of your answer<small>{hint}</small></div>' if hide_answer else ""
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{htmllib.escape(card.slug)}</title>{FONTS}'
            f"<style>{style}</style></head><body><div class=\"card\">"
            f'<div class="top"><span class="project">{deck.title.upper()} · {topic.title.upper()}</span>'
            f'<span class="num">CARD {i} OF {len(topic.cards)}</span></div>'
            f'<div class="question"><div class="label">Question</div><h1>{card.question}</h1></div>'
            f'<div class="answer">{think}<div class="label">Answer</div>{card.body}</div>'
            f'<div class="foot"><span>{card.footer}</span><span class="tag">'
            + (f'<span class="src">Source: {card.source}</span>' if card.source else "") + f'{card.tag}</span></div>'
            "</div></body></html>")


def plain(text):
    return htmllib.unescape(re.sub(r"<[^>]+>", "", text)).strip()


@contextlib.contextmanager
def browser():
    """Headless Chrome if installed, otherwise Playwright's own Chromium."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("Playwright is missing. Install it with: pip install playwright && playwright install chromium")
    with sync_playwright() as p:
        try:
            b = p.chromium.launch(channel="chrome", headless=True)
        except Exception:
            try:
                b = p.chromium.launch(headless=True)
            except Exception:
                sys.exit("No browser for Playwright. Install Google Chrome, or run: playwright install chromium")
        try:
            yield b
        finally:
            b.close()


def shoot(tab, html, path):
    tab.set_content(html, wait_until="networkidle")
    tab.evaluate("document.fonts.ready")
    tab.screenshot(path=str(path))


def render_cards(deck, out, only=None):
    """Render every card (or only the given topic numbers) and return the cards that do not fit."""
    out = pathlib.Path(out)
    problems = []
    with browser() as b:
        tab = b.new_page(viewport={"width": WIDTH, "height": HEIGHT}, device_scale_factor=SCALE)
        for t, topic in enumerate(deck.topics, start=1):
            if only and t not in only:
                continue
            target = out / folder(t, topic)
            target.mkdir(parents=True, exist_ok=True)
            for old in target.glob("*.png"):
                old.unlink()  # a renamed or removed card must not linger
            for i, card in enumerate(topic.cards, start=1):
                path = target / file_name(i, card)
                shoot(tab, page(deck, t, i), path)
                extra = tab.evaluate(FIT_CHECK)
                # CSS px on the 1200 x 849 card (the PNG is 2x).
                status = f"fits (spare {-extra}px)" if extra <= 0 else f"DOES NOT FIT: {extra}px too much"
                print(f"{path.relative_to(out)}  {status}")
                if extra > 0:
                    problems.append((str(path.relative_to(out)), extra))
    return problems


def write_pdfs(deck, out):
    """One A4 landscape PDF per topic, plus one with every card."""
    from PIL import Image
    out = pathlib.Path(out)
    (out / "print").mkdir(exist_ok=True)
    everything = []
    for t, topic in enumerate(deck.topics, start=1):
        pngs = [out / folder(t, topic) / file_name(i, c) for i, c in enumerate(topic.cards, start=1)]
        everything += pngs
        _pdf(pngs, out / "print" / f"{folder(t, topic)}.pdf", Image)
    _pdf(everything, out / "print" / "all-cards.pdf", Image)


def _pdf(pngs, path, Image):
    pages = [Image.open(p).convert("RGB") for p in pngs]
    pages[0].save(path, save_all=True, append_images=pages[1:], resolution=WIDTH * SCALE / (297 / 25.4))


def write_readme(deck, out):
    out = pathlib.Path(out)
    total = sum(len(t.cards) for t in deck.topics)
    lines = [f"# {deck.title} flashcards", "",
             f"{total} cards in {len(deck.topics)} topics. Read the question at the top, answer it in your head, then check the answer below it.",
             "", "Each topic folder holds its cards as A4 landscape PNGs, in reading order. `print/` has one PDF per topic, "
             "one card per page, and `all-cards.pdf` with every card.", ""]
    if deck.credit:
        lines += [deck.credit, ""]
    for t, topic in enumerate(deck.topics, start=1):
        f = folder(t, topic)
        sourced = any(c.source for c in topic.cards)  # a Source column only when the cards say where they come from
        lines += [f"## {t}. {topic.title}", "", f"Print: [`print/{f}.pdf`](print/{f}.pdf)", "",
                  "| Card | Question |" + (" Source |" if sourced else ""), "| --- | --- |" + (" --- |" if sourced else "")]
        lines += [f"| [{i}]({f}/{file_name(i, c)}) | {plain(c.question)} |" + (f" {c.source} |" if sourced else "")
                  for i, c in enumerate(topic.cards, start=1)]
        lines.append("")
    (out / "README.md").write_text("\n".join(lines))
