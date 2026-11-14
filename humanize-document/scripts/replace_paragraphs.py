"""Replace paragraphs in a Word file with checked, humanized text, keeping the document's formatting.

Usage:
    python3 replace_paragraphs.py <file.docx> <mapping.json> --backup-dir <dir> [--log <run-log.json>]
                                  [--body-style NAME] [--code-style NAME] [--code-font NAME]

mapping.json maps each original paragraph's opening words (unique) to its new text. Wrap code
names in backticks: they are formatted the way the original paragraph formatted its code.

By default each paragraph keeps its own paragraph style and paragraph formatting, plain text
gets the look of the original's first plain run, and code gets the look of the original's first
code run (or, if it had none, --code-style, else a character style named like "...Code...",
else the --code-font, Consolas by default). --body-style resets the paragraph to that style and
clears its direct paragraph formatting, which is useful when pasted formatting got in.

The script backs up the file first, then checks that only the mapped paragraphs changed and
that tables and images are intact; if not, it restores the backup. --log appends every
before/after pair to a JSON file, so the whole run can be re-checked at the end.
"""

import argparse
import copy
import difflib
import json
import re
import shutil
import sys
import time
from pathlib import Path

import docx
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml.ns import qn

sys.path.insert(0, str(Path(__file__).resolve().parent))
from doc_prose import is_code_run  # type: ignore  # noqa: E402


def find_code_style(document, wanted):
    if wanted:
        return document.styles[wanted]
    for style in document.styles:
        if style.type == WD_STYLE_TYPE.CHARACTER and "code" in style.name.lower():
            return style
    return None


def run_properties(runs, code):
    for run in runs:
        if run.text.strip() and is_code_run(run) == code:
            properties = run._r.find(qn("w:rPr"))
            return copy.deepcopy(properties) if properties is not None else None, run.style
    return None, None


def rewrite(document, paragraph, marked_text, args, code_style):
    plain_rpr, plain_style = run_properties(paragraph.runs, code=False)
    code_rpr, code_run_style = run_properties(paragraph.runs, code=True)
    element = paragraph._p
    # Drop every run, hyperlink and bookmark, but keep the paragraph-properties node.
    for child in list(element):
        if child.tag != qn("w:pPr"):
            element.remove(child)
    if args.body_style:
        properties = element.find(qn("w:pPr"))
        if properties is not None:
            for child in list(properties):
                properties.remove(child)
        paragraph.style = document.styles[args.body_style]
        plain_rpr, plain_style = None, None
    # Odd-numbered pieces of a split on backticks are the code names.
    for index, piece in enumerate(re.split(r"`", marked_text)):
        if not piece:
            continue
        run = paragraph.add_run(piece)
        if index % 2 == 0:
            if plain_rpr is not None:
                run._r.insert(0, copy.deepcopy(plain_rpr))
            elif plain_style is not None:
                run.style = plain_style
        elif code_rpr is not None or code_run_style is not None:
            if code_rpr is not None:
                run._r.insert(0, copy.deepcopy(code_rpr))
            else:
                run.style = code_run_style
        elif code_style is not None:
            run.style = code_style
        else:
            run.font.name = args.code_font


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("docx_path")
    parser.add_argument("mapping_json")
    parser.add_argument("--backup-dir", required=True)
    parser.add_argument("--log")
    parser.add_argument("--body-style")
    parser.add_argument("--code-style")
    parser.add_argument("--code-font", default="Consolas")
    args = parser.parse_args()

    source = Path(args.docx_path)
    locks = [source.parent / ("~$" + source.name), source.parent / ("~$" + source.name[2:])]
    if any(lock.exists() for lock in locks):
        sys.exit("Word lock file found: save and close the document in Word first")
    mapping = json.loads(Path(args.mapping_json).read_text(encoding="utf-8"))
    if any(text.count("`") % 2 for text in mapping.values()):
        sys.exit("Unbalanced backticks in the mapping")

    backup = Path(args.backup_dir) / f"{source.stem}.before-{time.strftime('%Y%m%d-%H%M%S')}.docx"
    shutil.copy2(source, backup)

    document = docx.Document(str(source))
    code_style = find_code_style(document, args.code_style)
    before = [p.text for p in document.paragraphs]
    tables, images = len(document.tables), len(document.inline_shapes)

    pairs = []
    for prefix, new_text in mapping.items():
        matches = [p for p in document.paragraphs if p.text.strip().startswith(prefix)]
        if len(matches) != 1:
            sys.exit(f"{len(matches)} paragraphs start with {prefix!r}; nothing saved")
        pairs.append({"before": matches[0].text, "after": new_text.replace("`", "")})
        rewrite(document, matches[0], new_text, args, code_style)
    document.save(str(source))

    after_doc = docx.Document(str(source))
    after = [p.text for p in after_doc.paragraphs]
    changed = [line for line in difflib.ndiff(before, after) if line[:1] in "+-"]
    removed = sum(1 for line in changed if line.startswith("-"))
    added = sum(1 for line in changed if line.startswith("+"))
    intact = len(after_doc.tables) == tables and len(after_doc.inline_shapes) == images
    ok = removed == len(mapping) and added == len(mapping) and intact
    print(f"backup: {backup}")
    print(f"paragraphs replaced: {added} (expected {len(mapping)}); tables and images intact: {intact}")
    for line in changed:
        print("  ", line[:90])
    if not ok:
        shutil.copy2(backup, source)
        sys.exit("Unexpected changes: the backup was restored and nothing is saved")

    if args.log:
        log = Path(args.log)
        entries = json.loads(log.read_text(encoding="utf-8")) if log.exists() else []
        stamp = time.strftime("%Y-%m-%d %H:%M:%S")
        entries.extend({"time": stamp, **pair} for pair in pairs)
        log.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"logged {len(pairs)} pairs -> {log}")


if __name__ == "__main__":
    main()
