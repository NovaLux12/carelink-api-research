#!/usr/bin/env bash
# gate.sh — lane l2. Runs the repository gate under the pool's gate lock, with
# the pinned suite's own vendor requests logged into this pass's ledger.
#
# Phase order matters and is enforced by the brief: probe (host locks) is done,
# writing takes no locks, and this is the only step that takes the gate lock.
# A host lock and the gate lock are never held at once.
#
# The gate itself is the repository's own script, unmodified. This wrapper only
# (a) puts a recording `curl` shim first on PATH so the suite's requests are
# counted, and (b) appends those requests to results.jsonl afterwards, so the
# accounting line covers every request this pass caused — including the ones the
# gate caused.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../../../../.." && pwd)"
SHIMDIR="$REPO/.loop/l2-shim"
LEDGER="$HERE/results.jsonl"
RUNLOG="$HERE/run.log"
CURLLOG="$REPO/.loop/l2-curllog.jsonl"

mkdir -p "$SHIMDIR"
: > "$CURLLOG"
cp "$HERE/curl-shim.sh" "$SHIMDIR/curl"
chmod +x "$SHIMDIR/curl"

export L2_CURL_LOG="$CURLLOG"
export PATH="$SHIMDIR:$PATH"

# HERE is <main-clone>/.loop/worktrees/<w>/findings-log/<dir>, so four levels up
# is the WORKTREE root (where ./scripts/research-gate.sh lives) and five levels up
# is the main clone, where the shared locks live. Depth counted, not guessed:
#   ..1 findings-log  ..2 <w> = the worktree root (gate lives here)  ..3 worktrees  ..4 .loop  ..5 <main-clone> (shared locks)
cd "$HERE/../.." || exit 1
[ -x ./scripts/research-gate.sh ] || { echo "gate.sh: not at $(pwd)" >&2; exit 1; }
flock -w 1800 "$REPO/.loop/gate.lock" -c './scripts/research-gate.sh'
GATE_RC=$?
echo "GATE_EXIT=$GATE_RC"
cp "${SUITE_LOG:-/tmp/_gate_suite.log}" "$HERE/gate-suite.log" 2>/dev/null || true

python3 "$HERE/absorb-gate.py" "$CURLLOG" "$LEDGER" "$RUNLOG" 2>&1 | tail -20
# Repair is TOTAL, not per-run: verifier round 1 finding B1 was a repair scoped to one
# gate run while a second run's rows shipped with a response body in `http_status`.
python3 "$HERE/repair-status.py" "$LEDGER"

# The cap is read from probe.sh, never repeated here — see absorb-gate.py. If the ledger
# is at or over it after absorbing, that is a stop, not a warning.
CAP=$(sed -n 's/^CAP=\([0-9]*\).*/\1/p' "$HERE/probe.sh" | head -1)
ROWS=$(wc -l < "$LEDGER" | tr -d ' ')
if [ "${ROWS:-0}" -gt "${CAP:-0}" ]; then
  echo "GATE_LEDGER_OVER_CAP rows=$ROWS cap=$CAP" >&2
  CAP_STATE=OVER
else
  CAP_STATE=ok
fi

echo "GATE_EXIT=$GATE_RC LEDGER_ROWS=$ROWS CAP=$CAP CAP_STATE=$CAP_STATE"
exit $GATE_RC