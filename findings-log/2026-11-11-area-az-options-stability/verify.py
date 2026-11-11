#!/usr/bin/env python3
"""Area AZ — re-derive every published figure from the committed ledgers, at zero requests.

Exits 0 only when every one holds. Any printed FAIL is a published claim that has moved.

Checks:
  1. 23 rows, 3 hosts, row counts 8/8/7, and 20 same-host gaps == sum(rows_per_host - 1).
  2. Every control row is 403 / 42 B / the full no-route digest, on its own host.
  3. Each of the nine reproduction cells matches the AY ledger's answer for the same
     (host, method, path) on status, byte count, digest, ACAO and ACAM.
  4. Both depth-2 cells are 403 / 42 B / the no-route digest with no ACAO.
  5. Clock A: no gap under 2.5 s and no impossible negative duration.
  6. Clock B: 23 of 23 distinct body mtimes, no same-host gap under 2.5 s, and every mtime
     inside its own [t_sent, t_done] window (so it is a second clock, not one batch stamp).
  7. The stated gap since the AY pass, in hours, computed from the two ledgers.
"""
import json, sys
from collections import defaultdict
from datetime import datetime, timezone

AZ = 'findings-log/2026-11-11-area-az-options-stability/results.jsonl'
AY = 'findings-log/2026-11-11-area-aq-options-per-route/results.jsonl'
DIGEST_ABSENT = 'f249b63cb2fcb66b47e86f906c98f8fd912e82dd035b4e53d7e72fc1960cfd16'
FAIL = []


def load(p):
    return [json.loads(l) for l in open(p) if l.strip()]


def ts(s):
    return datetime.fromisoformat(s.replace('Z', '+00:00')).timestamp()


def check(cond, msg):
    print(('  ok   ' if cond else '  FAIL ') + msg)
    if not cond:
        FAIL.append(msg)


az = load(AZ)
ay = load(AY)

# 1 — row and gap counts
per_host = defaultdict(list)
for r in az:
    per_host[r['host']].append(r)
for v in per_host.values():
    v.sort(key=lambda r: r['seq'])
check(len(az) == 23, f'23 rows in the ledger (got {len(az)})')
check(len(per_host) == 3, f'3 hosts (got {len(per_host)})')
check([len(per_host[h]) for h in sorted(per_host)] == [7, 8, 8],
      'row counts 7/8/8 across the three hosts (got '
      f'{[len(per_host[h]) for h in sorted(per_host)]})')
gaps_n = sum(len(v) - 1 for v in per_host.values())
check(gaps_n == 20, f'20 same-host gaps == sum(rows_per_host - 1) (got {gaps_n})')

# 2 — controls are gates
controls = [r for r in az if r['method'] == 'GET']
check(len(controls) == 3, f'3 control GETs (got {len(controls)})')
for r in controls:
    check(r['http_status'] == '403' and r['body_bytes'] == 42 and r['body_sha256'] == DIGEST_ABSENT,
          f"control on {r['host']} is 403/42 B/no-route digest "
          f"(got {r['http_status']}/{r['body_bytes']}/{r['body_sha256'][:16]})")

# 3 — the nine reproduction cells against the AY ledger
ay_by = {(r['host'], r['method'], r['path']): r for r in ay}
repro = [r for r in az if r['tag'].startswith('r-')]
check(len(repro) == 18, f'18 reproduction cells, fabricated and leaf (got {len(repro)})')
matched = 0
for r in repro:
    ref = ay_by.get((r['host'], r['method'], r['path']))
    if ref is None:
        check(False, f"no AY row for {r['host']} {r['method']} {r['path']}")
        continue
    same = all(r[k] == ref[k] for k in
               ('http_status', 'body_bytes', 'body_sha256', 'acao', 'acam', 'errortype'))
    matched += same
    check(same, f"{r['tag']}: reproduces AY seq {ref['seq']} on status/bytes/digest/ACAO/ACAM "
                f"({r['http_status']}/{r['body_bytes']}/{r['acao']}/{r['acam']})")
