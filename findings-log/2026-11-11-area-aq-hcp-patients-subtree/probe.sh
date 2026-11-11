#!/usr/bin/env bash
# Area AQ — is the `hcp/patients/` subtree route-live, and which of its routes exist?
# Claim: NovaLux12/carelink-api-research#199. Cap 36, >=2.5 s per host, INSIDE the flock.
#
# THE SINGLE SOURCE OF THE CAP. One assignment, here; `cap_guard` reads it, and
# FINDINGS.md's "N of a 36 cap" line must equal `wc -l results.jsonl`.
#
#   CAP=36  ==  corpus control (1 build, 1 host)          =  1
#             + 2 controls x 4 hosts                      =  8
#             + absent-child boundary cell x 4 hosts      =  4  (one per host: the
#                                                   constant is read on the same host
#                                                   whose candidate column it judges)
#             + C candidate route literals x 1 host       =  23
#                                                          --
#                                                           36
#
# and C = 23 is what `derive.py` writes to `candidates.txt`: 21 eager literals
# + 1 chunk-only literal (`hcp/patients/checkPhoneNumber`, route-delta.json
# `chunk_only`) + 1 CLAIM-ONLY name (`hcp/patients`, the bare collection, which
# the claim names and neither source does). See ONE RECORDED CAP REVISION below.
#
# ONE RECORDED CAP REVISION: 24 → 36, taken BEFORE the second request and before
# any candidate. Reason: the claim's own list is 12 names; the build names 22
# probeable literals, and the DERIVED SET WINS (claim #199's instruction), plus
# the claim's bare-collection name that no build names. Twelve named routes
# cannot be swept for the price of twelve when the build names twenty-two — the
# difference is where the answer actually is. The itemisation above closes
# exactly, and no cell in it is slack.
#
# WHY THE CANDIDATES ARE ONE HOST AND THE BOUNDARY IS FOUR. Two different
# questions: (a) which literals exist and with what method — a property of the
# route TABLE, answered once, on the host whose build is the derivation source;
# (b) whether `hcp/patients/` carries the same absent-child 405 constant area AG
# measured under `/hcp/configuration/` — a property of the MOUNT, which is the
# kind of thing that can differ per deployment, so it is measured per host, on
# all four, and the baseline's own boundary cell is sent BEFORE its candidates so
# that column is read against a constant measured on that same host.
#
# GET + empty-body OPTIONS only. No POST, no token, no cookie, and NO PATIENT ID
# — not even a fabricated one. Literals containing `((patientId))` are recorded
# by `derive.py` as needs-id and never issued: an invented path segment would be
# a request about a patient, not about a route.
#
# Usage: probe.sh all|bundles|derive|sweep
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../../../../.." && pwd)"
RUNLOG="$HERE/run.log"
LEDGER="$HERE/results.jsonl"
SCRATCH="$REPO/.loop/aq-scratch"
ASSETS="$REPO/.loop/aq-assets"          # gitignored: the 3.4 MB build never enters findings-log/
mkdir -p "$SCRATCH" "$ASSETS"

UA="carelink-bridge-research/1.0"
DELAY=2.5
CAP=36
PROWEB="X-System-ID: ProWeb"

BASE=carelinkhp.minimed.eu
OTHER_HOSTS="carelink.medtronic.com carelink.medtronic.eu carelink-support.medtronic.com"
HOSTS="$BASE $OTHER_HOSTS"
# The certainly-absent name. `git grep -c 'zz-aq-absent-9157'` at this head returns 0:
# a name no repository file and no crawl record carries.
ABSENT=zz-aq-absent-9157

# The claimed set, as the claim issue types it (a human SUMMARY of a recon
# report). Compared by derive.py; the sweep is driven by derive.txt, never by this.
CLAIMED="hcp/patients hcp/patients/archivePatient hcp/patients/checkPhoneNumber \
hcp/patients/getInviteToPersonalTemplate hcp/patients/getPatient \
hcp/patients/getPatientsMealProfilesAndDailyHabits hcp/patients/linkPatient \
hcp/patients/otc-linking/allowed hcp/patients/otc-linking/code/sms/send \
hcp/patients/sendInviteToPersonal hcp/patients/unlinkPatient hcp/patients/updatePatient"

CHUNK_DELTA="$REPO/findings-log/2026-10-14-area-k-clinic-controlflow/route-delta.json"

CLINIC_ASSET=/main.fb5f8cb7eb60c4d5.js
# Recorded 2026-10-14 (differential.py:142), re-asserted by areas AB and AK.
CLINIC_SHA=2a7fa8e7af519c2b493caf62c00b46c5e75a357048444dbf7abff6136bfc02ba

