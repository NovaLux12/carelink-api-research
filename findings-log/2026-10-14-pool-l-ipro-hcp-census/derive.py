#!/usr/bin/env python3
"""derive.py — re-derive every number in FINDINGS.md from results.jsonl. Zero requests.

    python3 derive.py

The pass's own worst number should be its validation. Nothing here reads the
network; everything comes from the ledger, the crawl inventory fetched once
(seq 1) and the published crawl list on disk.
"""
import collections
import datetime as dt
import glob
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
BODIES = os.environ.get('L_BODIES', '')  # absolute scratch dir; empty disables the two mtime/inventory blocks
ROWS = [json.loads(l) for l in open(os.path.join(HERE, 'results.jsonl')) if l.strip()]


def t(s):
    return dt.datetime.strptime(s, '%Y-%m-%dT%H:%M:%S.%fZ')


def crawl_of(r):
    m = re.match(r'/CC-MAIN-([0-9]{4}-[0-9]{2})-index', r['path'])
    return 'CC-MAIN-' + m.group(1) if m else None


print('=== accounting ===')
print('rows in ledger:            %d' % len(ROWS))
print('distinct status codes:     %s' % dict(collections.Counter(r['http_status'] for r in ROWS)))
fails = [r for r in ROWS if r['http_status'] not in ('200', '404')]
print('failure rows:              %d of %d (%.0f%%)' % (len(fails), len(ROWS), 100 * len(fails) / len(ROWS)))
print('retry rows (attempt_tag):  %d' % sum(1 for r in ROWS if r['attempt_tag'] != r['attempt_tag'].split('-r')[0]))
print('jsessionid values redacted:%d' % sum(r['jsessionid_redacted'] for r in ROWS))
print('largest response:          %d B' % max(r['body_bytes'] for r in ROWS))

print()
print('=== spacing (counting rule: one gap per consecutive pair in request order) ===')
sent = [t(r['t_sent']) for r in ROWS]
gaps = [(sent[i + 1] - sent[i]).total_seconds() for i in range(len(sent) - 1)]
print('t_sent   gaps=%d  floor=%.3fs  max=%.3fs  under3.5=%d  under2.0=%d  negative durations=%d'
      % (len(gaps), min(gaps), max(gaps),
         sum(1 for g in gaps if g < 3.5), sum(1 for g in gaps if g < 2.0),
         sum(1 for r in ROWS if t(r['t_done']) < t(r['t_sent']))))
bodies = sorted(os.path.getmtime(f) for f in glob.glob(os.path.join(BODIES, '*.body')))
mg = [bodies[i + 1] - bodies[i] for i in range(len(bodies) - 1)] if len(bodies) > 1 else []
if mg:
    print('mtime    bodies=%d  floor=%.3fs  under3.5=%d  under2.0=%d' % (len(bodies), min(mg), sum(1 for g in mg if g < 3.5), sum(1 for g in mg if g < 2.0)))

print()
print('=== census table (verdict decided by: did ANY row for that crawl answer 200?) ===')
print('%-15s %-34s %-22s %-5s %s' % ('crawl', 'control (seq/status/rec)', 'probe (seq/status/rec)', 'ipro', 'verdict'))
for c in sorted({crawl_of(r) for r in ROWS if crawl_of(r)}):
    rs = [r for r in ROWS if crawl_of(r) == c]
    ctrl = [r for r in rs if r['role'].startswith('control') and 'absent' not in r['role']]
    probe = [r for r in rs if r['role'] in ('probe-domain', 'probe-host', 'control-positive')]
    last = probe[-1]
    any200 = any(r['http_status'] == '200' for r in rs)
    cs = ', '.join('%s:%s/%d' % (r['seq'], r['http_status'], r['records']) for r in ctrl) or '-'
    if last['http_status'] == '200':
        v = 'RECORD'
    elif last['http_status'] == '404':
        v = 'ABSENCE' if any200 else 'INDETERMINATE'
    else:
        v = 'FAILURE'
    print('%-15s %-34s %-22s %-5d %s'
          % (c, cs, '%s:%s/%d' % (last['seq'], last['http_status'], last['records']), len(last['ipro_hcp']), v))

print()
print('=== every /ipro/hcp/* member in this pass ===')
for r in ROWS:
    for m in r['ipro_hcp']:
        print('  seq %-3s %-15s %s' % (r['seq'], crawl_of(r), m))

print()
print('=== crawl inventory ===')
print("    counting rule: a crawl is IN the window when from <= '2022-05-13T00:00:00' AND")
print("    to >= '2013-05-17T00:00:00', compared as the SAME ISO-8601 shape collinfo")
print("    publishes (YYYY-MM-DDThh:mm:ss), endpoints inclusive. Comparing those strings")
print("    against a dashless '20220513' form is silently wrong: '-' (0x2d) sorts below")
print("    '0' (0x30), so a 2013 'to' reads as SMALLER than a 2013 bound — that variant")
print("    silently drops the two 2013 crawls and reports a window that is too small.")
inv = None
for b in glob.glob(os.path.join(BODIES, '1-collinfo.body')):
    inv = json.load(open(b))
if inv:
    win = [c for c in inv if c['from'] <= '2022-05-13T00:00:00' and c['to'] >= '2013-05-17T00:00:00']
    read_by_prior = {'CC-MAIN-2013-20', 'CC-MAIN-2013-48', 'CC-MAIN-2014-10', 'CC-MAIN-2015-06',
                     'CC-MAIN-2015-22', 'CC-MAIN-2017-04', 'CC-MAIN-2019-51', 'CC-MAIN-2020-24',
                     'CC-MAIN-2020-50', 'CC-MAIN-2021-04', 'CC-MAIN-2021-25', 'CC-MAIN-2022-05',
                     'CC-MAIN-2022-21'}
    unread = [c for c in win if c['id'] not in read_by_prior]
    print('published indexes: %d | in window: %d | already read by a prior L pass: %d | unread: %d'
          % (len(inv), len(win), len(win) - len(unread), len(unread)))
    read_here = {crawl_of(r) for r in ROWS if r['role'] in ('probe-domain', 'probe-host') and crawl_of(r)}
    fresh = sorted(c for c in read_here if c not in read_by_prior)
    print('read new by this pass (%d): %s' % (len(fresh), ' '.join(fresh)))
    print('still unread after this pass: %d' % (len(unread) - len(fresh)))
else:
    print('L_BODIES unset or the collinfo body is not on this machine —')
    print('inventory block not re-derivable here (it is not part of the tree by policy)')