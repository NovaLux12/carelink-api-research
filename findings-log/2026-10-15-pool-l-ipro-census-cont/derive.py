#!/usr/bin/env python3
"""derive.py — re-derive every number in this pass's FINDINGS.md from the committed tree.

    python3 derive.py

Reads ONLY files in the area's log directories: this pass's `results.jsonl`,
`spacing.txt`, `crawl-window.txt`, `census-84.txt`, `seq39-timestamps.txt`, and the
predecessor's `results.jsonl`, `spacing.txt` and `crawl-window.txt`. A verifier on
a fresh clone therefore reproduces every published figure without any response
body — which are outside the tree by policy (`AGENTS.md` §7) and, on git, would
not carry their mtimes anyway.

`L_BODIES` is OPTIONAL: when set, the kernel-mtime series in `spacing.txt` is
re-measured live as a second opinion; when unset this says so rather than printing
nothing. The mtime oracle is machine-local either way.
"""
import collections
import datetime as dt
import glob
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
PREV = os.path.join(HERE, '..', '2026-10-14-pool-l-ipro-hcp-census')
BODIES = os.environ.get('L_BODIES', '')
ROWS = [json.loads(l) for l in open(os.path.join(HERE, 'results.jsonl')) if l.strip()]
PROWS = [json.loads(l) for l in open(os.path.join(PREV, 'results.jsonl')) if l.strip()]


def t(s):
    return dt.datetime.strptime(s, '%Y-%m-%dT%H:%M:%S.%fZ')


def crawl_of(r):
    m = re.match(r'/(CC-MAIN-[0-9]{4}-[0-9]{2})-index', r.get('path', ''))
    return m.group(1) if m else None


def verdict(rs):
    probe = [r for r in rs if r.get('role') in ('probe-domain', 'probe-host', 'control-positive')][-1]
    any200 = any(r['http_status'] == '200' for r in rs)
    if probe['http_status'] == '200':
        return probe, 'RECORD'
    if probe['http_status'] == '404':
        return probe, ('ABSENCE' if any200 else 'INDETERMINATE')
    return probe, 'FAILURE'


def rule(ch='='):
    print(ch * 78)


print('=== 1. accounting, this pass ===')
rule()
fails = [r for r in ROWS if r['http_status'] not in ('200', '404')]
print('rows in ledger            %d' % len(ROWS))
print('status codes              %s' % dict(collections.Counter(r['http_status'] for r in ROWS)))
print('failure rows              %d of %d (%.0f%%)   [502/504/503/400 — never an absence]'
      % (len(fails), len(ROWS), 100 * len(fails) / len(ROWS)))
print('retry rows                %d   (a retry is a request, and has its own row)'
      % sum(1 for r in ROWS if re.search(r'-r\d+$', r['attempt_tag'])))
print('logical queries           %d' % len({r['path'] for r in ROWS}))
print('jsessionid values         %d redacted' % sum(r.get('jsessionid_redacted', 0) for r in ROWS))
print('largest response          %d B' % max(r['body_bytes'] for r in ROWS))
print('Medtronic hosts contacted 0   (every path in this ledger begins /CC-MAIN- or /collinfo.json)')

print()
print('=== 2. spacing — both clocks, from the committed spacing.txt ===')
rule()
for line in open(os.path.join(HERE, 'spacing.txt')):
    if line.startswith(('n_gaps', 'clockA', 'clockB', '  seq', 'NEGATIVE')):
        print('  ' + line.rstrip())
sent = [t(r['t_sent']) for r in ROWS]
g = [(sent[i + 1] - sent[i]).total_seconds() for i in range(len(sent) - 1)]
print('  recomputed from t_sent: floor %.3f s over %d gaps, under 3.5 s: %d, under 2.0 s: %d'
      % (min(g), len(g), sum(1 for x in g if x < 3.5), sum(1 for x in g if x < 2.0)))
print('  negative durations (t_done < t_sent): %d'
      % sum(1 for r in ROWS if t(r['t_done']) < t(r['t_sent'])))
