#!/bin/bash
# Area V spacing measurement — ZERO requests, re-derived from the captured
# bodies and the ledger. Two independent series, per docs/09 §4:
#
#   SEND series  : t_sent deltas from results.jsonl. t_sent is emitted INSIDE
#                  the per-host flock immediately before curl execs, so it is
#                  the instant the request left this machine.
#   MTIME series : kernel write-time of each body file (st_mtime_ns). Set by the
#                  kernel, independent of the harness clock.
#
# The series is VALIDATED before use: a trustworthy run's mtime span equals the
# harness span. If they disagree the mtime series is rejected, not reported.
#
# DISCLOSED LIMIT: results.jsonl's body_mtime_epoch column comes from
# `stat -c%Y`, which truncates to whole seconds and therefore cannot resolve a
# 2.5 s sleep. The sub-second figure below is re-stat'ed with nanosecond
# resolution from the still-present bodies, so it is not re-derivable from the
# committed ledger alone, and git does not preserve mtimes on a fresh clone.
#
# Usage: TMPBODIES=/path/to/bodies bash spacing.sh > spacing.txt
set -u
: "${TMPBODIES:?set TMPBODIES}"
HERE="$(cd "$(dirname "$0")" && pwd)"
TMPBODIES="$TMPBODIES" python3 - "$HERE" <<'EOF'
import json, os, sys, datetime
from collections import defaultdict
HERE = sys.argv[1]
rows = [json.loads(l) for l in open(os.path.join(HERE, 'results.jsonl')) if l.strip()]
def ts(s): return datetime.datetime.fromisoformat(s.replace('Z', '+00:00'))
def ns(r): return os.stat(f"{os.environ['TMPBODIES']}/{r['host_tag']}.b").st_mtime_ns

print('AREA V — SPACING, two independent series (docs/09 §4)')
print(f'rows in results.jsonl: {len(rows)}')
print()
print('per request:')
print('  seq  host                          t_sent (inside flock)      dur      mtime-t_sent')
for r in rows:
    print('  %-4d %-30s %-24s %7.3fs  %8.3fs' % (
        r['seq'], r['host'], r['t_sent'],
        (ts(r['t_done']) - ts(r['t_sent'])).total_seconds(),
        (ns(r) - ts(r['t_sent']).timestamp() * 1e9) / 1e9))

byhost = defaultdict(list)
for r in rows:
    byhost[r['host']].append(r)
send, mtm = [], []
print('\nsame-host gaps (counting rule: one gap per consecutive pair in request order,')
print('N requests on a host give N-1 gaps — docs/09 §4):')
for h, rs in byhost.items():
    for x, y in zip(rs, rs[1:]):
        a = (ts(y['t_sent']) - ts(x['t_sent'])).total_seconds()
        c = (ns(y) - ns(x)) / 1e9
        send.append(a); mtm.append(c)
        print('  %-30s seq%-3d->%-3d  send %7.3fs   mtime %7.3fs' % (h, x['seq'], y['seq'], a, c))

harness = (ts(rows[-1]['t_done']) - min(ts(r['t_sent']) for r in rows)).total_seconds()
kspan = (max(ns(r) for r in rows) - min(ns(r) for r in rows)) / 1e9
print()
print('SERIES VALIDATION (the mtime series is only usable if this holds):')
print('  harness span  (first t_sent -> last t_done): %.3fs' % harness)
print('  kernel mtime span                          : %.3fs' % kspan)
print('  difference                                  : %.3fs' % abs(harness - kspan))
print('  verdict                                    : %s' % (
    'USABLE — spans agree' if abs(harness - kspan) < 1.0 else 'REJECT — spans disagree'))
print()
print('MEASURED FLOOR')
print('  SEND  series: n=%d gaps, min %.3fs, max %.3fs, %d under the declared 2.5s, %d under the 2s floor'
      % (len(send), min(send), max(send), sum(1 for x in send if x < 2.5), sum(1 for x in send if x < 2.0)))
print('  MTIME series: n=%d gaps, min %.3fs, max %.3fs, %d under the declared 2.5s, %d under the 2s floor'
      % (len(mtm), min(mtm), max(mtm), sum(1 for x in mtm if x < 2.5), sum(1 for x in mtm if x < 2.0)))
neg = [r['seq'] for r in rows if (ts(r['t_done']) - ts(r['t_sent'])).total_seconds() < 0]
print('  negative request durations (impossible; the corrupt-t0 signature, docs/09 §4):',
      neg if neg else 'none')
badm = [r['seq'] for r in rows if (ns(r) - ts(r['t_sent']).timestamp() * 1e9) < 0]
print('  bodies written before their own t_sent (same signature):', badm if badm else 'none')
EOF