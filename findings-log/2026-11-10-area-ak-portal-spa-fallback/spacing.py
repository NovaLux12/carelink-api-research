#!/usr/bin/env python3
"""Zero-request re-derivation of the delay series from results.jsonl alone.

TWO CLOCKS, because `docs/09` §4 requires both and this pass's harness is in the
recorded corrupt-`t0` class:

  A. `t_sent` / `t_done`, committed in results.jsonl — re-derivable from a clean clone,
     but written by `date` from the harness, which is the instrument docs/09 §4 names
     as the suspect one.
  B. kernel body-file mtimes in $REPO/.loop/ak-scratch — set by the kernel when curl
     writes the body, so independent of the harness clock. NOT re-derivable from a
     clone: git does not preserve mtimes. Recorded here as a point-in-time measurement.

Gaps are same-HOST only. A sleep inside a per-host flock says nothing about the gap
between two different hosts, and counting those would inflate the floor.

The diagnostic that matters is the PER-GAP comparison (docs/09 §4: "run the comparison
over the interval both clocks actually measured"), not the span comparison, which
telescopes to the first row's latency and cannot fail.
"""
import json, os, sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
SCRATCH = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..', '..', '.loop', 'ak-scratch'))

rows = [json.loads(l) for l in open(os.path.join(HERE, 'results.jsonl')) if l.strip()]
rows.sort(key=lambda r: r['seq'])

def ts(s): return datetime.strptime(s, '%Y-%m-%dT%H:%M:%S.%fZ')

print("== clock A: t_sent (committed, re-derivable) ==")
# impossible durations, named before the gaps they manufacture
imposs = [(r['seq'], r['host'], (ts(r['t_done']) - ts(r['t_sent'])).total_seconds())
          for r in rows if ts(r['t_done']) < ts(r['t_sent'])]
print(f"rows {len(rows)}  negative durations (t_done < t_sent): {len(imposs)}")
for s, h, d in imposs: print(f"  IMPOSSIBLE seq {s} {h} duration {d:+.3f} s")

byhost = {}
for r in rows:
    byhost.setdefault(r['host'], []).append(r)
gaps = []
for host, rs in byhost.items():
    for a, b in zip(rs, rs[1:]):
        gaps.append((host, a['seq'], b['seq'], (ts(b['t_sent']) - ts(a['t_sent'])).total_seconds()))
vals = [g[3] for g in gaps]
print(f"same-host gaps {len(gaps)}  min {min(vals):.3f} s  max {max(vals):.3f} s  mean {sum(vals)/len(vals):.3f} s")
print(f"under declared 2.5 s: {sum(1 for v in vals if v < 2.5)}")
print(f"under repository 2.0 s floor: {sum(1 for v in vals if v < 2.0)}")
for g in sorted(gaps, key=lambda x: x[3])[:3]:
    print(f"  shortest {g[0]} seq {g[1]}->{g[2]} {g[3]:.3f} s")

print()
print("== clock B: kernel body mtimes (NOT re-derivable from a clone) ==")
if not os.path.isdir(SCRATCH):
    print(f"  scratch dir absent ({SCRATCH}) — clock B unavailable on this host")
    sys.exit(0)
tags = {r['seq']: r['tag'] for r in rows}
mt = {}
for r in rows:
    p = os.path.join(SCRATCH, r['tag'] + '.b')
    if os.path.exists(p):
        mt[r['seq']] = os.stat(p).st_mtime
mgaps = [(rows[i]['host'], rows[i]['seq'], rows[i+1]['seq'], mt[rows[i+1]['seq']] - mt[rows[i]['seq']])
         for i in range(len(rows)-1) if rows[i]['host'] == rows[i+1]['host']
         and rows[i]['seq'] in mt and rows[i+1]['seq'] in mt]
mvals = [g[3] for g in mgaps]
print(f"bodies stat-able {len(mt)} of {len(rows)}  same-host gaps {len(mgaps)}")
print(f"min {min(mvals):.3f} s  max {max(mvals):.3f} s  mean {sum(mvals)/len(mvals):.3f} s")
print(f"under declared 2.5 s: {sum(1 for v in mvals if v < 2.5)}")
print(f"under repository 2.0 s floor: {sum(1 for v in mvals if v < 2.0)}")
print(f"under minus t_sent minus first-row latency, per gap >0.5 s: "
      f"{sum(1 for (a,b) in zip(sorted(gaps,key=lambda x:(x[0],x[1])), sorted(mgaps,key=lambda x:(x[0],x[1]))) if abs(a[3]-b[3]) > 0.5)}")
print(f"FLOOR ON THIS CLOCK: {min(mvals):.3f} s")
