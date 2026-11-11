#!/usr/bin/env bash
# probe.sh — area AO: does the `Auth0SSOConfiguration` key appear in a CP[] entry
# on the five `android/` discovery tails area AH did NOT measure
# (`3.5`, `3.7`, `3.8`, `3.9`, `3.10`), on `clcloud.minimed.com` and
# `clcloud.minimed.eu`?
#
# THE QUESTION, and where it comes from:
#   `selectAuth0ConfigUrl()` computes
#       const key = cpEntry.UseSSOConfiguration ?? 'Auth0SSOConfiguration'
#   so the `??` fallback can only resolve to the second name when that key is
#   actually present in the chosen CP[] entry.  `docs/03` §3 carried a code finding
#   that the fallback makes the ADR 0002 pin guard INERT because the key was
#   believed present on every version.  Area AH measured the key by CP-entry
#   membership on EIGHT tails across TWO hosts and found it on `3.6` ONLY —
#   absent on `3.4`, `4.0`, `4.1`, `4.2`, `5.0` and on both fabricated controls
#   [source: findings-log/2026-11-10-area-ah-discovery-4x/FINDINGS.md §3].
#   The universal form of that finding is therefore refuted.  Five tails were
#   left unmeasured: `3.5`, `3.7`, `3.8`, `3.9`, `3.10`.  This pass measures
#   exactly those ten cells and claims nothing about any other tail.
#
#   The tails are the area letter's own five, named verbatim in
#   docs/11-suggested-research-areas.md (`### AO.`), which took them from AH §3's
#   stated scope limit.  They are consecutive members of the same naming
#   convention the axis is already known to key on — no wordlist, no guessing.
#
# THE SINGLE SOURCE OF THE CAP.  One assignment, here; `cap_guard` reads it, and
# FINDINGS.md's "N of a 12 cap" line must equal `wc -l results.jsonl`.
#
#   CAP=12 ==  1 host x 2 controls                    =  2
#            + 2 hosts x 5 tails (3.5/3.7/3.8/3.9/3.10) = 10
#            --                                           12 spent
#
# There is deliberately NO headroom: the letter's budget is `<=12` and the
# ten question cells are the entire deliverable.  A failed cell (000/5xx/timeout)
# is recorded AS a failure and is NOT a negative — it is reported as a non-answer
# rather than retried, because a retry would spend a cell that does not exist.
#
# GET only.  No POST, no OPTIONS, no token, no cookie, no auth header of any kind.
# `sleep 2.5` sits INSIDE the per-host flock, before the send, so consecutive
# requests to the same host are >= 2.5 s apart across any concurrent invocation.
#
# Usage:  ./probe.sh controls | .com | .eu | all

set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(git -C "$HERE" rev-parse --show-toplevel)"
RUNLOG="$HERE/run.log"
LEDGER="$HERE/results.jsonl"
SCRATCH="${AO_SCRATCH:-$REPO/.loop/ao-scratch}"
mkdir -p "$SCRATCH"

UA="carelink-bridge-research/1.0"
DELAY=2.5
CAP=12
BASE=v13
TAILS="3.5 3.7 3.8 3.9 3.10"
CTRL_TAIL="3.6"                 # positive control: AH §3 measured the key present here
ABSENT_TAIL="zz-ao-absent-3141" # certainly-absent control: no convention produces it
HOST_A=clcloud.minimed.com
HOST_B=clcloud.minimed.eu

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
  local out="$SCRATCH/$tag" t0 ts td code exitc
  local path="/connect/carepartner/$BASE/discover/android/$tail"

  touch "$SCRATCH/host-$host.lock" 2>/dev/null || true
  exec 9>"$SCRATCH/host-$host.lock"
  flock 9
  sleep "$DELAY"                                  # the sleep is INSIDE the per-host lock
  t0=$(date +%s.%N)                               # epoch seconds, before the send
  ts=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)
  code=$(curl -s --compressed --max-time 60 -A "$UA" -D "$out.h" -o "$out.b" \
              -w '%{http_code}' "https://$host$path" 2>>"$RUNLOG")
  exitc=$?
  flock -u 9
  exec 9>&-
  td=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)

  python3 - "$LEDGER" "$out.h" "$out.b" "$SEQ" "$host" "$tail" "$role" "$path" \
            "$code" "$exitc" "$t0" "$ts" "$td" <<'PY'
import hashlib, json, os, sys
(L, hp, bp, seq, host, tail, role, path, code, exitc, t0, ts, td) = sys.argv[1:14]
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

