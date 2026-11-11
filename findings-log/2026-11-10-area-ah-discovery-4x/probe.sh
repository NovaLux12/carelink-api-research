#!/usr/bin/env bash
# probe.sh — area AH: do the `android/{4.0,4.1,4.2,5.0}` discovery cells still
# serve the cumulus-v2 / carelink-v1 / pde-v1 document with no Auth0 selection?
# Pass of 2026-11-10, claim #180, branch research/ah-discovery-4x.
#
# THE CLAIM UNDER TEST, verbatim from findings-log/cumulus-v2-spike.md:13-15:
#
#   "Discovery cells `android/{4.0,4.1,4.2,5.0}` return cumulus **v2** + CareLink
#    API v1 + PDE v1 configs with NO Auth0 and no CLINICAL region."
#
# That reading came from 2026-08-22 and has NEVER been re-derived from a ledger:
# `git ls-files 'findings-log/*/results.jsonl' | xargs grep -l '/discover/android/4\.'`
# returns nothing at this head (61 committed ledgers).  The nearest ledgered pass,
# area AE (2026-11-10), laddered STRICTLY INSIDE (3.6,3.9) and recorded `3.89` as the
# last legacy cell — it never reached 4.x.  So the 4.x reading rests on prose alone.
#
# THE SINGLE SOURCE OF THE CAP. One assignment, here; `cap_guard` reads it, and
# FINDINGS.md's "N of a 20 cap" line must equal `wc -l results.jsonl`.
#
#   CAP=20 ==  2 hosts x 2 controls            =  4
#            + 2 hosts x 4 tails (4.0/4.1/4.2/5.0) =  8
#            --                                      12 spent
#            + 8 held back for the failure class      = 20
#
# The 8 unspent are deliberate: AGENTS.md §8 and the claim both say a failure
# (000/5xx/timeout) is a FAILURE, never an absence, and a re-issue costs a request.
# If nothing fails they stay unspent, and the FINDINGS line reads "12 of a 20 cap".
#
# GET only.  No POST, no OPTIONS, no token, no cookie, no auth header of any kind.
# No wordlist: the four tails are the claim's own four, written down in the spike
# and in findings-log/probe-2026-10-08/PROBE-FINDINGS.md:60.  The absent control is
# the fabricated tail `zz-absent-8713`, which no naming convention would produce.
# `sleep 2.5` sits INSIDE the per-host flock, before the send.
#
# Usage:  ./probe.sh host1 | host2 | all

set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../../../../.." && pwd)"
RUNLOG="$HERE/run.log"
LEDGER="$HERE/results.jsonl"
SCRATCH="$REPO/.loop/ah-scratch"
mkdir -p "$SCRATCH"

UA="carelink-bridge-research/1.0"
DELAY=2.5
CAP=20
BASE=v13
TAILS="4.0 4.1 4.2 5.0"
ABSENT_TAIL="zz-absent-8713"
CTRL_TAIL="3.6"

[ -f "$LEDGER" ] || : > "$LEDGER"
[ -f "$RUNLOG" ] || : > "$RUNLOG"
SEQ=$(awk 'NF' "$LEDGER" 2>/dev/null | wc -l | tr -d ' '); SEQ=${SEQ:-0}

log() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)" "$*" >> "$RUNLOG"; }
ledger_len() { awk 'NF' "$LEDGER" 2>/dev/null | wc -l | tr -d ' '; }

cap_guard() {
  local n; n=$(ledger_len)
  if [ "$n" -ge "$CAP" ]; then
    log "CAP STOP at $n of $CAP"
    echo "CAP STOP: $n of $CAP" >&2
    return 1
  fi
  return 0
}

# req <host> <tail> <role> <tag>
req() {
  local host="$1" tail="$2" role="$3" tag="$4"
  cap_guard || return 1
  SEQ=$((SEQ+1))
  local out="$SCRATCH/$tag" tq ts td code exitc
  local path="/connect/carepartner/$BASE/discover/android/$tail"
  tq=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)

  touch "$REPO/.loop/host-$host.lock" 2>/dev/null || true
  exec 9>"$REPO/.loop/host-$host.lock"
  flock 9
  sleep "$DELAY"                                 # the sleep is INSIDE the per-host lock
  ts=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)
  code=$(curl -s --compressed --max-time 60 -A "$UA" -D "$out.h" -o "$out.b" \
              -w '%{http_code}' "https://$host$path" 2>>"$RUNLOG")
  exitc=$?
  flock -u 9
  exec 9>&-
  td=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)

  python3 - "$LEDGER" "$out.h" "$out.b" "$SEQ" "$host" "$tail" "$role" "$path" \
            "$code" "$exitc" "$tq" "$ts" "$td" <<'PY'
