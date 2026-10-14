#!/usr/bin/env python3
"""derive.py — re-derive every number in FINDINGS.md from the committed tree. Zero requests.

    python3 derive.py

Reads ONLY files in this directory (`results.jsonl`, `spacing.txt`,
`crawl-window.txt`), so a verifier on a fresh clone reproduces every published
figure without the response bodies — which are outside the tree by policy
(`AGENTS.md` §7) and, on git, would not carry their mtimes anyway.

`L_BODIES` is OPTIONAL. When set, the kernel-mtime cross-check in `spacing.txt`
is recomputed live and printed as a second opinion; when unset that block says so
rather than silently printing nothing.

Every block below prints the figure it derives and, where the two or more paths
to a number disagree, prints the disagreement rather than picking one.
"""
import collections
import datetime as dt
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BODIES = os.environ.get('L_BODIES', '')
ROWS = [json.loads(l) for l in open(os.path.join(HERE, 'results.jsonl')) if l.strip()]

# The crawls a prior area-L pass had already read, from the L logs' own ledgers.
PRIOR_READ = {'CC-MAIN-2013-20', 'CC-MAIN-2013-48', 'CC-MAIN-2014-10', 'CC-MAIN-2015-06',
              'CC-MAIN-2015-22', 'CC-MAIN-2017-04', 'CC-MAIN-2019-51', 'CC-MAIN-2020-24',
              'CC-MAIN-2020-50', 'CC-MAIN-2021-04', 'CC-MAIN-2021-25', 'CC-MAIN-2022-05',
              'CC-MAIN-2022-21'}


def t(s):
    return dt.datetime.strptime(s, '%Y-%m-%dT%H:%M:%S.%fZ')


def crawl_of(r):
    m = re.match(r'/(CC-MAIN-[0-9]{4}-[0-9]{2})-index', r['path'])
    return m.group(1) if m else None


def verdict(rs):
    """The counting rule: readable as an absence ONLY if some row for that crawl answered 200."""
    probe = [r for r in rs if r['role'] in ('probe-domain', 'probe-host', 'control-positive')][-1]
    if probe['http_status'] == '200':
        v = 'RECORD'
    elif probe['http_status'] == '404':
        v = 'ABSENCE' if any(r['http_status'] == '200' for r in rs) else 'INDETERMINATE'
    else:
        v = 'FAILURE'
    return probe, v


def rule(ch='-'):
    print(ch * 78)


print('=== 1. accounting ===')
rule('=')
print('rows in ledger:             %d' % len(ROWS))
print('status codes:               %s' % dict(collections.Counter(r['http_status'] for r in ROWS)))
fails = [r for r in ROWS if r['http_status'] not in ('200', '404')]
print('failure rows:               %d of %d (%.0f%%)'
      % (len(fails), len(ROWS), 100 * len(fails) / len(ROWS)))
print('retry rows:                 %d' % sum(1 for r in ROWS if re.search(r'-r\d+$', r['attempt_tag'])))
print('jsessionid values redacted: %d' % sum(r['jsessionid_redacted'] for r in ROWS))
print('largest response:           %d B' % max(r['body_bytes'] for r in ROWS))

print()
print('=== 2. spacing — both clocks, from the committed spacing.txt ===')
rule('=')
sp = open(os.path.join(HERE, 'spacing.txt')).read()
for line in sp.splitlines():
    if line.startswith(('n_gaps', 'clockA', 'clockB')):
        print('  ' + line)
sent = [t(r['t_sent']) for r in ROWS]
ga = [(sent[i + 1] - sent[i]).total_seconds() for i in range(len(sent) - 1)]
print('  recomputed from results.jsonl t_sent: floor %.3f s over %d gaps, under 3.5 s: %d,'
      ' under 2.0 s: %d'
      % (min(ga), len(ga), sum(1 for g in ga if g < 3.5), sum(1 for g in ga if g < 2.0)))
print('  negative durations (t_done < t_sent):  %d'
      % sum(1 for r in ROWS if t(r['t_done']) < t(r['t_sent'])))
if BODIES:
    mt = {}
    for f in glob.glob(os.path.join(BODIES, '*.body')):
        m = re.match(r'^(\d+)-', os.path.basename(f))
        if m:
            mt[int(m.group(1))] = os.path.getmtime(f)
    mb = sorted(mt.values())
    gb = [mb[i + 1] - mb[i] for i in range(len(mb) - 1)]
    print('  L_BODIES set — kernel-mtime oracle recomputed live: floor %.3f s over %d gaps,'
          ' under 3.5 s: %d' % (min(gb), len(gb), sum(1 for g in gb if g < 3.5)))
