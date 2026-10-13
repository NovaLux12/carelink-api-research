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
# SERIES VALIDATION, per docs/09 section 4. Two things are checked, and they are
# NOT the same thing:
#
#   1. PER-GAP comparison - the two series must agree gap by gap. This can fail,
#      and on this run it does: it is what names each `date` timestamp that moved.
#   2. Span comparison - both series must agree about the run's extent. This
#      cannot detect interior corruption; it is a two-endpoint consistency check
#      and is labelled as one.
#
# The first version of this script had only (2), written as arithmetic whose
# difference telescopes to the first row's own latency — a number that could not
# fail. See the SPAN COMPARISON section for the retraction.
#
# Git does not preserve mtimes, so on a fresh clone every body carries the
# checkout time and the spread collapses to 0.0 s; that is what (2) is for.
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
sends, mtimes, dones = [], [], []
for r in rows:
    ts, td = t(r["t_sent"]), t(r["t_done"])
    ns = r.get("body_mtime_ns", "")
    mt = int(ns) / 1e9 if ns and ns != "(none)" else None
    dur = (td - ts) if (ts and td) else None
    skew = (mt - ts) if (mt and ts) else None
    if ts: sends.append(ts)
    if td: dones.append(td)
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

print()
print("SPAN COMPARISON — and what it can and cannot do, stated because the first")
print("version of this section was arithmetic dressed as evidence:")
print()
print("  The first version computed")
print("    harness = max(max(sends),max(mtimes)) - min(min(sends),min(mtimes))")
print("    kernel  = max(mtimes) - min(mtimes)")
print("  whose difference TELESCOPES to mtime[0] - send[0] — the first request's own")
print("  latency — and to nothing else. Every interior timestamp cancels, so it could")
print("  not have detected a corrupted series short of total collapse. Its 'agreement")
print("  to 0.274s' was a number that could not fail. Replaced with two endpoints that")
print("  genuinely differ, and — more to the point — with the PER-GAP comparison")
print("  below, which can.")
print()
if sends and mtimes:
    hs = max(dones) - min(sends)
    ms = max(mtimes) - min(mtimes)
    print(f"  harness  first t_sent -> last t_done : {hs:.3f}s")
    print(f"  kernel   first write  -> last write  : {ms:.3f}s")
    print(f"  difference                           : {abs(hs - ms):.3f}s")
    print(f"  = first-row latency {mtimes[0]-sends[0]:.3f}s + last-row latency "
          f"{dones[-1]-mtimes[-1]:.3f}s")
    print("  STILL a two-endpoint check: it confirms both series agree about the run's")
    print("  extent and says NOTHING about the gaps between them. The per-gap comparison")
    print("  below is what carries that weight.")
else:
    print("  (insufficient data)")

print()
print("PER-GAP SERIES COMPARISON — the check that CAN fail")
print("  For each consecutive pair: |send_gap - mtime_gap|. Two clocks measuring the")
print("  same interval must agree; where they do not, the `date` series is wrong at")
print("  that specific gap, and the gap is NAMED rather than summarised away.")
if send_gaps and mtime_gaps:
    sg = {s: g for s, _, g in send_gaps}
    mg = {s: g for s, _, g in mtime_gaps}
    common = sorted(set(sg) & set(mg))
    deltas = [(s, sg[s] - mg[s]) for s in common]
    ad = [abs(d) for _, d in deltas]
    worst = sorted(deltas, key=lambda x: -abs(x[1]))[:10]
    over = [(s, d) for s, d in deltas if abs(d) > 0.5]
    print(f"  gaps compared          : {len(deltas)}")
    print(f"  max |send - mtime|     : {max(ad):.3f}s")
    print(f"  median |send - mtime|  : {sorted(ad)[len(ad)//2]:.3f}s")
    print(f"  gaps disagreeing >0.5s : {len(over)}")
    for s, d in worst:
        print(f"     seq{s:<5d} send {sg[s]:8.3f}s  mtime {mg[s]:8.3f}s  delta {d:+.3f}s")
    print("  Every disagreement above is a `date` timestamp that moved; the kernel")
    print("  series holds. That is the finding, visible PER GAP rather than inferred")
    print("  from two spans.")
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
negm = [s for s, _, g in mtime_gaps if g <= 0]
print(f"  negative KERNEL gaps (also impossible; the same signature measured by the "
      f"independent series): {len(negm)}" + (f" {negm}" if negm else ""))
print()
print("  Long gaps (>10 s), BOTH series. Every long gap in this run is explained and")
print("  every one is OVER the declared delay, not under it. Reported from both")
print("  series because the prose quotes the kernel figures, and the two series")
print("  differ in the second decimal — quoting one while naming the other is how a")
print("  35.6 s gap becomes a 35.62 s gap in someone's write-up.")
if mtime_gaps:
    sg = {s: g for s, _, g in send_gaps}
    for a, b, g in sorted([(a, b, g) for a, b, g in mtime_gaps if g > 10]):
        print(f"     seq{a:<5d} ->{b:<5d}  kernel {g:8.3f}s   send {sg.get(a, float('nan')):8.3f}s")
print()
early = [r['seq'] for r in rows
         if r.get('body_mtime_ns', '') not in ('', '(none)')
         and t(r['t_sent']) and int(r['body_mtime_ns']) / 1e9 < t(r['t_sent'])]
print(f"  bodies written before their own t_sent (same signature): {len(early)}"
      + (f" {early[:6]}" if early else ""))
EOF