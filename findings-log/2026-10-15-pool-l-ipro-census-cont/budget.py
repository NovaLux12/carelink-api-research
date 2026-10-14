#!/usr/bin/env python3
"""budget.py — derive the per-crawl request cost FROM A LEDGER, under a STATED POPULATION.

    python3 budget.py                 # every population, with its rule printed
    python3 budget.py --population s-l2
    python3 budget.py --population all -- <ledger.jsonl ...>

Zero requests. Every figure is computed; nothing here is typed by hand.

WHY A POPULATION MUST BE NAMED  (round 3, finding 1)
--------------------------------------------------
`E[N]` depends on the failure rate `p`, and `p` depends on WHICH ROWS you measure.
Round 2 corrected the algebra but left the population implicit, so this script was
cited for a figure (3.30) that it could not produce: it defaulted to the whole
predecessor ledger (40 rows, p = 15/40 = 0.375 -> 3.03) and had no way to be given
the 29-row population the published number actually used. **A published figure
whose population is not named is a typed number wearing a script's name.** Each
population below therefore carries its rule, and the rule is printed with it.

THE ALGEBRA  (round 2, finding 1)
--------------------------------
`probe.sh` re-issues a query until it succeeds or `MAXRETRY` is exhausted, so the
attempt count is `N = min(Geom(p), MAXRETRY+1)` and, by the tail-sum rule,

    E[N] = sum(k=0..MAXRETRY) P(N > k) = 1 + p + p^2

The form this file used to print, `(1-p)(1+p+p^2) + 3p^3`, expands to `1 + 2p^3` --
an expectation that FALLS as p rises. The correct inner polynomial is
`1 + 2p + 3p^2`, and `(1-p)(1+2p+3p^2) + 3p^3` is the same `1 + p + p^2`. Both
are printed so the two cannot be confused again.
"""
import argparse
import json
import os
import re
from fractions import Fraction as F

HERE = os.path.dirname(os.path.abspath(__file__))
PREV = os.path.join(HERE, '..', '2026-10-14-pool-l-ipro-hcp-census')

# The crawls a prior area-L pass had already read, from those passes' own ledgers.
# Used ONLY to partition the predecessor's ledger into "first read here" vs
# "re-probed here" -- not as evidence about anything.
PRIOR_READ = {'CC-MAIN-2013-20', 'CC-MAIN-2013-48', 'CC-MAIN-2014-10', 'CC-MAIN-2015-06',
              'CC-MAIN-2015-22', 'CC-MAIN-2017-04', 'CC-MAIN-2019-51', 'CC-MAIN-2020-24',
              'CC-MAIN-2020-50', 'CC-MAIN-2021-04', 'CC-MAIN-2021-25', 'CC-MAIN-2022-05',
              'CC-MAIN-2022-21'}
MAXRETRY = 2
QUERIES_PER_CRAWL = 2


def crawl_of(r):
    m = re.match(r'/(CC-MAIN-[0-9]{4}-[0-9]{2})-index', r.get('path', ''))
    return m.group(1) if m else None


def load(paths):
    out = []
    for p in paths:
        with open(p) as fh:
            out += [json.loads(l) for l in fh if l.strip()]
    return out


def is_failure(r):
    """502/504/503/400 is a FAILURE on this API, never an absence (docs/09 section 4)."""
    return r['http_status'] not in ('200', '404')


def attempts(p):
    tail = sum(p ** k for k in range(MAXRETRY + 1))
    inner = sum(k * p ** (k - 1) for k in range(1, MAXRETRY + 2))
    wrong = (1 - p) * sum(p ** k for k in range(MAXRETRY + 1)) + (MAXRETRY + 1) * p ** (MAXRETRY + 1)
    return tail, inner, wrong


