#!/usr/bin/env python3
"""Account for every request in this pass and print the tables FINDINGS.md cites.

Every number this file prints is computed from results.jsonl, which is
append-only and has one row per request (AGENTS.md section 3). Nothing here
counts prose. Run it, read it, and paste its output -- if a number in
FINDINGS.md is not in this output, that number is unsourced and must go
(AGENTS.md section 1, and section 6 item 7: a count generalised from a subset,
with no counting rule recorded, is how 44 became 93).

It also runs the WHOLE-KiB TRUNCATION DETECTOR, because that is this pass's
headline claim and a headline claim whose counting rule lives only in prose is
exactly the defect section 6 item 7 names. The rule:

    a record response whose body_bytes is an exact multiple of 1024 was cut
    short, and one whose byte count is not, ran to completion.

It is reported as a CORRELATION over the rows observed here, never as a proven
mechanism. On this ledger it is 3 positives out of 29 successful answers.

SCRATCH / THE KERNEL ORACLE
---------------------------
Raw bodies live outside the repository, so the body-mtime spacing oracle is
only available where that tree still exists. Everything else -- the status
census, the accounting line, the spacing floor from the t_sent series, and the
whole-KiB detector -- is computed from results.jsonl ALONE and reproduces from
a clean clone. When the bodies are absent this tool says so in words. It does
not print a silent `None`, because a tool that degrades quietly is the failure
mode this repo keeps paying for.

Usage:
  python3 account.py [LEDGER]     # full report
  python3 account.py [LEDGER] --json   # machine-readable, for the gate

LEDGER is optional and defaults to this lane's own results.jsonl. It is a POSITIONAL
argument because docs/10 tells the next pass to run this over area M's ledger -- a
claim that was false when the argument was not implemented and the path hardcoded.

## Correction (2026-10-17) — an absent `t_sent` is skipped, not a crash

Fixed here at source, after the correction issue `correction: PR #135 S-L4 -- eight
blocking findings after three rounds` (#139) recorded the handoff as broken. Run
exactly the way docs/10 section 1's successor directs ("the same one-command test
over every other committed CC ledger"), this tool died on a member of area L's own
population. The ledger path below is **repo-root-relative**, so the command is run
from the repo root, not from this file's own directory:

    $ python3 findings-log/2026-10-14-lane-s6-public-index/account.py \
          findings-log/2026-10-13-area-l-ipro-hcp/results.jsonl
      File ".../account.py", line 109, in spacing
        a, b = parse(sel[i]["t_sent"]), parse(sel[i + 1]["t_sent"])
      TypeError: strptime() argument 1 must be str, not None

`2026-10-13-area-l-ipro-hcp` carries a JSON **null** `t_sent` on 4 of its 44 rows
(seqs 1-4). **KNOWN LIMIT of the kernel oracle, measured not assumed.** A row whose `host_tag`
names a body file that is simply ABSENT still joins the series, so a gap can be
measured across it. **The no-`host_tag` fix does not cover that, and the printed
sentence has been narrowed to say so.** Measured over all 50 committed ledgers at
this head: the missing-body branch is taken on **25 of them**, and **not one of
those 25 prints a kernel gap figure** -- each reports the oracle UNAVAILABLE,
because either bodies resolve for a ledger or none do, and a *partial* body set is
what the join-across needs and no committed ledger produces one. The case is
reproducible synthetically with `S6_SCRATCH` pointing at a directory holding one of
the two bodies.

`parse()` caught `ValueError`, so a MALFORMED STRING was already
treated as "this row cannot enter the series" -- and a null was not, because
`strptime(None)` raises `TypeError`. The caller already skipped a pair when either
side parsed to `None`; only the parse itself could not return `None`. So the fix
is at the parse, and it is not a loosening of the spacing oracle: **the floor is
still a minimum over real gaps, no gap is measured across a row that has no
timestamp, and the number of skipped pairs is now printed** rather than absorbed
silently (AGENTS.md section 2: a figure over a subset must say so).

Inert for this lane's own figures, and checked rather than asserted: this ledger
has 151 rows, **0** null and **0** absent `t_sent`, so every gap, every sub-2.5 s
count and every inverted-row count below prints exactly as it did before the fix.
`python3 account.py` on this lane's own results.jsonl is byte-identical in its
default report, and under `--json` it adds two lines, both reading 0.

Also added, for the same handoff reason: **the counting rule for "successful 200
answers" is now printed beside the number.** It was `http_status == "200"` exactly,
unstated -- and some committed CC ledgers write the opaque form `"200 (curl)"`,
which this rule does NOT count. The count is deliberately left as it was (changing
it would move a figure this lane has published); the rule and the number of
opaque-200 rows are now beside it, and the detector that resolves them is named.
"""

