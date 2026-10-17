#!/usr/bin/env python3
"""spacing.py — two-clock check of this pass's own request spacing.

`docs/09` §4 is explicit that the `date` series is the suspect instrument on
this repo's harnesses, and that the kernel's body-write mtime is the counter.
So this pass measures BOTH, per host, and publishes the per-gap difference
rather than only the endpoints — a span comparison telescopes to the first
row's latency and cannot detect interior corruption (`AGENTS.md` §6 item 2).

Counting rule (the repo's, from `docs/09` §4): one gap per consecutive pair in
REQUEST ORDER, restricted to same-host pairs. N bodies give N-1 gaps.

The mtime series is printed at full resolution because git does not preserve
mtimes, so a verifier on a fresh clone cannot re-derive it from the files.

Zero requests. Run after probe.sh.
"""

import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, 'results.jsonl')
OUT = os.path.join(HERE, 'spacing.txt')

HOSTS = ['clcloud.minimed.eu', 'clcloud.minimed.com', 'clcloud-trials.minimed.com']


def main():
    rows = []
    with open(LEDGER) as fh:
        for line in fh:
            if line.strip():
                rows.append(json.loads(line))

    per_host = defaultdict(list)
    for r in rows:
        body = os.path.join(HERE, 'headers', r['capture'] + '.b')
        mt = os.stat(body).st_mtime  # kernel sets this at write time
        per_host[r['host']].append({
            'seq': r['seq'],
            't_sent': float(r['t_sent']),
            't_done': float(r['t_done']),
            'mtime': mt,
        })

    lines = []
    def emit(s=''):
        print(s)
        lines.append(s)

    emit('Two-clock spacing check — discover 3-host matrix, 2026-10-17')
    emit('Counting rule: one gap per consecutive same-host pair in request order;')
    emit('N bodies give N-1 gaps. Declared delay 2.5 s; repo floor >=2 s.')
    emit()

    negatives = [h for h in per_host
                 if any(r['t_done'] < r['t_sent'] for r in per_host[h])]
    emit('## 0. Self-conviction check — impossible durations (t_done < t_sent)')
    if negatives:
        for h in negatives:
            for r in per_host[h]:
                if r['t_done'] < r['t_sent']:
                    emit(f'  {h} seq {r["seq"]}: t_done - t_sent = '
                         f'{r["t_done"] - r["t_sent"]:+.6f} s  (IMPOSSIBLE)')
    else:
        emit('  0 of %d rows carry a negative duration — the date series is not'
             % len(rows))
        emit('  self-refuting on this pass, so its gaps are evidence, not artefacts.')
    emit()

    worst = None
    for h in HOSTS:
        if h not in per_host:
            continue
        rs = per_host[h]
        send = [b['t_sent'] - a['t_sent'] for a, b in zip(rs, rs[1:])]
        mt = [b['mtime'] - a['mtime'] for a, b in zip(rs, rs[1:])]
        diff = [abs(s - m) for s, m in zip(send, mt)]
        emit(f'## {h}')
        emit(f'  gaps: {len(rs) - 1}   bodies: {len(rs)}')
        emit(f'  t_sent series : min {min(send):.3f} s  max {max(send):.3f} s  '
             f'under 2.5 s: {sum(1 for g in send if g < 2.5)}  '
             f'under 2.0 s: {sum(1 for g in send if g < 2.0)}')
        emit(f'  mtime  series : min {min(mt):.3f} s  max {max(mt):.3f} s  '
             f'under 2.5 s: {sum(1 for g in mt if g < 2.5)}  '
             f'under 2.0 s: {sum(1 for g in mt if g < 2.0)}')
        emit(f'  per-gap |send - mtime| : max {max(diff):.3f} s  '
             f'median {sorted(diff)[len(diff) // 2]:.4f} s  '
             f'disagreeing >0.5 s: {sum(1 for d in diff if d > 0.5)}')
        emit(f'  span check: mtime span {max(r["mtime"] for r in rs) - min(r["mtime"] for r in rs):.3f} s'
             f'  vs t_sent span {max(r["t_sent"] for r in rs) - min(r["t_sent"] for r in rs):.3f} s'
             f'  vs t_done span {max(r["t_done"] for r in rs) - min(r["t_done"] for r in rs):.3f} s')
        emit('  per-row (microsecond mtime series, so a fresh clone can re-read it):')
        for a, b, s, m, d in zip(rs, rs[1:], send, mt, diff):
            flag = '  <-- send gap under the declared 2.5 s' if s < 2.5 else ''
            emit(f'    {a["seq"]:>2}->{b["seq"]:<2} send {s:.6f}  mtime {m:.6f}  '
                 f'|d| {d:.6f}{flag}')
        if worst is None or min(send) < worst[0]:
            worst = (min(send), h)
        emit()

    emit(f'## measured floor')
    emit(f'  t_sent series, same-host, all three hosts: {worst[0]:.3f} s ({worst[1]})')
    emit(f'  mtime series  is reported per host above and is the counter the page trusts.')

    with open(OUT, 'w') as fh:
        fh.write('\n'.join(lines) + '\n')
    print(f'\nwrote {OUT}')
    return 0


if __name__ == '__main__':
    sys.exit(main())