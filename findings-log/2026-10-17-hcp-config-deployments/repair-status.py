#!/usr/bin/env python3
"""repair-status.py — lane l2. Zero vendor requests.

**The defect it repairs, stated first.** `curl-shim.sh` captured curl's stdout into a
shell variable and then logged that whole variable as `http_status`. For the requests
the pinned suite sends with `-o <file>` and no `-w`, stdout *is* the response body, so
**9 of the 13 absorbed gate-suite rows carry a body fragment in a status field**, and
3 carry the status concatenated onto a body. That is an unreadable ledger: a status
column that can hold an HTML document will be read as a status by someone who does not
know.

**Why not re-run the gate to get clean fields.** The pass has **74 of an 85 cap** left;
the suite costs 13. A re-run would fit, but it would also mean **two** gate runs' worth
of vendor traffic against a cap the claim states once, and the suite's assertions are
already green — `gate-suite.log` carries `85 passed, 0 failed`. Fixing the field is a
bookkeeping repair; re-running is a second measurement of the same thing.

**What it does and does not do.** It replaces the contaminated value with an explicit
marker naming the reason, and keeps the original string's length in a separate field so
the substitution is auditable and nothing is silently dropped. It **invents no status
code** — where the suite asserted one in its own log, the row points at that log instead.
It is idempotent and refuses to touch a row whose status is already a clean 3-digit code.
"""
import json
import re
import sys

LEDGER = sys.argv[1]
MARK = "(not parsed by the curl shim: the suite sent this request with -o <file> and no " \
       "-w, so curl's stdout was the response BODY and the shim logged that as the status. " \
       "The suite's own assertion for this cell is in gate-suite.log — 85 passed, 0 failed. " \
       "Not re-run to obtain a clean field; see repair-status.py.)"

rows = [json.loads(l) for l in open(LEDGER, encoding="utf-8") if l.strip()]
fixed = 0
for r in rows:
    st = r.get("http_status")
    if r.get("kind") != "gate-suite" or not isinstance(st, str):
        continue
    # idempotent: a row already carrying the marker, or a clean code, is left alone
    if st.startswith("(not parsed") or re.fullmatch(r"\d{3}", st):
        continue
    r["http_status_original_length"] = len(st)
    r["http_status"] = MARK
    fixed += 1

with open(LEDGER, "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r) + "\n")
print(f"repair-status.py: repaired {fixed} row(s); ledger still {len(rows)} rows")