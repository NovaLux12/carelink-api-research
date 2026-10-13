#!/usr/bin/env python3
"""Area E spacing measurement — offline, zero requests.

Counting rule (docs/09 §4, the row that answers area D's open question):
  * one gap per consecutive pair IN REQUEST ORDER, same host only;
  * the AUTHORITY is the body-file mtime, which the kernel sets at write time and
    which is therefore independent of the harness's own clock;
  * the harness `date` series is reported ALONGEside, never instead, because it
    has produced sub-declared gaps and negative durations in five prior passes;
  * the mtime series is validated before it is trusted — a trustworthy run's
    mtime span equals the harness t_sent span. (Git does not preserve mtimes, so
    the epoch values are carried in results.jsonl; a fresh clone would collapse
    the spread to 0.0 s and this script would report that rather than hide it.)
  * sub-declared gaps are reported at full resolution and never rounded away,
    and no cause is asserted for any of them.

Writes spacing.txt next to results.jsonl.
"""

import json
import os
import sys

RESULTS = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(RESULTS))
rows = [json.loads(l) for l in open(RESULTS, encoding='utf-8') if l.strip()]

DECLARED = 2.5
FLOOR = 2.0


def ms(iso):
    import datetime
    t = iso.rstrip('Z')
    dt = datetime.datetime.strptime(t, '%Y-%m-%dT%H:%M:%S.%f')
    return dt.replace(tzinfo=datetime.timezone.utc).timestamp() * 1000.0


out = open(os.path.join(HERE, 'spacing.txt'), 'w', encoding='utf-8')


def emit(s=''):
    print(s)
    out.write(s + '\n')


hosts = []
for r in rows:
    if r['host'] not in hosts:
        hosts.append(r['host'])

emit('Area E — spacing measurement')
emit(f'declared: {DECLARED} s sleep inside the per-host flock; repo floor {FLOOR} s')
emit(f'counting rule: consecutive pairs in request order, per host; '
     f'BODY mtime is the authority (docs/09 section 4)')
emit()

grand = {}
for h in hosts:
    hr = [r for r in rows if r['host'] == h]
    gaps = []
    for a, b in zip(hr, hr[1:]):
        gaps.append(('mtime', (b['body_mtime_ms'] - a['body_mtime_ms']) / 1000.0, a['seq'], b['seq']))
    for a, b in zip(hr, hr[1:]):
        gaps.append(('tsent', (ms(b['t_sent']) - ms(a['t_sent'])) / 1000.0, a['seq'], b['seq']))
    mg = [g[1] for g in gaps if g[0] == 'mtime']
    sg = [g[1] for g in gaps if g[0] == 'tsent']
    neg = [r for r in hr if ms(r['t_done']) < ms(r['t_sent'])]
    span_m = (hr[-1]['body_mtime_ms'] - hr[0]['body_mtime_ms']) / 1000.0
    span_t = (ms(hr[-1]['t_sent']) - ms(hr[0]['t_sent'])) / 1000.0
    grand[h] = dict(mg=mg, sg=sg, neg=neg, span_m=span_m, span_t=span_t,
                    under_declared=[g for g in gaps if g[0] == 'mtime' and g[1] < DECLARED],
                    under_floor=[g for g in gaps if g[0] == 'mtime' and g[1] < FLOOR])
    emit(f'--- {h} ---')
    emit(f'  requests {hr[0]["seq"]}..{hr[-1]["seq"]} ({len(hr)} rows)')
    emit(f'  mtime series  : {len(mg)} gaps, min {min(mg):.3f} s, max {max(mg):.3f} s, '
         f'span {span_m:.1f} s')
    emit(f'    under the declared {DECLARED} s: {len(grand[h]["under_declared"])}   '
         f'under the {FLOOR} s floor: {len(grand[h]["under_floor"])}')
    for kind, v, a, b in grand[h]['under_declared']:
        emit(f'      seq {a}->{b}: {v:.3f} s')
    emit(f'  t_sent series : {len(sg)} gaps, min {min(sg):.3f} s, max {max(sg):.3f} s, '
         f'span {span_t:.1f} s')
    emit(f'    under the declared {DECLARED} s: '
         f'{len([1 for v in sg if v < DECLARED])}   under the {FLOOR} s floor: '
         f'{len([1 for v in sg if v < FLOOR])}')
    emit(f'  NEGATIVE durations (t_done < t_sent, impossible): {len(neg)}'
         + (f' — seq {[r["seq"] for r in neg]}' if neg else ''))
    emit(f'  span agreement (mtime vs t_sent): {abs(span_m - span_t):.3f} s — '
         f'{"series is the run\'s own" if abs(span_m - span_t) < 5 else "DIVERGENT"}')
    emit()

allmg = [g for h in hosts for g in grand[h]['mg']]
allsg = [g for h in hosts for g in grand[h]['sg']]
emit('=== pass total ===')
emit(f'  bodies: {len(rows)}   same-host gaps: {len(allmg)}')
emit(f'  mtime floor (the authority): {min(allmg):.3f} s   '
     f'under 2.5 s: {len([g for g in allmg if g < DECLARED])}   '
     f'under 2.0 s: {len([g for g in allmg if g < FLOOR])}')
emit(f'  t_sent floor (reported alongside): {min(allsg):.3f} s   '
     f'under 2.5 s: {len([g for g in allsg if g < DECLARED])}   '
     f'under 2.0 s: {len([g for g in allsg if g < FLOOR])}')
emit(f'  negative durations across the pass: {sum(len(grand[h]["neg"]) for h in hosts)}')
out.close()