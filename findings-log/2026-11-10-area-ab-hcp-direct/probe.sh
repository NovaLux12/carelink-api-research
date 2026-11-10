#!/usr/bin/env bash
# Area AB — are the six DIRECT `/hcp/configuration/*` verdicts deployment-portable?
# Claim: NovaLux12/carelink-api-research#162. Cap 43, >=2.5 s per host, INSIDE the flock.
#
# THE SINGLE SOURCE OF THE CAP. One assignment, here; `cap_guard` reads it, and
# FINDINGS.md's "N of a 43 cap" line must equal `wc -l results.jsonl`.
#
#   CAP=43  ==  6 candidates x 3 hosts        = 18
#             + 4 controls    x 3 hosts       = 12
#             + 3 POST-only routes x 3 hosts  =  9   (empty-body OPTIONS)
#             + corpus control, per HOST      =  4   (4 build digests, one per host)
#                                                --
#                                                43
#
# The sweep is THREE hosts, not four. `carelinkhp.minimed.eu` is the recorded
# BASELINE (`findings-log/probe-2026-10-08/recon/HCP-CONFIG-SCHEMA.md` §3, §10) and
# §10 is titled "Do not re-run": re-sweeping it answers "do they exist", which is
# settled, not "are those verdicts portable", which is AB. It is still touched by the
# corpus control, because that control is performed PER HOST (the 2026-10-17 lesson,
# recorded in docs/11's AB correction blockquote: per host, not per build).
#
# GET only, plus empty-body OPTIONS on the three routes recorded POST-only. No POST,
# no token, no cookie, no auth beyond the X-System-ID control header, no wordlist.
#
# Usage: probe.sh all      # corpus control -> derivation -> sweep
#        probe.sh bundles  # batch 1 only (4 requests)
#        probe.sh sweep    # batch 2 only (39 requests), requires batch 1's assets
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../../../../.." && pwd)"
RUNLOG="$HERE/run.log"
LEDGER="$HERE/results.jsonl"
SCRATCH="$REPO/.loop/ab-scratch"
ASSETS="$REPO/.loop/ab-assets"          # gitignored: 3.4 MB bundles never enter findings-log/
mkdir -p "$SCRATCH" "$ASSETS"
export AB_ASSETS="$ASSETS"

UA="carelink-bridge-research/1.0"
DELAY=2.5
CAP=43
PROWEB="X-System-ID: ProWeb"

# The six, as the record states them (self-check target only — the list actually
# issued is re-derived from the builds in `derive` below, and the derivation aborts
# the sweep if it does not return exactly this set).
SIX="access/config appContext application productContext user whitelisted"
POST_ONLY="application productContext user"
HOSTS="carelink.medtronic.com carelink.medtronic.eu carelink-support.medtronic.com"
BASE=carelinkhp.minimed.eu

CLINIC_ASSET=/main.fb5f8cb7eb60c4d5.js
SUPPORT_ASSET=/main.759cddab23085086.js

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

# req <method> <host> <path> <role> <tag> [header] [keep]
req() {
  local method="$1" host="$2" path="$3" role="$4" tag="$5" hdr="${6:-}" keep="${7:-}"
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
  [ "$keep" = asset ] && [ -f "$out.b" ] && cp "$out.b" "$ASSETS/$tag.b"
  python3 - "$LEDGER" "$out.h" "$out.b" "$SEQ" "$method" "$host" "$tag" "$path" "$role" "${hdr:-(none)}" "$code" "$exitc" "$tq" "$ts" "$td" <<'PY'
import json, sys, os, hashlib
(L, hp, bp, seq, method, host, tag, path, role, sent, code, exitc,
 tq, ts, td) = sys.argv[1:16]
KEEP = ('content-type','content-length','content-encoding','allow','server','vary',
        'cache-control','access-control-allow-origin','access-control-allow-methods',
        'access-control-allow-headers','access-control-expose-headers')
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
       "content_encoding": hdrs.get('content-encoding','(none)'),
       "server": hdrs.get('server','(none)'),
       "headers": hdrs, "t_queued": tq, "t_sent": ts, "t_done": td}
open(L, 'a').write(json.dumps(row) + "\n")
print(f"seq={seq} {method} {host}{path} -> {code} ctype={hdrs.get('content-type','-')} "
      f"bytes={n} allow={hdrs.get('allow','-')} acam={hdrs.get('access-control-allow-methods','-')} "
      f"sha256={d[:16]}")
