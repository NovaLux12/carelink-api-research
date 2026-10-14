#!/usr/bin/env python3
"""budget.py — derive the per-crawl request cost FROM A LEDGER. Zero requests.

    python3 budget.py [ledger.jsonl ...]

Round 2 found this pass's expectation formula wrong: `probe.sh` re-issues a query
until it succeeds or `MAXRETRY=2` is exhausted, so the number of attempts is

    N = min(Geom(p), MAXRETRY + 1) = min(Geom(p), 3)

and by the tail-sum rule

    E[N] = sum_{k=0}^{2} P(N > k) = 1 + p + p^2

The predecessor published `(1-p)(1+p+p^2) + 3p^3`, which expands to `1 + 2p^3` --
an expectation that FALLS as p rises, which cannot be right. The correct inner
polynomial is `1 + 2p + 3p^2`; `(1-p)(1+2p+3p^2) + 3p^3` expands to the same
`1 + p + p^2`. Both forms are printed below so the two cannot be confused again.

Every figure here is computed, never typed, so prose quoting it cannot drift.
"""
import json
import re
import sys
from fractions import Fraction as F

MAXRETRY = 2
LEDGERS = sys.argv[1:] or ['../2026-10-14-pool-l-ipro-hcp-census/results.jsonl']


def load(paths):
    rows = []
    for p in paths:
        try:
            rows += [json.loads(l) for l in open(p) if l.strip()]
        except FileNotFoundError:
            pass
    return rows


def crawl_of(r):
    m = re.match(r'/(CC-MAIN-[0-9]{4}-[0-9]{2})-index', r['path'])
    return m.group(1) if m else None


def e_attempts(p):
    """E[min(Geom(p), MAXRETRY+1)] by the tail-sum rule."""
    tail = sum(p ** k for k in range(MAXRETRY + 1))            # 1 + p + p^2
    inner = sum(k * p ** (k - 1) for k in range(1, MAXRETRY + 2))  # 1 + 2p + 3p^2
    wrong = (1 - p) * sum(p ** k for k in range(MAXRETRY + 1)) + (MAXRETRY + 1) * p ** (MAXRETRY + 1)
    return tail, inner, wrong


rows = load(LEDGERS)
fail = [r for r in rows if r['http_status'] not in ('200', '404')]
p = F(len(fail), len(rows)) if rows else F(0)

print('ledgers            : %s' % ', '.join(LEDGERS))
print('rows               : %d   failures %d   p = %d/%d = %.6f'
      % (len(rows), len(fail), len(fail), len(rows), float(p)))
tail, inner, wrong = e_attempts(p)
print()
print('E[N] = 1 + p + p^2                      = %.6f   <-- CORRECT (tail-sum)' % tail)
print('  = (1-p)(1+2p+3p^2) + 3p^3             = %.6f' % ((1 - p) * inner + 3 * p ** 3))
print('  published (1-p)(1+p+p^2) + 3p^3       = %.6f   <-- WRONG, == 1 + 2p^3' % wrong)
print()
print('two queries per crawl -> %.4f requests/crawl (derived)' % (2 * tail))
if rows:
    logical = len({r['path'] for r in rows})
    print('logical queries (distinct paths)      = %d' % logical)
    print('mean attempts/query OBSERVED          = %d/%d = %.6f'
          % (len(rows), logical, len(rows) / logical))
    print('retries observed                      = %d  (= rows - logical)' % (len(rows) - logical))
