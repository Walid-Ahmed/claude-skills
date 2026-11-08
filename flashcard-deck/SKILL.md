---
name: flashcard-deck
description: Build a study flashcard deck from any subject, or from material the user already has (lecture PDFs, slides, Word or Markdown notes, a course folder, a repo, or existing Anki or Quizlet cards), by first asking the user what they need. Produces print-friendly A4 landscape question-and-answer card images grouped by topic, one PDF per topic, and a README index, and on request YouTube videos (question then answer, a questions-only quiz, or a cards-only review) with chapter descriptions and thumbnails. Use this whenever the user asks for flashcards, study cards, review cards, revision cards, a Q&A deck, quiz cards, or "cards to remember" something, or wants to turn a codebase, course, chapter, or topic into cards, printable cards, or a flashcard video, even if they do not say "deck". Also use it to add, fix, split, or regroup cards in a deck made with this skill.
---

# Flashcard deck

Turn a subject into a deck of question-and-answer cards that teach the general concept first, print cleanly, and can become YouTube videos. The cards are written in one Python file (`deck.py`) with small helpers, and bundled scripts render everything from it, so a fix to one card is one edit and one rebuild.

The work goes in four stages. Ask before each stage that costs the user time or publishes anything, because a deck is only useful if it covers what *they* need, and videos take minutes to encode.

1. **Interview**: ask what to build.
2. **Plan**: propose topics and card questions; get a yes.
3. **Cards**: write `deck.py`, render, look at every card, fix what does not fit.
4. **Extras** (only if wanted): videos, thumbnails, publishing.

## 1. Interview

Start by asking, not building. Use the AskUserQuestion tool so the user can click answers. Ask everything in one call (it takes up to 4 questions), and skip any question the user's message or the open project already answers. Offer a recommended option first, marked "(Recommended)".

Ask about the following. The tool takes up to 4 questions, so when the source is the user's material and a fifth question is needed, ask the last one in a second call.

- **Source**: what the cards cover. Options such as: material they already have (files or a folder: PDFs, slides, Word or Markdown notes, a course, a repo, or existing flashcards), this repo, a subject from your own knowledge, or notes they will paste. If the request already names the source, skip this.
- **How closely to follow it** (only when the source is their material): only what the material says (Recommended), the material plus missing basics marked as added, or the material as a starting point.
- **Audience and depth**: beginner (one idea per card, plain words), intermediate (concepts plus a short code example), or advanced (trade-offs, edge cases).
- **Maximum number of cards**: up to 10 (a quick set), up to 20 (Recommended), up to 40 (a full course), or no limit (as many as the material needs). The user can type any other number. Record it as `deck(..., max_cards=N)`: the build stops if the deck grows past it, so splitting cards later cannot quietly break the limit. More cards means more topics, not longer cards.
- **Outputs**: card images and PDFs only (Recommended), plus videos, plus videos and thumbnails. Videos come after the cards are approved either way.

Then, if still unknown, ask in plain text (no tool needed): the deck title shown on every card (such as "FastAPI" or "Kubernetes"), where to save the output (suggest a `flashcards/` folder in the current project, or a new folder), and whether code examples may name the source project or should stay generic. For the user's own material, also ask whether each card should show where it comes from (such as "Ch. 3, p. 42").

## 2. Plan

Read the source first. **If it is material the user already has, read `references/existing-material.md` now**: it covers reading PDFs, slides, Word files, folders, and existing flashcards, mapping all of the material so nothing is silently dropped, staying faithful to it, and pointing each card back to its page. For a subject from your own knowledge, decide what a learner at the chosen level needs. Then propose the deck as a short list: topics in learning order, and under each, one line per card with its question. Group by concept (HTTP basics, validation, auth), not by file. Aim for 3 to 9 cards per topic. A small deck (under about 12 cards) is fine as 2 or 3 topics of 2 to 4 cards.

Keep the plan within the maximum number of cards, and leave room for a split or two. If the material needs more cards than the maximum allows, cover the core ideas first, then list the topics or sections left out, and offer to raise the limit.

Show the plan and ask for a yes, changes, or cuts before writing cards. Writing 40 cards on the wrong topics wastes the most time, so this check is worth one round trip.

## 3. Cards

### Write deck.py, first topic first

Copy `references/deck_template.py` next to where the output will go. Write the first topic's cards, render just that topic (`--topic 1`), show the user two or three of them, and ask whether the style and depth are right. Then write the rest. Finding out on card 3 that the user wanted shorter cards is cheap; finding out on card 40 is not. Read `references/components.md` before writing the first card: it shows every building block (lead sentence, boxes, steps, tables, code examples, callouts, diagrams) with the HTML to use.

How to write a good card, and why:

