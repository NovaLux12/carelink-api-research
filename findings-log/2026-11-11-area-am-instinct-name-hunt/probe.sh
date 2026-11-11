#!/usr/bin/env bash
# Area AM — do SKU-78963/78964/78965/78968-01 carry a product name anywhere the vendor
# serves publicly? Claim: NovaLux12/carelink-api-research#195. Cap 16, >=2.5 s per host,
# INSIDE the per-host flock. GET only. No POST, no token, no cookie, no auth, no wordlist.
#
# THE SINGLE SOURCE OF THE CAP. One assignment, here; `cap_guard` reads it, and
# FINDINGS.md's "N of a 16 cap" line must equal `wc -l results.jsonl`.
#
#   CAP=16  ==  2 controls x 3 hosts        =  6
#             + 2 assets   x 3 hosts        =  6
#             + reserve (re-fetch only)     =  4
#                                             --
#                                             16
#
# The plan is itemised in PLAN.md, written BEFORE the first request. Hosts are this
# lane's patient deployments ONLY: carelink.minimed.com, carelink.minimed.eu,
# carelink-trials.minimed.com. The HCP/portal host family belongs to another lane and
# is NOT touched — the committed 2026-10-17 HCP report-config bodies are scanned
# offline at zero requests instead.
#
# Controls FIRST, per host, before any asset fetch on that host:
#   zzz.not.a.real.key.zzz            -> 404, 0 B, text/vnd.a   (absence is real here)
#   logbook.supported.entry.types     -> 200, 281 B, 7f0a5bb4…  (the route family is live)
# Either disagreeing with that STOPS the run before an asset is requested.
#
# Usage: probe.sh all     # controls -> assets
#        probe.sh assets  # assets only (controls already recorded)
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
# five levels up = the MAIN clone root (this dir is <clone>/.loop/worktrees/lam/findings-log/<area>)
# so the gitignored scratch dir lands beside the other passes' scratch dirs
REPO="$(cd "$HERE/../../../../.." && pwd)"
RUNLOG="$HERE/run.log"
LEDGER="$HERE/results.jsonl"
SCRATCH="$REPO/.loop/am-scratch"
mkdir -p "$SCRATCH" "$HERE/headers"

UA="carelink-bridge-research/1.0"
DELAY=2.5
CAP=16

# Recorded, not candidate: the patient eager bundle's content-hashed name (area V, seq 3/7)
# and the clinic build's content-hashed name (area G, seq 3). Asking a patient host for the
# clinic name is a single recorded string, not a filename sweep.
PATIENT_ASSET=/main.6595daf83bd6d4b1.js
CLINIC_ASSET=/main.fb5f8cb7eb60c4d5.js
HOSTS="carelink.minimed.com carelink.minimed.eu carelink-trials.minimed.com"

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

# req <host> <path> <role> <tag> [keep]
req() {
  local host="$1" path="$2" role="$3" tag="$4" keep="${5:-}"
  cap_guard || return 1
  SEQ=$((SEQ+1))
  local out="$SCRATCH/$tag" tq ts td code exitc
  tq=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)
  local -a cargs=(-s --compressed --max-time 180 -A "$UA" -D "$out.h" -o "$out.b" -w '%{http_code}')
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
  # the body stays in the gitignored scratch dir; only derived matches are committed
  cp "$out.h" "$HERE/headers/$tag.h" 2>/dev/null || true
  python3 - "$LEDGER" "$out.h" "$out.b" "$SEQ" "$host" "$tag" "$path" "$role" \
           "$code" "$exitc" "$tq" "$ts" "$td" <<'PY'
import json, sys, os, hashlib
(L, hp, bp, seq, host, tag, path, role, code, exitc, tq, ts, td) = sys.argv[1:14]
KEEP = ('content-type','content-length','content-encoding','etag','last-modified',
        'server','vary','cache-control','access-control-allow-origin','x-cache')
hdrs = {}
if os.path.exists(hp):
    for line in open(hp, 'rb').read().decode('latin-1').splitlines():
        if ':' in line:
            k, v = line.split(':', 1)
            if k.strip().lower() in KEEP:
                hdrs[k.strip().lower()] = v.strip()
n = os.path.getsize(bp) if os.path.exists(bp) else 0
d = hashlib.sha256(open(bp,'rb').read()).hexdigest() if n else ''
row = {"seq": int(seq), "host": host, "tag": tag, "method": "GET", "path": path,
       "role": role, "http_status": code, "curl_exit": int(exitc),
       "body_bytes": n, "body_sha256": d,
       "content_type": hdrs.get('content-type','(none)'),
       "content_encoding": hdrs.get('content-encoding','(none)'),
       "etag": hdrs.get('etag','(none)'),
       "server": hdrs.get('server','(none)'),
       "headers": hdrs, "t_queued": tq, "t_sent": ts, "t_done": td}
