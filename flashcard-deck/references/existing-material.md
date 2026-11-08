# Working from material the user already has

Read this when the cards come from the user's own material: notes, a PDF, slides, a Word document, a course folder, a repo, or flashcards they already made. The goal is a deck that teaches what *their* material teaches, in its terms, without dropping parts of it or quietly adding new ones.

## 1. Find and read all of it

Start by listing what is there, then read it all before planning. Tell the user what you found and anything you could not read, such as "3 PDFs (212 pages), 2 slide decks (64 slides). The scanned PDF in `week4/` has no text, so I read its pages as images."

| Material | How to read it |
| --- | --- |
| Folder | List it recursively first. Skip build output, `node_modules`, `.git`, and caches. |
| PDF | The Read tool with `pages` (up to 20 pages per call). For long PDFs, `pdftotext -layout file.pdf -` is faster to scan. Read scanned pages as images. |
| Slides (`.pptx`) and Word (`.docx`) | The pptx or docx skill if one is available. Otherwise `python-pptx` or `python-docx`, or unzip and read the XML. Slide notes often hold the explanation the slide only hints at. |
| Markdown, text, notes | Read directly. Headings usually map onto topics. |
| Images, screenshots, whiteboards | The Read tool shows them. Transcribe what matters. |
| A repo | The README and docs first, then the main modules and tests. Tests show how the code is meant to behave, which makes good cards. |
| Existing flashcards | Anki exports (`.txt` or `.csv`, tab-separated, often with HTML), Quizlet exports, spreadsheets, or a Markdown Q&A list. Parse them into question and answer pairs, as in section 5. |

## 2. Map the material before planning

Write a short outline of the material (chapters, sections, slide groups, modules). In the plan, show which part each topic covers. Then list the parts with no card and say why, such as "too thin" or "setup only, no concept". A gap the user can see is fine. One they find later in the printed deck is not.

Slide decks often repeat pages, as build-up animations or a section shown twice. Note duplicates in the map ("pp. 7-10 repeat 3-6") instead of listing them as gaps.

For large material (over about 100 pages or 60 slides), ask which parts matter most before planning everything. Or plan and build one chapter at a time, showing each before starting the next.

## 3. Stay faithful to it

The interview asks how closely to follow the material. Respect the answer:

- **Only what the material says**: every fact on a card should trace back to the material. Use its terms, names, examples, numbers, and code, so the cards match what the user studied.
- **The material plus missing basics**: mark added cards "(added)" in the plan, so the user can drop them.
- **As a starting point**: you may restructure and extend freely, but keep its examples where they fit.

Concept first still applies. Stating the general rule that a slide or passage demonstrates is fine when it is a direct reading: if the slide is titled "Route order matters" and shows the fixed path first, the card can say "the first matching route wins". If the rule is your own inference and the user chose "only what the material says", phrase it as what the material shows, or ask.

If something in the material looks wrong or out of date, such as a deprecated API, an off-by-one, or a claim that contradicts the official docs, do not fix it silently. Tell the user what you found and ask which version the card should teach. A flashcard that disagrees with the user's course without saying so causes confusion at exam time.

Rewrite rather than copy. A card needs a short lead and a structure (boxes, steps, a table), not a pasted paragraph. Keep quotes short, especially from material someone else wrote.

## 4. Point back to the source

Offer source references. They are recommended for course or book material, so the learner can go back for more:

```python
card("jwt", "What is a JWT?", body, footer="...", tag="JWT", source="Ch. 7, p. 142")
```

The footer then shows "Source: Ch. 7, p. 142" in small grey text, and the README gets a Source column. Formats that read well:

- A book or PDF: "Ch. 7, p. 142", or a range: "pp. 36-38".
- One PDF of slides: "Slide 12" or "Slides 36-38, 40". Several slide decks: "Week 3, slide 12".
- A repo: the file path, such as "app/routers/auth.py".

Use the number printed on the page. When the material prints none (slide exports often do not), use the PDF page number, and say so once in the README with `deck(..., credit="Slide numbers are PDF page numbers in week3.pdf.")`.

## 5. Converting existing flashcards

When the user already has cards, they mostly want them grouped, cleaned up, and printable, not rewritten:

- Keep each question. It becomes the card's question.
- The answer becomes the lead. Add structure (boxes, a table, an example) only where the answer already has parts, or the user asked for richer cards.
- Split a card that asks two things. Merge exact duplicates.
- Group cards into topics by concept, not by their original order.
- Report what you changed: cards split, merged, or dropped, and any answer you think is wrong (see section 3). Ask before rewording answers heavily. They are the user's.

## 6. Who owns the material

A deck made from a paid course, a book, or a colleague's notes is fine for the user's own study. Before anything goes public (a repo, YouTube), mention where the content comes from and offer a credit line: `deck(..., credit="Based on ...")` puts it in the README. Don't publish copied code or text from someone else's material without the user deciding that knowingly.
