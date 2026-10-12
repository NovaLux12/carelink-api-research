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
    # The CANONICAL series is the body-file mtime, not the harness `date`.
    # curl wrote each body with -o bodies/cc-XX.json, so the kernel set that
    # mtime when the write completed — a series independent of the harness's
    # own clock, which is the thing under suspicion. Reported first and labelled
    # canonical; the `date` series follow, labelled non-canonical, because they
    # disagree with it and the disagreement is the finding.
    #
    # LIMIT, stated in the output: git does not preserve mtimes, so on a fresh
    # clone or `git archive` this series collapses to a 0.0 s spread. It is valid
    # on the machine that ran the probe, and the numbers are what get committed.
    lines = []
    mt = []
    for r in rows:
        cc = r['path'].split('countryCode=')[1]
        p = os.path.join(DIR, 'bodies', f'cc-{cc}.json')
        if os.path.exists(p):
            mt.append((r['seq'], cc, os.stat(p).st_mtime))
    mt.sort(key=lambda x: x[0])
    mg = [(mt[i + 1][1], mt[i][1], mt[i + 1][2] - mt[i][2])
          for i in range(len(mt) - 1)]
    if mg:
        span = mt[-1][2] - mt[0][2]
        lines.append('CANONICAL — bodies/ mtime (kernel-set at write time)')
        lines.append(f'  counting rule: one gap per consecutive pair in run.log '
                     f'REQUEST ORDER,')
        lines.append(f'  (mtime[n+1]) - (mtime[n]); {len(mt)} bodies, {len(mg)} '
                     f'gaps; the two 400')
        lines.append('  envelopes (ZZ, ID) are included. min %.3fs  max %.3fs  '
                     '<2.5s: %d  <2.0s: %d'
                     % (min(x[2] for x in mg), max(x[2] for x in mg),
                        sum(1 for x in mg if x[2] < 2.5),
                        sum(1 for x in mg if x[2] < 2.0)))
        lines.append(f'  span: {span:.1f}s')
        # Guard against reading an oracle that is really a checkout artefact:
        # the mtime span must equal the harness span, or the series is not the
        # run's own. Reported either way, never silently.
        hspan = (ts(rows[-1]['t_sent']) - ts(rows[0]['t_sent'])).total_seconds()
        agree = abs(span - hspan) < 1.0
        lines.append(f'  cross-check vs t_sent span {hspan:.1f}s: '
                     f'{"AGREES - these are the run files" if agree else "DISAGREES - series is NOT the run"}')
        lines.append('')
        lines.append('NON-CANONICAL — harness `date` series (see FINDINGS.md §1;')
        lines.append('they cannot all be faithful: negative durations are present. '
                     'No cause asserted.)')
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
        fh.write('# pass contacted).\n')
        fh.write('#\n')
        fh.write('# THE CANONICAL MEASUREMENT IS THE MTIME ONE, NOT THE `date` ONE.\n')
        fh.write('#\n')
        fh.write('# ORACLE: body-file mtimes. probe.sh writes each response body\n')
        fh.write('# with `-o bodies/cc-XX.json`, so the kernel sets that mtime when\n')
        fh.write('# the write completes. It is independent of the harness\'s own\n')
        fh.write('# `date` calls, which is what makes it the one series here that\n')
        fh.write('# does not depend on the thing under suspicion.\n')
        fh.write('#\n')
        fh.write('# LIMIT OF THIS ORACLE — read before reusing it. Git does NOT\n')
        fh.write('# preserve mtimes: on a fresh clone or `git archive` the body\n')
        fh.write('# files all carry the checkout time and the spread collapses to\n')
        fh.write('# 0.0 s. Valid only on the machine that ran the probe, so the\n')
        fh.write('# NUMBERS get committed. Verify the series is real before\n')
        fh.write('# trusting it: the mtime span should equal the harness span.\n')
        fh.write('#\n')
        fh.write('# The `date` series follow, reported because they disagree with\n')
        fh.write('# the canonical one and the disagreement is itself the finding.\n')
        fh.write('# No cause is asserted for any gap below the declared 2.5 s.\n')
        fh.write('\n'.join(lines) + '\n')
    print('\n'.join(lines))
    print(f'\nrows={len(rows)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())