[ -f "$LEDGER" ] || : > "$LEDGER"
SEQ=$(awk 'NF' "$LEDGER" 2>/dev/null | wc -l | tr -d ' '); SEQ=${SEQ:-0}
[ -f "$RUNLOG" ] || : > "$RUNLOG"

log() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)" "$*" >> "$RUNLOG"; }
ledger_len() { awk 'NF' "$LEDGER" 2>/dev/null | wc -l | tr -d ' '; }

cap_guard() {
  local n; n=$(ledger_len)
  if [ "$n" -ge "$CAP" ]; then log "CAP STOP at $n of $CAP"; echo "CAP STOP: $n of $CAP" >&2; return 1; fi
  return 0
}

# req <method> <host> <path> <role> <tag> [header]
req() {
  local method="$1" host="$2" path="$3" role="$4" tag="$5" hdr="${6:-}"
  cap_guard || return 1
  SEQ=$((SEQ+1))
  local out="$SCRATCH/$tag" tq ts td code exitc
  tq=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)
  local -a cargs=(-s --compressed --max-time 120 -A "$UA" -D "$out.h" -o "$out.b" -w '%{http_code}')
  [ "$method" = OPTIONS ] && cargs+=(--request OPTIONS)
  [ -n "$hdr" ] && cargs+=(-H "$hdr")
  touch "$REPO/.loop/host-$host.lock" 2>/dev/null || true
  exec 9>"$REPO/.loop/host-$host.lock"
  flock 9
  sleep "$DELAY"                       # the sleep is INSIDE the per-host lock
  ts=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)
  code=$(curl "${cargs[@]}" "https://$host$path" 2>>"$RUNLOG")
  exitc=$?
  flock -u 9
  exec 9>&-
  td=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)
  python3 - "$LEDGER" "$out.h" "$out.b" "$SEQ" "$method" "$host" "$tag" "$path" "$role" "${hdr:-(none)}" "$code" "$exitc" "$tq" "$ts" "$td" <<'PY'
import json, sys, os, hashlib
(L, hp, bp, seq, method, host, tag, path, role, sent, code, exitc,
 tq, ts, td) = sys.argv[1:16]
KEEP = ('content-type','content-length','content-encoding','allow','server','vary',
        'cache-control','access-control-allow-origin','access-control-allow-methods',
        'access-control-allow-headers','access-control-expose-headers','etag')
hdrs = {}
if os.path.exists(hp):
    for line in open(hp, 'rb').read().decode('latin-1').splitlines():
        if ':' in line:
            k, v = line.split(':', 1)
            if k.strip().lower() in KEEP:
                hdrs[k.strip().lower()] = v.strip()
n = os.path.getsize(bp) if os.path.exists(bp) else 0
d = hashlib.sha256(open(bp,'rb').read()).hexdigest() if n else ''
row = {"seq": int(seq), "host": host, "tag": tag, "method": method, "path": path,
       "role": role, "sent_headers": sent, "http_status": code, "curl_exit": int(exitc),
       "body_bytes": n, "body_sha256": d,
       "content_type": hdrs.get('content-type','(none)'),
       "allow": hdrs.get('allow','(none)'),
       "acam": hdrs.get('access-control-allow-methods','(none)'),
       "acao": hdrs.get('access-control-allow-origin','(none)'),
       "acah": hdrs.get('access-control-allow-headers','(none)'),
       "content_encoding": hdrs.get('content-encoding','(none)'),
       "server": hdrs.get('server','(none)'),
       "headers": hdrs, "t_queued": tq, "t_sent": ts, "t_done": td}
open(L, 'a').write(json.dumps(row) + "\n")
print(f"seq={seq} {method} {host}{path} -> {code} ctype={hdrs.get('content-type','-')} "
      f"bytes={n} allow={hdrs.get('allow','-')} sha256={d[:16]}")
PY
  log "seq=$SEQ $method https://$host$path status=$code exit=$exitc tag=$tag role=[$role]"
}

bundles() {
  # Corpus control, request 1 of 36. The build is needed twice over: it is the
  # derivation source for the candidate list, AND its digest is the assertion
  # that the route table being read is the one this repository recorded.
  req GET "$BASE" "$CLINIC_ASSET" \
    "CORPUS-CONTROL clinic build on the baseline host; recorded 3397615 B sha256 2a7fa8e7af519c2b… (2026-10-14-area-k-clinic-controlflow/differential.py:142, re-asserted by areas AB and AK). Derivation source AND build-identity assertion" \
    b01-baseline-clinic-asset || return 0
  cp "$SCRATCH/b01-baseline-clinic-asset.b" "$ASSETS/main.js" 2>/dev/null || true
}

