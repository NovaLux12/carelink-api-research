#!/bin/bash
# Area K — spacing, two INDEPENDENT series (docs/09 section 4).
#
# Why two. docs/09 section 4 records five passes in which the harness `date`
# series disagreed with the declared sleep, and one pass (area D) that settled
# the question by finding 11 of 119 requests with a NEGATIVE duration —
# impossible — so those timestamps cannot all be faithful. The independent series
# is the kernel's own st_mtime_ns on the response bodies: curl -o makes the
# kernel set it at write time, and no harness clock is involved.
#
# The rule being checked is a rule about SENDS, so only t_sent can establish it.
# The mtime series bounds it from below (a body cannot be written before its own
# request went out), which is why both are reported and neither is reported
# instead of the other.
#
# COUNTING RULE, stated so the number is reproducible: one gap per consecutive
# pair in REQUEST ORDER taken from results.jsonl, so N rows give N-1 gaps. All
# rows are on one host.
#
# SERIES VALIDATION, per docs/09 section 4: a trustworthy run's mtime span EQUALS
# the harness span. Git does not preserve mtimes, so on a fresh clone every body
# carries the checkout time and the spread collapses to 0.0 s. The spans are
# compared here and the verdict printed, so the reader does not have to take the
# series on trust.
set -u
LEDGER=${1:?usage: spacing.sh <results.jsonl>}
python3 - "$LEDGER" <<'EOF'
import json, sys
from datetime import datetime, timezone

rows = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
rows.sort(key=lambda r: r["seq"])

def t(s):
    if not s or s.startswith("("):
        return None
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc).timestamp()

print("AREA K — SPACING, two independent series (docs/09 §4)")
print(f"rows in results.jsonl: {len(rows)}")
print(f"hosts in this ledger : {sorted({r['host'] for r in rows})}")
print()

# --- per request --------------------------------------------------------------
print("per request:")
print("  seq  t_sent (inside flock)        dur      mtime-t_sent   status  path")
sends, mtimes = [], []
for r in rows:
    ts, td = t(r["t_sent"]), t(r["t_done"])
    ns = r.get("body_mtime_ns", "")
    mt = int(ns) / 1e9 if ns and ns != "(none)" else None
    dur = (td - ts) if (ts and td) else None
    skew = (mt - ts) if (mt and ts) else None
    if ts: sends.append(ts)
    if mt: mtimes.append(mt)
    print(f"  {r['seq']:<4d} {r['t_sent']:<26s} "
          f"{('%.3fs' % dur) if dur is not None else '(none)':<9s}"
          f"{('%.3fs' % skew) if skew is not None else '(none)':<14s}"
          f"{r['http_status']:<8s} {r['path']}")

print()
print("same-host gaps (counting rule: one gap per consecutive pair in request")
print("order, N rows give N-1 gaps — docs/09 §4):")
send_gaps, mtime_gaps = [], []
for a, b in zip(rows, rows[1:]):
    ta, tb = t(a["t_sent"]), t(b["t_sent"])
    if ta and tb:
        send_gaps.append((a["seq"], b["seq"], tb - ta))
    na, nb = a.get("body_mtime_ns", ""), b.get("body_mtime_ns", "")
    if na and nb and na != "(none)" and nb != "(none)":
        mtime_gaps.append((a["seq"], b["seq"], int(nb) / 1e9 - int(na) / 1e9))
# Print the shortest ten first, so a sub-declared gap cannot hide in the middle
# of a long list where nobody reads to it.
for seq_a, seq_b, g in sorted(send_gaps, key=lambda x: x[2])[:10]:
    print(f"  seq{seq_a:<5d} ->{seq_b:<6d} send {g:.3f}s")
print(f"  ({len(send_gaps)} send-series gaps; the ten shortest are printed above)")
print()

print("SERIES VALIDATION (the mtime series is only usable if this holds):")
if sends and mtimes:
    hs = max(max(sends), max(mtimes)) - min(min(sends), min(mtimes))
    ms = max(mtimes) - min(mtimes)
    print(f"  harness span  (first t_sent -> last body write): {hs:.3f}s")
    print(f"  kernel mtime span                            : {ms:.3f}s")
    print(f"  difference                                   : {abs(hs - ms):.3f}s")
    print(f"  verdict                                     : "
          f"{'USABLE — spans agree' if abs(hs - ms) < 5.0 else 'SUSPECT — spans disagree'}")
else:
    print("  (insufficient data)")

print()
print("MEASURED FLOOR")
for name, gaps in (("SEND ", send_gaps), ("MTIME", mtime_gaps)):
    if not gaps:
        print(f"  {name} series: no gaps")
        continue
    v = [g for _, _, g in gaps]
    print(f"  {name} series: n={len(v)} gaps, min {min(v):.3f}s, max {max(v):.3f}s, "
          f"{sum(1 for x in v if x < 2.5)} under the declared 2.5s, "
          f"{sum(1 for x in v if x < 2.0)} under the 2s floor")
neg = [(r['seq'], round((t(r['t_done']) - t(r['t_sent'])) * 1000)) for r in rows
       if t(r['t_done']) and t(r['t_sent']) and t(r['t_done']) < t(r['t_sent'])]
print(f"  negative request durations (impossible; the corrupt-t0 signature, "
      f"docs/09 §4): {len(neg)}" + (f" {neg[:6]}" if neg else ""))
early = [r['seq'] for r in rows
         if r.get('body_mtime_ns', '') not in ('', '(none)')
         and t(r['t_sent']) and int(r['body_mtime_ns']) / 1e9 < t(r['t_sent'])]
print(f"  bodies written before their own t_sent (same signature): {len(early)}"
      + (f" {early[:6]}" if early else ""))
EOF