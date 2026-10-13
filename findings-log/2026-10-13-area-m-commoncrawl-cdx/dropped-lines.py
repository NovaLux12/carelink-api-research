#!/usr/bin/env python3
"""Area M — derive which query lines were never sent, from the committed files.

WHY THIS EXISTS
---------------
Two published numbers were wrong in the same direction, and both under-counted:
FINDINGS.md said "three query lines were dropped", probe.sh's comment said
"four ... three of them have no ledger row at all", and the truth is FIVE across
FIVE files. Under-counting silently-lost cells is the unsafe direction: a cell
that never ran reads as a cell that ran and found nothing, which is exactly the
failure this whole area was opened to correct.

THE COMPARISON
--------------
For every `queries-*.txt` in this directory: take each line that looks like a
query (matches `^<tag>|<role>|<host>|<path>`), and check whether `<tag>` appears
as `host_tag` in `results.jsonl`. A tag with no row was never sent.

It reads ONLY committed files, so it reproduces from a clean clone.

CAVEAT THIS SCRIPT CANNOT FIX — and it is the reason two of the five are
invisible in the committed files
--------------------------------------------------------
The trailing-newline defect is *repaired* in the committed query files (the
newline was appended, and the loop was guarded). A reader of the committed
files therefore cannot see that those files once lacked a newline. What
survives in the committed record is the ledger, which shows the run stopping
short. `run.log` is the evidence: the last request each file dispatched is one
line short of the line count in the file. `--verbose` prints that per file.

Exit 0 always. This reports; it does not gate.
"""
from __future__ import annotations

import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
QUERY = re.compile(r"^([A-Za-z0-9_.-]+)\|[^|]*\|[^|]*\|[^|]*\|")


def sent_tags() -> set[str]:
    return {json.loads(l)["host_tag"]
            for l in open(os.path.join(HERE, "results.jsonl"), encoding="utf-8")}


def main() -> int:
    verbose = "--verbose" in sys.argv
    sent = sent_tags()
    total_lines = 0
    never: list[tuple[str, str]] = []
    print(f"committed query lines vs ledger tags "
          f"({len(sent)} tags in results.jsonl)\n")
    for f in sorted(glob.glob(os.path.join(HERE, "queries-*.txt"))):
        name = os.path.basename(f)
        raw = open(f, encoding="utf-8").read()
        lines = [l for l in raw.split("\n") if QUERY.match(l)]
        total_lines += len(lines)
        missing = [QUERY.match(l).group(1) for l in lines
                   if QUERY.match(l).group(1) not in sent]
        never += [(name, t) for t in missing]
        mark = "  <-- SHORT" if missing else ""
        print(f"  {name:<42} {len(lines):>2} query lines, "
              f"{len(missing)} never sent{mark}")
        if verbose:
            print(f"      ends with newline: {raw.endswith(chr(10))}")
            for t in missing:
                print(f"      NEVER SENT: {t}")
    print(f"\n  TOTAL {total_lines} committed query lines, "
          f"{len(sent)} ledger rows, {len(never)} query lines never sent:")
    for name, t in never:
        print(f"    {t}   ({name})")
    print("\n  A 'never sent' line is a cell that produced NO evidence. It is not")
    print("  an absence, and nothing in FINDINGS.md may rest on one.")
    return 0


if __name__ == "__main__":
    sys.exit(main())