import hashlib, json, os, sys
(L, hp, bp, seq, host, tail, role, path, code, exitc, tq, ts, td) = sys.argv[1:15]
KEEP = ('content-type', 'content-length', 'content-encoding', 'x-amzn-errortype',
        'x-amzn-requestid', 'x-cache', 'server', 'vary', 'cache-control')
hdrs = {}
if os.path.exists(hp):
    for line in open(hp, 'rb').read().decode('latin-1').splitlines():
        if ':' in line:
            k, v = line.split(':', 1)
            if k.strip().lower() in KEEP:
                hdrs[k.strip().lower()] = v.strip()
n = os.path.getsize(bp) if os.path.exists(bp) else 0
raw = open(bp, 'rb').read() if n else b''
sha = hashlib.sha256(raw).hexdigest() if n else ''

# --- the claim's four fields, extracted from the body (bounded projection) ----
# AGENTS.md §7: facts only, captures never.  The CP array is projected to the
# three baseUrl values VERBATIM (they are route literals, not credentials) plus
# key-presence booleans; `certificates[].cert` is base64 X.509 and is never read.
proj = None
if n and (hdrs.get('content-type', '').startswith('application/json')):
    try:
        doc = json.loads(raw)
        cps = doc.get('CP') or []
        proj = {
            "config_echo": doc.get('config'),
            "n_cp": len(cps),
            "regions": [c.get('region') for c in cps],
            "baseUrlCumulus": [c.get('baseUrlCumulus') for c in cps],
            "baseUrlCareLink": [c.get('baseUrlCareLink') for c in cps],
            "baseUrlPde": [c.get('baseUrlPde') for c in cps],
            "has_Auth0SSOConfiguration_key": ['Auth0SSOConfiguration' in c for c in cps],
            "has_UseSSOConfiguration_key": ['UseSSOConfiguration' in c for c in cps],
            "SSOConfiguration_filenames": [ (c.get('SSOConfiguration') or '').rsplit('/', 1)[-1] for c in cps ],
            "n_supported_countries": len(doc.get('supportedCountries') or []),
            "top_level_keys": sorted(doc.keys()),
        }
    except Exception as e:
        proj = {"parse_error": type(e).__name__ + ": " + str(e)[:120]}

row = {"seq": int(seq), "host": host, "tail": tail, "role": role, "method": "GET",
       "base": "v13", "path": path, "url": "https://" + host + path,
       "http_status": code, "curl_exit": int(exitc), "body_bytes": n,
       "body_sha256": sha,
       "content_type": hdrs.get('content-type', '(none)'),
       "x_amzn_errortype": hdrs.get('x-amzn-errortype', '(none)'),
       "x_cache": hdrs.get('x-cache', '(none)'),
       "server": hdrs.get('server', '(none)'),
       "headers": hdrs, "document": proj,
       "t_queued": tq, "t_sent": ts, "t_done": td}
open(L, 'a').write(json.dumps(row) + "\n")
print("seq=%s %s android/%s [%s] -> %s %s %sB sha=%s err=%s"
      % (seq, host, tail, role, code, hdrs.get('content-type', '-'), n,
         sha[:12], hdrs.get('x-amzn-errortype', '-')))
PY
  log "seq=$SEQ GET https://$host$path [$role] status=$code exit=$exitc"
}

host_controls() {
  local h="$1"
  local k; k=$(echo "$h" | tr . -)
  # CONTROL 1 — plausible, known-live: base v13, tail 3.6.  Recorded 200 with the
  # Auth0+v13 document on both hosts (area AE ledger seq 2 and seq 10 re-derived it
  # 2026-11-10; PROBE-FINDINGS.md §3 records it from 2026-10-08).  If this fails,
  # NOTHING on this host is readable and every 4.x cell is a non-answer.
  req "$h" "$CTRL_TAIL" "CONTROL-live: base v13 tail 3.6, recorded 200 + Auth0/v13 document on both hosts" \
      "c1-$k-live-3.6" || return 1
  # CONTROL 2 — certainly absent.  A fabricated tail no convention produces.
  # Under Oracle A on clcloud.* the no-route envelope is 403
  # MissingAuthenticationTokenException, 42 B, body sha256 f249b63cb2fc… — but a
  # 200 here would ALSO be a valid control result, because AA established the tail
  # is never validated (§3b.1).  So this control is read as: does the host answer
  # at all, or does it hand back the same document it gives a real tail?
  req "$h" "$ABSENT_TAIL" "CONTROL-absent: fabricated tail zz-absent-8713 — no naming convention produces it" \
      "c2-$k-absent" || return 1
}