PY
  log "seq=$SEQ $method https://$host$path host_seq=? status=$code exit=$exitc tag=$tag role=[$role]"
}

bundles() {
  # Corpus control, performed PER HOST (four requests, four digests). On this family
  # the catch-all IS the entry document, so only a content-hashed chunk tells a
  # deployment from a fallback (area A). Recorded digests: clinic 2a7fa8e7af519c2b…
  # 3397615 B, support a054555a0f22176e… 3410666 B.
  req GET "$BASE" "$CLINIC_ASSET" "CORPUS-CONTROL baseline clinic build; recorded 3397615 B sha256 2a7fa8e7af519c2b… (2026-10-14-area-k-clinic-controlflow/differential.py:142)" \
    b01-baseline-clinic-asset "" asset || return 0
  req GET carelink.medtronic.com "$CLINIC_ASSET" "CORPUS-CONTROL clinic build on .com; same anchor" \
    b02-com-clinic-asset "" asset || return 0
  req GET carelink.medtronic.eu "$CLINIC_ASSET" "CORPUS-CONTROL clinic build on .eu; same anchor" \
    b03-eu-clinic-asset "" asset || return 0
  req GET carelink-support.medtronic.com "$SUPPORT_ASSET" "CORPUS-CONTROL support build; recorded 3410666 B sha256 a054555a0f22176e… (2026-10-13-area-g-device-tables/FINDINGS.md:70)" \
    b04-support-asset "" asset || return 0
}

derive() {
  # Zero requests. Re-derive the six from the two fetched builds and REFUSE to sweep
  # if the extraction does not return exactly the six this plan names.
  python3 - "$ASSETS" "$SIX" "$RUNLOG" <<'PY'
import hashlib, os, re, sys
assets, six, runlog = sys.argv[1], sys.argv[2].split(), sys.argv[3]
CLINIC = "/main.fb5f8cb7eb60c4d5.js"   # clinic build, recorded 2a7fa8e7af519c2b…
rec = {"b01-baseline-clinic-asset": "2a7fa8e7af519c2b493caf62c00b46c5e75a357048444dbf7abff6136bfc02ba",
       "b02-com-clinic-asset":      "2a7fa8e7af519c2b493caf62c00b46c5e75a357048444dbf7abff6136bfc02ba",
       "b03-eu-clinic-asset":       "2a7fa8e7af519c2b493caf62c00b46c5e75a357048444dbf7abff6136bfc02ba",
       "b04-support-asset":         "a054555a0f22176ecb51d8f6439680a394e2be5e889494bec5004c93be28c954"}
out = []
ok = True
DIRECT = re.compile(rb"hcp/configuration/(?!public/)([A-Za-z0-9._?=&/()-]+)")
PUB = re.compile(rb"hcp/configuration/public/([A-Za-z0-9._?=&/()-]+)")
sets = {}
for tag in sorted(rec):
    p = os.path.join(assets, tag + ".b")
    if not os.path.exists(p):
        out.append(f"DERIVE STOP: {tag} body missing — batch 1 did not retain it")
        ok = False; continue
    body = open(p, 'rb').read()
    d = hashlib.sha256(body).hexdigest()
    same = (d == rec[tag])
    direct = sorted({m.group(1).decode() for m in DIRECT.finditer(body)})
    pubs = sorted({m.group(1).decode() for m in PUB.finditer(body)})
    sets[tag] = (direct, pubs, same)
    out.append(f"DERIVE {tag}: status=asserted bytes={len(body)} sha256={d[:16]}… "
               f"recorded={rec[tag][:16]}… reproduces={same} public_literals={len(pubs)} "
               f"direct_literals={len(direct)}")
    if not same:
        ok = False
        out.append(f"DERIVE STOP: {tag} digest does not reproduce — this host serves a build "
                   f"no recorded route table applies to. Do not extrapolate onto it.")
for tag, (direct, pubs, same) in sorted(sets.items()):
    out.append(f"DERIVE {tag} direct set: {' '.join(direct)}")
# Self-check: the extraction must return 6 direct literals, and the same 6 in both builds.
for tag, (direct, pubs, same) in sets.items():
    if len(direct) != 6:
        ok = False; out.append(f"DERIVE STOP: {tag} yields {len(direct)} direct literals, "
                               f"HCP-CONFIG-SCHEMA.md §10 records 6")
    if sorted(direct) != sorted(six):
        ok = False; out.append(f"DERIVE STOP: {tag} set {sorted(direct)} != planned {sorted(six)}")
c = sets.get("b01-baseline-clinic-asset", ([], [], False))[0]
s = sets.get("b04-support-asset", ([], [], False))[0]
out.append(f"DERIVE shared={len(set(c) & set(s))} clinic_only={sorted(set(c)-set(s))} "
           f"support_only={sorted(set(s)-set(c))}")
out.append("DERIVE VERDICT: " + ("PROCEED — 4 of 4 digests reproduce, both builds name the same 6"
                                 if ok else "STOP — see above"))
text = "\n".join(out)
open(os.path.join(os.path.dirname(runlog), "derive.txt"), "w").write(text + "\n")
with open(runlog, "a") as f:
    f.write(text + "\n")
print(text)
sys.exit(0 if ok else 3)
PY
}