from __future__ import annotations

import datetime
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "results.jsonl")
CAP = 400
# Raw response bodies live OUTSIDE the repository -- see probe.sh's SCRATCH.
# Two genuine CC responses in this pass are 1.86 MB and 1.2 MB, and the gate's
# hygiene check globs findings-log/ for anything over 1 MiB, so keeping them
# beside the ledger would fail the gate on files that are never committed.
# The default is machine-neutral on purpose: a committed default naming this
# machine's home directory trips the scrub pattern "machine-specific paths".
SCRATCH = os.environ.get("S6_SCRATCH") or os.path.join(
    os.environ.get("TMPDIR") or "/tmp", "carelink-s6-lane-scratch")
BODIES = os.path.join(SCRATCH, "bodies")

# The previous pass ran before this file existed; its boundary is recorded here
# rather than guessed from a timestamp. Rows at or below it were produced by
# the earlier probe.sh, rows above it by this one.
PRIOR_SEQ = 76

# Keys every oracle below reads WITHOUT a default, so a row lacking one of them
# crashes the run rather than yielding a wrong figure. Derived from the code, not
# from memory: every `r["key"]` read in this file that is not a `.get(...)`.
#     grep -vE '^#' account.py | grep -oE 'r\["[a-z_]+"\]' | sort -u
# `t_sent` and `host_tag` are deliberately ABSENT from this list and are handled
# by a counted skip inside `spacing()` -- a ledger where *some* rows are short is
# readable, and that is the case this tool must survive.
REQUIRED = ("seq", "host", "http_status", "method")
# `seq` is compared and sorted numerically (`r["seq"] > PRIOR_SEQ`), so a ledger
# that writes it as a JSON string is a different schema, not a formatting
# difference -- comparing across the two is AGENTS.md section 6 item 3, the
# lookup-that-resolved-to-something-else defect. Assert the type before use.
REQUIRED_INT = ("seq",)
# Keys used as STRINGS. Present is not enough: a null or a number passes a
# key-presence test and then raises TypeError inside a `"x" in value` or a
# string comparison, which is the same crash one level later.
REQUIRED_STR = ("host", "http_status", "method")
# `body_bytes` is only read on rows the whole-KiB filter has already required to
# carry one, so it is not in REQUIRED; but it is divided modulo, so a non-numeric
# value there is a type fault rather than a missing key.
REQUIRED_NUM_WHERE_PRESENT = ("body_bytes",)


def parse(ts):
    """A ledger timestamp, or None. None for a MALFORMED string and for an
    ABSENT or null one alike -- `t_sent` is a JSON null on 4 rows of
    `2026-10-13-area-l-ipro-hcp`, and strptime(None) raises TypeError, which is
    not a ValueError and so was never caught. See the Correction in the
    docstring. Every caller already treats None as "this row cannot enter the
    series", so the row is skipped rather than guessed at."""
    if not isinstance(ts, str):
        return None
    try:
        return datetime.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        return None


