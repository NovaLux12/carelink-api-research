#!/usr/bin/env python3
"""ledger.py — build results.jsonl from the files probe.sh left on disk.

Issues ZERO requests. One row per request, in the schema the pool brief
requires, so every claim in FINDINGS.md can be cited to a row and the row count
equals the request count.

Columns read from run.log:
  seq, cc, role, http_status, curl_exit, t_queued, t_sent, t_done
Everything else is derived from headers/<tag>.h and bodies/<tag>.json.

Writes:
  results.jsonl          one JSON object per request
  spacing.txt            the measured same-host gap series, both timestamp
                         conventions, with every gap under the declared 2.5 s
                         listed individually rather than summarised away
"""

import hashlib
import json
import os
import re
import sys
from datetime import datetime

DIR = os.path.dirname(os.path.abspath(__file__))
HOST = 'carelink.minimed.eu'
PATH_FMT = '/patient/countries/settings?countryCode=%s'


def parse_headers(path):
    hdrs = {}
    raw = ''
    if os.path.exists(path):
        with open(path, encoding='utf-8', errors='replace') as fh:
            raw = fh.read()
        block = raw.strip().split('\r\n\r\n')[-2] if '\r\n\r\n' in raw else raw
        for line in block.replace('\r\n', '\n').split('\n'):
            if ':' in line:
                k, _, v = line.partition(':')
                hdrs[k.strip().lower()] = v.strip()
    return hdrs, raw


def ts(s):
    if not s or s == '(none)':
        return None
    return datetime.strptime(s, '%Y-%m-%dT%H:%M:%S.%fZ')


def main():
    rows = []
    with open(os.path.join(DIR, 'run.log'), encoding='utf-8') as fh:
        for line in fh:
            if line.startswith('#') or not line.strip():
                continue
            parts = line.rstrip('\n').split('\t')
            if len(parts) < 8:
                continue
            seq, cc, role, code, cexit, tq, tsent, tdone = parts[:8]
            tag = f'cc-{cc}'
            body_path = os.path.join(DIR, 'bodies', f'{tag}.json')
            hdr_path = os.path.join(DIR, 'headers', f'{tag}.h')
            hdrs, ctype_full = parse_headers(hdr_path)
            raw = b''
            if os.path.exists(body_path):
                with open(body_path, 'rb') as fh:
                    raw = fh.read()
            rows.append({
                'seq': int(seq),
                'host_seq': int(seq),      # one host only in this pass
                'host': HOST,
                'host_tag': tag,
                'method': 'GET',
                'path': PATH_FMT % cc,
                'role': role,
                'sent_headers': 'User-Agent: carelink-bridge-research/1.0 (area D, research); Accept-Encoding: deflate, gzip (curl --compressed). No Authorization, no Cookie, no api-key.',
                'http_status': code,
                'curl_exit': cexit,
                'content_type': hdrs.get('content-type', '(none)'),
                'content_encoding': hdrs.get('content-encoding', '(none)'),
                'content_length': hdrs.get('content-length', '(none)'),
                'vary': hdrs.get('vary', '(none)'),
                'server': hdrs.get('server', '(none)'),
                'ctype_full': '|'.join(f'{k}: {v}' for k, v in hdrs.items()),
                'body_bytes': len(raw),
                'body_sha256': hashlib.sha256(raw).hexdigest(),
                't_queued': tq,
                't_sent': tsent,
                't_done': tdone,
                'err': (open(os.path.join(DIR, 'headers', f'{tag}.err'),
                             encoding='utf-8', errors='replace').read().strip()
                        if os.path.exists(os.path.join(DIR, 'headers', f'{tag}.err'))
                        else '(none)')[:200],
            })

    with open(os.path.join(DIR, 'results.jsonl'), 'w', encoding='utf-8') as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + '\n')

    # --- spacing ------------------------------------------------------------
    lines = []
    for series, key in (('t_sent', 't_sent'), ('t_queued', 't_queued')):
        times = [(r['seq'], ts(r[key])) for r in rows if ts(r[key])]
        gaps = []
        for (s1, t1), (s2, t2) in zip(times, times[1:]):
            gaps.append((s2 - s1, s1, s2, (t2 - t1).total_seconds()))
        if not gaps:
            continue
        under = [g for g in gaps if g[3] < 2.5]
        under2 = [g for g in gaps if g[3] < 2.0]
        lines.append(f'{series}: gaps={len(gaps)} >=2.5s={len(gaps) - len(under)} '
                     f'<2.5s={len(under)} <2.0s={len(under2)} '
                     f'min={min(g[3] for g in gaps):.3f}s '
                     f'max={max(g[3] for g in gaps):.3f}s')
        for d, s1, s2, v in sorted(under, key=lambda g: g[3]):
            lines.append(f'  {v:.3f}s  seq {s1} -> {s2}')
    with open(os.path.join(DIR, 'spacing.txt'), 'w', encoding='utf-8') as fh:
        fh.write('# Measured same-host gaps on ' + HOST + ' (the only host this\n')
        fh.write('# pass contacted). Both timestamp conventions are reported: the\n')
        fh.write('# declared-sleep series (t_sent, in-lock after the sleep) and the\n')
        fh.write('# queue series (t_queued, before the lock is taken). The repo rule\n')
        fh.write('# is >= 2 s on the same host. No cause is asserted for any gap\n')
        fh.write('# below the harness\'s declared 2.5 s.\n')
        fh.write('\n'.join(lines) + '\n')
    print('\n'.join(lines))
    print(f'\nrows={len(rows)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())