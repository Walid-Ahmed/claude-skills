"""Extract fenced code blocks from a Markdown chapter and run each one.

Usage: python check_code.py chapter.md
Runs python and bash blocks; reports PASS/FAIL per block.
Blocks marked with a first line of "# no-run" are skipped.
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

RUNNERS = {"python": ["python3"], "py": ["python3"], "bash": ["bash"], "sh": ["bash"]}
FENCE = re.compile(r"^```(\w+)[^\n]*\n(.*?)^```", re.DOTALL | re.MULTILINE)


def main(path: str) -> int:
    text = Path(path).read_text(encoding="utf-8")
    failures = 0
    for i, (lang, code) in enumerate(FENCE.findall(text), start=1):
        lang = lang.lower()
        if lang not in RUNNERS:
            print(f"Block {i} ({lang}): SKIPPED (not runnable here)")
            continue
        if code.lstrip().startswith("# no-run"):
            print(f"Block {i} ({lang}): SKIPPED (marked no-run)")
            continue
        with tempfile.NamedTemporaryFile("w", suffix=".py" if "py" in lang else ".sh", delete=False) as f:
            f.write(code)
        try:
            result = subprocess.run(RUNNERS[lang] + [f.name], capture_output=True, text=True, timeout=60)
            ok = result.returncode == 0
            err = result.stderr.strip().splitlines()[-1:] if not ok else []
        except subprocess.TimeoutExpired:
            ok, err = False, ["timed out after 60s"]
        print(f"Block {i} ({lang}): {'PASS' if ok else 'FAIL'} {' '.join(err)}")
        failures += not ok
    print(f"\n{failures} failing block(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
