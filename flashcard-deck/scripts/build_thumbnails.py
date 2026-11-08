"""Make YouTube thumbnails for a deck's videos: 1280 x 720 JPEGs, far under YouTube's 2 MB limit.

    python build_thumbnails.py DECK.py --cards CARDS_DIR --out VIDEO_DIR/thumbnails

Makes one per video build_videos.py can make, named to match: one per topic, plus the three
all-topics versions. Thumbnails use bold colour and very large text, since YouTube shows them
small: a short headline, a yellow badge, and two real cards fanned on the right. Headlines shrink
until they fit. The bottom-right corner stays clear for YouTube's length label.
"""
import argparse
import base64
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from flashcards import engine  # noqa: E402

PAGE = """<!doctype html><html><head><meta charset="utf-8">{fonts}<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  html, body {{ width: 1280px; height: 720px; overflow: hidden; font-family: Inter, sans-serif; }}
  body {{ background: linear-gradient(135deg, {main} 0%, {dark} 100%); position: relative; }}
  .text {{ position: absolute; left: 64px; top: 70px; width: 660px; color: #fff; }}
  .kicker {{ font-size: 30px; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; opacity: .85; }}
  h1 {{ font-size: 112px; font-weight: 900; line-height: .98; letter-spacing: -.035em; margin-top: 18px; text-shadow: 0 4px 18px rgba(0,0,0,.25); }}
  .hook {{ font-size: 34px; font-weight: 700; margin-top: 26px; opacity: .92; }}
  .badge {{ position: absolute; left: 64px; bottom: 64px; background: #facc15; color: #1a1a2e; font-size: 40px; font-weight: 900;
            padding: 14px 30px; border-radius: 16px; box-shadow: 0 8px 24px rgba(0,0,0,.3); }}
  .card {{ position: absolute; width: 560px; border-radius: 14px; box-shadow: 0 18px 50px rgba(0,0,0,.45); }}
  .back {{ left: 735px; top: 70px; transform: rotate(7deg); }}
  .front {{ left: 690px; top: 250px; transform: rotate(-5deg); }}
  .mark {{ position: absolute; left: 1040px; top: 40px; width: 190px; height: 190px; border-radius: 50%; background: #facc15; color: #1a1a2e;
           font-size: 150px; font-weight: 900; line-height: 190px; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,.35); transform: rotate(10deg); }}
</style></head><body>
<img class="card back" src="{back}"><img class="card front" src="{front}">{mark}
<div class="text"><div class="kicker">{kicker}</div><h1>{title}</h1><div class="hook">{hook}</div></div>
<div class="badge">{badge}</div></body></html>"""

FIT = """(() => {
    const h1 = document.querySelector('h1'), text = document.querySelector('.text');
    const badgeTop = document.querySelector('.badge').getBoundingClientRect().top;
    let size = parseFloat(getComputedStyle(h1).fontSize);
    while (size > 48 && (h1.scrollWidth > h1.clientWidth || text.getBoundingClientRect().bottom > badgeTop - 24)) {
        size -= 2; h1.style.fontSize = size + 'px';
    }
    return size;
})()"""


def inline(path):
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()


def thumbnails(deck, cards_dir, mode="both"):
    total = sum(len(t.cards) for t in deck.topics)
    pngs = [(t, sorted((cards_dir / engine.folder(t, topic)).glob("*.png"))) for t, topic in enumerate(deck.topics, start=1)]
    first, last = pngs[0][1], pngs[-1][1]
    minutes = max(1, round((5 + 3 * len(deck.topics) + 15 * total) / 60))  # length of the cards-only video
    hook = f"From {deck.topics[0].title} to {deck.topics[-1].title}"
    main, dark = deck.topics[-1].colour
    full = dict(main=main, dark="#1e1b4b" if main == "#4f46e5" else dark, kicker=f"{deck.title} flashcards", hook=hook,
                back=inline(last[min(1, len(last) - 1)]), front=inline(first[0]), mark="")
    yield f"{deck.slug}-all-topics", {**full, "title": f"Test Your {deck.title} Knowledge", "badge": f"{total} Q&amp;A"}
    yield f"{deck.slug}-all-topics-questions", {**full, "title": f"Can You Answer These {total}?", "badge": "QUIZ · NO ANSWERS",
                                                 "mark": '<div class="mark">?</div>'}
    yield f"{deck.slug}-all-topics-cards", {**full, "title": f"{deck.title} in {minutes} Minute{'' if minutes == 1 else 's'}", "badge": f"{total} FLASHCARDS"}
    for t, topic in enumerate(deck.topics, start=1):
        files = pngs[t - 1][1]
        suffix = {"both": "", "questions": "-questions", "cards": "-cards"}[mode]  # match build_videos.py names
        yield f"{deck.slug}-{engine.folder(t, topic)}{suffix}", dict(
            main=topic.colour[0], dark=topic.colour[1], kicker=f"{deck.title} flashcards", title=topic.title,
            hook=topic.hook, badge=f"{len(topic.cards)} Q&amp;A", back=inline(files[min(1, len(files) - 1)]),
            front=inline(files[0]), mark="")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("deck")
    parser.add_argument("--cards", required=True, help="the folder build_deck.py wrote")
    parser.add_argument("--out", required=True, help="where the thumbnails go")
    parser.add_argument("--mode", choices=["both", "questions", "cards"], default="both",
                        help="the video style, so topic thumbnails match the video names")
    args = parser.parse_args()
    deck = engine.load_deck(args.deck)
    cards_dir = pathlib.Path(args.cards).resolve()
    out = pathlib.Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    with engine.browser() as b:
        tab = b.new_page(viewport={"width": 1280, "height": 720})
        for name, settings in thumbnails(deck, cards_dir, args.mode):
            tab.set_content(PAGE.format(fonts=engine.FONTS, **settings), wait_until="networkidle")
            tab.evaluate("document.fonts.ready")
            size = tab.evaluate(FIT)
            path = out / f"{name}.jpg"
            tab.screenshot(path=str(path), type="jpeg", quality=90)
            print(f"{path.name}  {path.stat().st_size // 1024} KB  headline {size:g}px")
    print("Done. Thumbnails under", out)


if __name__ == "__main__":
    main()
