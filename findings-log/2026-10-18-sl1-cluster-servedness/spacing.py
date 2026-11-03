#!/usr/bin/env python3
"""spacing.py — re-derive this pass's request accounting from the committed
ledger alone, and write spacing.txt beside it. Zero requests.

Two numbers are kept apart on purpose and must never be summed into one
"requests" figure without saying which is which:

  * ATTEMPTS — every row. A retry is a request. This is what the cap counts.
  * TIMED SENDS — the subset carrying a t_sent. Rows 1 and 2 are the
    pre-instrument reachability probes: real requests, appended to the ledger
    under the one-row-per-request rule, but issued outside the instrument by
    a bare curl that reported only time_total, so their spacing cannot be
    measured. That is a real limitation and is stated rather than smoothed
    over; it is also the safe direction, since both were issued minutes
    before the instrument's first send.

Usage: python3 spacing.py [path/to/results.jsonl]
"""

import datetime
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FLOOR = 3.5
REPO_FLOOR = 2.0
ONLY_HOSTS = {"index.commoncrawl.org", "data.commoncrawl.org"}


def parse(t):
    return datetime.datetime.fromisoformat(t.replace("Z", "+00:00"))


def main():
    led = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "results.jsonl")
    rows = [json.loads(l) for l in open(led) if l.strip()]

    out = []
    w = out.append
    w("spacing.txt — S-L1 cluster servedness, 2026-10-19 (pass #152)")
    w("")
    w("Accounting method: every row in the committed ledger is one request. A")
    w("retry is a request and is counted. Nothing is inferred from wall clock")
    w("outside the ledger.")
    w("")
    w("ROWS (attempts, what the cap counts): %d" % len(rows))
    w("  of which carry a t_sent (measurable spacing): %d" % sum(1 for r in rows if r.get("t_sent")))
    w("  without a t_sent (spacing uncheckable, disclosed): %s"
      % ([r["seq"] for r in rows if not r.get("t_sent")] or "none"))
    w("  methods present: %s" % sorted(set(r["method"] for r in rows)))
    w("  hosts present:   %s" % sorted(set(r["host"] for r in rows)))
    foreign = sorted(set(r["host"] for r in rows) - ONLY_HOSTS)
    w("  hosts outside the two permitted: %s" % (foreign or "NONE"))
    vendor = [r["seq"] for r in rows
              if any(t in r["host"] for t in ("minimed", "medtronic", "carelink", "clcloud"))]
    w("  requests to any Medtronic host: %d %s" % (len(vendor), vendor or ""))
    w("")

    by = {}
    for r in rows:
        if r.get("t_sent"):
            by.setdefault(r["host"], []).append(r)

    w("PER-HOST SPACING, from t_sent only")
    overall = None
    for h in sorted(by):
        rs = sorted(by[h], key=lambda r: parse(r["t_sent"]))
        gaps = [(parse(b["t_sent"]) - parse(a["t_sent"])).total_seconds() for a, b in zip(rs, rs[1:])]
        floor = min(gaps) if gaps else None
        under = [g for g in gaps if g < FLOOR]
        under_repo = [g for g in gaps if g < REPO_FLOOR]
        w("  %-24s %2d timed sends, %2d gaps" % (h, len(rs), len(gaps)))
        w("      floor %.3f s   gaps under %.1f s: %d   under AGENTS.md s8 %.1f s: %d"
          % (floor if floor is not None else float("nan"), FLOOR, len(under), REPO_FLOOR, len(under_repo)))
        if overall is None or (floor is not None and floor < overall):
            overall = floor
    w("  OVERALL FLOOR across both hosts: %.3f s (declared delay 3.5 s, held inside the"
      % (overall if overall is not None else float("nan")))
    w("  held lock(s), so it is a floor on the SEND-to-SEND gap and not on the gap")
    w("  between a response completing and the next request being built.)")
    w("")

    w("SEND TIMESTAMPS, in order")
    for r in sorted((r for r in rows if r.get("t_sent")), key=lambda r: parse(r["t_sent"])):
        w("  %2d  %s  %-24s %-16s %-4s %8s B" % (
            r["seq"], r["t_sent"], r["host"], r["role"], r["http_status"], r["body_bytes"]))
    w("")

    w("WHY THE FLOOR EXCEEDS THE DECLARED 3.5 s")
    w("  The 3.5 s sleep is INSIDE the held lock(s), and the lock is released only")
    w("  after the response has been read. A same-host gap is therefore")
    w("  3.5 s + the previous response's duration, so the measured floor is a floor")
    w("  on the send-to-send spacing and sits above the declared sleep by exactly")
    w("  the response time. The sleep-outside-the-lock form would be worse than no")
    w("  lock at all: it converts sequential sends into simultaneous ones.")

    text = "\n".join(out) + "\n"
    with open(os.path.join(HERE, "spacing.txt"), "w") as fh:
        fh.write(text)
    print(text)


if __name__ == "__main__":
    main()