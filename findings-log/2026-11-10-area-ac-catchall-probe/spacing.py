#!/usr/bin/env python3
"""spacing.py — emit spacing.txt: the same-host delay series, from the committed ledger.

    python3 spacing.py > spacing.txt

Zero requests. Reads ONLY results.jsonl, so the series is re-computable from a
clean clone with no body file and no machine that ran the probe.

Spacing is measured from `t_sent`, consecutive pairs in ledger order. One host is
in scope (`carelink.minimed.eu`), so `host_seq` is the whole series — and every
row carries `host_seq` explicitly so that filter is not an assumption.
"""
import json
import os
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, 'results.jsonl')
DECLARED = 2.5          # this pass's declared same-host delay
REPO_FLOOR = 2.0        # AGENTS.md section 8 / docs/09 section 4


def ts(s):
    return datetime.strptime(s, '%Y-%m-%dT%H:%M:%S.%fZ')


rows = [json.loads(l) for l in open(LEDGER) if l.strip()]
rows.sort(key=lambda r: r['host_seq'])

print('spacing.txt — the same-host delay series for')
print('  findings-log/2026-11-10-area-ac-catchall-probe/results.jsonl')
print('  host: carelink.minimed.eu (ONE host in scope, so host_seq is the series)')
print('  declared delay: >= %.1f s, slept INSIDE flock; repository floor: >= %.1f s'
      % (DECLARED, REPO_FLOOR))
print('  rows in the ledger: %d' % len(rows))
print('  distinct hosts in the ledger: %s' % ', '.join(sorted({r['host'] for r in rows})))
print()

print('CLOCK A — t_sent (the harness clock; re-derivable from this file alone)')
print('%-5s %-9s %-26s %-9s %-9s' % ('n', 'host_seq', 't_sent', 'gap', 'verdict'))
gaps, neg, under_decl, under_floor = [], 0, 0, 0
prev = None
for i, r in enumerate(rows):
    t = ts(r['t_sent'])
    if prev is None:
        print('%-5d %-9s %-26s %-9s %-9s' % (i + 1, r['host_seq'], r['t_sent'], '-', '-'))
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
    print('%-5d %-9s %-26s %9.3f %-9s' % (i + 1, r['host_seq'], r['t_sent'], g, v))
print()
if gaps:
    print('  gaps %d   min %.3f s   max %.3f s   mean %.3f s'
          % (len(gaps), min(gaps), max(gaps), sum(gaps) / len(gaps)))
    print('  under the declared %.1f s: %d' % (DECLARED, under_decl))
    print('  under the repository %.1f s floor: %d' % (REPO_FLOOR, under_decl + under_floor))
    print('  negative durations (impossible; a corrupt-t0 signature): %d' % neg)
    print('  FLOOR ON THIS CLOCK: %.3f s' % min(gaps))
print()

dur = [(ts(r['t_done']) - ts(r['t_sent'])).total_seconds() for r in rows]
print('REQUEST DURATIONS (t_done - t_sent): min %.3f s   max %.3f s   mean %.3f s'
      % (min(dur), max(dur), sum(dur) / len(dur)))
print('  negative: %d' % sum(1 for d in dur if d < 0))
print()

print('REQUEST ACCOUNTING')
print('  rows: %d   failures: %d   retries: %d'
      % (len(rows), sum(1 for r in rows if r['is_failure']),
         sum(1 for r in rows if r['attempt'])))
print('  distinct statuses: %s' % ', '.join(sorted({r['http_status'] for r in rows})))
