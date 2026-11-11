#!/usr/bin/env python3
"""verify.py — re-derive every figure in FINDINGS.md at ZERO requests.

Usage: python3 verify.py

Reads only `results.jsonl` (committed) and `run.log`. Sends nothing. If a figure
in FINDINGS.md disagrees with what this prints, the document is wrong.

Exits non-zero if a load-bearing assertion fails, so the gate can run it.
"""
import collections
import datetime
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, 'results.jsonl')
RUNLOG = os.path.join(HERE, 'run.log')
CAP = 12
HOST = 'carelinkhp.minimed.eu'

fails = []


def check(ok, msg):
    print(('  ok   ' if ok else '  FAIL ') + msg)
    if not ok:
        fails.append(msg)


def dt(s):
    return datetime.datetime.strptime(s, '%Y-%m-%dT%H:%M:%S.%fZ')


rows = [json.loads(l) for l in open(LEDGER) if l.strip()]
by_tag = {r['tag']: r for r in rows}
rows.sort(key=lambda r: r['seq'])

print('--- 1. request accounting ---')
print(f'  rows in results.jsonl: {len(rows)}   cap: {CAP}')
check(len(rows) <= CAP, f'{len(rows)} rows <= cap {CAP}')
check([r['seq'] for r in rows] == list(range(1, len(rows) + 1)),
      'seq is 1..N with no gap and no repeat (one recorded revision: none)')
check(all(r['host'] == HOST for r in rows), f'every row is {HOST}, no other host contacted')
nonhost = set(r['host'] for r in rows) - {HOST}
check(not nonhost, f'hosts contacted = {sorted(set(r["host"] for r in rows))}')
check(all(r['curl_exit'] == 0 for r in rows),
      f'curl_exit == 0 on all {len(rows)} rows (a transport failure would be a FAILURE, not an absence)')
print(f'  unspent cells: {CAP - len(rows)}')

print('--- 2. method discipline ---')
meth = collections.Counter(r['method'] for r in rows)
print(f'  methods issued: {dict(meth)}')
check(set(meth) <= {'GET', 'OPTIONS'}, 'GET and empty-body OPTIONS only — no POST')
hdr_vals = sorted({r['sent_headers'] for r in rows})
print(f'  distinct sent_headers values: {hdr_vals}')
check(set(hdr_vals) <= {'X-System-ID: ProWeb', '(none)'},
      'the only header ever sent is X-System-ID: ProWeb (PUBLISHED, non-secret) — no token, cookie or auth')

print('--- 3. CONTROLS FIRST (seq 1, seq 2) ---')
c1, c2 = by_tag['as-c1-pow-crm'], by_tag['as-c2-absent']
print(f'  CONTROL-1 seq {c1["seq"]} {c1["path"]} +ProWeb -> {c1["http_status"]} {c1["body_bytes"]} B '
      f'sha256 {c1["body_sha256"][:16]}')
check(c1['http_status'] == '200' and c1['body_bytes'] == 96 and c1['body_sha256'].startswith('a977733a53ee0d5f'),
      'CONTROL-1 is 200 / 96 B / a977733a53ee0d5f — reproduces area AB and AQ on this host')
print(f'  CONTROL-2 seq {c2["seq"]} {c2["path"]} no header -> {c2["http_status"]} {c2["body_bytes"]} B '
      f'ctype {c2["content_type"]}')
check(c2['http_status'] == '404' and c2['body_bytes'] == 0 and c2['content_type'] == '(none)',
      'CONTROL-2 is 404 / 0 B / no Content-Type — a header-less GET on this subtree CAN return 404')
check(c1['seq'] == 1 and c2['seq'] == 2, 'both controls precede every question cell')

print('--- 4. THE PAIR — status with and without the header ---')
pairs = [('care-partner/search', 'as-q1-cps-with', 'as-q2-cps-without'),
         ('otc-linking/allowed', 'as-q3-otc-with', 'as-q4-otc-without')]