sweep() {
  local h
  for h in $HOSTS; do
    # ---- controls first, per host (4) --------------------------------------
    req GET "$h" "/hcp/configuration/public/pow.crm.settings" \
      "CONTROL-1 positive: known-live key WITH X-System-ID: ProWeb (200 recorded HCP-CONFIG-SCHEMA.md:148). Proves the header is accepted here and the verdict rule is live" \
      "c1-$(echo "$h"|tr . -)-pow-crm" "$PROWEB" || return 0
    req GET "$h" "/hcp/configuration/public/CSU.CONTROL.CODES.SETTINGS" \
      "CONTROL-2 absent, UPPER-case spelling: 404 recorded (HCP-CONFIG-SCHEMA.md:121,188). Proves a 404 on THIS host is not the SPA fallback, so a 404 is a true absence" \
      "c2-$(echo "$h"|tr . -)-absent-upper" "$PROWEB" || return 0
    req GET "$h" "/hcp/configuration/public/cua.control.codes.settings" \
      "CONTROL-3 case control, lower-case: 200 recorded (HCP-CONFIG-SCHEMA.md:125,155). With CONTROL-2 this re-derives case-sensitivity ON THIS HOST" \
      "c3-$(echo "$h"|tr . -)-case-lower" "$PROWEB" || return 0
    req GET "$h" "/hcp/configuration/public/logbook.supported.entry.types" \
      "CONTROL-4 header ABSENT: 412 recorded (HCP-CONFIG-SCHEMA.md:151). Proves the header gate is real on this host, and that a 412 means 'header rejected', not 'absent'" \
      "c4-$(echo "$h"|tr . -)-no-header" "" || return 0
    # ---- the six candidates (6) --------------------------------------------
    local k
    for k in $SIX; do
      req GET "$h" "/hcp/configuration/$k" \
        "CANDIDATE direct route literal \`$k\`, derived offline from both builds' route tables (derive.txt), WITH X-System-ID: ProWeb. Recorded baseline on carelinkhp.minimed.eu: 405 POST-only for application/productContext/user, 401 token-gated for access/config/appContext/whitelisted (HCP-CONFIG-SCHEMA.md:112,166-178). This cell is the portability comparison" \
        "k-$(echo "$h"|tr . -)-$(echo "$k"|tr '/A-Z' '-a-z')" "$PROWEB" || return 0
    done
    # ---- empty-body OPTIONS on the three POST-only routes (3) --------------
    for k in $POST_ONLY; do
      req OPTIONS "$h" "/hcp/configuration/$k" \
        "OPTIONS (empty body, no -d) on \`$k\` — recorded POST-only (405) on the baseline. Establishes the allow-methods / ACAM the deployment advertises. OPTIONS is not a POST; AGENTS.md §8 permits an empty-body preflight" \
        "o-$(echo "$h"|tr . -)-$(echo "$k"|tr 'A-Z' 'a-z')" "$PROWEB" || return 0
    done
  done
}

case "${1:-}" in
  bundles) bundles ;;
  derive)  derive ;;
  sweep)   derive >/dev/null || { echo "DERIVE FAILED — sweep not issued" >&2; exit 3; }; sweep ;;
  all)     bundles; derive || { echo "DERIVE FAILED — sweep not issued" >&2; exit 3; }; sweep ;;
  *) echo "usage: probe.sh all|bundles|derive|sweep" >&2; exit 64 ;;
esac
echo "LEDGER_ROWS=$(ledger_len) CAP=$CAP"
