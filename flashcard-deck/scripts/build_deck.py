"""Render a deck file into A4 landscape flashcard PNGs, grouped by topic, with PDFs and a README index.

    python build_deck.py DECK.py --out OUT_DIR             # every card, then PDFs and README
    python build_deck.py DECK.py --out OUT_DIR --topic 3   # only topic 3, for quick checks (no PDFs)

Output:
    OUT_DIR/README.md                     topic index with every question
    OUT_DIR/01-topic-name/01-card.png     2400 x 1698 px each
    OUT_DIR/print/01-topic-name.pdf       one A4 page per card
    OUT_DIR/print/all-cards.pdf

Exits with an error, naming the cards, if any card's content does not fit its A4 card.
"""
import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from flashcards import engine  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("deck", help="the deck file, such as deck.py")
    parser.add_argument("--out", required=True, help="output folder")
    parser.add_argument("--topic", type=int, action="append", help="only render this topic number (repeatable)")
    args = parser.parse_args()

    deck = engine.load_deck(args.deck)
    total = sum(len(t.cards) for t in deck.topics)
    if deck.max_cards and total > deck.max_cards:
        sys.exit(f"The deck has {total} cards, but the user asked for at most {deck.max_cards}. "
                 "Merge or drop cards, or ask the user to raise max_cards.")
    out = pathlib.Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    problems = engine.render_cards(deck, out, only=args.topic)
    if problems:
        sys.exit("These cards do not fit. Shorten them or split each into two cards:\n"
                 + "\n".join(f"  {name}: {extra}px too much" for name, extra in problems))
    if args.topic:
        print("Rendered the chosen topics only. Run without --topic for the PDFs and README.")
        return
    engine.write_pdfs(deck, out)
    engine.write_readme(deck, out)
    limit = f" (limit {deck.max_cards})" if deck.max_cards else ""
    print(f"Done: {total} cards{limit} in {len(deck.topics)} topics, under {out}")


if __name__ == "__main__":
    main()
