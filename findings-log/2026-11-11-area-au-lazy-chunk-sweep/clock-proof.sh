#!/bin/bash
# Area AU — proof that the harness clock (`date -u +%FT%T.%3NZ`) is not monotone
# on this host, so the `t_sent` series cannot carry the spacing claim.
#
# WHY THIS FILE EXISTS. The ledger's `t_sent` column reads 30 gaps under the
# declared 2.5 s and 26 rows where `t_done` PRECEDES `t_sent` — a negative
# duration, which is physically impossible for a completed request. Two readings
# are available: the requests really were too close, or the clock that stamped
# them is broken. This script settles which, with NO NETWORK AT ALL: it runs the
# identical nesting the harness uses (parent `date` -> flock sub-shell -> inner
# `date`) N times against no host, and tests the ordering of the three stamps.
#
# THE TEST is full monotonicity of each trial (`tq <= ts <= td`) AND of `tq`
# across trials. A trial that fails either is a clock inversion: an instant
# recorded before another instant that was itself recorded earlier. If that
# happens with no socket in the loop, a negative duration in the ledger is a
# property of the harness rather than of the vendor.
set -u
N=${N:-120}
LOCK=/tmp/au-clock-proof.lock
: > "$LOCK"

rows=0
bad=0
prev_tq=""
printf 'outer_before\tinner\touter_after\tverdict\n'
for _ in $(seq 1 "$N"); do
  tq=$(date -u +%FT%T.%3NZ)
  ts=$(flock "$LOCK" bash -c '
    date -u +"%FT%T.%3NZ"
    # stand in for the body write: a file whose mtime is the completion instant
    : > /tmp/au-clock-proof.body
  ')
  td=$(date -u +%FT%T.%3NZ)
  rows=$((rows+1))
  verdict=$(python3 - "$tq" "$ts" "$td" "${prev_tq:-$tq}" <<'PY'
import datetime as d, sys
f = lambda s: d.datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%fZ")
tq, ts, td, prev = (f(x) for x in sys.argv[1:5])
bad = []
if ts < tq:
    bad.append(f"inner predates outer_before by {(tq - ts).total_seconds():+.3f}s")
if td < ts:
    bad.append(f"outer_after predates inner by {(ts - td).total_seconds():+.3f}s")
if td < tq:
    bad.append(f"outer_after predates outer_before by {(tq - td).total_seconds():+.3f}s")
if tq < prev:
    bad.append(f"outer_before predates the PREVIOUS trial's by {(prev - tq).total_seconds():+.3f}s")
print("; ".join(bad) if bad else "ok")
PY
)
  [ "$verdict" = "ok" ] || bad=$((bad + 1))
  printf '%s\t%s\t%s\t%s\n' "$tq" "$ts" "$td" "$verdict"
  prev_tq=$tq
done

echo
echo "trials: $rows"
echo "trials with at least one inversion: $bad"
echo "requests sent by this script: 0"
if [ "$bad" -eq 0 ]; then
  echo "VERDICT: clock monotone in $rows/$rows trials — the ledger's negative durations are NOT reproducible here, and the t_sent series stands."
  exit 0
fi
echo "VERDICT: clock NOT monotone in $bad of $rows trials with ZERO network involved — the ledger's negative durations are a HARNESS artefact, not a request that went out early."
echo "Consequence: spacing is asserted from the kernel body-mtime oracle, the only clock in the ledger this harness does not write."