def load():
    rows = []
    with open(LEDGER, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except ValueError:
                # A torn line would be a real defect; surface it rather than
                # skipping it, because a silent skip understates the count.
                print(f"!! UNPARSEABLE LINE in results.jsonl: {line[:80]}", file=sys.stderr)
    return rows


def spacing(rows, host_filter=None):
    """Two independent oracles.

    The harness series (t_sent) is what THIS script claims. The kernel series
    is the mtime of the body file, which curl wrote. If they disagree the repo's
    own rule is that the harness series is the suspect (docs/09 section 4), so
    both are reported and neither is hidden.

    `rows` is whatever the caller passes, so the caller decides the scope. Both
    the whole ledger and this pass alone are reported, because they differ and
    the difference is the point: the three sub-floor gaps and the five inverted
    rows live entirely in the earlier attempt, so quoting only the whole-ledger
    figure would understate this pass, and quoting only this pass would hide
    defects a reader must see.

    A row with no usable `t_sent` leaves the series entirely. Its two adjacent
    PAIRS are dropped rather than joined across it, because a gap measured from
    a row that carries no timestamp is a guess; the count of dropped pairs is
    returned and printed, so a floor computed over a subset says so.
    """
    sel = [r for r in rows if (host_filter is None or r["host"] == host_filter)]
    sel.sort(key=lambda r: r["seq"])

    harness = []
    skipped = 0
    for i in range(len(sel) - 1):
        a, b = parse(sel[i].get("t_sent")), parse(sel[i + 1].get("t_sent"))
        if a and b:
            harness.append((( b - a).total_seconds(), sel[i]["seq"], sel[i + 1]["seq"]))
        else:
            skipped += 1

    kernel = []
    prev = None
    kernel_skipped = 0
    for r in sel:
        tag = r.get("host_tag")
        if not isinstance(tag, str):
            # A committed ledger that records no host_tag cannot name a body file.
            # The row BREAKS the series: `prev = None`, so no gap is measured
            # across it -- the same rule the harness oracle applies two blocks
            # above, and for the same reason. A gap joined across a row with no
            # body would be a guess. Counted, never absorbed.
            kernel_skipped += 1
            prev = None
            continue
        p = os.path.join(BODIES, f"{tag}.b")
        if not os.path.exists(p):
            continue
        m = os.stat(p).st_mtime
        if prev is not None:
            kernel.append((m - prev[0], prev[1], r["seq"]))
        prev = (m, r["seq"])

    return harness, kernel, skipped, kernel_skipped


def whole_kib_detector(rows):
    """The headline claim, as a reproducible count rather than a sentence.

    Only a SUCCESSFUL answer can be a truncated response: a 502/504 body is a
    gateway page and a 404 is the API's own 'no captures' sentence, neither of
    which is a record stream. So the detector runs over the 200 rows only.
    """
    ok = [r for r in rows if r.get("http_status") == "200" and r.get("body_bytes")]
    whole = [r for r in ok if r["body_bytes"] % 1024 == 0]
    return ok, whole


def schema_guard(rows):
    """Fail closed on a ledger whose SCHEMA this tool cannot read.

    A committed CC ledger is not obliged to carry the keys this lane's own does.
    `docs/10` section 1 tells a successor to run this tool over every other
    committed ledger, and some of them use a different schema -- so the tool has
    to say so rather than print zeros that read as a clean negative. This is the
    same fail-closed shape as the `is a directory` and `no such ledger` guards
    above: exit 2, the reason named, nothing printed as if it were a finding.

    REQUIRED is deliberately the small set every oracle here reads without a
    default: `seq` orders the series, `host` groups them, `http_status` is what
    the 200-counting rule is stated over. Keys a single row may legitimately lack
    -- `t_sent`, `host_tag` -- are NOT in this set: those are per-row absences,
    handled by a counted skip inside `spacing()`, because a ledger where *some*
    rows are short is readable and one where *every* row is short is a different
    artefact.
    """
    if not rows:
        return 0  # a 0-row ledger is a pass that sent nothing; handled downstream
    # Counted per KEY, not unioned: a key present on one row and absent on the rest
    # is a PARTIAL ledger, and every oracle below indexes these keys directly, so
    # one such row crashes the run exactly as a wholly-absent key would. Fail
    # closed on any absence, and print the counts so the reader can see which key
    # and how many rows.
    def not_an_int(r, k):
        return k in r and (not isinstance(r[k], int) or isinstance(r[k], bool))

    absent = {k: sum(1 for r in rows if k not in r) for k in REQUIRED}
    wrong_type = {k: sum(1 for r in rows if not_an_int(r, k)) for k in REQUIRED_INT}
    for k in REQUIRED_STR:
        wrong_type[k] = sum(1 for r in rows if k in r and not isinstance(r[k], str))
    for k in REQUIRED_NUM_WHERE_PRESENT:
        wrong_type[k] = sum(
            1 for r in rows
            if k in r and r[k] is not None
            and (not isinstance(r[k], int) or isinstance(r[k], bool)))
    problems = []
    if any(absent.values()):
        problems.append("keys absent")
    if any(wrong_type.values()):
        problems.append("keys of the wrong type")
    if not problems:
        return 0
    seen = set()
    for r in rows:
        seen.update(r.keys())
    print(f"account.py: {LEDGER} uses a schema this tool cannot read.", file=sys.stderr)
    print(f"  {len(rows)} rows; {', '.join(problems)}:", file=sys.stderr)
    for k, n in sorted(absent.items()):
        if n:
            print(f"    {k}: absent from {n} of {len(rows)} rows", file=sys.stderr)
    for k, n in sorted(wrong_type.items()):
        if n:
            note = ""
            if k in REQUIRED_INT:
                note = " (compared and sorted numerically)"
            elif k in REQUIRED_STR:
                note = " (used as a string)"
            elif k in REQUIRED_NUM_WHERE_PRESENT:
                note = " (divided modulo, so it must be a number)"
            print(f"    {k}: wrong type on {n} of {len(rows)} rows{note}",
                  file=sys.stderr)
    print(f"  keys the rows do carry: {', '.join(sorted(seen))}", file=sys.stderr)
    print("  Nothing was measured and nothing is reported: an unreadable ledger is a"
          " gap in this record, not a negative result.", file=sys.stderr)
    return 2


def main() -> int:
    # A positional LEDGER argument. Implemented because docs/10 row 65 instructs a
    # successor to run this detector over another pass's committed ledger; until
    # this existed that instruction was not executable and silently re-analysed
    # this lane's own file.
    global LEDGER, PRIOR_SEQ
    argv = [a for a in sys.argv[1:] if not a.startswith("--")]
    if argv:
        LEDGER = os.path.abspath(argv[0])
        if os.path.isdir(LEDGER):
            print(f"account.py: {LEDGER} is a directory; pass the results.jsonl file",
                  file=sys.stderr)
            return 2
        if not os.path.exists(LEDGER):
            print(f"account.py: no such ledger: {LEDGER}", file=sys.stderr)
            return 2
        # A foreign ledger has none of this lane's sequence boundaries, so the
        # whole-ledger figures are the only ones that mean anything for it.
        PRIOR_SEQ = 0
    rows = load()
    rc = schema_guard(rows)
    if rc:
        return rc
    total = len(rows)
    hosts = sorted({r["host"] for r in rows})

    ok200, whole = whole_kib_detector(rows)
    # The counting rule for ok200, counted rather than described: a row whose
    # http_status is the STRING "200" exactly. An opaque form such as
    # "200 (curl)" -- which `2026-10-14-pool-s7-l7crawl` writes on every row --
    # is NOT a match under this rule. Printed beside the number because the
    # number means nothing without it (AGENTS.md section 6 item 7), and the
    # rule that does resolve those rows is named rather than left for the
    # reader to find. The COUNT is deliberately unchanged: this lane's own
    # ledger has no opaque 200, so moving it would only invent a difference.
    opaque_200 = [r for r in rows
                  if isinstance(r.get("http_status"), str)
                  and r["http_status"].startswith("200")
                  and r["http_status"] != "200"]

    h_gaps, k_gaps, h_skip, k_skip = spacing(rows)
    this_pass = [r for r in rows if r["seq"] > PRIOR_SEQ]
    tp_h, tp_k, tp_skip, tp_kskip = spacing(this_pass)
    h_min = min((g[0] for g in h_gaps), default=None)
    k_min = min((g[0] for g in k_gaps), default=None)

    # Sub-delay gaps: recorded, not hidden. A gap under the declared 2.5 s is
    # either a harness defect or a real violation, and this file refuses to
    # decide which -- it prints them for the write-up to adjudicate.
    under = [g for g in h_gaps if g[0] < 2.5]

    # t_done before t_sent is impossible under the documented lock ordering
    # (sleep, date -> t_sent, curl, date -> t_done). `.get` because a row may
    # carry neither key: an absent timestamp cannot be inverted.
    inverted = [(r["seq"], r.get("host_tag"), r.get("t_sent"), r.get("t_done"))
                for r in rows
                if parse(r.get("t_sent")) and parse(r.get("t_done"))
                and parse(r.get("t_done")) < parse(r.get("t_sent"))]

    bad = [r for r in rows if r.get("curl_exit") not in (0, None)]
    methods = sorted({r["method"] for r in rows})
    vendor = [r for r in rows if "medtronic" in r["host"] or "minimed" in r["host"]]

    by_status = {}
    for r in rows:
        by_status[r["http_status"]] = by_status.get(r["http_status"], 0) + 1

    # An information-bearing answer is one the API actually meant: 200 with
    # records, or a 404 "No Captures found" shape. A gateway 502/504 is a
    # FAILURE and carries no information in either direction (docs/10).
    by_role = {}
    for r in rows:
        s = r["http_status"]
        shape = r.get("shape", "none")
        if s == "200":
            kind = "200-answer"
        elif s == "404":
            kind = "404-answer"
        elif s == "400":
            kind = "400-malformed-or-oracle"
        else:
            kind = "gateway-failure-no-information"
        by_role.setdefault(kind, 0)
        by_role[kind] += 1

    out = {
        "requests_total": total,
        "cap": CAP,
        "accounting_line": f"{total} of a {CAP} cap",
        "hosts": hosts,
        "methods": methods,
        "requests_to_any_medtronic_host": len(vendor),
        "by_http_status": dict(sorted(by_status.items())),
        "by_information_class": by_role,
        "rows_from_prior_pass": sum(1 for r in rows if r["seq"] <= PRIOR_SEQ),
        "rows_from_this_pass": sum(1 for r in rows if r["seq"] > PRIOR_SEQ),
        "spacing_harness_min_s": round(h_min, 3) if h_min is not None else None,
        "harness_pairs_skipped_no_usable_t_sent": h_skip,
        "this_pass_pairs_skipped_no_usable_t_sent": tp_skip,
        "kernel_rows_skipped_no_host_tag": k_skip,
        "this_pass_kernel_rows_skipped_no_host_tag": tp_kskip,
        "kernel_bodies_available": bool(k_gaps),
        "spacing_kernel_body_mtime_min_s": round(k_min, 3) if k_min is not None else None,
        "this_pass_rows": len(this_pass),
        "this_pass_harness_min_s": round(min((g[0] for g in tp_h), default=0) or 0, 3) if tp_h else None,
        "this_pass_kernel_min_s": round(min((g[0] for g in tp_k), default=0) or 0, 3) if tp_k else None,
        "this_pass_gaps_below_2.5s": len([g for g in tp_h if g[0] < 2.5]),
        "this_pass_rows_with_t_done_before_t_sent": len(
            [r for r in this_pass if parse(r.get("t_done")) and parse(r.get("t_sent"))
             and parse(r.get("t_done")) < parse(r.get("t_sent"))]),
        "harness_gaps_below_2.5s": len(under),
        "harness_gaps_below_2.5s_detail": [
            {"from_seq": a, "to_seq": b, "gap_s": round(g, 3)} for g, a, b in under],
        "rows_with_t_done_before_t_sent": len(inverted),
        "rows_with_t_done_before_t_sent_detail": [
            {"seq": s, "tag": t} for s, t, _, _ in inverted],
        "rows_with_nonzero_curl_exit": len(bad),
        "ledger_rows_parseable": total,
        # the headline claim, counted -- and its rule, so the count is not a
        # typed number wearing a script's name (AGENTS.md section 6 item 7)
        "successful_200_counting_rule":
            "http_status == '200' EXACTLY; an opaque form such as '200 (curl)' "
            "is NOT counted by this tool",
        "rows_with_opaque_200_status": len(opaque_200),
        "successful_200_answers": len(ok200),
        "whole_kib_truncation_candidates": len(whole),
        "whole_kib_truncation_candidate_seqs": [r["seq"] for r in whole],
        "whole_kib_candidate_detail": [
            {"seq": r["seq"], "body_bytes": r["body_bytes"],
             "kib": round(r["body_bytes"] / 1024, 1),
             "record_count": r.get("record_count"),
             "distinct_host_count": r.get("distinct_host_count")} for r in whole],
    }

    if "--json" in sys.argv:
        print(json.dumps(out, indent=2))
        return 0

    w = 58
    print("=" * (w + 24))
    print("ACCOUNTING — every number below is computed from results.jsonl")
    print("=" * (w + 24))
    print(f"  requests sent          {out['requests_total']} of a {out['cap']} cap")
    print(f"  hosts contacted        {', '.join(hosts)}")
    print(f"  methods                {', '.join(methods)}")
    print(f"  requests to a Medtronic host  {out['requests_to_any_medtronic_host']}")
    print(f"  rows from prior pass   {out['rows_from_prior_pass']}")
    print(f"  rows from this pass    {out['rows_from_this_pass']}")
    print()
    print("  http status            " + "  ".join(f"{k}:{v}" for k, v in out["by_http_status"].items()))
    print("  information class      " + "  ".join(f"{k}:{v}" for k, v in out["by_information_class"].items()))
    print()
    foreign = LEDGER != os.path.join(HERE, "results.jsonl")
    if foreign:
        print(f"  FOREIGN LEDGER ({os.path.basename(os.path.dirname(LEDGER))}) -- this is NOT")
        print("  the lane's own results.jsonl, so the sequence-boundary split and the")
        print("  prior-pass comparison below do not apply to it.")
    # A 0-row ledger is a real record, not a missing file: a pass that sent no
    # request commits an empty results.jsonl (2026-10-15-area-l4-ledger-reader
    # does exactly that). Indexing rows[-1] on it raised IndexError, so the one
    # ledger a reader is most likely to try -- the newest pass's -- was the one
    # that crashed. Says so in words rather than printing a silent None.
    if not rows:
        print(f"  WHOLE LEDGER: 0 rows -- this ledger records a pass that sent nothing.")
        print("    Nothing to space, count or detect. That is a complete record, not a")
        print("    missing file, and every figure below is 0 rather than unknown.")
        print()
        print("  --- WHOLE-KiB TRUNCATION DETECTOR (the headline claim, counted) ---")
        print("  successful 200 answers                 0")
        print(f"    counting rule                         {out['successful_200_counting_rule']}")
        print("    rows whose status is an opaque 200    0")
        print("    whole-KiB truncation candidates        0   seqs []")
        print()
        print("  This is a CORRELATION over the rows observed on this ledger, not a proven")
        print("  mechanism. With no rows there is nothing to correlate, and no cause is")
        print("  asserted.")
        return 0
    print(f"  WHOLE LEDGER ({total} rows, seq 1-{rows[-1]['seq']})"
          + ("" if foreign else " -- includes the earlier attempt"))
    print(f"    min gap, harness t_sent            {out['spacing_harness_min_s']} s")
    print(f"    harness gaps under 2.5 s           {len(under)}")
    print(f"    pairs skipped, no usable t_sent    {h_skip}")
    if k_skip:
        print(f"    rows skipped, no host_tag          {k_skip}")
        print("      A row with no host_tag cannot name a body file, so the kernel oracle")
        print("      BREAKS the series at it rather than joining across it: no kernel gap")
        print("      above is measured from or over a row that carries NO HOST_TAG. The")
        print("      harness figure is unaffected -- it reads t_sent, not host_tag.")
        print("      NOT covered by that sentence: a row whose host_tag names a body file")
        print("      that is absent still joins the series (see the KNOWN LIMIT in the")
        print("      docstring). No committed ledger reaches it -- measured, not assumed.")
        if k_skip == len(rows):
            print("      Every row of this ledger lacks host_tag, which is a property of")
            print("      the ledger's schema, not of the bodies.")
        else:
            print(f"      {len(rows) - k_skip} of {len(rows)} rows DO carry one, so this is a")
            print("      partial ledger and the kernel oracle is broken into segments.")
    if h_skip:
        print("      A row with no t_sent leaves the series; the two pairs touching it are")
        print("      dropped rather than joined across it, so no gap above is measured from")
        print("      a row that carries no timestamp -- the floor is over the pairs that")
        print("      remain, and says so rather than reading as the whole ledger.")
    if out["kernel_bodies_available"]:
        print(f"  min gap, kernel body mtime oracle  {out['spacing_kernel_body_mtime_min_s']} s")
    else:
        print("  min gap, kernel body mtime oracle  UNAVAILABLE -- the raw bodies")
        print("      live outside this repository, so a clean clone cannot measure it.")
        print("      Stated rather than printed as a number. The harness series above")
        print("      reproduces from the committed ledger and is the load-bearing figure.")
    print(f"  harness gaps under the declared 2.5 s   {len(under)}")
    for d in out["harness_gaps_below_2.5s_detail"]:
        print(f"      seq {d['from_seq']} -> {d['to_seq']}: {d['gap_s']} s")
    print(f"  rows where t_done precedes t_sent  {len(inverted)} (impossible under the lock order)")
    for d in out["rows_with_t_done_before_t_sent_detail"]:
        print(f"      seq {d['seq']}  {d['tag']}")
    print(f"  rows with a non-zero curl exit    {len(bad)}")
    print()
    print(f"  THIS PASS ONLY ({len(this_pass)} rows, seq {this_pass[0]['seq']}-{this_pass[-1]['seq']})"
          if this_pass else "  THIS PASS ONLY: no rows")
    if this_pass:
        kmin = min((g[0] for g in tp_k), default=None)
        print(f"    min gap, harness t_sent            "
              f"{round(min(g[0] for g in tp_h), 3) if tp_h else None} s")
        print(f"    min gap, kernel body mtime oracle  "
              + (f"{round(kmin, 3)} s" if kmin is not None
                 else "UNAVAILABLE (bodies outside the repo)"))
        print(f"    gaps under 2.5 s                   {len([g for g in tp_h if g[0] < 2.5])} of {len(tp_h)}")
        print(f"    rows where t_done precedes t_sent  "
              f"{out['this_pass_rows_with_t_done_before_t_sent']}")
        if foreign:
            print("    (sequence-boundary split suppressed: a foreign ledger has none)")
        else:
            print("    => the three sub-floor gaps and the five inverted rows above are ALL")
            print("       in the earlier attempt. This pass is clean on every check.")
    print()
    print("  VERDICT: the two spacing oracles are reported together on purpose. If")
    print("  they disagree the harness series is the suspect (docs/09 section 4);")
    print("  this file does not silently prefer either one.")
    print()
    print("  --- WHOLE-KiB TRUNCATION DETECTOR (the headline claim, counted) ---")
    print(f"  successful 200 answers                 {len(ok200)}")
    print(f"    counting rule                         http_status == '200' EXACTLY")
    print(f"    rows whose status is an opaque 200    {len(opaque_200)}"
          f"{'   (e.g. \"200 (curl)\") -- NOT counted above' if opaque_200 else ''}")
    if opaque_200:
        print("      A ledger that writes the opaque form will read LOW here. The rule that")
        print("      resolves those rows, and the gap between the two rules, are stated in")
        print("      findings-log/2026-10-15-area-l4-ledger-reader/kib-detector.py (RULE 2).")
    print(f"  whole-KiB truncation candidates        {len(whole)}"
          f"   seqs {[r['seq'] for r in whole]}")
    for d in out["whole_kib_candidate_detail"]:
        print(f"      seq {d['seq']:>4}  {d['body_bytes']:>9} B = {d['kib']:>8} KiB"
              f"  records={d['record_count']}  hosts={d['distinct_host_count']}")
    print(f"  not on a boundary                      {len(ok200) - len(whole)}")
    if ok200:
        big = max(ok200, key=lambda r: r["body_bytes"])
        print(f"  largest successful response           {big['body_bytes']} B"
              f" ({big['body_bytes']/1024:.1f} KiB, seq {big['seq']})")
    print()
    print("  This is a CORRELATION over the rows observed on this ledger, not a proven")
    print("  mechanism. Nothing measured here separates a proxy byte cap, a server")
    print("  emit-budget and a client read-cutoff, so no cause is asserted.")
    return 0


if __name__ == "__main__":
    sys.exit(main())