# --- the measurement: CP[] KEY MEMBERSHIP, not a substring search of the body ---
# AGENTS.md §7: facts only, captures never.  `certificates[].cert` is base64 X.509
# and is never read.  The two SSO fields' VALUES are route/file literals already
# published in this repo's ledgers, and only their basename is kept.
proj = None
if n and (hdrs.get('content-type', '').startswith('application/json')):
    try:
        doc = json.loads(raw)
        cps = doc.get('CP') or []
        proj = {
            "config_echo": doc.get('config'),
            "n_cp": len(cps),
            "regions": [c.get('region') for c in cps],
            "cp_key_sets": [sorted(c.keys()) for c in cps],
            "baseUrlCumulus": [c.get('baseUrlCumulus') for c in cps],
            "baseUrlCareLink": [c.get('baseUrlCareLink') for c in cps],
            "has_Auth0SSOConfiguration_key": ['Auth0SSOConfiguration' in c for c in cps],
            "has_UseSSOConfiguration_key": ['UseSSOConfiguration' in c for c in cps],
            "sso_filenames": [ (c.get('SSOConfiguration') or '').rsplit('/', 1)[-1] for c in cps ],
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
       "t0_epoch": float(t0), "t_sent": ts, "t_done": td}
open(L, 'a').write(json.dumps(row) + "\n")
print("seq=%s %s android/%s [%s] -> %s %s %sB sha=%s err=%s"
      % (seq, host, tail, role, code, hdrs.get('content-type', '-'), n,
         sha[:12], hdrs.get('x-amzn-errortype', '-')))
PY
  log "seq=$SEQ GET https://$host$path [$role] status=$code exit=$exitc"
}

# ---- CONTROLS FIRST, on the host swept first.  Both must pass or the pass aborts:
# a positive control that fails means no cell on this host is readable, and an
# absent control that carries the key means the measurement cannot discriminate.
controls() {
  log "=== controls on $HOST_A — both must pass before any question cell ==="
  req "$HOST_A" "$CTRL_TAIL" \
      "CONTROL-positive: android/3.6, AH §3 measured Auth0SSOConfiguration PRESENT on all 3 CP entries on both hosts" \
      "c1-pos-3-6" || return 1
  req "$HOST_A" "$ABSENT_TAIL" \
      "CONTROL-absent: fabricated tail $ABSENT_TAIL — no naming convention produces it; must NOT carry the key" \
      "c2-abs" || return 1
}

# The gate that reads the two control rows.  Exit 1 -> the pass aborts here and
# no question cell is spent.
check_controls() {
  python3 - "$LEDGER" <<'PY'
import json, sys
rows = {}
for line in open(sys.argv[1]):
    if line.strip():
        r = json.loads(line)
        rows[(r['host'], r['tail'])] = r
pos = rows.get(('clcloud.minimed.com', '3.6'))
neg = rows.get(('clcloud.minimed.com', 'zz-ao-absent-3141'))
ok = True
if not pos or pos['http_status'] != '200' or not pos.get('document') \
        or not all(pos['document'].get('has_Auth0SSOConfiguration_key') or [False]):
    print('CONTROL FAIL: positive control 3.6 did not return 200 with the key present on every CP entry')
    ok = False
else:
    print('CONTROL PASS: positive — 3.6 carries Auth0SSOConfiguration on %d of %d CP entries'
          % (sum(pos['document']['has_Auth0SSOConfiguration_key']), pos['document']['n_cp']))
if not neg or neg['http_status'] != '200' or not neg.get('document'):
    print('CONTROL FAIL: absent control returned no parseable 200 document')
    ok = False
elif any(neg['document'].get('has_Auth0SSOConfiguration_key') or []):
    print('CONTROL FAIL: absent control DOES carry the key — the measurement cannot discriminate')
    ok = False
else:
    print('CONTROL PASS: absent — %s carries Auth0SSOConfiguration on 0 of %d CP entries'
          % ('zz-ao-absent-3141', neg['document']['n_cp']))
sys.exit(0 if ok else 1)
PY
}

host_tails() {
  local h="$1" t
  local k; k=$(echo "$h" | tr . -)
  for t in $TAILS; do
    req "$h" "$t" "CANDIDATE: android/$t at base v13 — unmeasured by AH, classified here by CP-entry key membership" \
        "q-$k-$(echo "$t" | tr '.' '-')" || return 1
  done
}

case "${1:-}" in
  controls) controls ;;
  .com)     host_tails "$HOST_A" ;;
  .eu)      host_tails "$HOST_B" ;;
  all)      controls && check_controls && host_tails "$HOST_A" && host_tails "$HOST_B" ;;
  *) echo "usage: probe.sh controls|.com|.eu|all" >&2; exit 64 ;;
esac
echo "LEDGER_ROWS=$(ledger_len) CAP=$CAP"