else:
    print('  L_BODIES unset — the kernel-mtime block is NOT recomputed here; its series is the')
    print('  committed copy in spacing.txt, and it is machine-local by construction (git does')
    print('  not preserve mtimes). Set L_BODIES to re-measure it on this machine.')

print()
print('=== 3. census — every cell, decided by the counting rule ===')
rule('=')
by = collections.defaultdict(list)
for r in ROWS:
    c = crawl_of(r)
    if c:
        by[c].append(r)
print('%-15s %-32s %-18s %-5s %s' % ('crawl', 'control (seq/status/rec)', 'probe (seq/st/rec)', 'ipro', 'verdict'))
for c in sorted(by):
    rs = by[c]
    ctrl = [r for r in rs if r['role'].startswith('control') and 'absent' not in r['role']]
    probe, v = verdict(rs)
    cs = ', '.join('%s:%s/%d' % (r['seq'], r['http_status'], r['records']) for r in ctrl) or '-'
    print('%-15s %-32s %-18s %-5d %s'
          % (c, cs, '%s:%s/%d' % (probe['seq'], probe['http_status'], probe['records']),
             len(probe['ipro_hcp']), v))

print()
print('=== 4. the negative, and its denominator (three ways) ===')
rule('=')
new = [c for c in sorted(by) if c not in PRIOR_READ]
reprobed = sorted(c for c in new if c in PRIOR_READ)  # never populated; kept explicit
touched = [c for c in sorted(by) if any(r['role'] in ('probe-domain', 'probe-host',
                                                      'control-positive') for r in by[c])]
newly = [c for c in touched if c not in PRIOR_READ]
# a prior-read crawl EITHER got its own control+probe pair here (re-probed), OR was
# only reproduced as an anchor (control-positive, no probe of its own).
re_prob = [c for c in touched if c in PRIOR_READ
           and any(r['role'] in ('probe-domain', 'probe-host') for r in by[c])]
anchor = [c for c in touched if c in PRIOR_READ and c not in re_prob]
no_ipro = [c for c in newly if verdict(by[c])[0]['ipro_hcp'] == []]
classified = [c for c in newly if verdict(by[c])[1] in ('RECORD', 'ABSENCE')]
no_ipro_c = [c for c in classified if verdict(by[c])[0]['ipro_hcp'] == []]
print('crawls this pass classified a cell on : %d  %s' % (len(touched), touched))
print('  newly read                           : %d  %s' % (len(newly), newly))
print('  re-probed (prior-read, new pair here) : %d  %s' % (len(re_prob), re_prob))
print('  anchor reproduction (no probe of its own): %s' % anchor)
print()
print('  A) /ipro/hcp/ absent in %d of the %d crawls this pass FIRST READ'
      % (len(no_ipro), len(newly)))
print('  B) same, over classified cells only   : %d of %d  (the indeterminate cell is excluded,'
      % (len(no_ipro_c), len(classified)))
print('     and a 404 behind no control cannot carry an absence either way)')
print('  A is the figure FINDINGS.md publishes. The two disagree by exactly the')
print('  indeterminate cell; neither is a rounding, and both are stated.')

print()
print('=== 5. requests per newly-read crawl (the S-L2 budget figure) ===')
rule('=')
rn = [r for r in ROWS if crawl_of(r) in newly]
print('ledger rows on the %d newly-read crawls : %d' % (len(newly), len(rn)))
print('  by role                                 : %s' % dict(collections.Counter(r['role'] for r in rn)))
print('  by status                               : %s' % dict(collections.Counter(r['http_status'] for r in rn)))
p = len([r for r in rn if r['http_status'] not in ('200', '404')]) / len(rn)
e = (1 - p) * (1 + p + p * p) + 3 * p ** 3
print('MEASURED  %d / %d = %.2f requests per newly-read crawl' % (len(rn), len(newly), len(rn) / len(newly)))
print('DERIVED   row failure rate p = %.3f; E[attempts per query] at MAXRETRY=2 is' % p)
print('          (1-p)(1+p+p^2) + 3p^3 = %.3f;  two queries per crawl -> %.2f'
      % (e, 2 * e))