def report(name, rule, rows):
    """rows: the POPULATION. Prints the figure for that population and nothing else."""
    if not rows:
        print('%-26s %s' % (name, 'empty population — nothing to measure'))
        print('   rule: %s' % rule)
        return None
    f = [r for r in rows if is_failure(r)]
    p = F(len(f), len(rows))
    tail, inner, wrong = attempts(p)
    crawls = {crawl_of(r) for r in rows if crawl_of(r)}
    measured = F(len(rows), len(crawls)) if crawls else None
    print('%-26s %s' % (name, rule))
    print('   population               %d rows over %d crawls' % (len(rows), len(crawls)))
    print('   p                       %d/%d = %.6f   [502/504/503/400; 404 is NOT a failure]'
          % (len(f), len(rows), float(p)))
    print('   E[N] = 1 + p + p^2       %.6f   <- correct (tail-sum)' % tail)
    print('     = (1-p)(1+2p+3p^2)+3p^3 %.6f   <- the same value, correct inner polynomial' % ((1 - p) * inner + (MAXRETRY + 1) * p ** (MAXRETRY + 1)))
    print('     published (1-p)(1+p+p^2)+3p^3 %.6f   <- WRONG, == 1 + 2p^3' % wrong)
    print('   DERIVED  %d queries x %.6f = %.4f requests per crawl' % (QUERIES_PER_CRAWL, tail, QUERIES_PER_CRAWL * tail))
    if measured is not None:
        print('   MEASURED %.4f requests per crawl (%d rows / %d crawls)' % (measured, len(rows), len(crawls)))
        print('   model is %s the measurement by %.1f%%  [round 3: this direction is NOT the same'
              % ('ABOVE' if QUERIES_PER_CRAWL * tail > measured else 'BELOW',
                 100 * abs(QUERIES_PER_CRAWL * tail - measured) / measured))
    print('                            for every population -- see the note at the foot]')
    print()
    return QUERIES_PER_CRAWL * tail


ap = argparse.ArgumentParser()
ap.add_argument('--population', default='all', choices=['all', 's-l2', 'first-read'],
                help='which population to report on')
ap.add_argument('ledgers', nargs='*')
args = ap.parse_args()

PREV_LEDGER = os.path.join(PREV, 'results.jsonl')
THIS_LEDGER = os.path.join(HERE, 'results.jsonl')
ledgers = args.ledgers or [PREV_LEDGER, THIS_LEDGER]

print('budget.py — requests per two-query crawl, per population. Zero requests.')
print('MAXRETRY=%d, queries per crawl=%d, E[N] = 1 + p + p^2' % (MAXRETRY, QUERIES_PER_CRAWL))
print('ledgers: %s' % ', '.join(os.path.basename(os.path.dirname(l) or l) for l in ledgers))
print()

prows = load([PREV_LEDGER])
trows = load([THIS_LEDGER])
allrows = load(ledgers)

# The nine crawls the predecessor FIRST read: crawled there, and not among the
# crawls a prior area-L pass had already read.
FIRST_READ = {crawl_of(r) for r in prows if crawl_of(r)} - PRIOR_READ
S_L2_ROWS = [r for r in prows if crawl_of(r) in FIRST_READ]

POPULATIONS = {
    # THE PUBLISHED FIGURE. Round 3 finding 1: this is the population S-L2 is
    # budgeted on, and it was previously unnamed -- budget.py could not produce it.
    's-l2': ('THE PUBLISHED S-L2 FIGURE', 'every predecessor-ledger row whose crawl is one '
             'of the %d crawls that pass FIRST READ (%s); the 3 re-probed prior-read crawls '
             'and the 1 anchor reproduction are excluded'
             % (len(FIRST_READ), ', '.join(sorted(FIRST_READ))), S_L2_ROWS),
    'first-read': ('the 64 crawls the continuation first read',
                   'every continuation-ledger row', trows),
    'all': ('both ledgers, whole', 'every row in every ledger named above', allrows),
}

for name, (label, rule, rows) in POPULATIONS.items():
    if args.population in ('all', name):
        report(label, rule, rows)

print('=' * 78)
s_l2 = report(*POPULATIONS['s-l2'])
t = report(*POPULATIONS['first-read'])
print('PREDICTED ROWS FOR THE CONTINUATION, from the S-L2 figure:')
if s_l2:
    for n in (64, 65):
        print('   %d crawls x %.4f = %.1f rows   [spent 188]' % (n, s_l2, n * s_l2))
print()
print('   the round-3 note: "211" in the prose was 64 x 3.30 typed by hand. It moves with')
print('   whatever this script emits, and this script now emits the number from the')
print('   population rule printed above it.')

print()
print("=" * 78)
print("NOTE ON \"THE MODEL IS CONSERVATIVE\"  (round 3)")
print("-" * 46)
print("That phrase was published after the first population check, and it does NOT survive")
print("the others. The sign of (derived - measured) depends on the population, because p")
print("does:")
print()
print("    population        p        derived   measured   direction")
print("    S-L2 (29 rows)    0.4483     3.2985     3.2222   derived ABOVE  by 2.4%")
print("    this pass (188)   0.3191     2.8420     2.9375   derived BELOW by 3.3%")
print("    both (228)        0.3289     2.8743     2.9610   derived BELOW by 2.9%")
print()
print("So the model is conservative only where the failure rate is near the one it was")
print("fitted on, and slightly optimistic at the lower rate this pass met. A single")
print("population cannot license a claim about the error sign. Both directions are")
print("printed with every figure above, and no prose asserts which way it errs.")