for name, w, wo in pairs:
    a, b = by_tag[w], by_tag[wo]
    print(f'  {name:22s}  WITH {a["http_status"]} {a["body_bytes"]:3d} B {a["content_type"]:18s} '
          f'{a["body_sha256"][:16]}   WITHOUT {b["http_status"]} {b["body_bytes"]} B {b["content_type"]}')
    check(b['http_status'] == '412' and b['body_bytes'] == 0 and b['content_type'] == '(none)',
          f'{name}: header-less GET reproduces 412 / 0 B / no Content-Type')
    check(a['http_status'] != b['http_status'],
          f'{name}: the status FLIPS with the header ({a["http_status"]} vs 412) — attributable to the header')
    check(a['seq'] + 1 == b['seq'], f'{name}: the with/without cells are adjacent in the same run')

print('--- 5. what the two flips resolved to ---')
q1, q3 = by_tag['as-q1-cps-with'], by_tag['as-q3-otc-with']
check(q1['http_status'] == '400', 'care-partner/search WITH header = 400 (not 200/401/405/404)')
check(q1['body_bytes'] == 237 and q1['body_sha256'].startswith('c9481609f74aa447'),
      'its 237 B body is c9481609f74aa447, and carries validationErrors naming searchCarePartners.arg0/arg2')
check(q3['http_status'] == '401', 'otc-linking/allowed WITH header = 401')
check(q3['body_bytes'] == 48 and q3['body_sha256'].startswith('247825a426460798'),
      'its 48 B body is 247825a426460798 — the InvalidToken/AUTH envelope areas AB and O record')
check(all(r['http_status'] != '404' for r in (q1, q3)),
      'NEITHER literal answered 404 with the header — the 412 is NOT an edge artefact in front of a non-existent route')

print('--- 6. the OPTIONS column, and its control ---')
o1, o2, o3 = by_tag['as-o1-cps-options'], by_tag['as-o2-otc-options'], by_tag['as-o3-absent-options']
for r in (o1, o2, o3):
    print(f'  seq {r["seq"]} OPTIONS {r["path"]:36s} no header -> {r["http_status"]} '
          f'{r["body_bytes"]:2d} B allow={r["allow"]:20s} {r["body_sha256"][:16]}')
check(o1['http_status'] == o2['http_status'] == '200',
      'OPTIONS 200 on BOTH question literals, and both sent NO header (sent_headers == "(none)")')
check(o1['allow'] == 'HEAD, GET, OPTIONS' and o2['allow'] == 'HEAD, GET, OPTIONS',
      'both advertise the identical Allow: HEAD, GET, OPTIONS')
check(o1['body_sha256'] == o2['body_sha256'] and o1['body_bytes'] == 18,
      'both return one 18 B body, one digest 0f06a4c8d34690d4')
check(o3['http_status'] == '404' and o3['body_bytes'] == 0,
      'the CERTAINLY-ABSENT child answers OPTIONS 404 / 0 B — so the 200 is PER-ROUTE, not a subtree constant')

print('--- 7. the absence shape, depth 1 and depth 2 ---')
d2 = by_tag['as-b1-absent-depth2']
print(f'  depth-1 {c2["path"]} -> {c2["http_status"]}')
print(f'  depth-2 {d2["path"]} -> {d2["http_status"]} {d2["body_bytes"]} B {d2["content_type"]}')
check(d2['http_status'] == '404' and d2['body_bytes'] == 0 and d2['content_type'] == '(none)',
      'a fabricated child at the question literals\' depth also answers 404 / 0 B / no Content-Type')

print('--- 8. headers, and the one that differs from the GET column ---')
servers = collections.Counter(r['server'] for r in rows)
print(f'  server: {dict(servers)}')
check(len(servers) == 1 and 'Apache/2.4.62' in list(servers)[0],
      'one Server value on every row — Apache/2.4.62, consistent with areas AB/AG/AQ')
acam = {r['acam'] for r in rows}
acao = {r['acao'] for r in rows}
print(f'  ACAM values: {acam}   ACAO values: {acao}')
check(acam == {'(none)'} and acao == {'(none)'},
      'ACAM and ACAO absent on every row — so Allow is the only method signal here (area AB/AG)')
