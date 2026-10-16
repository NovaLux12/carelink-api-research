#!/usr/bin/env python3
"""repair-status.py — lane l2. Zero vendor requests.

**The defect it repairs, stated first.** `curl-shim.sh` v1 captured curl's whole stdout
into a shell variable and logged that variable as `http_status`. For the requests the
pinned suite sends with `-o <file>` and no `-w`, stdout *is* the response body. So every
such row carries a response body in a status column — in this ledger, **22 of the 26
gate-suite rows**, two of which held a 5513-byte HTML document (seq 82, 83). A status
column that can hold an HTML document will be read as a status by someone who does not
know, and this file is that someone.

**It repairs every gate row, not one run's worth.** v1 of this script ran after the first
gate run and fixed its 13 rows; the second gate run then added 13 more and **nothing
touched them**, which is how 11 rows shipped with a body in a status field and a
`ledger_note` that mentioned only the `t_sent` caveat. That is the whole shape of the bug
in verifier round 1 finding B1: a repair scoped to an event rather than to a state. This
version is therefore **idempotent and total** — it walks every `kind: gate-suite` row
every time it is run, and it reports what it found and what it changed, so a reader can
tell the coverage from the claim.

**What it does and does not do.** It replaces a contaminated value with an explicit marker
naming the reason, keeps the original string's length in `http_status_original_length` so
the substitution is auditable, and leaves the row's `ledger_note` corrected to mention the
status field. It **invents no status code.** Where the suite asserted one in its own log,
the row points at that log (`gate-suite.log`, `85 passed, 0 failed`). It is safe to run any
number of times: a row already carrying the marker, or a clean 3-digit code, is left alone.

**Why the gate is not re-run to obtain clean fields.** Every run of the suite costs 13
vendor requests against this pass's cap, and the suite is already green. This is a
bookkeeping repair; a re-run is a second measurement of the same thing.
"""
import json
import re
import sys

LEDGER = sys.argv[1]
MARK = ("(not captured: the suite sent this request with -o <file> and no -w, so curl's "
        "stdout was the response BODY and the shim logged that as the status. The suite's "
        "own assertion for this cell is in gate-suite.log. The shim was rewritten "
        "2026-10-17 to ask curl for the status on stderr, so later absorbed runs carry a "
        "real code; rows from the two runs before that rewrite cannot. NOT re-run to "
        "obtain a clean field — see repair-status.py.)")

rows = [json.loads(l) for l in open(LEDGER, encoding="utf-8") if l.strip()]
gate = [r for r in rows if r.get("kind") == "gate-suite"]
clean = [r for r in gate if isinstance(r.get("http_status"), str)
         and re.fullmatch(r"\d{3}", r["http_status"])]
marked = [r for r in gate if isinstance(r.get("http_status"), str)
          and r["http_status"].startswith("(not captured")]
dirty = [r for r in gate if r not in clean and r not in marked]

for r in dirty:
    r["http_status_original_length"] = len(r["http_status"])
    r["http_status"] = MARK
    note = r.get("ledger_note", "")
    r["ledger_note"] = (
        note + " STATUS FIELD: the value here was originally a response body of "
        f"{r['http_status_original_length']} characters and has been replaced with an "
        "explicit marker naming the reason. It was not a status code and never is."
    ).strip()

with open(LEDGER, "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r) + "\n")

print(f"repair-status.py: {len(gate)} gate-suite row(s) — "
      f"{len(clean)} already clean, {len(marked)} already marked, "
      f"**{len(dirty)} repaired now**; ledger {len(rows)} rows")
if dirty:
    print("  repaired seqs: " + ", ".join(str(r["seq"]) for r in dirty))
    print("  body lengths replaced: " +
          ", ".join(f"{r['seq']}={r['http_status_original_length']}B" for r in dirty))