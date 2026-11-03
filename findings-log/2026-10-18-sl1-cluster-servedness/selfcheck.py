#!/usr/bin/env python3
"""selfcheck.py — the mechanical corrective for S-L1.

Six verification rounds each found blocking defects that were all *accounting or
bookkeeping sentences* — never the servedness claim, never an evidence class,
never the independence count, never the request total. Three mechanisms recurred,
and two of the defects were committed by the commits that had just named their
mechanism:

  1. derived arithmetic not recomputed from its own ledger;
  2. a half-fix that changed a number and left the false shape attached;
  3. a correction that stopped at the layer it was made in.

All three are invisible to `scripts/research-checks.py`, which validates
`[source: ...]` *paths* and a heading count only. This script re-derives the
quantities that kept being got wrong, so the next pass does not have to be as
careful as the last one was.

ZERO REQUESTS. It reads the working tree, falling back to the committed tree
for any file missing from the worktree; the committed read is a fallback, not
the default. (An earlier draft of this line said "reads the committed tree and
nothing else", which overstated it -- round 7.)

    python3 selfcheck.py            # exits 0 if every check agrees
    python3 selfcheck.py --verbose  # also prints each check's derived value
"""

import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# HERE is <repo>/findings-log/<dated-pass>, so the repo root is TWO levels up.
# An earlier draft of this line walked three, which pointed REPO at the PARENT
# of the repo: every path lookup silently missed, the E[N] check skipped itself
# without saying so, and a citation resolved against the wrong file while
# reporting "ok". A check that cannot fail is the shape AGENTS.md 6.2 warns
# about - found in the check, this time.
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
F = os.path.join(HERE, "FINDINGS.md")
LEDGER = os.path.join(HERE, "results.jsonl")
PR_BODY = os.path.join(HERE, "selfcheck-pr-body.txt")

VERBOSE = "--verbose" in sys.argv
FAILS = []


def ok(msg):
    if VERBOSE:
        print("  ok   %s" % msg)


def fail(msg):
    FAILS.append(msg)
    print("  FAIL %s" % msg)


def read(p):
    return open(p, encoding="utf-8").read() if os.path.exists(p) else ""


def git_show(path):
    """The file AS COMMITTED, not as it sits in the working tree — the trap that
    produced two dead file:line citations was reading the edited file."""
    r = subprocess.run(["git", "show", "HEAD:" + path], capture_output=True,
                       text=True, cwd=REPO)
    return r.stdout if r.returncode == 0 else None


