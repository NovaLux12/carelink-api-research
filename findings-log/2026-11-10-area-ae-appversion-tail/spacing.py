#!/usr/bin/env python3
"""Area AE — measured same-host spacing floor.  Zero requests.

Counting rule: one gap per consecutive same-host pair in request order, using
the ledger's `t_sent` series.  The floor is the minimum gap; a gap under the
declared 2.5 s is reported, and a gap under the repo's 2 s floor (AGENTS.md
§8) is reported separately because it would be a discipline failure rather
than a tight margin.

Self-conviction check: any row with t_done < t_sent means the series is
self-refuting and its gaps are not evidence.
"""
import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    rows = [json.loads(l) for l in open(os.path.join(HERE, "results.jsonl")) if l.strip()]
    rows.sort(key=lambda r: r["seq"])
    bad = [r["seq"] for r in rows if r["t_done"] < r["t_sent"]]
    print(f"rows: {len(rows)}; self-conviction (t_done < t_sent): {len(bad)} {bad}")
    per = defaultdict(list)
    for r in rows:
        per[r["host"]].append(r)
    print()
    print(f"{'host':28s} {'gaps':>5} {'min':>9} {'max':>9} {'<2.5s':>6} {'<2.0s':>6}")
    for host in sorted(per):
        rs = per[host]
        gaps = [(float(rs[i + 1]["t_sent"]) - float(rs[i]["t_sent"]), rs[i]["seq"], rs[i + 1]["seq"])
                for i in range(len(rs) - 1)]
        if not gaps:
            continue
        vals = [g[0] for g in gaps]
        under25 = [g for g in gaps if g[0] < 2.5]
        under20 = [g for g in gaps if g[0] < 2.0]
        print(f"{host:28s} {len(gaps):5d} {min(vals):9.3f} {max(vals):9.3f} "
              f"{len(under25):6d} {len(under20):6d}")
        for g in under25:
            print(f"   under 2.5 s: {g[0]:.3f} s between seq {g[1]} and {g[2]}")
    allg = []
    for host in per:
        rs = per[host]
        allg += [float(rs[i + 1]["t_sent"]) - float(rs[i]["t_sent"]) for i in range(len(rs) - 1)]
    if allg:
        print()
        print(f"MEASURED FLOOR (all hosts, same-host gaps only): {min(allg):.3f} s "
              f"over {len(allg)} gaps; under 2.5 s: {sum(1 for x in allg if x < 2.5)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
