"""Make YouTube videos from a rendered deck: 1920 x 1080, 30 fps, H.264, with a silent audio track.

    python build_videos.py DECK.py --cards CARDS_DIR --out VIDEO_DIR                    # mode "both"
    python build_videos.py DECK.py --cards CARDS_DIR --out VIDEO_DIR --mode questions
    python build_videos.py DECK.py --cards CARDS_DIR --out VIDEO_DIR --mode cards
    python build_videos.py DECK.py --cards CARDS_DIR --out VIDEO_DIR --descriptions-only

Modes:
    both       each question with the answer hidden (6 s), then the full card (12 s).
               Makes one video per topic and one with every card.
    questions  one video of every question, no answers (10 s each), as a quiz.
    cards      one video of every full card (15 s each), as a quick review.
Every video starts with an intro, each topic with a title screen, and every question has a
shrinking time bar. Each video gets a .txt description with YouTube chapters, one per card.
YouTube ignores all chapters if any is under 10 seconds, so title screens fold into the next
card's chapter. Run build_deck.py first. Needs ffmpeg.
"""
import argparse
import pathlib
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from flashcards import engine  # noqa: E402

TITLE, INTRO = 3, 5
SECONDS = {"both": (6, 12), "questions": (10, 0), "cards": (0, 15)}  # (question frame, full card)

SCREEN = """<!doctype html><html><head><meta charset="utf-8">{fonts}<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  html, body {{ width: 1920px; height: 1080px; background: #fff; font-family: Inter, sans-serif; color: #1a1a2e; }}
  body {{ border-top: 18px solid {main}; padding: 150px 160px 0; }}
  .kicker {{ font-size: 30px; font-weight: 600; letter-spacing: .14em; color: {main}; text-transform: uppercase; }}
  h1 {{ font-size: 112px; font-weight: 800; letter-spacing: -.03em; line-height: 1.05; margin-top: 26px; }}
  p {{ font-size: 38px; color: #374151; margin-top: 40px; line-height: 1.4; }}
  ol {{ margin-top: 34px; columns: 2; font-size: 34px; color: #374151; line-height: 1.6; padding-left: 48px; }}
  .foot {{ position: absolute; left: 160px; bottom: 90px; font-size: 26px; color: #64748b; }}
</style></head><body>{body}</body></html>"""


def stamp(s):
    return f"{s // 60}:{s % 60:02d}"


def clip(image, seconds, out, bar=None):
    """A still image as a 1920 x 1080 clip, with a bottom bar that shrinks to nothing when bar is a colour."""
    video = "[0:v]scale=-2:1010,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:white"
    if bar:
        video += (f"[card];color=c={bar}:s=1920x14:r=30:d={seconds}[bar];"
                  f"[card][bar]overlay=x='-w*t/{seconds}':y=1066:eval=frame:shortest=1")
    video += ",format=yuv420p[v]"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-framerate", "30", "-t", str(seconds), "-i", str(image),
                    "-f", "lavfi", "-t", str(seconds), "-i", "anullsrc=r=48000:cl=stereo",
                    "-filter_complex", video, "-map", "[v]", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                    "-tune", "stillimage", "-r", "30", "-c:a", "aac", "-b:a", "128k", "-shortest", str(out)], check=True)


def join(clips, out):
    listing = out.with_suffix(".list")
    listing.write_text("".join(f"file '{c}'\n" for c in clips))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(listing),
                    "-c", "copy", "-movflags", "+faststart", str(out)], check=True)
    listing.unlink()


def frames(deck, mode, work):
    """Intro, topic title screens, and (unless mode is cards) question frames with the answer hidden."""
    total = sum(len(t.cards) for t in deck.topics)
    q, c = SECONDS[mode]
    intro = {"both": f"{total} cards in {len(deck.topics)} topics. Read the question, answer it in your head, then check.",
             "questions": f"{total} questions in {len(deck.topics)} topics. Answer each one in your head. The answers are in the full flashcards video.",
             "cards": f"{total} cards in {len(deck.topics)} topics. Each card shows a question and its answer."}[mode]
    hint = "Say it out loud or write it down" if mode == "questions" else "The answer comes next"
    with engine.browser() as b:
        card_tab = b.new_page(viewport={"width": engine.WIDTH, "height": engine.HEIGHT}, device_scale_factor=engine.SCALE)
        screen = b.new_page(viewport={"width": 1920, "height": 1080})
        topics = "".join(f"<li>{t.title}</li>" for t in deck.topics)
        engine.shoot(screen, SCREEN.format(fonts=engine.FONTS, main=deck.topics[0].colour[0], body=(
            f'<div class="kicker">Flashcards</div><h1>{deck.title}</h1><p>{intro}</p><ol>{topics}</ol>')), work / "intro.png")
        for t, topic in enumerate(deck.topics, start=1):
            line = {"both": f"{len(topic.cards)} cards. Each question shows for {q} seconds, then the answer.",
                    "questions": f"{len(topic.cards)} questions. Each one shows for {q} seconds.",
                    "cards": f"{len(topic.cards)} cards. Each one shows for {c} seconds."}[mode]
            foot = "Pause any time you need more time." if mode == "questions" else "Pause on any card to read it fully."
            engine.shoot(screen, SCREEN.format(fonts=engine.FONTS, main=topic.colour[0], body=(
                f'<div class="kicker">{deck.title} flashcards · Topic {t} of {len(deck.topics)}</div><h1>{topic.title}</h1>'
                f'<p>{line}</p><div class="foot">{foot}</div>')), work / f"t{t}.png")
            if mode != "cards":
                for i in range(1, len(topic.cards) + 1):
                    engine.shoot(card_tab, engine.page(deck, t, i, hide_answer=True, hint=hint), work / f"t{t}-q{i}.png")