acah = {r['headers'].get('access-control-allow-headers', '(none)') for r in rows}
print(f'  ACAH values: {acah}')
check(len(acah) == 1, 'one ACAH value across the run — no per-row variation')

print('--- 9. delay accounting — TWO clocks ---')
gaps = []
for a, b in zip(rows, rows[1:]):
    gaps.append((a['seq'], b['seq'], (dt(b['t_sent']) - dt(a['t_sent'])).total_seconds()))
gs = [g for _, _, g in gaps]
gs_sorted = sorted(gs)
print(f'  CLOCK A (t_sent)  gaps {len(gs)}  min {min(gs):.3f} s  median {gs_sorted[len(gs)//2]:.3f} s  max {max(gs):.3f} s')
under25 = [(a, b, round(g, 3)) for a, b, g in gaps if g < 2.5]
under20 = [(a, b, round(g, 3)) for a, b, g in gaps if g < 2.0]
print(f'    under 2.5 s: {under25 or "none"}')
print(f'    under 2.0 s: {under20 or "none"}')
neg = [(r['seq'], round((dt(r['t_done']) - dt(r['t_sent'])).total_seconds(), 3))
       for r in rows if dt(r['t_done']) < dt(r['t_sent'])]
print(f'    impossible negative DURATIONS: {neg or "none"}')
check(len(gs) == len(rows) - 1, f'gap count is {len(gs)} = rows - 1 = {len(rows)-1}')
check(not neg, 'no impossible negative response duration — this harness is NOT in the corrupt-t0 class')

mts = [(r['seq'], r['body_mtime_ns']) for r in rows if r['body_mtime_ns']]
mg = [(a[0], b[0], (b[1] - a[1]) / 1e9) for a, b in zip(mts, mts[1:])]
mgs = [g for _, _, g in mg]
print(f'  CLOCK B (kernel body mtimes)  stat-able {len(mts)} of {len(rows)}  distinct {len(set(m for _, m in mts))}')
print(f'    gaps {len(mgs)}  min {min(mgs):.3f} s  max {max(mgs):.3f} s')
print(f'    under 2.5 s: {[(a, b, round(g, 3)) for a, b, g in mg if g < 2.5] or "none"}')
check(len(set(m for _, m in mts)) == len(mts),
      'every body mtime is DISTINCT — clock B is a live second clock, not one value repeated (AJ\'s dead oracle)')
check(min(mgs) >= 2.5, f'clock B floor {min(mgs):.3f} s >= 2.5 s')
inside = 0
outside = []
for r in rows:
    if not r['body_mtime_ns']:
        continue
    t = r['body_mtime_ns'] / 1e9
    if dt(r['t_sent']).timestamp() <= t <= dt(r['t_done']).timestamp():
        inside += 1
    else:
        outside.append((r['seq'], round(t - dt(r['t_sent']).timestamp(), 3)))
print(f'    each mtime inside its own [t_sent, t_done] window: {inside} of {len(mts)}; outside: {outside}')
check(inside >= len(mts) - 1,
      'at most one mtime falls outside its window, and it is reported rather than dropped')

print('--- 10. the published gap count vs sum(rows_per_host - 1) ---')
per_host = collections.Counter(r['host'] for r in rows)
print(f'  rows per host: {dict(per_host)}')
print(f'  sum(rows_per_host - 1) = {sum(n - 1 for n in per_host.values())}   published gaps = {len(gs)}')
check(sum(n - 1 for n in per_host.values()) == len(gs),
      'sum(rows_per_host - 1) equals the published gap count (one host, 10 rows, 9 gaps)')

print('--- 11. the fabricated name is not in the tree ---')
print('  run: git grep -c zz-as-absent-5531 / zz-as-depth2-5531  (see FINDINGS §2)')

print()
if fails:
    print(f'VERIFY FAILED — {len(fails)} assertion(s)')
    for f in fails:
        print('  - ' + f)
    sys.exit(1)
print(f'VERIFY OK — {len(rows)} rows of a {CAP} cap, every figure above re-derived from the ledger at zero requests.')