check(matched == 18, f'18 of 18 reproduction cells match AY (got {matched})')

# the nine fabricated siblings in particular
fabs = [r for r in repro if r['tag'].endswith('-fab')]
check(len(fabs) == 9, f'9 fabricated-sibling cells (got {len(fabs)})')
for r in fabs:
    check(r['http_status'] == '403' and r['body_bytes'] == 42 and
          r['body_sha256'] == DIGEST_ABSENT and r['acao'] == '(none)',
          f"{r['host']} {r['path']}: 403 at the no-route digest, 42 B, no ACAO")
leaves = [r for r in repro if r['tag'].endswith('-leaf')]
check(len(leaves) == 9, f'9 real-leaf cells (got {len(leaves)})')
for r in leaves:
    check(r['http_status'] == '200' and r['body_bytes'] == 0 and r['acao'] == '*',
          f"{r['host']} {r['path']}: 200, 0 B, ACAO * (got {r['http_status']}/{r['body_bytes']}/{r['acao']})")

# 4 — depth-2 cells
d2 = [r for r in az if r['tag'].startswith('d2-')]
check(len(d2) == 2, f'2 depth-2 cells (got {len(d2)})')
for r in d2:
    check(r['http_status'] == '403' and r['body_bytes'] == 42 and
          r['body_sha256'] == DIGEST_ABSENT and r['acao'] == '(none)',
          f"{r['host']} {r['path']}: depth 2 is 403 at the no-route digest, no ACAO")

# 5 — clock A
floor_a = None
under_a = 0
for h, v in per_host.items():
    for i in range(len(v) - 1):
        g = ts(v[i + 1]['t_sent']) - ts(v[i]['t_sent'])
        floor_a = g if floor_a is None else min(floor_a, g)
        if g < 2.5:
            under_a += 1
negs = [r['seq'] for r in az if ts(r['t_done']) < ts(r['t_sent'])]
check(under_a == 0, f'clock A: 0 of 20 gaps under 2.5 s (got {under_a})')
check(not negs, f'clock A: no impossible negative duration (got {negs})')
check(floor_a is not None and floor_a >= 2.5, f'clock A floor {floor_a:.3f} s >= 2.5')

# 6 — clock B
mt = [float(r['body_mtime']) for r in az]
check(len(set(mt)) == 23, f'clock B: 23 of 23 distinct body mtimes (got {len(set(mt))})')
floor_b = None
under_b = 0
for h, v in per_host.items():
    for i in range(len(v) - 1):
        g = float(v[i + 1]['body_mtime']) - float(v[i]['body_mtime'])
        floor_b = g if floor_b is None else min(floor_b, g)
        if g < 2.5:
            under_b += 1
check(under_b == 0, f'clock B: 0 of 20 gaps under 2.5 s (got {under_b})')
check(floor_b is not None and floor_b >= 2.5, f'clock B floor {floor_b:.3f} s')
outside = [r['seq'] for r in az
           if not (ts(r['t_sent']) - 0.05 <= float(r['body_mtime']) <= ts(r['t_done']) + 0.05)]
check(not outside, f'clock B: every mtime inside its own [t_sent, t_done] window (outside: {outside})')

# 7 — the gap since the AY pass
ay_first = min(ts(r['t_sent']) for r in ay)
az_first = min(ts(r['t_sent']) for r in az)
hours = (az_first - ay_first) / 3600.0
check(10.0 < hours < 11.0, f'gap since the AY pass is {hours:.2f} h (expected the 10.2 h published)')

print()
if FAIL:
    print(f'VERIFY FAIL — {len(FAIL)} claim(s) moved')
    sys.exit(1)
print(f'VERIFY OK — 18 of 18 reproduction cells reproduce AY, 9 of 9 fabricated siblings at the '
      f'no-route digest, 2 of 2 depth-2 cells the same, both clocks clean, {hours:.2f} h since AY.')
