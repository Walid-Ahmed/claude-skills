---
name: book-writer
description: Write a book on any topic step by step: ask the topic, suggest titles, propose an outline, write chapters after approval, test all code, and finish with a plagiarism and AI-content check reminder.
---

# Book Writer

A simple, generic workflow for writing a book on any subject. Move one stage at a time and wait for the user's approval before moving to the next stage.

## Stage 1: Ask for the topic

Ask in one short message:
- What is the book about?
- Who is the reader (beginner, practitioner, expert, general public)?
- Rough length (short guide, ~100 pages, full-length book)?
- Does it include code? If yes, which language?

If the user only gives a topic, assume sensible defaults and say what you assumed.

## Stage 2: Recommend titles

Suggest 5 title options, each with a subtitle and one line on its angle. Mix styles: descriptive, benefit-led, and catchy. Ask the user to pick one or combine them.

## Stage 3: Recommend an outline

For the chosen title, propose an outline:
- Short book description (3–4 sentences)
- Target reader and what they will be able to do after reading
- Chapter list: number, title, 2–3 sentence summary, main sections, estimated pages
- Note which chapters include code or exercises

Save the outline in Markdown and Word (.docx). Ask the user to approve it or request changes. Revise until approved. Do not start writing until the user approves the outline.

## Stage 4: Write the book

Write one chapter at a time, in outline order, and share each chapter before starting the next.

Each chapter has:
1. An introduction saying what the chapter covers and why it matters
2. Sections that follow the approved outline
3. Examples, and code where relevant
4. A short summary
5. Optional: review questions or exercises

Writing rules:
- Write everything originally. Do not copy text from websites, books, or other sources.
- Explain concepts before showing code.
- Use clear, plain language suited to the target reader.
- Keep terms consistent across chapters.
- Save each chapter in Markdown and Word (.docx).

## Code formatting rules

- Put every code sample in a fenced code block with its language tag (```python, ```bash, etc.).
- Add one sentence before each block saying what it does.
- Follow the language's standard style (PEP 8 for Python: 4-space indents, clear names, lines under ~79 characters).
- Keep samples short and focused on one idea.
- Add comments that explain *why*, not what is obvious.
- Show the expected output after code that prints something.
- State any packages to install, e.g. `pip install requests`.
- For code that cannot run on its own (fragments, pseudo-code), make the first line `# no-run`.

## Check that the code runs

Before delivering any chapter with code:

1. Save the chapter as a Markdown file, e.g. `chapter-01.md`.
2. Run the checker bundled with this skill:
   ```bash
   python3 scripts/check_code.py chapter-01.md
   ```
   It runs every `python` and `bash` block and prints PASS, FAIL or SKIPPED for each one.
3. Fix every FAIL in the chapter, then run it again until all blocks pass.
4. Also run any separate code files the chapter refers to.
5. Tell the user which blocks were tested, and list any that could not be run (other languages, missing services, API keys) as not verified.

## Stage 5: Finish and recommend checks

When all chapters are done:
1. Combine them into one full manuscript (Markdown and Word).
2. Give a short summary: chapters, approximate page count, code test results.
3. Recommend that the user, before publishing:
   - Run a **plagiarism check** (for example Grammarly, Copyleaks, Turnitin, or Quetext).
   - Run an **AI-content check** (for example GPTZero, Originality.ai, or Copyleaks AI Detector).
   - Revise flagged passages in their own voice, and add personal examples and experience.
   - Have a human editor or technical reviewer read the manuscript.