def build(deck, cards_dir, out, mode, text_only):
    q, c = SECONDS[mode]
    per_card = q + c
    total = sum(len(t.cards) for t in deck.topics)
    with tempfile.TemporaryDirectory() as tmp:
        work = pathlib.Path(tmp)
        if not text_only:
            frames(deck, mode, work)
            clip(work / "intro.png", INTRO, work / "intro.mp4")
        every, every_chapters, elapsed = [work / "intro.mp4"], [], INTRO
        for t, topic in enumerate(deck.topics, start=1):
            title_clip = work / f"t{t}.mp4"
            if not text_only:
                clip(work / f"t{t}.png", TITLE, title_clip)
            clips, chapters, at = [title_clip], [], TITLE
            topic_start = 0 if t == 1 else elapsed
            elapsed += TITLE
            for i, card in enumerate(topic.cards, start=1):
                if q:
                    clips.append(work / f"t{t}-q{i}.mp4")
                    if not text_only:
                        clip(work / f"t{t}-q{i}.png", q, clips[-1], bar=topic.colour[0])
                if c:
                    clips.append(work / f"t{t}-c{i}.mp4")
                    if not text_only:
                        png = cards_dir / engine.folder(t, topic) / engine.file_name(i, card)
                        clip(png, c, clips[-1], bar=None if q else topic.colour[0])
                question = engine.plain(card.question)
                chapters.append(f"{stamp(0 if i == 1 else at)} {i}. {question}")
                every_chapters.append(f"{stamp(topic_start if i == 1 else elapsed)} {topic.title} {i}: {question}")
                at += per_card
                elapsed += per_card
            every += clips
            if mode == "both":
                name = f"{deck.slug}-{engine.folder(t, topic)}"
                if not text_only:
                    join(clips, out / f"{name}.mp4")
                (out / f"{name}.txt").write_text(
                    f"{deck.title} flashcards: {topic.title} ({len(topic.cards)} cards)\n\n"
                    f"Each question shows for {q} seconds. Answer it in your head, then check the card. "
                    "Pause on any card to read it fully.\n\nChapters\n" + "\n".join(chapters) + "\n")
                print(f"{name}.mp4  {stamp(at)}")
        suffix = {"both": "", "questions": "-questions", "cards": "-cards"}[mode]
        name = f"{deck.slug}-all-topics{suffix}"
        if not text_only:
            join(every, out / f"{name}.mp4")
    heading, how = {
        "both": (f"{deck.title} flashcards: all {total} cards in {len(deck.topics)} topics",
                 f"Each question shows for {q} seconds. Answer it in your head, then check the card. Pause on any card to read it fully."),
        "questions": (f"{deck.title} flashcards quiz: all {total} questions in {len(deck.topics)} topics, without the answers",
                      f"Each question shows for {q} seconds. Answer it in your head, then check yourself with the full flashcards video."),
        "cards": (f"{deck.title} flashcards: all {total} cards in {len(deck.topics)} topics, with the answers",
                  f"Each card shows a question and its answer for {c} seconds. Pause on any card to read it fully."),
    }[mode]
    (out / f"{name}.txt").write_text(f"{heading}\n\n{how}\n\nChapters\n" + "\n".join(every_chapters) + "\n")
    print(f"{name}.mp4  {stamp(elapsed)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("deck")
    parser.add_argument("--cards", required=True, help="the folder build_deck.py wrote")
    parser.add_argument("--out", required=True, help="where the videos go; keep it out of git, videos are large")
    parser.add_argument("--mode", choices=["both", "questions", "cards"], default="both")
    parser.add_argument("--descriptions-only", action="store_true", help="only rewrite the .txt descriptions")
    args = parser.parse_args()
    if not args.descriptions_only and not shutil.which("ffmpeg"):
        sys.exit("ffmpeg is not installed. On a Mac: brew install ffmpeg")
    deck = engine.load_deck(args.deck)
    cards_dir = pathlib.Path(args.cards).resolve()
    if not args.descriptions_only and not any(cards_dir.glob("01-*/*.png")):
        sys.exit(f"No rendered cards in {cards_dir}. Run build_deck.py first.")
    out = pathlib.Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    build(deck, cards_dir, out, args.mode, args.descriptions_only)
    print("Done. Videos and descriptions under", out)


if __name__ == "__main__":
    main()
