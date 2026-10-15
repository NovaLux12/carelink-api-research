#!/usr/bin/env python3
"""runlog.py — regenerate run.log from results.jsonl. Zero requests.

Why this exists: probe.sh's own run.log printf had one conversion too few for
its argument list, and bash printf reuses the format string when arguments
outnumber conversions — so it emitted extra lines instead of failing. The
defect was in run.log only; the ledger is one python3 row per request and was
never affected. The ledger is the record; run.log is a rendering of it.

Columns, tab separated:
  t_queued  t_sent  t_done  body_mtime  host  method  url  status
  content-type  bytes  role  tag
"""
import json
import pathlib
import sys

here = pathlib.Path(__file__).resolve().parent
ledger = here / "results.jsonl"
out = here / "run.log"

rows = []
for line in ledger.read_text().splitlines():
    line = line.strip()
    if line:
        rows.append(json.loads(line))
rows.sort(key=lambda r: r["seq"])

with out.open("w") as fh:
    for r in rows:
        fh.write("\t".join(str(x if x is not None else "") for x in (
            r["t_queued"], r["t_sent"], r["t_done"], r.get("body_mtime"),
            r["host"], r["method"], r["url"], r["status"],
            r.get("content_type"), r["body_bytes"], r["role"], r["tag"],
        )) + "\n")
print(f"run.log: {len(rows)} rows from results.jsonl", file=sys.stderr)