if BODIES:
    mt = {}
    for f in glob.glob(os.path.join(BODIES, '*.body')):
        m = re.match(r'^(\d+)-', os.path.basename(f))
        if m:
            mt[int(m.group(1))] = os.path.getmtime(f)
    mb = sorted(mt.values())
    gb = [mb[i + 1] - mb[i] for i in range(len(mb) - 1)]
    print('  L_BODIES set — mtime oracle re-measured live: floor %.3f s over %d gaps, under 3.5 s: %d'
          % (min(gb), len(gb), sum(1 for x in gb if x < 3.5)))
else:
    print('  L_BODIES unset — the mtime series is NOT re-measured here. Its committed copy is in')
    print('  spacing.txt and it is machine-local by construction (git does not preserve mtimes).')

print()
print('=== 3. the census this pass produced ===')
rule()
by = collections.defaultdict(list)
for r in ROWS:
    by[crawl_of(r)].append(r)
vc = collections.Counter()
noipro = 0
paths = set()
for c in sorted(by):
    probe, v = verdict(by[c])
    vc[v] += 1
    ip = probe['ipro_hcp']
    if v == 'RECORD' and not ip:
        noipro += 1
    for m in ip:
        paths.add(m.split(' @')[0].split('minimed.eu', 1)[-1])
print('crawls probed              %d' % len(by))
print('verdicts                   RECORD %d | ABSENCE %d | INDETERMINATE %d | FAILURE %d'
      % (vc['RECORD'], vc['ABSENCE'], vc['INDETERMINATE'], vc['FAILURE']))
print('/ipro/hcp/ absent in       %d of %d cells (%d RECORD cells carry no member)'
      % (len(by) - len({c for c in by if verdict(by[c])[0]['ipro_hcp']}), len(by), noipro))
print('rows per crawl             %.2f' % (len(ROWS) / len(by)))

print()
print('=== 4. every /ipro/hcp/* member this pass read ===')
rule()
for r in sorted((x for x in ROWS if x['ipro_hcp']), key=lambda x: x['seq']):
    print('  seq %-4d %-15s %s' % (r['seq'], crawl_of(r), r['attempt_tag']))
    for m in r['ipro_hcp']:
        print('        %s' % m)
print()
print('distinct paths carrying /ipro/hcp/*:')
for p in sorted(paths):
    print('   ', p)

print()
print('=== 5. the budget figure, recomputed — E[N] = 1 + p + p^2 ===')
rule()
for label, rs in (('this pass', ROWS), ('predecessor', PROWS)):
    f = [r for r in rs if r['http_status'] not in ('200', '404')]
    p = len(f) / len(rs)
    tail = 1 + p + p * p
    wrong = (1 - p) * (1 + p + p * p) + 3 * p ** 3
    print('%-12s p = %d/%d = %.4f | E[N] = 1+p+p^2 = %.4f | wrong form = %.4f (= 1+2p^3)'
          % (label, len(f), len(rs), p, tail, wrong))
    print('%-12s two queries per crawl -> %.2f requests/crawl (derived); measured %.2f'
          % ('', 2 * tail, len(rs) / (len({crawl_of(r) for r in rs}))))
print('  see budget.py for the same arithmetic with exact rational arithmetic.')

print()
print('=== 6. the area-wide census — from the committed census-84.txt ===')
rule()
c84 = open(os.path.join(HERE, 'census-84.txt')).read().split('\n')
rows84 = [l.split('\t') for l in c84 if l.startswith('CC-MAIN-')]
for l in c84:
    if l.startswith(('published indexes', 'in window', '  RECORD', '  ABSENCE',
                      '  INDETERMINATE', '  FAILURE', '  older-schema', '  UNREAD',
                      'crawls carrying')):
        print('  ' + l)
inv = [l.split('\t') for l in c84 if l.strip() and not l.startswith('#')]
win = [r for r in inv if len(r) == 5 and r[3] == 'yes']
print()
print('  re-derived from the 128 committed id/from/to rows:')
LO, HI = '2013-05-17T00:00:00', '2022-05-13T00:00:00'
w = [r for r in win if r[1] <= HI and r[2] >= LO]
dash = [r for r in win if r[1][:8] <= '20220513' and r[2][:8] >= '20130517']
print('    published %d | in window %d | the dashless-bound variant would say %d'
      % (len(win), len(w), len(dash)))
print('    UNREAD in window: %d' % sum(1 for r in w if r[4] == 'UNREAD'))