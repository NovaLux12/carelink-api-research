#!/usr/bin/env python3
"""matrix.py — turn results.jsonl into the version x host verdict table.

Reads only the ledger this pass wrote (`results.jsonl`). It re-derives every
verdict from the recorded status + `x-amzn-errortype` + content-type +
body digest, per Oracle A (`docs/09` §2) — status alone is never consulted,
because on `clcloud.*` the 403 line is uniform and useless (AGENTS.md §7).

The classification is deliberately FAIL-CLOSED: a response that does not match
one of the recorded classes is printed as AMBIGUOUS rather than being forced
into the nearest one. An unexpected `x-amzn-errortype` is a finding about the
oracle, not permission to pick the convenient class.

Usage:  python3 matrix.py            (from this directory)
"""

import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, 'results.jsonl')

# The corpus no-route digest, recorded in ORACLE-PROBE-MATRIX.md and
# reproduced byte-for-byte by every no-route capture in the repo.
NOROUTE_SHA = 'f249b63cb2fc'
NOROUTE_BYTES = 42

HOSTS = ['clcloud.minimed.eu', 'clcloud.minimed.com', 'clcloud-trials.minimed.com']
SHORT = {'clcloud.minimed.eu': '.eu',
         'clcloud.minimed.com': '.com',
         'clcloud-trials.minimed.com': '-trials'}


def classify(r):
    """Return (class_name, detail). Fails closed to AMBIGUOUS."""
    st = r['status']
    et = (r.get('x_amzn_errortype') or '').strip()
    ct = (r.get('content_type') or '').strip()
    cum = r.get('x_cum_signature_present') == 'yes'
    n = r['bytes']
    sha = (r.get('body_sha256') or '')

    if st == 403:
        if et.startswith('MissingAuthenticationTokenException') \
                and n == NOROUTE_BYTES and sha.startswith(NOROUTE_SHA):
            return ('no-route',
                    '403 MissingAuthenticationTokenException, 42 B, corpus no-route digest')
        if et.startswith('MissingAuthenticationTokenException'):
            return ('AMBIGUOUS',
                    f'403 MissingAuthenticationTokenException but {n} B / sha {sha[:12]} '
                    '— matches neither the corpus digest nor any other recorded shape')
        return ('AMBIGUOUS',
                f'403 with unexpected x-amzn-errortype {et!r}')
    if st == 401:
        if et.startswith('UnauthorizedException'):
            return ('routed-token-gated', '401 UnauthorizedException — routed, token-gated')
        return ('AMBIGUOUS', f'401 with unexpected x-amzn-errortype {et!r}')
    if st == 200:
        if cum:
            return ('served-signed', '200 + x-cum-signature — a signed discovery document')
        return ('served-unsigned',
                '200 WITHOUT x-cum-signature — not the signed-document shape; '
                'a catch-all on this host would look like this')
    if st == 204:
        return ('served-empty', '204 — routed, returns nothing')
    return ('AMBIGUOUS', f'unexpected status {st}')


def main():
    rows = []
    with open(LEDGER) as fh:
        for line in fh:
            if line.strip():
                rows.append(json.loads(line))

    print(f'ledger rows: {len(rows)}')
    seqs = [r['seq'] for r in rows]
    assert seqs == sorted(seqs) and seqs == list(range(1, len(rows) + 1)), \
        'seq is not 1..N in send order'

    # ---- per-host control outcomes -------------------------------------
    print('\n--- controls, in send order ---')
    for r in rows:
        if r['role'].startswith('control'):
            cls, detail = classify(r)
            print(f"  seq {r['seq']:>2}  {r['host']:<28} {r['ver']:<4} "
                  f"-> {r['status']}  {cls:<20} {detail}")

    # ---- the grid -------------------------------------------------------
    cell = {}
    for r in rows:
        cell[(r['ver'], r['host'])] = classify(r)[0]

    versions = [f'v{i}' for i in range(1, 17)]
    controls = sorted({r['ver'] for r in rows} - set(versions))

    print('\n--- verdict grid: version x host ---')
    print(f"{'ver':<5}" + ''.join(f'{SHORT[h]:<26}' for h in HOSTS) + 'splits?')
    for v in controls + versions:
        if (v, HOSTS[0]) not in cell:
            continue
        cs = [cell.get((v, h), 'MISSING') for h in HOSTS]
        distinct = sorted(set(cs))
        tag = '' if len(distinct) == 1 else 'SPLIT -> ' + ' | '.join(distinct)
        tag = f'{"uniform (" + distinct[0] + ")":<26}' if not tag else tag
        print(f'{v:<5}' + ''.join(f'{c:<26}' for c in cs) + tag)

    # ---- body-digest grouping ------------------------------------------
    print('\n--- distinct bodies by class ---')
    groups = defaultdict(list)
    for r in rows:
        groups[(classify(r)[0], r['body_sha256'][:12], r['bytes'])].append(
            f"{r['host']}/{r['ver']}")
    for (cls, sha, n), members in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        print(f'  {cls:<20} {sha}  {n:>6} B  x{len(members):<3} {" ".join(members)}')

    # ---- measured spacing ----------------------------------------------
    print('\n--- measured same-host send spacing (floor is 2.5 s declared, '
          '>=2 s repo floor) ---')
    per_host = defaultdict(list)
    for r in rows:
        per_host[r['host']].append(float(r['t_sent']))
    overall_min = None
    for h in HOSTS:
        ts = per_host[h]
        gaps = [b - a for a, b in zip(ts, ts[1:])]
        if not gaps:
            continue
        mn = min(gaps)
        overall_min = mn if overall_min is None else min(overall_min, mn)
        under25 = sum(1 for g in gaps if g < 2.5)
        under20 = sum(1 for g in gaps if g < 2.0)
        print(f'  {h:<28} {len(gaps)} gaps  min {mn:.3f} s  '
              f'max {max(gaps):.3f} s  under 2.5 s: {under25}  under 2.0 s: {under20}')
    print(f'  MEASURED t_sent FLOOR: {overall_min:.3f} s')

    # ---- the question ----------------------------------------------------
    print('\n--- cross-host split, over the 16 matrix versions only ---')
    splits, ambiguous = [], []
    for v in versions:
        cs = [cell.get((v, h), 'MISSING') for h in HOSTS]
        if 'MISSING' in cs or 'AMBIGUOUS' in cs:
            ambiguous.append((v, cs))
        elif len(set(cs)) > 1:
            splits.append((v, cs))
    print(f'  versions compared across all three hosts: '
          f'{sum(1 for v in versions if all((v, h) in cell for h in HOSTS))}')
    print(f'  SPLITS: {len(splits)} -> {[(v, cs) for v, cs in splits] or "none"}')
    print(f'  AMBIGUOUS / incomplete: {ambiguous or "none"}')
    print(f'  v6 row: {cell.get(("v6", HOSTS[0]))} / {cell.get(("v6", HOSTS[1]))} / '
          f'{cell.get(("v6", HOSTS[2]))}')

    return 0


if __name__ == '__main__':
    sys.exit(main())