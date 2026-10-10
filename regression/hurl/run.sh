#!/usr/bin/env bash
# Medtronic CareLink endpoint re-probe.
#
# Usage:
#   ./run.sh                 # run all suites, print pass/fail summary
#   ./run.sh 01-discovery    # run one suite
#
# Deliberately low-rate and read-only: discovery / SSO config / OIDC / patient
# API are all public or unauthenticated. --delay spaces requests by 1.2s so we
# never look like a scanner. No credentials are used and nothing is written to
# Medtronic.
#
# Exit 0 = all assertions held (endpoint surface unchanged).
# Exit 1 = something drifted. Diff against the notes in this directory.

set -uo pipefail
cd "$(dirname "$0")"

DELAY_MS=1200
SUITES=${*:-01-discovery-pin 02-sso-oidc 03-patient-api 04-deep-surface 05-public-config}
FAILS=0

echo "=== Medtronic CareLink re-probe $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
echo "    delay=${DELAY_MS}ms/request  mode=read-only/unauthenticated"
echo

for s in $SUITES; do
  echo "--- $s ---"
  # Suites come in two forms. A .hurl file is driven by hurl; a .check.sh is a
  # curl+jq harness, needed where the endpoint's response encoding defeats hurl
  # (see the header of 05-public-config.check.sh for the RFC 9110 detail).
  # $s is a bare suite name; resolve it to a concrete file by extension.
  if [ -f "$s.hurl" ]; then
    CMD=(hurl --test --delay "$DELAY_MS" --no-color "$s.hurl")
  elif [ -f "$s.check.sh" ]; then
    CMD=(bash "$s.check.sh")
  else
    echo "no such suite: $s.hurl or $s.check.sh"
    FAILS=$((FAILS+1))
    continue
  fi
  if "${CMD[@]}" 2>&1; then
    echo ">>> PASS"
  else
    echo ">>> FAIL"
    FAILS=$((FAILS+1))
  fi
  echo
done

echo "=== summary: $FAILS suite(s) failed ==="
[ "$FAILS" -eq 0 ]
