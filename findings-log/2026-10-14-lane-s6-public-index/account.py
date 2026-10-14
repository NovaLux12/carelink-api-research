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
  python3 account.py            # full report
  python3 account.py --json     # machine-readable, for the gate
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


def parse(ts: str):
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
    """
    sel = [r for r in rows if (host_filter is None or r["host"] == host_filter)]
    sel.sort(key=lambda r: r["seq"])

    harness = []
    for i in range(len(sel) - 1):
        a, b = parse(sel[i]["t_sent"]), parse(sel[i + 1]["t_sent"])
        if a and b:
            harness.append((( b - a).total_seconds(), sel[i]["seq"], sel[i + 1]["seq"]))

    kernel = []
    prev = None
    for r in sel:
        p = os.path.join(BODIES, f"{r['host_tag']}.b")
        if not os.path.exists(p):
            continue
        m = os.stat(p).st_mtime
        if prev is not None:
            kernel.append((m - prev[0], prev[1], r["seq"]))
        prev = (m, r["seq"])

    return harness, kernel


def whole_kib_detector(rows):
    """The headline claim, as a reproducible count rather than a sentence.

    Only a SUCCESSFUL answer can be a truncated response: a 502/504 body is a
    gateway page and a 404 is the API's own 'no captures' sentence, neither of
    which is a record stream. So the detector runs over the 200 rows only.
    """
    ok = [r for r in rows if r.get("http_status") == "200" and r.get("body_bytes")]
    whole = [r for r in ok if r["body_bytes"] % 1024 == 0]
    return ok, whole


def main() -> int:
    rows = load()
    total = len(rows)
    hosts = sorted({r["host"] for r in rows})

    ok200, whole = whole_kib_detector(rows)

    h_gaps, k_gaps = spacing(rows)
    h_min = min((g[0] for g in h_gaps), default=None)
    k_min = min((g[0] for g in k_gaps), default=None)

    # Sub-delay gaps: recorded, not hidden. A gap under the declared 2.5 s is
    # either a harness defect or a real violation, and this file refuses to
    # decide which -- it prints them for the write-up to adjudicate.
    under = [g for g in h_gaps if g[0] < 2.5]

    # t_done before t_sent is impossible under the documented lock ordering
    # (sleep, date -> t_sent, curl, date -> t_done).
    inverted = [(r["seq"], r["host_tag"], r["t_sent"], r["t_done"]) for r in rows
                if parse(r["t_sent"]) and parse(r["t_done"])
                and parse(r["t_done"]) < parse(r["t_sent"])]

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
        "kernel_bodies_available": bool(k_gaps),
        "spacing_kernel_body_mtime_min_s": round(k_min, 3) if k_min is not None else None,
        "harness_gaps_below_2.5s": len(under),
        "harness_gaps_below_2.5s_detail": [
            {"from_seq": a, "to_seq": b, "gap_s": round(g, 3)} for g, a, b in under],
        "rows_with_t_done_before_t_sent": len(inverted),
        "rows_with_t_done_before_t_sent_detail": [
            {"seq": s, "tag": t} for s, t, _, _ in inverted],
        "rows_with_nonzero_curl_exit": len(bad),
        "ledger_rows_parseable": total,
        # the headline claim, counted
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
    print(f"  min gap, harness t_sent            {out['spacing_harness_min_s']} s")
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
    print("  VERDICT: the two spacing oracles are reported together on purpose. If")
    print("  they disagree the harness series is the suspect (docs/09 section 4);")
    print("  this file does not silently prefer either one.")
    print()
    print("  --- WHOLE-KiB TRUNCATION DETECTOR (the headline claim, counted) ---")
    print(f"  successful 200 answers                 {len(ok200)}")
    print(f"  whole-KiB truncation candidates        {len(whole)}"
          f"   seqs {[r['seq'] for r in whole]}")
    for d in out["whole_kib_candidate_detail"]:
        print(f"      seq {d['seq']:>4}  {d['body_bytes']:>9} B = {d['kib']:>8} KiB"
              f"  records={d['record_count']}  hosts={d['distinct_host_count']}")
    print(f"  not on a boundary                      {len(ok200) - len(whole)}")
    print()
    print("  This is a CORRELATION over the rows observed on this ledger, not a proven")
    print("  mechanism. Nothing measured here separates a proxy byte cap, a server")
    print("  emit-budget and a client read-cutoff, so no cause is asserted.")
    return 0


if __name__ == "__main__":
    sys.exit(main())