host_tails() {
  local h="$1" t
  local k; k=$(echo "$h" | tr . -)
  for t in $TAILS; do
    req "$h" "$t" "CANDIDATE: the claim's cell android/$t at base v13" \
        "k-$k-$(echo "$t" | tr '.' '-')" || return 1
  done
}

run_host() {
  local h="$1"
  log "=== host $h — controls first, then 4 tails at base $BASE ==="
  host_controls "$h" || return 1
  host_tails "$h" || return 1
  log "=== host $h done; ledger $(ledger_len) of cap $CAP ==="
}

# ADDENDUM after the 12-request sweep (2 requests, cap unchanged at 20).
# `docs/03-discovery-and-versions.md:164-169` states the `Auth0SSOConfiguration` KEY
# "now exists on every version 3.4 -> 5.0, including the cumulus-v2 no-Auth0 cells",
# and builds on it a code finding: that `selectAuth0ConfigUrl()`'s
# `?? 'Auth0SSOConfiguration'` fallback makes the ADR 0002 guard INERT, so bumping
# the pin to android/4.0 would "fail later at the data call, with no named error".
# The 4.x bodies in this pass carry NO such key (see results.jsonl, seq 3-6, 9-12:
# CP key sets are {SSOConfiguration, baseUrlAem, baseUrlCareLink, baseUrlCumulus,
# baseUrlPde, region}).  So the doc's claim is refuted at its middle.  3.4 is the
# only other version the doc names and the one cell that would test its lower
# bound, so it is measured here rather than argued from the middle.  Justified,
# bounded, and recorded before the send.
auth0_lower_bound() {
  local h="$1"; local k; k=$(echo "$h" | tr . -)
  req "$h" "3.4" "ADDENDUM: docs/03:164 claims the Auth0SSOConfiguration KEY spans 3.4 -> 5.0; 3.4 is that claim's lower bound" \
      "a-$k-3-4" || return 1
}

# ADDENDUM 2 (2 requests, ledger 14 -> 16 of the SAME 20 cap; no revision).
# The absent control is the result, not a caveat: `zz-absent-8713` returned 200 with
# the SAME tail-erased document as all four 4.x cells on each host.  That reads as
# "v2 is the FALLBACK; 3.4 and 3.6 are the keyed exceptions" — the inverse of the
# spike's "4.x cells return v2".  One fabricated tail is a single point; a value
# that is obviously not a version (`99.99`, above every tail ever recorded on this
# axis, where the highest real string is `12.0` per PROBE-FINDINGS §7) tests the
# same claim where no reading of "maybe Medtronic has a 99.x build" can rescue it.
# Bounded, justified, recorded before the send.
fallback_confirm() {
  local h="$1"; local k; echo "$h" | tr . - >/dev/null
  k=$(echo "$h" | tr . -)
  req "$h" "99.99" "FALLBACK-CONFIRM: tail 99.99 is above every string this axis has ever served (max recorded 12.0); if it returns the same document as 4.x, v2 is the default and not a version selection" \
      "f-$k-99-99" || return 1
}

case "${1:-}" in
  host1) run_host clcloud.minimed.com ;;
  host2) run_host clcloud-trials.minimed.com ;;
  all)   run_host clcloud.minimed.com && run_host clcloud-trials.minimed.com ;;
  auth0-bound)
         log "=== addendum: Auth0SSOConfiguration lower bound (docs/03:164) ==="
         auth0_lower_bound clcloud.minimed.com &&
         auth0_lower_bound clcloud-trials.minimed.com ;;
  fallback)
         log "=== addendum 2: fallback confirmation at tail 99.99 ==="
         fallback_confirm clcloud.minimed.com &&
         fallback_confirm clcloud-trials.minimed.com ;;
  *) echo "usage: probe.sh host1|host2|all|auth0-bound|fallback" >&2; exit 64 ;;
esac
echo "LEDGER_ROWS=$(ledger_len) CAP=$CAP"
