#!/usr/bin/env bash
# probe.sh — area H (reportFileNamingSupportedPumpModels, entry by entry).
# Claim #33. Cap 6, delay 2.5 s inside the per-host flock, GET only.
#
# CORPUS CORRECTION recorded before probing (see FINDINGS.md §0): the claim
# located the 214-entry list in the patient public config
# (personal.common.core.report.generation...). That key does not exist there;
# the list lives in the HCP family at
# /hcp/configuration/public/pow.common.core.report.generation
# (findings-log/probe-2026-10-08/recon/HCP-CONFIG-SCHEMA.md:164). The probe
# therefore spans two hosts instead of the one the claim named. Request total
# stays under the 6 cap (5 of 6).
#
# Controls (seq 1-3) are sent before any candidate (seq 4-5).
#   seq1 CONTROL-absent-hp .../zzz.this.does.not.exist.zzz -> 404
#        (proves absence reads on the hcp/configuration/public namespace;
#         same path the 2026-10-08 matrix used)
#   seq2 CONTROL-live-hp    .../cua.control.codes.settings -> 200 JSON 778 B
#        (proves the host serves and the X-System-ID client-identity header
#         is accepted; value recorded 2026-10-08)
#   seq3 CONTROL-absent-patient /patient/configuration/system/zzz... -> 404
#        (claim control 1: proves absence reads on the patient per-key form)
#   seq4 CANDIDATE hp pow.common.core.report.generation (the 214-entry list)
#   seq5 CANDIDATE patient /patient/v2/configuration/public (69 keys incl.
#        the 16-family map; claim control 2 doubles as corpus source)
#
# X-System-ID: ProWeb on the HCP family is the client-identity header the
# vendor's own portal sends (committed matrix used it throughout; without it
# every key 412s). It is not a credential, session, or token.
set -uo pipefail
MAIN=/home/jack/.openclaw/workspace/projects/novas-github/carelink-api-research
OUT="$(dirname "$0")"
mkdir -p "$OUT/headers"
: > "$OUT/run.log"
echo "probe start: $(date -u +%FT%TZ)" | tee -a "$OUT/run.log"

req() { # req <seq> <host> <url> <role> <tag> [extra curl args...]
  local seq="$1" host="$2" url="$3" role="$4" tag="$5"; shift 5
  local t_q t_s t_d code exitc
  t_q="$(date -u +%FT%TZ)"
  code=$(flock "$MAIN/.loop/host-$host.lock" -c "
    sleep 2.5
    curl -s --compressed -D '$OUT/headers/$tag.h' -o '$OUT/headers/$tag.b' -w '%{http_code}' $* '$url'
  ")
  exitc=$?
  t_d="$(date -u +%FT%TZ)"
  echo "$code" > "$OUT/headers/$tag.code"
  printf '%s seq=%s host=%s role=%s http=%s exit=%s\n' "$t_d" "$seq" "$host" "$role" "$code" "$exitc" | tee -a "$OUT/run.log"
}

SYSID=( -H "X-System-ID: ProWeb" )

req 1 carelinkhp.minimed.eu \
  'https://carelinkhp.minimed.eu/hcp/configuration/public/zzz.this.does.not.exist.zzz' \
  'CONTROL-absent-hp' hp-absent "${SYSID[@]}"

req 2 carelinkhp.minimed.eu \
  'https://carelinkhp.minimed.eu/hcp/configuration/public/cua.control.codes.settings' \
  'CONTROL-live-hp' hp-live "${SYSID[@]}"

req 3 carelink.minimed.eu \
  'https://carelink.minimed.eu/patient/configuration/system/zzz.not.a.real.key.zzz' \
  'CONTROL-absent-patient' pt-absent

req 4 carelinkhp.minimed.eu \
  'https://carelinkhp.minimed.eu/hcp/configuration/public/pow.common.core.report.generation' \
  'CANDIDATE-report-generation' hp-reportgen "${SYSID[@]}"

req 5 carelink.minimed.eu \
  'https://carelink.minimed.eu/patient/v2/configuration/public' \
  'CANDIDATE-patient-public-config' pt-public

echo "probe end: $(date -u +%FT%TZ)" | tee -a "$OUT/run.log"
echo "5 of a 6 cap. GET only. sleep 2.5 s inside each per-host flock." | tee -a "$OUT/run.log"