- **Concept first.** The question and the opening sentence (the `lead`) state the general idea in words that apply anywhere. Project-specific code goes in an `example(...)` box captioned "Example: ...", so the reader learns the rule, then sees one case. Where the example project differs from common practice, say so in the example's comment.
- **One idea per card.** A question that joins two separate ideas ("What is X, and how do you deploy it?") wants two cards. A contrast ("How is X different from Y?") or a pair that only makes sense together is one idea.
- **Lead, then structure, then example.** A one- or two-sentence answer, then two or three boxes, steps, or a small table that break it down, then an optional callout and code example. The reader should get the answer from the lead alone.
- **The footer is the line to remember**, under 15 words. The tag is one or two words naming the idea.
- **Plain, exact wording.** Short sentences. Name real status codes, function names, and commands; do not hint at them.
- **Diagrams only where they add something**: a flow, a decision with failure paths, or the parts of a URL or message. Not on cards whose table already shows the structure.
- **Cross-references** say where to look: "Card 4 in App structure shows the server side."

### Render and check

```bash
python3 <skill-dir>/scripts/build_deck.py deck.py --out OUT_DIR             # every card, PDFs, README
python3 <skill-dir>/scripts/build_deck.py deck.py --out OUT_DIR --topic 1   # one topic, quick check
```

`<skill-dir>` is the folder this SKILL.md is in. Use `python3`, or `python` where that is Python 3. The script needs Python with `playwright` and `Pillow` (`pip install playwright pillow`), plus Google Chrome or `playwright install chromium`. It renders every card as a 2400 x 1698 px A4 landscape PNG, checks that each card's content fits (height and width), and stops naming any card that does not. Then it writes one PDF per topic, `print/all-cards.pdf`, and `README.md`.

- **Repeated content**: the fit check measures size, not sense. Look for a box that repeats a step or the lead, and cut it.
- **Over the maximum**: the build stops if the deck has more cards than `max_cards`. Merge or drop the least important cards, or ask the user to raise the limit. Do not raise it on your own.
- **A card does not fit**: shorten the text, drop a box, or split it into two cards (such as "9a" and "9b", or two questions). Never shrink the font to squeeze it in; the cards must stay readable when printed.
- **Look at every card** after rendering, by opening the PNGs. The fit check catches overflow, not a confusing card, a diagram that misleads, or a typo. Fix and re-render; `--topic N` re-renders one topic quickly.
- **Spare space is normal.** The build reports spare space in CSS px on the 1200 x 849 card (the PNG is twice that). A simple card often leaves 150 to 350 px empty, and that is fine for reading and printing. Do not pad a card to fill it. If a card leaves over about 400 px and feels thin, it may deserve a diagram or an example, or it may belong merged into a neighbouring card.

## 4. Extras: videos, thumbnails, publishing

Only when the user wants them, and after they approve the cards. Ask which video style, and say roughly how long encoding takes (about 15 seconds of encoding per card on a laptop).

```bash
python3 <skill-dir>/scripts/build_videos.py deck.py --cards OUT_DIR --out VIDEO_DIR [--mode both|questions|cards]
python3 <skill-dir>/scripts/build_thumbnails.py deck.py --cards OUT_DIR --out VIDEO_DIR/thumbnails
```

- `--mode both` (default): each question with the answer hidden and a time bar (6 s), then the full card (12 s). Makes one video per topic and one with every card.
- `--mode questions`: a quiz, every question for 10 s, no answers.
- `--mode cards`: a review, every full card for 15 s.
- Every video has an intro and topic title screens, and a `.txt` description whose chapters YouTube turns into clickable sections. Chapters are at least 10 seconds, which YouTube requires.
- Videos need `ffmpeg`. Keep `VIDEO_DIR` outside any git repo, since videos are large.
- Thumbnails are 1280 x 720 JPEGs named to match each video. `topic(..., hook="A · B · C")` sets the small line under each topic's headline.
- After building, offer paste-ready YouTube titles and descriptions: a title under 70 characters with the subject and the hook, a description with the opening line, a bullet per topic, any links, and the chapters from the `.txt`.

Ask before pushing, publishing, or uploading anything; those reach other people. If the deck's code examples come from someone else's course or repo, mention that before making it public and offer a credit line (`deck(..., credit="...")` puts one in the README).

## Changing a deck later

Edit `deck.py` and run `build_deck.py` again; it rebuilds every card, the PDFs, and the README, and removes images of deleted cards. Rebuild videos only if the user wants them updated, and `--descriptions-only` rewrites just the video descriptions.

## Files in this skill

- `scripts/build_deck.py`: cards, fit check, PDFs, README.
- `scripts/build_videos.py`, `scripts/build_thumbnails.py`: the extras.
- `scripts/flashcards/`: the helpers `deck.py` imports (`__init__.py`), the renderer (`engine.py`), and the card stylesheet (`card.css`: print-friendly, white with coloured outlines, fixed A4 landscape).
- `references/components.md`: every card building block with an example. Read before writing cards.
- `references/deck_template.py`: a small working deck to copy.
- `references/existing-material.md`: building a deck from the user's own notes, PDFs, slides, repo, or flashcards. Read when that is the source.