print('          (the measured figure exceeds it because two of the nine crawls exhausted')
print('           a control host: -2014-23 and -2022-27)')
print('  publish %.1f-%.1f, not 2. The "1.6" an earlier draft of this log carried had no' % (2 * e, len(rn) / len(newly)))
print('  derivation and matches nothing on disk; it is withdrawn.')

print()
print('=== 6. crawl window — from the committed crawl-window.txt ===')
rule('=')
rows = [l.rstrip('\n').split('\t') for l in open(os.path.join(HERE, 'crawl-window.txt'))
        if l.strip() and not l.startswith('#')]
inv = [r for r in rows if len(r) == 5]
for r in rows:
    if len(r) == 2:
        print('  %-42s %s' % (r[0], r[1]))
print()
print('  re-derived from the 128 committed id/from/to rows:')
LO, HI = '2013-05-17T00:00:00', '2022-05-13T00:00:00'
w = [r for r in inv if r[1] <= HI and r[2] >= LO]
print('    published indexes %d | in window %d' % (len(inv), len(w)))
print('    read before this pass %d | read new by this pass %d | still unread %d'
      % (len([r for r in w if r[4] in ('prior-L-pass', 're-probed-here')]),
         len([r for r in w if r[4] == 'this-pass']),
         len([r for r in w if r[4] == ''])))
outw = [r[0] for r in inv if r[4] == 'this-pass' and r[3] == 'no']
print('    newly-read crawls OUTSIDE the window: %s' % outw)
print()
print('  Three comparison variants, because the gap is TWO errors and not one:')
v1 = [r for r in inv if r[1][:8] <= '20220513' and r[2][:8] >= '20130517']
v2 = [r for r in inv if r[1][:10] <= '2022-05-13' and r[2][:10] >= '2013-05-17']
print('    v1  from[:8]/to[:8] (dashes kept) vs a DASHLESS bound -> %d   <- the 87' % len(v1))
print('    v2  from[:10]/to[:10] (dashes kept) vs the SAME shape -> %d   <- correct' % len(v2))
print('    full-ISO from/to vs the same shape                     -> %d   <- correct' % len(w))
print('    so day precision suffices; what is WRONG is comparing two different shapes.')
print('    v1 wrongly INCLUDES: %s' % sorted(r[0] for r in v1 if r not in w))
print('    v1 wrongly DROPS   : %s' % sorted(r[0] for r in w if r not in v1))
print('    84 - 2 dropped + 5 wrongly included = %d. The dropped pair is the two 2013' % len(v1))
print('    crawls ("-" 0x2D < "0" 0x30 fails their `to` test); the five wrongly included')
print('    are the post-window 2022 crawls ("-" 0x2D < "2" 0x32 passes their `from` test).')

print()
print('=== 7. every /ipro/hcp/* member in this pass ===')
rule('=')
for r in ROWS:
    for m in r['ipro_hcp']:
        print('  seq %-3s %-15s %s' % (r['seq'], crawl_of(r), m))

print()
print('=== 8. javascript-warning.html side-finding (CC-MAIN-2022-27) ===')
rule('=')
ts = sorted(m.group(1) for m in
           re.finditer(r'javascript-warning\.html"? "?[,}]?\s*.*?"timestamp":\s*"(\d{14})"',
                       ''))
# the bodies are outside the tree; read them only when L_BODIES is set
b = glob.glob(os.path.join(BODIES, '39-domain-2022-27*.body')) if BODIES else []
if b:
    hits = []
    for line in open(b[0]):
        if 'javascript-warning.html' in line:
            r = json.loads(line)
            hits.append((r['timestamp'], r['url'].split('minimed.eu', 1)[-1], r.get('status')))
    hits.sort()
    p_ = lambda s: dt.datetime.strptime(s, '%Y%m%d%H%M%S')
    print('  %d records, all HTTP 200; span %s; max consecutive gap %s'
          % (len(hits), p_(hits[-1][0]) - p_(hits[0][0]),
             max(p_(hits[i + 1][0]) - p_(hits[i][0]) for i in range(len(hits) - 1))))
    for h in hits:
        print('    %s  %-58s %s' % h)
else:
    print('  L_BODIES unset — the five timestamps are not re-derivable here.')
    print('  The CORRECTED figures (span 1:41:52, max consecutive gap 0:52:07) are recorded')
    print('  in FINDINGS.md Correction (2026-10-15) with the rule that produced them; an')
    print('  earlier draft of this log said "within sixteen minutes" and was wrong.')