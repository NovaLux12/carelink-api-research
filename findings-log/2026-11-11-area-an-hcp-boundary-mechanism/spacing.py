#!/usr/bin/env python3
"""Zero-request re-derivation of area AN's two delay series (docs/09 §4).

Clock A: t_sent / t_done from results.jsonl (re-derivable from a clean clone).
Clock B: kernel body mtimes of the retained bodies (NOT re-derivable from a clone;
         git does not preserve mtimes) — reported as a point-in-time measurement.

Counting rule (docs/09 §4): one gap per consecutive pair IN REQUEST ORDER on the
SAME HOST, measured on that clock. Negative durations (t_done < t_sent) are
impossible and are named, not clamped.

Usage: python3 spacing.py [SCRATCH_DIR]
"""
import datetime
import json
import os
import sys

LEDGER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results.jsonl")
SCRATCH = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(os.path.abspath(__file__)), ".scratch")


def ts(s):
    return datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%fZ").timestamp()


def report(name, series, note):
    gaps = [(b[0], b[1], b[2] - a[2]) for a, b in zip(series, series[1:]) if a[1] == b[1]]
    g = [x[2] for x in gaps]
    print(f"== clock {name} ==")
    print(note)
    print(f"rows {len(series)}  same-host gaps {len(gaps)}")
    if not g:
        print("no same-host gap\n")
        return
    print(f"min {min(g):.3f} s   max {max(g):.3f} s   mean {sum(g)/len(g):.3f} s")
    short = [x for x in gaps if x[2] < 2.5]
    print(f"under the declared 2.5 s: {len(short)}")
    print(f"under the repository 2.0 s floor: {sum(1 for x in g if x < 2.0)}")
    for seq, host, d in short:
        print(f"  SHORT seq->{seq} {host} {d:.3f} s")
    print()


rows = [json.loads(l) for l in open(LEDGER) if l.strip()]
print(f"ledger rows {len(rows)}\n")

report("A: t_sent (committed, re-derivable)",
       [(r["seq"], r["host"], ts(r["t_sent"])) for r in rows],
       "series: consecutive t_sent on the same host")

neg = [(r["seq"], r["host"], ts(r["t_done"]) - ts(r["t_sent"])) for r in rows
       if ts(r["t_done"]) < ts(r["t_sent"])]
print(f"== impossible durations (t_done < t_sent) == {len(neg)}")
for seq, host, d in neg:
    print(f"  IMPOSSIBLE seq {seq} {host} duration {d:+.3f} s")
print()

series = []
for r in rows:
    p = os.path.join(SCRATCH, r["tag"] + ".b")
    if os.path.exists(p):
        series.append((r["seq"], r["host"], os.path.getmtime(p)))
report("B: kernel body mtimes (NOT re-derivable from a clone)",
       series, f"bodies stat-able {len(series)} of {len(rows)}; series: consecutive body mtimes, same host")
