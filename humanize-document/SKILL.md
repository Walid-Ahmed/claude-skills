---
name: humanize-document
description: Lower a document's AI-content score in the JustDone AI detector below a target (default 50%) by rewriting its most-flagged paragraphs in the Grubby humanizer, one small batch at a time, with Claude checking every rewrite so the meaning, terms and clarity stay correct and the Word formatting survives. Works on Word (.docx), Markdown and plain-text files, driving both sites in the user's own Chrome through Claude in Chrome. Use when the user asks to humanize a document, report, article, essay or chapter, to bring its AI content or AI score under a percentage, to "make it pass the AI detector", or to "do more paragraphs in Grubby", e.g. "humanize report.docx until it is under 50%".
---

# Humanize a document with Grubby, checked against JustDone

Loop over the document's most-flagged paragraphs. Each round: put a batch into **Grubby** (grubby.ai, the humanizer), click Humanize, read the output, make minimal fixes so meaning, clarity and flow are unchanged, save it into the file with its own formatting, re-score the whole document with **JustDone** (justdone.ai, the AI-content detector), and report. Repeat until JustDone's score is below the target (50% unless the user names another).

**Meaning and clarity come before the score.** If keeping a sentence accurate costs a few points, keep it accurate and say so.

## What the user needs

- **Claude in Chrome** (the browser extension), connected to this session. Both sites are driven in the user's real Chrome, where they are signed in.
- **A Grubby account**, signed in at `https://grubby.ai`. The free tier has a small word allowance, so a whole document usually needs a **paid Grubby subscription**. Even the "Unlimited" plan has a rolling daily cap (30,000 words per 24 hours in November 2026).
- **A JustDone account** with AI-detector words, signed in at `https://app.justdone.ai`. Each scoring run spends detector words for the whole document, so a 5,000-word document scored ten times uses about 50,000 words. This needs a **paid JustDone subscription** or bought word packs.
- Python 3 with `python-docx` (`pip install python-docx`) for Word files.

If either site shows a sign-in page, ask the user to sign in; never sign in, upgrade, or buy anything for them.

## Hard rules

- **Edit the file the user names, in place, after a backup.** If that file is generated from another source (a Word file built from Markdown, say), warn the user that rebuilding it later would wipe the rewrites.
- **Ask which parts are off-limits** if it is not obvious: quotations, legal text, text the user wrote by hand and wants kept, other people's sections. Never touch them.
- **Word must not have the file open.** On a Mac check with `osascript -e 'tell application "Microsoft Word" to get full name of every document'`, and look for a `~$…docx` lock file next to it. If it is open, ask the user to save and close it.
- **Clicking Humanize in Grubby.** At the start of the run, ask once whether Claude may click Humanize for every batch of this run. The permission covers only the Humanize button on `https://grubby.ai/dashboard/humanizer` with this run's batch in it: never click other Grubby tools, an upgrade, or a purchase. If the click is blocked (by the session's permission mode or a declined prompt), stop and ask the user to click Humanize.
- **In JustDone, never click "Humanize Text" or "Remove AI", and never buy words.** If an "Add AI Content Detector Words" dialog appears, the account is out of detector words: click Close, stop, and tell the user.
- **If Grubby shows "Daily Limit Reached"**, close the dialog with its ✕ (never "Upgrade Subscription"), stop, and tell the user the time the dialog says words free up again. Save the work done so far; the run can continue later from the same log.
- **Never send another person's private data** to either site without the user's say-so: both are third-party services.
- **Do not commit or share the file** unless the user asks.
- Back up the file to the scratchpad before every write (`replace_paragraphs.py` does this for Word files).

## Setup, once per run

1. Resolve the file. For Word, make sure Word isn't holding it.
2. Get a baseline score (see **Scoring with JustDone**), unless one from the last few minutes is known for the same file.
3. Open Chrome with `tabs_context_mcp`. Reuse a JustDone detector tab (`https://app.justdone.ai/tools/ai_content_detector`) and a Grubby humanizer tab (`https://grubby.ai/dashboard/humanizer`), or create them. Check both are signed in.
4. Create a run log path in the scratchpad (for example `<scratchpad>/humanize-log.json`) and pass it to every save, so the final check can see every rewrite.

## Picking the next batch

