#!/usr/bin/env python3
"""spacing.py — emit spacing.txt: the same-host delay series, on the committed ledger.

    python3 spacing.py > spacing.txt

Zero requests. Reads ONLY results.jsonl, so the series is re-computable by a
reviewer from a clean clone with no body file and no machine that ran the probe.

Two clocks, because the repo has been bitten by this twice:

  clock A — `t_sent`, the harness's own clock, one ISO-8601 stamp per row.
  clock B — the kernel's body-file mtime. INDEPENDENT of the harness clock but
           NOT re-derivable from a clean clone (git does not preserve mtimes), so
           it is an optional cross-check that says so when it is absent, rather
           than a second promise the tree cannot keep. This is area L's C6 fix
           (a re-derivation tool that prints a notice, not a table).

Spacing is measured from `t_sent`, consecutive pairs in ledger order, because one
host is in scope and `host_seq` is therefore the whole series. Every row carries
`host_seq` explicitly so this filter is not an assumption.
"""
import json
import os
import re
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, 'results.jsonl')
DECLARED = 3.5          # this pass's declared same-host delay
REPO_FLOOR = 2.0        # AGENTS.md section 8 / docs/09 section 4


def ts(s):
    return datetime.strptime(s, '%Y-%m-%dT%H:%M:%S.%fZ')


rows = [json.loads(l) for l in open(LEDGER) if l.strip()]
rows.sort(key=lambda r: r['host_seq'])

print('spacing.txt — the same-host delay series for')
print('  findings-log/2026-10-17-sl2-outwindow-census/results.jsonl')
print('  host: index.commoncrawl.org (ONE host in scope, so host_seq is the series)')
print('  declared delay: >= %.1f s, slept INSIDE flock; repository floor: >= %.1f s'
      % (DECLARED, REPO_FLOOR))
print('  rows in the ledger: %d' % len(rows))
print('  distinct hosts in the ledger: %s' % ', '.join(sorted({r['host'] for r in rows})))
print()

# --- clock A: t_sent ---------------------------------------------------------
print('CLOCK A — t_sent (the harness clock; re-derivable from this file alone)')
print('%-5s %-13s %-26s %-9s %-9s' % ('n', 'host_seq', 't_sent', 'gap', 'verdict'))
gaps, neg, under_decl, under_floor = [], 0, 0, 0
prev = None
for i, r in enumerate(rows):
    t = ts(r['t_sent'])
    if prev is None:
        print('%-5d %-13s %-26s %-9s %-9s' % (i + 1, r['host_seq'], r['t_sent'], '-', '-'))
        prev = t
        continue
    g = (t - prev).total_seconds()
    prev = t
    gaps.append(g)
    if g < 0:
        neg += 1
        v = 'NEGATIVE'
    elif g < DECLARED:
        under_decl += 1
        v = 'UNDER declared'
    elif g < REPO_FLOOR:
        under_floor += 1
        v = 'under repo floor'
    else:
        v = 'ok'
    print('%-5d %-13s %-26s %9.3f %-9s' % (i + 1, r['host_seq'], r['t_sent'], g, v))
print()
if gaps:
    print('  gaps %d   min %.3f s   max %.3f s   mean %.3f s'
          % (len(gaps), min(gaps), max(gaps), sum(gaps) / len(gaps)))
    print('  under the declared %.1f s: %d' % (DECLARED, under_decl))
    print('  under the repository %.1f s floor: %d' % (REPO_FLOOR, under_decl + under_floor))
    print('  negative durations (impossible; a corrupt-t0 signature): %d' % neg)
    print('  FLOOR ON THIS CLOCK: %.3f s' % min(gaps))
print()

# --- request durations ------------------------------------------------------
dur = [(ts(r['t_done']) - ts(r['t_sent'])).total_seconds() for r in rows]
print('REQUEST DURATIONS (t_done - t_sent): min %.3f s   max %.3f s   mean %.3f s'
      % (min(dur), max(dur), sum(dur) / len(dur)))
print('  negative: %d' % sum(1 for d in dur if d < 0))
print()

# --- clock B: kernel body mtime (optional cross-check) -----------------------
bodies = os.environ.get('L_BODIES')
print('CLOCK B — kernel body-file mtime')
if not bodies or not os.path.isdir(bodies):
    print('  NOT AVAILABLE (set L_BODIES to the scratch directory outside the tree).')
    print('  This is not a re-derivable oracle: git does not preserve mtimes, so a')
    print('  clean clone has no series here. It is printed only when present.')
else:
    mt = {}
    for r in rows:
        for fn in os.listdir(bodies):
            if fn.startswith('%d-' % r['seq']) and fn.endswith('.body'):
                p = os.path.join(bodies, fn)
                if os.path.getsize(p) or r['http_status'] != '200':
                    mt[r['seq']] = os.path.getmtime(p)
                    break
    srt = sorted(mt.items())
    bg = [srt[i + 1][1] - srt[i][1] for i in range(len(srt) - 1)]
    if bg:
        print('  bodies with an mtime: %d of %d rows' % (len(srt), len(rows)))
        print('  gaps %d   min %.3f s   max %.3f s   under the declared %.1f s: %d'
              % (len(bg), min(bg), max(bg), DECLARED, sum(1 for g in bg if g < DECLARED)))
        print('  FLOOR ON THIS CLOCK: %.3f s' % min(bg))
    else:
        print('  no two consecutive bodies available; series not computable.')