open(L, 'a').write(json.dumps(row) + "\n")
print(f"seq={seq} GET {host}{path} -> {code} ctype={hdrs.get('content-type','-')} "
      f"bytes={n} sha256={d[:16]}")
PY
  log "seq=$SEQ GET https://$host$path status=$code exit=$exitc tag=$tag role=[$role]"
}

# control_verdict <tag>  — reads the ledger row just written and applies the STOP rule
control_verdict() {
  local tag="$1" expect="$2"
  python3 - "$LEDGER" "$tag" "$expect" <<'PY' || return 3
import json, sys
L, tag, expect = sys.argv[1], sys.argv[2], sys.argv[3]
rows = [json.loads(l) for l in open(L) if l.strip()]
r = [x for x in rows if x["tag"] == tag][-1]
ct = r["content_type"].split(';')[0].strip()
if expect == "absent":
    ok = r["http_status"] == "404" and r["body_bytes"] == 0 and ct == "text/vnd.a"
    print(f"CONTROL {tag}: 404={r['http_status']=='404'} 0B={r['body_bytes']==0} text/vnd.a={ct=='text/vnd.a'} -> {'PASS' if ok else 'FAIL'}")
elif expect == "live":
    ok = r["http_status"] == "200" and r["body_bytes"] == 281
    print(f"CONTROL {tag}: 200={r['http_status']=='200'} 281B={r['body_bytes']==281} -> {'PASS' if ok else 'FAIL'}")
else:
    ok = True
sys.exit(0 if ok else 3)
PY
}

controls() {
  local h t
  for h in $HOSTS; do
    t="c-$(echo "$h" | tr . -)-absent"
    req "$h" "/patient/configuration/system/zzz.not.a.real.key.zzz" \
      "CONTROL-1 certainly-absent dotted key: must be 404, 0 B, text/vnd.a. If it is not, a 200 on this namespace is a shell and every asset verdict below is worthless" \
      "$t" || return 1
    control_verdict "$t" absent || { echo "STOP: absent control failed on $h" >&2; return 3; }
    t="c-$(echo "$h" | tr . -)-live"
    req "$h" "/patient/configuration/system/logbook.supported.entry.types" \
      "CONTROL-2 known-live key: must be 200, 281 B, sha256 7f0a5bb4… (area E seq 2/78, area AI seq 2/6/10). If it is not, this host is not serving the patient config family" \
      "$t" || return 1
    control_verdict "$t" live || { echo "STOP: live control failed on $h" >&2; return 3; }
  done
}

assets() {
  local h
  for h in $HOSTS; do
    req "$h" "$PATIENT_ASSET" \
      "DATA patient eager bundle on its content-hashed name; recorded 3417255 B sha256 0fb4fbd4… (area V seq 3/7, area R2 seq 2). Whole-bundle local scan for 7896x — no per-SKU probe" \
      "a-$(echo "$h" | tr . -)-patient" || return 1
    req "$h" "$CLINIC_ASSET" \
      "CANDIDATE does the clinic build's recorded content-hashed name answer on a PATIENT host? Recorded 3397615 B sha256 2a7fa8e7… on carelinkhp/carelink.medtronic. A patient-host 200 with that digest would put the clinic device table (module 68462) inside this lane's reach; a 404 costs one request" \
      "a-$(echo "$h" | tr . -)-clinic" || return 1
  done
}

# Recorded revision 1 (see PLAN.md). The patient bundle names a key-addressable route this
# repository has only ever inventoried as a call site:
#   getDeviceModelMapping(V){return this.http.get(`patient/configuration/system/model-mapping/${V}`)}
# at byte 3374392 of the .com body. These four spend the reserve. The namespace is the SAME
# one control 1 lives in, so a 404 reads as absence and no fresh control is owed.
modelmap() {
  req carelink.minimed.com "/patient/configuration/system/model-mapping/US" \
    "CANDIDATE-1 key-addressable name route, discovered in the patient bundle at byte 3374392 and never probed before. Namespace = control 1's, so 404 = absent, 200 = document" \
    "m-us-com" || return 1
  req carelink.minimed.eu "/patient/configuration/system/model-mapping/US" \
    "CANDIDATE-2 same code, second deployment — does the route itself port?" \
    "m-us-eu" || return 1
  req carelink.minimed.eu "/patient/configuration/system/model-mapping/GB" \
    "CANDIDATE-3 a market area D measured with its own published key set" \
    "m-gb-eu" || return 1
  req carelink.minimed.eu "/patient/configuration/system/model-mapping/DE" \
    "CANDIDATE-4 the EU deployment's largest market" \
    "m-de-eu" || return 1
}

case "${1:-}" in
  controls) controls ;;
  assets)   assets ;;
  modelmap) modelmap ;;
  all)      controls || { echo "CONTROLS FAILED — assets not requested" >&2; exit 3; }; assets ;;
  *) echo "usage: probe.sh all|controls|assets|modelmap" >&2; exit 64 ;;
esac
echo "LEDGER_ROWS=$(ledger_len) CAP=$CAP"