derive() {
  # Zero requests.
  python3 "$HERE/derive.py" "$ASSETS/main.js" "$CHUNK_DELTA" "$CLAIMED" \
    "$HERE/derive.txt" "$HERE/candidates.txt" || { echo "DERIVE FAILED" >&2; return 3; }
  # Digest assertion, separate from the extraction so the two failure modes are
  # distinguishable: a build that MOVED is not a route table that CHANGED.
  python3 - "$ASSETS/main.js" "$CLINIC_SHA" "$HERE/derive.txt" <<'PY'
import hashlib, sys
p, want, out = sys.argv[1], sys.argv[2], sys.argv[3]
got = hashlib.sha256(open(p,'rb').read()).hexdigest()
ok = (got == want)
line = f"BUILD-IDENTITY: sha256={got} recorded={want} reproduces={ok}"
if not ok:
    line += "  <-- THE BUILD HAS MOVED; the derived set is not the recorded surface"
print(line); open(out, 'a').write(line + "\n")
sys.exit(0 if ok else 4)
PY
}

sweep() {
  local h k n_cand
  n_cand=$(grep -c . "$HERE/candidates.txt")
  if [ "$n_cand" -ne 23 ]; then
    echo "CAP ARITHMETIC MISMATCH: candidates.txt holds $n_cand, cap itemisation assumes 23" >&2
    log "CAP ARITHMETIC MISMATCH n_cand=$n_cand expected=23 — sweep aborted"
    return 3
  fi
  # ---- controls first, per host (8) --------------------------------------
  for h in $HOSTS; do
    req GET "$h" "/hcp/configuration/public/pow.crm.settings" \
      "CONTROL-1 positive: known-live key WITH X-System-ID: ProWeb — recorded 200, 97 B on .com/support and 96 B on .eu (2026-10-17-hcp-config-deployments/analysis.md:104,109,114). Proves the header is accepted here and the host serves this family, so a bare status below is not the SPA fallback" \
      "c1-$(echo "$h"|tr . -)-pow-crm" "$PROWEB" || return 0
    req GET "$h" "/hcp/$ABSENT" \
      "CONTROL-2 certainly-absent name at namespace level — recorded 404, 0 B (2026-11-10-area-ag-allow-vs-acam/FINDINGS.md §2). The cell that says a 404 on this host is a TRUE absence rather than a subtree constant" \
      "c2-$(echo "$h"|tr . -)-absent-ns" "" || return 0
    # ---- the absent CHILD under hcp/patients/ — the AG trap, tested (4) ---
    # The SAME fabricated token one level deeper. If this answers 405 + Allow
    # instead of 404, the subtree mounts a handler that answers every child and
    # a 405 on a candidate proves nothing — exactly what area AG found one
    # subtree over. Sent before the candidates on the baseline host.
    req GET "$h" "/hcp/patients/$ABSENT" \
      "BOUNDARY absent child directly under hcp/patients/. 404 = the subtree is transparent to absence (candidates are judgeable by status). 405 + Allow = the subtree carries its own handler constant and a 405 on a candidate is a subtree property, not a route" \
      "b-$(echo "$h"|tr . -)-absent-child" "" || return 0
  done
  # ---- the candidates, on the derivation host (23) ----------------------
  while read -r k; do
    [ -n "$k" ] || continue
    req GET "$BASE" "/$k" \
      "CANDIDATE route literal \`$k\`, extracted offline from this host's own build (derive.txt candidate list) — no X-System-ID. A GET establishes the route's existence and its method filter; no POST is sent and none is claimed" \
      "k-$(echo "$k" | sed 's#hcp/patients/##; s#/#-#g')" "" || return 0
  done < "$HERE/candidates.txt"
}

case "${1:-}" in
  bundles) bundles ;;
  derive)  derive ;;
  sweep)   derive >/dev/null || { echo "DERIVE FAILED — sweep not issued" >&2; exit 3; }; sweep ;;
  all)     bundles; derive || { echo "DERIVE FAILED — sweep not issued" >&2; exit 3; }; sweep ;;
  *) echo "usage: probe.sh all|bundles|derive|sweep" >&2; exit 64 ;;
esac
echo "LEDGER_ROWS=$(ledger_len) CAP=$CAP"
