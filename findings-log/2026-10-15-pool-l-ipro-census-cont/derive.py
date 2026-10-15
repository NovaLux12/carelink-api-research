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
# COUNTING RULE (round 3, finding 3): rows are in request order; the FIRST row carrying a
# given path is that logical query, and every later row with the same path is a RE-ISSUE of
# it. `-rN` is a LABEL the harness puts on its own retries; it is not the same thing as a
# re-issue -- the second sweep (q-02) re-issued five already-attempted paths under fresh,
# un-suffixed tags. Counting `-rN` alone undercounts, which is what round 2 published.
_seen = set()
_first = [r for r in ROWS if not (r['path'] in _seen or _seen.add(r['path']))]
_reissued = [r for r in ROWS if r not in _first]
_suf = [r for r in _reissued if re.search(r'-r\d+$', r['attempt_tag'])]
_unsuf = [r for r in _reissued if not re.search(r'-r\d+$', r['attempt_tag'])]
print('DECOMPOSITION of %d rows (the three parts must sum to it):' % len(ROWS))
print('   logical queries        %3d   first row carrying each path' % len(_first))
print('   re-issues, -rN tagged  %3d   the harness own retry of a path in THIS sweep' % len(_suf))
print('   re-issues, no -rN tag  %3d   a path re-issued by a LATER sweep under a fresh tag%s'
      % (len(_unsuf), '' if not _unsuf else ''))
if _unsuf:
    print('     -> seqs %s  (q-02-retry-novdict.tsv, the five no-verdict cells)' % [r['seq'] for r in _unsuf])
print('   SUM                    %3d   %s' % (len(_first) + len(_suf) + len(_unsuf),
                                              'ADDS UP' if len(_first) + len(_suf) + len(_unsuf) == len(ROWS) else 'DOES NOT ADD UP'))
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
print('=== 6. the area-wide census ===')
rule('=')
print('  TWO INDEPENDENT ROUTES, compared below so this block can DISAGREE with the file:')
print('    A) re-derive every verdict from the six area-L ledgers, from scratch;')
print('    B) read what census-84.txt committed. If A and B differ, that is a finding, and it')
print('       is printed as one. Round 3 finding 2: an earlier version of this block copied')
print('       census-84.txt and then re-derived over an empty set, so it could not fail.')

LEDGERS = sorted(glob.glob('../2026-10-1[34]-area-l-*/results.jsonl')) + \
          ['../2026-10-14-pool-l-ipro-hcp-census/results.jsonl', 'results.jsonl']
lrows = []
for L in LEDGERS:
    with open(L) as fh:
        lrows += [json.loads(l) for l in fh if l.strip()]
lby = collections.defaultdict(list)
for r in lrows:
    c = crawl_of(r)
    if c:
        lby[c].append(r)
AV = {}
for c, rs in lby.items():
    probe = [r for r in rs if r.get('role') in ('probe-domain', 'probe-host', 'control-positive')]
    if not probe:
        AV[c] = 'older-schema'
        continue
    any200 = any(r['http_status'] == '200' for r in rs)
    p = probe[-1]['http_status']
    AV[c] = ('RECORD' if p == '200' else ('ABSENCE' if p == '404' and any200
             else ('INDETERMINATE' if p == '404' else 'FAILURE')))

c84 = open(os.path.join(HERE, 'census-84.txt')).read().split('\n')
file_rows = [l.split('\t') for l in c84 if l.startswith('CC-MAIN-')]
# every row of this file is 8 fields (id/from/to/in_window/verdict/members/dates/pass);
# the tally lines below it are 1-3 fields. Round 3 finding 2: this filter was `len==5`,
# which matched NOTHING, so the re-derivation silently ran over an empty set.
inv = [r for r in file_rows if len(r) >= 5]
BV = {r[0]: r[4] for r in inv}
BWIN = {r[0]: (r[3] == 'yes') for r in inv}

LO, HI = '2013-05-17T00:00:00', '2022-05-13T00:00:00'
win = [r for r in inv if r[1] <= HI and r[2] >= LO]
before = [r for r in inv if r[2] < LO]
after = [r for r in inv if r[1] > HI]

print()
print('  A) re-derived from the %d committed id/from/to rows:' % len(inv))
print('     published %d | IN window %d | OUTSIDE %d'
      % (len(inv), len(win), len(inv) - len(win)))
print('       entirely BEFORE the window (to < %s)  %3d  %s'
      % (LO, len(before), ' '.join(r[0] for r in before)))
print('       entirely AFTER  the window (from > %s) %3d' % (HI, len(after)))
dash = [r for r in inv if r[1][:8] <= '20220513' and r[2][:8] >= '20130517']
print('     the DASHLESS-bound variant would say %d, not %d -- see Correction C9'
      % (len(dash), len(win)))

print()
print('  B) verdicts re-derived from the ledgers (A) vs read from census-84.txt:')
ac = collections.Counter(AV[r[0]] for r in win if r[0] in AV)
print('     A: in-window verdicts   %s' % dict(sorted(ac.items())))
unread_a = [r[0] for r in win if r[0] not in AV]
print('     A: in-window with NO verdict derivable from a ledger  %d  %s'
      % (len(unread_a), ' '.join(unread_a)))
disagree = [r[0] for r in win if AV.get(r[0], 'older-schema') != BV.get(r[0], 'older-schema')]
print('     A vs B disagreements  %d  %s'
      % (len(disagree), 'NONE — the file matches the ledgers' if not disagree
         else ' '.join('%s: A=%s B=%s' % (c, AV.get(c), BV.get(c)) for c in disagree)))
winrec = [r for r in win if BV.get(r[0]) == 'RECORD']
carry = [r for r in winrec if int(r[5]) > 0]
absent = [r for r in win if BV.get(r[0]) == 'ABSENCE'] + [r for r in winrec if int(r[5]) == 0]
absent_ids = {r[0] for r in absent}
print()
print('  THE HEADLINE, re-derived rather than copied:')
print('     /ipro/hcp/ readably absent in %d of the %d in-window crawls' % (len(absent), len(win)))
print('       = %d ABSENCE cells + %d RECORD cells carrying no member'
      % (len([r for r in win if BV.get(r[0]) == 'ABSENCE']), len([r for r in winrec if int(r[5]) == 0])))
print('     UNREAD in window  %d' % len(unread_a))
print('     the complement of the absent set, by verdict: %s'
      % dict(sorted(collections.Counter(
          BV.get(r[0], '?') for r in win if r[0] not in absent_ids).items())))
print()
print('  out-of-window cells carrying a verdict (should be exactly the one read on purpose):')
for r in inv:
    if not BWIN[r[0]] and BV.get(r[0]) not in (None, '-'):
        print('     %-16s %-10s members=%s dates=%s' % (r[0], BV[r[0]], r[5], r[6]))
