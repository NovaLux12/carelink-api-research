#!/usr/bin/env python3
"""spacing.py — the measured same-host spacing floor for area AB. Zero requests.

Reads results.jsonl's `t_sent` series, sorts per host, and reports the floor, the
gap count and how many gaps fall under the declared 2.5 s. `t_sent` is stamped
inside the per-host flock, so this is the series the lock actually governed.
"""
import json, sys
from datetime import datetime

L = sys.argv[1] if len(sys.argv) > 1 else "results.jsonl"
rows = [json.loads(l) for l in open(L) if l.strip()]

def ts(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%fZ").timestamp()

per = {}
for r in rows:
    per.setdefault(r["host"], []).append((ts(r["t_sent"]), r["seq"], r["method"], r["path"]))

allg = []
print(f"{'host':38} {'reqs':>4} {'gaps':>4} {'floor(s)':>9} {'#<2.5s':>6}")
for h, v in sorted(per.items()):
    v.sort()
    gaps = [(v[i][0] - v[i-1][0], v[i][1]) for i in range(1, len(v))]
    allg += gaps
    under = [g for g, _ in gaps if g < 2.5]
    print(f"{h:38} {len(v):>4} {len(gaps):>4} {(min(g for g, _ in gaps) if gaps else 0):>9.3f} {len(under):>6}")
    for g, s in gaps:
        if g < 2.5:
            print(f"    under 2.5 s: {g:.3f} s at seq {s}")

floor = min(g for g, _ in allg) if allg else 0
neg = [ (g,s) for g,s in allg if g < 0 ]
print(f"\noverall floor {floor:.3f} s over {len(allg)} same-host gaps; "
      f"{sum(1 for g,_ in allg if g < 2.5)} under 2.5 s; {len(neg)} negative (impossible) "
      f"durations: {[ (round(g,3), s) for g,s in neg ]}")