Run `python3 scripts/doc_prose.py <file> --list` to list the prose paragraphs with an index, section, word count and opening words. Then run `scripts/justdone_paragraph_shares.js` on the current JustDone result (fill its `PREFIXES` with the paragraphs' opening words) to get each paragraph's highlighted share.

Choose up to **three paragraphs, about 250 to 600 words**:

- **Highest highlighted share first**, among paragraphs of 40 words or more.
- **Prefer consecutive paragraphs** in one section. JustDone scores sentences in context, so a rewritten run lowers the score far more than scattered edits.
- **Finish a section once it is started.** When most of a section's paragraphs have been rewritten, JustDone often clears the rest of it too. In testing on a long technical document, rewriting the last paragraphs of one section dropped the score from 73% to 68% and took an untouched paragraph in that section to 0%. A lone batch inside a long, fully flagged stretch can change nothing.
- **Reading order** within a section, and earlier sections first when shares tie.
- **Skip:** short lead-ins ("The following table shows:"), numbered steps, list items, glossary entries, questions and exercises, table cells, captions, references and code. They are templated or short, and humanizers tend to damage them.
- **A second pass works.** A paragraph Grubby already rewrote can still be 100% flagged; running it again together with its now-flagged neighbours can clear it (in testing, one opener went from 100% to 50% on its second pass, and the score from 62% to 58%).
- **Leave alone** paragraphs the user wrote by hand, and paragraphs already rewritten this run that are under 20% highlighted.

State the batch in one line (section plus opening words), then fill Grubby.

## Filling Grubby

1. Navigate the Grubby tab to `https://grubby.ai/dashboard/humanizer` to clear it. Click the **Academic (Turnitin)** mode button (bottom-left, starred) **before** pasting; Grubby refuses input otherwise. (Another mode is fine if the user prefers it; Academic gave the lowest JustDone scores in testing.)
2. The input is a ProseMirror editor, so neither keyboard paste nor setting `textarea.value` works. Run `scripts/grubby_fill.js` with `__T` set to the batch's paragraphs joined by a blank line, as a JSON string (`python3 -c "import json,sys;print(json.dumps(open(sys.argv[1]).read()))" batch.txt`). Confirm the returned word counter and paragraph count.
3. `find` the **Humanize** button and click it by `ref`. Wait about 15 s, then read the output. If the output is still empty, wait 10 s and read again, up to about a minute in all.

## Reading Grubby's output

Read the output with `scripts/grubby_read_output.js`. Tool results over about 1,000 characters get truncated, so it stores the text in `window.__O` and returns it in slices (`window.__S = 900, 1800, …`). If the output panel is empty, look at `https://grubby.ai/dashboard/history` **in a new tab**, because navigating the humanizer tab clears it. Check the newest entry's *Prompt* matches this batch. If it doesn't, the click didn't go through: click Humanize once more, and if that also fails, tell the user.

**Two versions: Humanized and Polished.** The output panel has three view tabs: **Humanized** (the default), **Polished** and **Detection**. Switching between them only changes the view. Every round:

1. Read **Humanized** (`window.__TAB = 'Humanized'`). This is the version to check and save.
2. Read **Polished** (`window.__TAB = 'Polished'`). It appears a few seconds after Humanized; if it reads "Generating polished version...", wait about 8 s and read again. If it reports `sameAsInput=true`, it is the original text and cannot lower the score: ignore it. If it matches Humanized sentence by sentence, there is nothing new. If it differs from Humanized only by small proofreading fixes, use it as the base for the meaning check.
3. If Polished **differs** from both the input and Humanized, keep it as a second candidate. Save Humanized first. If a paragraph is still 50% or more flagged after re-scoring, try its Polished version: same meaning check, save it in place of the Humanized text, re-score, keep whichever scored lower, and report both numbers.
4. Leave the view on **Humanized**.

History keeps only the Humanized output, so read Polished before navigating the humanizer tab away.

## Meaning check: minimal fixes only

Compare each output paragraph with its original, sentence by sentence. Keep Grubby's wording wherever it is correct; change only what fails one of these checks:

- **Facts and mechanisms** are unchanged: who does what, cause and effect, numbers, dates, limits, names, and what a figure, table or example actually shows.
- **Scope words** are unchanged: "every" versus "most", "could" versus "would", "each" versus "together", "either … or" versus "or both", "a" versus "the".
- **Cross-references stay true:** "Section 3 returns to …" must not become "as discussed earlier" when it has not been discussed yet.
- **The document's own terms:** keep the words the document defines or uses consistently (check its glossary or key terms, if any). Humanizers swap in synonyms ("component" for "module", "diagram" for "figure"); put the document's term back.
- **Code and names:** code names, file paths, commands, product names and identifiers stay exactly as in the original. Humanizers eat underscores and change case.
- **Clarity:** fix a phrase that is ungrammatical or ambiguous, restore a lost antecedent ("this" → "this change"), and add commas Grubby drops after an introductory clause.
- **Flow:** the paragraph's first sentence still links to the one before it, and a lead-in still ends with a colon before its list, table or figure.
- **The document's style:** if the original avoids contractions, bold, emoji or em dashes, the rewrite does too; keep its spelling variant (US or UK) and voice ("you" versus "we"); spell out abbreviations where the original did.

Report the fixes as a short list (original claim → fix), then save.

## Saving

**Word files.** Write a JSON file mapping each original paragraph's **opening words** (unique, about 40 characters) to the final text. Mark every code name with backticks, using the original's code-formatted pieces as the checklist (`python3 scripts/doc_prose.py <file> --codes "<prefix>"`). Then run:

```bash
python3 scripts/replace_paragraphs.py <file.docx> <mapping.json> --backup-dir <scratchpad> --log <scratchpad>/humanize-log.json
```

Each paragraph keeps its paragraph style and formatting, plain text keeps the look of the original's plain text, and code keeps the look of the original's code. The script prints a check that only the mapped paragraphs changed and that tables and images are intact; otherwise it restores the backup. Use `--body-style "<style>"` only when pasted formatting got into a paragraph and it should be reset to the document's body style.

**Markdown and text files.** Back up the file, replace each paragraph with the Edit tool (keep backticks, links and emphasis as in the original), and append the before/after pair to the run log yourself.

## Scoring with JustDone

1. `python3 scripts/doc_prose.py <file> --out <scratchpad>/prose.txt`. It takes every prose paragraph and leaves out headings, captions, code, tables and (in Markdown) lists.
2. **Upload the file instead of using the clipboard.** Several Claude sessions can share the computer's clipboard, so a copy followed by a paste can deliver another session's text. Navigate the JustDone tab to the detector and wait 3 s. `find` its hidden file input (it accepts `.pdf, .docx, .txt`), upload `prose.txt` with `file_upload`, and wait 3 s.
3. **Verify the box holds this document:** `document.querySelector('textarea').value` must have the same length as `prose.txt` (in characters) and contain a sentence from this round's batch. If not, re-upload; never score unverified text. Only if the upload fails, fall back to the clipboard (`LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 pbcopy < prose.txt` on a Mac, click the textarea by `ref`, paste) and run the same check.
4. `find` "Detect AI" and click it, wait 10 s, then run `scripts/justdone_paragraph_shares.js`. It returns the displayed score ("NN% Possibly AI"), the highlighted-word share, and each listed paragraph's share.

JustDone has a per-check length limit; if the document is longer, score it in parts at section boundaries and report each part.

## Reporting each round

One short table: JustDone score before and after, and each paragraph in the batch with its highlighted share before and after. Then the meaning fixes made. Then ask whether to continue with the next batch (or continue without asking if the user said to run until the target). Stop when the displayed score is **below the target**.

## Final check before handing back

A batch-by-batch check cannot see problems that cross batches. When the target is reached, read every pair in the run log in document order, with the paragraphs around each, and look for:

| Humanizer output | Problem | Fix |
|---|---|---|
| "the user id and the cache map" | code names lost their underscores or backticks | restore the exact names, e.g. `user_id`, `_cache` |
| "each fulfils all three roles" | scope changed: they share the roles | drop "each" |
| "with either a default or a limit" | overstated: it can be both | "a default, a limit, or both" |
| "It checks… / The data is validated. / It logs…" | a parallel list broken across batches | make the items parallel again, or First / Second / Third |
| "It" or "This" opening a paragraph after a rewritten neighbour | lost antecedent | name the thing |
| "is covered later" for something already covered | cross-reference now wrong | restore the original reference |
| a synonym for a defined term | not the document's word | put the term back |

Report what you checked and what you fixed, re-score once more if anything changed, and give the final numbers: the starting score, the final score, the number of paragraphs rewritten, and the backup's path.

## Scripts

- `scripts/doc_prose.py`: lists prose paragraphs (`--list`), shows a paragraph's code pieces (`--codes`), and writes detector prose (`--out`), for `.docx`, `.md` and `.txt`.
- `scripts/replace_paragraphs.py`: replaces Word paragraphs by opening words, keeping their formatting, with a backup, a diff check and a run log.
- `scripts/grubby_fill.js`: inserts `window.__T` into Grubby's input.
- `scripts/grubby_read_output.js`: switches to the view in `window.__TAB` (`'Humanized'` by default, or `'Polished'`), stores that output in `window.__O`, and returns `view=…`, `sameAsInput=…` and a slice (`window.__S`, default 0).
- `scripts/justdone_paragraph_shares.js`: the score, the highlighted share, and per-paragraph shares for `PREFIXES`.

Paste a `.js` file's contents into `javascript_tool` after filling in its constants. They run in the page and change nothing on it, except `grubby_fill.js`, which fills the input. Both sites change their pages from time to time; if a script stops finding things, inspect the page and adjust the selector.
