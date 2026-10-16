#!/bin/bash
# Area K close probe harness — no vendor requests sent.
# Area K is closed on existing committed evidence from prior passes
# (issues #56, #78, #103, #121). This probe.sh records that decision.

set -euo pipefail

REPO="$(git rev-parse --show-toplevel)"
OUT="${REPO}/findings-log/2026-10-16-k-chunk-corpus"

echo "Area K close: 0 vendor requests."
echo "Closing on existing committed evidence:"
echo "  - Patient 211 chunks swept (issue #56)"
echo "  - Clinic 225 denominator body-verified (issue #78)"
echo "  - Control-flow / call-site shapes recovered (issue #103)"
echo "  - system.logbook.entry.validation.config recovered (issue #121)"
echo "  - Cross-client differential declined as not meaningful"
echo ""
echo "No curl, no hurl, no vendor host contact."
echo "Cap: 0 of 0. Delay: n/a."

# Write an empty results.jsonl (zero requests)
: > "${OUT}/results.jsonl"

# Write run.log
{
  echo "Area K close — 0 requests"
  echo "Cap: 0 of 0"
  echo "Delay: n/a (no requests sent)"
  echo "All evidence from committed findings logs referenced in docs/11 addenda under K"
} > "${OUT}/run.log"

echo "Done. results.jsonl has $(wc -l < "${OUT}/results.jsonl") rows."
