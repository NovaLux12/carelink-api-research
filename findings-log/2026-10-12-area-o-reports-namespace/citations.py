#!/usr/bin/env python3
"""citations.py — check every citation in this log, because the PR gate cannot.

Issues no requests, touches no network, and reads only committed files.

WHY THIS EXISTS
---------------
`scripts/research-gate.sh`'s citation check is a **path-existence test over three
page locations**: it opens `docs/*.md`, `README.md` and `AGENTS.md` and looks for
`findings-log/….md` and `recon/….md` strings. Consequences, each confirmed by
running its own two regexes (see FINDINGS.md section 9):

  * `findings-log/**` is read only as the set of *valid targets*; a findings-log
    file is never scanned *as a citation source*, so citations written inside one
    are out of scope entirely;
  * the `findings-log/….md` regex stops at `.md`, so a `:NN` suffix falls outside
    the match and line numbers can never be validated;
  * there is no `docs/…` pattern, so a `docs/NN` citation is invisible to it;
  * the `recon/…` regex carries a `(?<![\\w./-])` lookbehind and `/` is in that
    class, so a relative link `](../probe-2026-10-08/recon/X.md)` can never match.

It found two real errors in this pass and would have found neither.

WHAT IT CHECKS
--------------
  1. every relative markdown link in this file resolves on disk;
  2. every line-numbered citation (`file:NN`, `file:NN,NN`, `file:NN-MM`)
     resolves, is in range, and lands on a non-empty line — and it PRINTS that
     line, so the reader can confirm it says what the sentence claims rather
     than merely that something is there.

SELF-TEST
---------
`--selftest` plants a citation that is off by one line and a link to a file that
does not exist, and asserts both are reported. A checker that has never been seen
to fail is not evidence.

    python3 citations.py            # the report
    python3 citations.py --selftest # prove the net can fire
"""
import os
import re
import sys

LOG = "FINDINGS.md"
HERE = os.path.dirname(os.path.abspath(__file__))
# Repo-relative, never absolute: an absolute path here would print this machine's
# home directory into a committed artefact and trip the gate's
# `machine-specific paths` scrub pattern.
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))

# markdown link whose text carries `:NN` / `:NN,NN` / `:NN-MM`
LINK_WITH_LINES = re.compile(r'\[`?([^`\]]*?)`?\]\((\.\.[^)]+)\)')
ANY_REL_LINK = re.compile(r'\]\((\.{1,2}/[^)]+)\)')
# Fenced blocks and inline code spans are prose about links, not links. Matching
# inside them produced a false positive on this file's own explanation of the
# lookbehind, which quotes `](../probe-2026-10-08/recon/X.md)` as an example.
FENCED = re.compile(r"```.*?```", re.S)
INLINE_CODE = re.compile(r"`[^`\n]*`")


def strip_nonlinks(text):
    """Blank out fenced blocks and inline code, preserving offsets."""
    def blank(m):
        return re.sub(r"[^\n]", " ", m.group(0))
    return INLINE_CODE.sub(blank, FENCED.sub(blank, text))


def rel(path):
    """Repo-relative display path, so nothing machine-specific is ever printed."""
    try:
        r = os.path.relpath(path, REPO_ROOT)
    except ValueError:
        r = os.path.basename(path)
    return r if not r.startswith("..") else os.path.basename(path)


def cell(text, width=88):
    """Escape pipes so a cited line cannot break the markdown table."""
    t = (text or "").replace("|", "\\|")
    return t[:width]


def check(text, base):
    broken, resolved = [], []

    # Pass 1 — bare relative links. Runs on code-stripped text, because this
    # file quotes a relative link inside backticks as an *example* of one the
    # gate cannot match; matching that would be a false positive.
    for m in ANY_REL_LINK.finditer(strip_nonlinks(text)):
        target = m.group(1)
        real = os.path.normpath(os.path.join(base, target))
        if not os.path.exists(real):
            broken.append(("relative link", target, "does not resolve"))
        else:
            resolved.append((rel(real), None))

    # Pass 2 — line-numbered citations. Runs on the RAW text, deliberately:
    # citation labels are conventionally written in backticks, so stripping code
    # spans here would silently disable the most valuable check in the file.
    seen = set()
    for m in LINK_WITH_LINES.finditer(text):
        label, target = m.group(1), m.group(2)
        nums = re.search(r":(\d+)(?:-(\d+))?(?:,(\d+))?", label)
        if not nums:
            continue
        wanted = [int(x) for x in nums.groups() if x]
        real = os.path.normpath(os.path.join(base, target))
        if not os.path.exists(real):
            broken.append((label, rel(target), "target file missing"))
            continue
        lines = open(real, encoding="utf-8", errors="replace").read().splitlines()
        for n in wanted:
            key = (real, n)
            if key in seen:
                continue
            seen.add(key)
            if n < 1 or n > len(lines):
                broken.append((label, rel(real), f"line {n} out of range ({len(lines)} lines)"))
            elif not lines[n - 1].strip():
                broken.append((label, rel(real), f"line {n} is blank"))
            else:
                resolved.append((f"{rel(real)}:{n}", lines[n - 1].strip()))
    return broken, resolved


def main():
    if "--selftest" in sys.argv:
        # Planted: a link to nowhere, an out-of-range line, and a blank line.
        fake = ("[a](../../nowhere/missing.md) and [b:2](../../AGENTS.md)\n"
                "[c:99999](../../AGENTS.md) and [d:3](../../AGENTS.md)\n")
        broken, _ = check(fake, HERE)
        got = sorted(x[2].split(" (")[0] for x in broken)
        want = sorted(["does not resolve", "line 2 is blank", "line 99999 out of range"])
        ok = got == want
        print(f"selftest: {len(broken)} planted defects, want {len(want)}")
        for g in got:
            print(f"  caught: {g}")
        print("selftest:", "PASS — the checker can fail" if ok else "FAIL — checker is blind")
        return 0 if ok else 1

    text = open(LOG, encoding="utf-8").read()
    broken, resolved = check(text, HERE)

    print(f"## Citation and link report — {LOG}\n")
    print(f"- relative links + line-numbered citations resolved: **{len(resolved)}**")
    print(f"- broken: **{len(broken)}**\n")
    if resolved:
        print("| citation | target line |")
        print("|---|---|")
        for ref, line in sorted(resolved):
            print(f"| `{ref}` | {cell(line)} |")
        print()
    if broken:
        print("| citation | target | problem |")
        print("|---|---|---|")
        for label, target, why in broken:
            print(f"| `{label}` | `{target}` | **{why}** |")
        print()
    print("No requests were issued. Run `python3 citations.py --selftest` to confirm")
    print("this checker can fail before trusting a zero here.")
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())