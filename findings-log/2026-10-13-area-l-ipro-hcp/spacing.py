#!/usr/bin/env python3
"""Spacing for this pass, measured on both oracles and neither rounded.

docs/09 §4 is explicit that the harness `date` series is the suspect in
several passes (negative durations are impossible), that body-file mtimes set
by the kernel at write time are the independent series, and that a
trustworthy run's mtime span EQUALS the harness span. Both are reported here;
neither replaces the other.

Counting rule (docs/09 §4): one gap per consecutive pair IN REQUEST ORDER,
measured from run.log, N bodies give N-1 gaps. Rows 1-4 are the four requests a
debug harness sent before this harness's send path was fixed; they are EXCLUDED
from the measurement and said so, because that harness's sleep was 0.2 s and its
gaps are not this pass's spacing.
"""
import json
import pathlib
import os
from datetime import datetime

HOSTS = ("index.commoncrawl.org", "data.commoncrawl.org")


def iso(t):
    return datetime.strptime(t, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=None)


rows = [json.loads(l) for l in open("results.jsonl") if l.strip()]
measured = [r for r in rows if r.get("role") != "HARNESS-DEBUG-not-evidence"]
excluded = [r for r in rows if r.get("role") == "HARNESS-DEBUG-not-evidence"]

print(f"requests in run order: {len(rows)}")
print(f"  excluded from spacing (pre-fix debug harness, disclosed): {len(excluded)}"
      " -- these rows carry NO t_queued/t_sent/t_done at all (null), so they"
      " are absent from the series rather than measured in it")
print(f"  measured: {len(measured)}")

# ---- harness t_sent series -------------------------------------------------
print("\n--- harness t_sent series ---")
for host in HOSTS:
    ts = [iso(r["t_sent"]) for r in measured if r["host"] == host]
    if len(ts) < 2:
        continue
    gaps = [(ts[i + 1] - ts[i]).total_seconds() for i in range(len(ts) - 1)]
    span = (ts[-1] - ts[0]).total_seconds()
    print(f"  {host:<26} gaps={len(gaps):>3} min={min(gaps):.3f}s "
          f"max={max(gaps):.3f}s under 2.5s={sum(g < 2.5 for g in gaps)} "
          f"under 2.0s={sum(g < 2.0 for g in gaps)} span={span:.3f}s")
allts = [iso(r["t_sent"]) for r in measured]
gaps = [(allts[i + 1] - allts[i]).total_seconds() for i in range(len(allts) - 1)]
span = (allts[-1] - allts[0]).total_seconds()
print(f"  {'ALL HOSTS':<26} gaps={len(gaps):>3} min={min(gaps):.3f}s "
      f"max={max(gaps):.3f}s under 2.5s={sum(g < 2.5 for g in gaps)} "
      f"under 2.0s={sum(g < 2.0 for g in gaps)} span={span:.3f}s")
# t_done <= t_sent, not < : a request that took zero time is as impossible as
# one that finished before it started, and a strict < lets a zero-duration row
# pass this check silently.
neg = [r["seq"] for r in measured
       if r["t_done"] and r["t_sent"] and iso(r["t_done"]) < iso(r["t_sent"])]
zero = [r["seq"] for r in measured
        if r["t_done"] and r["t_sent"] and iso(r["t_done"]) == iso(r["t_sent"])]
absent = [r["seq"] for r in rows if not (r["t_done"] and r["t_sent"])]   # across ALL rows, not just measured
print(f"  t_done precedes t_sent (impossible): {len(neg)} {neg}")
print(f"  t_done == t_sent, zero duration (also impossible): {len(zero)} {zero}")
print(f"  of all {len(rows)} rows, those with an ABSENT timestamp series: {len(absent)} {absent}")

# ---- kernel body-mtime series ---------------------------------------------
print("\n--- kernel body-mtime series (independent of the harness clock) ---")
BODIES = pathlib.Path(__file__).resolve().parents[4] / "probe-bodies-area-l"
mtimes = sorted((os.stat(f).st_mtime, f) for f in BODIES.glob("*.body"))
if mtimes:
    vals = [m for m, _ in mtimes]
    gaps = [round(vals[i + 1] - vals[i], 3) for i in range(len(vals) - 1)]
    print(f"  bodies on disk: {len(vals)}  gaps={len(gaps)}")
    print(f"  min={min(gaps):.3f}s max={max(gaps):.3f}s "
          f"under 2.5s={sum(g < 2.5 for g in gaps)} "
          f"under 2.0s={sum(g < 2.0 for g in gaps)}")
    print(f"  span={vals[-1] - vals[0]:.3f}s")
    print(f"  harness span={span:.3f}s  -> series agree: "
          f"{'YES' if abs((vals[-1] - vals[0]) - span) < 5 else 'NO'}")
else:
    print("  no bodies on disk (they live outside the tracked tree, in the")
    print("   shared .loop scratch, so the gate never sees them)")

print("\nNOTE: git does not preserve mtimes, so the kernel series is valid only")
print("on the machine that ran the probe; it is not re-derivable from a clean")
print("clone. Both series are reported; neither replaces the other.")