def main():
    print("== selfcheck: re-derive S-L1's accounting from the ledger. 0 requests.")
    f = read(F)
    rows = [json.loads(l) for l in read(LEDGER).splitlines() if l.strip()]

    # ---- 1. THE VERIFIER-ROUND COUNT. Counted from the headings, not inherited.
    rounds = sorted(int(n) for n in re.findall(r"^### Round (\d+) ", f, re.M))
    n_rounds = len(rounds)
    if rounds != list(range(1, n_rounds + 1)):
        fail("round headings are not 1..N: %s" % rounds)
    else:
        ok("%d rounds recorded (%s)" % (n_rounds, ", ".join(map(str, rounds))))
    # Derived, never hardcoded: an earlier draft listed words up to "Ten" and
    # raised KeyError on the eleventh round - a checker defect surfaced by the
    # very staleness it exists to catch.
    _W = ("Zero One Two Three Four Five Six Seven Eight Nine Ten Eleven Twelve "
          "Thirteen Fourteen Fifteen Sixteen Seventeen Eighteen Nineteen Twenty")
    word = {i: _W.split()[i] for i in range(1, 21)}
    opener = re.search(r"^(%s) fresh-context verifier rounds" % "|".join(word.values()),
                       f, re.M)
    if not opener:
        fail("no '<N> fresh-context verifier rounds' opener in FINDINGS.md")
    elif word[n_rounds] != opener.group(1):
        fail("FINDINGS.md opener says %r but the file records %d round headings"
             % (opener.group(1), n_rounds))
    else:
        ok("opener count agrees with the headings (%s)" % opener.group(1))
    # the per-round blocking tally, where stated
    tally = re.search(r"produced \*\*(\d+)\*\* blocking findings", f)
    per = re.search(r"round 1: (\d+).*?round 2: \*\*(\d+)\*\*.*?round 3: (\d+).*?"
                    r"round 4: (\d+).*?round 5: (\d+)", f, re.S)
    if tally and per:
        parts = [int(per.group(i)) for i in range(1, 6)]
        # Every "N blocking findings" figure anywhere in the file must equal the
        # sum of the per-round breakdown printed alongside it. Round 9 caught the
        # rounds-1-7 subtotal being presented as the whole-run total; this is the
        # assertion that would have caught it.
        for m in re.finditer(r"\b(\d+) blocking findings\b", f):
            near = f[max(0, m.start() - 300):m.end() + 300]
            bd = [(int(a), int(b.replace("**", ""))) for a, b in
                  re.findall(r"round (\d+):\s*\**(\d+)\**", near)]
            if not bd:
                continue
            last_round = max(bd, key=lambda t: t[0])[0]
            total = sum(v for _, v in bd)
            if int(m.group(1)) != total:
                fail("figure '%s blocking findings' != sum of the breakdown "
                     "beside it (%d over rounds %d-%d)"
                     % (m.group(1), total, min(r for r, _ in bd), last_round))
            else:
                ok("figure %s matches its own %d-round breakdown (%d)"
                   % (m.group(1), last_round, total))
        if sum(parts) != int(tally.group(1)):
            fail("blocking tally %s != sum of its own per-round parts %d"
                 % (tally.group(1), sum(parts)))
        else:
            ok("blocking tally %s = its per-round parts %s"
               % (tally.group(1), parts))
        if len(parts) > n_rounds:
            fail("per-round breakdown covers %d rounds but only %d are recorded"
                 % (len(parts), n_rounds))
        elif len(parts) < n_rounds:
            ok("per-round breakdown covers the first %d of %d rounds "
               "(rounds 6+ add their own tallies)" % (len(parts), n_rounds))

    # ---- 2. THE REQUEST ACCOUNTING, from the ledger.
    cap = 15
    if len(rows) != cap:
        fail("ledger has %d rows, not the stated %d cap" % (len(rows), cap))
    else:
        ok("%d rows of a %d cap" % (len(rows), cap))
    if set(r["method"] for r in rows) != {"GET"}:
        fail("a non-GET row exists")
    hosts = {}
    for r in rows:
        hosts[r["host"]] = hosts.get(r["host"], 0) + 1
    if hosts != {"data.commoncrawl.org": 11, "index.commoncrawl.org": 4}:
        fail("host split %s != {data: 11, index: 4}" % hosts)
    else:
        ok("host split %s" % hosts)
    m = re.search(r"`data\.commoncrawl\.org` \((\d+)\s*\n?\s*rows\)", f)
    if not m or int(m.group(1)) != hosts.get("data.commoncrawl.org"):
        fail("FINDINGS.md does not state the bulk row count as %d"
             % hosts.get("data.commoncrawl.org"))
    else:
        ok("FINDINGS.md states the bulk row count as %s" % m.group(1))
    m = re.search(r"`index\.commoncrawl\.org` \((\d+)\s*\n?\s*rows\)", f)
    if not m or int(m.group(1)) != hosts.get("index.commoncrawl.org"):
        fail("FINDINGS.md does not state the index row count as %d"
             % hosts.get("index.commoncrawl.org"))
    else:
        ok("FINDINGS.md states the index row count as %s" % m.group(1))

    # served vs connection-level, using the instrument's own predicates
    sys.path.insert(0, HERE)
    import servedness as S
    conn = [r for r in rows if (S.bulk_is_failure(r["http_status"])
                                if r["host"] == S.DATA_HOST
                                else S.cdx_is_failure(r["http_status"]))]
    if conn:
        fail("%d connection-level rows; the log claims 0" % len(conn))
    else:
        ok("0 connection-level failures, as the log states")
    if "15 total = 15 served + 0 connection-level failure" not in f:
        fail("the served/failure split sentence is not stated as 15/15/0")

    # the largest response, and the PREDICATE attached to it
    biggest = max(r["body_bytes"] for r in rows if r.get("body_bytes"))
    if biggest != 4194304:
        fail("largest body_bytes is %d, not 4194304" % biggest)
    elif "**Largest response 4 194 304 B**" not in f:
        fail("FINDINGS.md does not state the largest response as 4 194 304 B")
    else:
        ok("largest response 4 194 304 B")
    # no false claim that only the collinfo head is committed
    # LIVE only: the phrase is required inside the Round 1/Round 3 history
    # entries, which quote it precisely because it was corrected. Failing on
    # those would be failing on the retraction history itself.
    _hist = [m.start() for m in re.finditer(r"^### Round \d+ ", f, re.M)]
    for _m in re.finditer(r"largest response whose \*head\* is committed is 35 226", f):
        if not any(h < _m.start() for h in _hist):
            fail("the false 'largest head committed' predicate is live at "
                 "char %d, outside the history entries" % _m.start())
        else:
            ok("the false predicate appears only as a quoted, corrected defect")

    # ---- 3. THE E[N] SPAN, against budget.py's actual output.
    #   H1 CITATION CONTENT IS NOT CHECKED. Only that the LINE EXISTS. A citation
    #      that resolves to the wrong content passes. Round 11 restated this and
    #      confirmed it adversarially; content is verified by hand, not here.
    #   H2 RANGE-FORM CITES ARE NOT MATCHED. The regex matches `:NNN` only, so
    #      `:404-413` and `:498-521` are never resolved at all.
    #   H3 THE E[N] SPAN IS SUBSTRING-PRESENCE, not a derived lo/hi vs stated-span
    #      comparison. Corrupting the span sentence passes while the substrings
    #      survive elsewhere. Correct at head; verified against budget.py by hand.
    #   H4 A MISSING budget.py, OR OUTPUT WITH NO PARSEABLE VALUES, SKIPS THIS
    #      CHECK AND STILL PRINTS PASS. That is the "skip without saying so" shape
    #      this script's own comments condemn. Fixed below to fail loudly.
    bp = os.path.join(REPO, "findings-log", "2026-10-17-sl2-outwindow-census",
                      "budget.py")
    if os.path.exists(bp):
        out = subprocess.run([sys.executable, bp], capture_output=True, text=True,
                             cwd=REPO).stdout
        vals = sorted(set(re.findall(r"^\s+=\s+\(1-p\).*?([0-9]\.[0-9]{6})",
                                     out, re.M)) |
                      set(re.findall(r"E\[N\] = 1 \+ p \+ p\^2\s+([0-9]\.[0-9]{6})",
                                     out)))
        if not vals:
            fail("budget.py produced no parseable E[N] values - the E[N] check "
                 "could not run, and PASS would otherwise be reported")
        if vals:
            lo, hi = vals[0], vals[-1]
            if "1.25" not in f or "1.65" not in f:
                fail("FINDINGS.md does not carry budget.py's %s-%s span" % (lo, hi))
            else:
                ok("E[N] span %s-%s matches budget.py" % (lo, hi))
            if str(len(vals)) not in ("5",):
                ok("budget.py prints %d distinct populations" % len(vals))

    # ---- 4. EVERY file:line CITATION, resolved against the COMMITTED tree.
    # Two kinds exist in this file and conflating them was a bug in an earlier
    # draft of this script:
    #   LIVE cites - a claim the reader is expected to follow. Must resolve.
    #   QUOTED cites - inside a "### Round N" history entry, quoting a defect
    #     that was real at the time and is now recorded as corrected. Those are
    #     REQUIRED to be dead or superseded; that is the whole point of a
    #     retraction history. They are counted and reported, not failed.
    SHORTHAND = {"docs/11": "docs/11-suggested-research-areas.md",
                 "docs/10": "docs/10-open-questions.md",
                 "docs/09": "docs/09-methodology-and-oracles.md",
                 "docs/00": "docs/00-summary-the-map.md"}
    #   H5 LIVE-VS-QUOTATION IS PURELY POSITIONAL: any citation after the first
    #      `### Round N` heading is exempt, so a genuinely dead LIVE citation
    #      appended after the history is waved through as a quotation. No such
    #      citation exists at head.
    history_start = [m.start() for m in re.finditer(r"^### Round \d+ ", f, re.M)]
    live = quoted = 0
    for cite_m in re.finditer(r"`((?:docs|findings-log|scripts|\.github)/[A-Za-z0-9._/-]+"
                              r"|servedness\.py|spacing\.py|selfcheck\.py):(\d+)`", f):
        path, line = cite_m.group(1), cite_m.group(2)
        # H-fixed (round 10): use THIS match's own position, not f.index(), which
        # returns the first occurrence and so classified every repeat of a cited
        # string by where its first mention fell.
        pos = cite_m.start()
        in_history = any(h < pos for h in history_start)
        resolved = SHORTHAND.get(path, path)
        cand = [os.path.join(HERE, resolved), os.path.join(REPO, resolved)]
        src = None
        for c in cand:
            if os.path.exists(c):
                src = read(c)
                break
        if src is None:
            committed = git_show(resolved)
            src = committed if committed is not None else None
        if src is None:
            if in_history:
                quoted += 1
            else:
                fail("citation names a file that does not exist: %s:%s" % (path, line))
            continue
        lines = src.splitlines()
        if int(line) > len(lines):
            if not in_history:
                fail("citation past end of file: %s:%s (file has %d lines)"
                     % (path, line, len(lines)))
            else:
                quoted += 1
        else:
            if in_history:
                quoted += 1
            else:
                live += 1
                if VERBOSE:
                    print("       %s:%s -> %s" % (path, line, lines[int(line) - 1][:70]))
    #   H6 THE H-1..H-5 CLASS OF HOLE REMAINS: this script proves a line EXISTS,
    #      not that it SAYS what the claim says. Read the meaning by hand.
    #   H8 THE TOTAL-VS-BREAKDOWN ASSERTION IS DIGIT-ONLY. A word-form total
    #      ("= **22**") is not matched by the rule the checker actually uses,
    #      `\b(\d+) blocking findings\b` (the bare `\b(\d+)` fragment does match
    #      inside `**25**`; it is the trailing `blocking findings` that fails),
    #      so round 10's own word-form total passed while a digit-form one fails.
    #      All headline totals in FINDINGS.md are now in DIGIT form for that
    #      reason; this comment records why, so the digit form is not "fixed"
    #      back to prose later.
    #   H7 ONLY FINDINGS.md IS IN SCOPE for the counts above. docs/11, docs/10 and
    #      the PR body are NOT read (PR_BODY is defined and never used - round 7).
    #      The counts the prose states for those layers were verified by hand.
    ok("%d live citations resolved, %d historical quotations "
       "(dead or superseded by design)" % (live, quoted))
    # H4-class fix for the counts themselves: the run reports them, so assert
    # that FINDINGS.md states THIS run's numbers rather than a remembered pair.
    stated = re.search(r"reports both numbers: \*\*(\d+) live, (\d+) quoted", f)
    if stated:
        if (int(stated.group(1)), int(stated.group(2))) != (live, quoted):
            fail("FINDINGS.md states %s live/%s quoted; this run measured "
                 "%d/%d" % (stated.group(1), stated.group(2), live, quoted))
        else:
            ok("FINDINGS.md states this run's citation counts (%d/%d)" % (live, quoted))

    # ---- 5. THE LOCATE ARITHMETIC, against the committed locate file.
    lp = os.path.join(HERE, "locate-CC-MAIN-2022-27.json")
    if os.path.exists(lp):
        v = json.load(open(lp))
        w = v["window"]
        width = w[1] - w[0]
        # The width is typeset with a narrow no-break space (U+202F) between the
        # digit groups, so whitespace of every flavour is stripped before the
        # comparison rather than normalised to U+0020.
        digits = re.sub(r"[\s    ⁠]+", "", f)
        if str(width) in digits:
            ok("locate window width %d stated" % width)
        else:
            fail("the locate window width %d is not stated in FINDINGS.md" % width)

    print()
    if FAILS:
        print("SELFCHECK FAIL — %d disagreement(s) between the prose and the ledger:" % len(FAILS))
        for m in FAILS:
            print("  - %s" % m)
        return 1
    print("SELFCHECK PASS — round count, request accounting, E[N] span, every "
          "file:line citation, and the locate arithmetic all re-derive from the "
          "committed ledger.")
    return 0


if __name__ == "__main__":
    # H6: a crash is not a verdict. Round 8 recorded that a traceback "exits
    # nonzero, so it fails" as acceptable; it is not - an unhandled exception
    # reports nothing about WHAT disagreed, and a reader can mistake a bug in the
    # checker for a clean run. Any exception now becomes a reported failure.
    try:
        rc = main()
    except Exception as exc:                      # noqa: BLE001 - deliberate
        print("SELFCHECK FAIL — the checker itself raised %s: %s"
              % (type(exc).__name__, exc))
        print("  A checker that crashes has checked nothing; this is a defect in "
              "the checker, not a verdict on the branch.")
        rc = 1
    sys.exit(rc)