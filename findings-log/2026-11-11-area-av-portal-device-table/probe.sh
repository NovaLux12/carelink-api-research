#!/usr/bin/env bash
# Area AV — has the portal device table (module 68462) grown past SKU-78960 since the
# 2026-10-13 build, and what does it NAME the four tail codes?
#
# Cap 14, GET only, >=2.5 s between requests to the SAME host, sleep INSIDE a per-host
# flock. No POST, no OPTIONS, no token, no cookie, no auth, no wordlist.
#
# Every asset fetch is on a CONTENT-HASHED ASSET NAME recorded by an earlier pass, and
# its sha256 + byte count are asserted against the pinned value BEFORE anything in the
# body is trusted. On this host family the catch-all IS the entry document (200
# text/html 5518 B for any absent path), so a status code proves nothing: only a
# content-hashed chunk plus a digest comparison detects a deployment.
#
# Usage: probe.sh control   # the one control that must pass before anything else
#        probe.sh assets    # the five per-host asset fetches
#        probe.sh entry <host> <tag>   # reserve: the entry document, if a digest MOVED
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
# five levels up = the MAIN clone root (<clone>/.loop/worktrees/lav/findings-log/<area>)
MAIN="$(cd "$HERE/../../../../.." && pwd)"
RUNLOG="$HERE/run.log"
LEDGER="$HERE/results.jsonl"
SCRATCH="$MAIN/.loop/av-scratch"
mkdir -p "$SCRATCH" "$HERE/headers"

UA="carelink-bridge-research/1.0"
DELAY=2.5
CAP=14

# Pinned artefacts (2026-10-13, area G seq 2/3/5/6; area A seq 8/19/20; area V seq 10/13)
CLINIC_ASSET=/main.fb5f8cb7eb60c4d5.js
CLINIC_SHA=2a7fa8e7af519c2b493caf62c00b46c5e75a357048444dbf7abff6136bfc02ba
CLINIC_BYTES=3397615
SUPPORT_ASSET=/main.759cddab23085086.js
SUPPORT_SHA=a054555a0f22176ecb51d8f6439680a394e2be5e889494bec5004c93be28c954
SUPPORT_BYTES=3410666
HP_ENTRY_SHA=0f2c5f6257a6fc6af22e4b31309264df4c148e08016c196e1048bdc19a87e32d
SUP_ENTRY_SHA=f637c8d0cd4ec6bc70944f7c9083ace6c205c5ecd22ce5da6ed533ece6d9a1bc
ENTRY_BYTES=5518

[ -f "$LEDGER" ] || : > "$LEDGER"
[ -f "$RUNLOG" ] || : > "$RUNLOG"
SEQ=$(awk 'NF' "$LEDGER" 2>/dev/null | wc -l | tr -d ' '); SEQ=${SEQ:-0}

log() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)" "$*" >> "$RUNLOG"; }
ledger_len() { awk 'NF' "$LEDGER" 2>/dev/null | wc -l | tr -d ' '; }

cap_guard() {
  local n; n=$(ledger_len)
  if [ "$n" -ge "$CAP" ]; then log "CAP STOP at $n of $CAP"; echo "CAP STOP: $n of $CAP" >&2; return 1; fi
  return 0
}

# req <host> <path> <role> <tag>
req() {
  local host="$1" path="$2" role="$3" tag="$4"
  cap_guard || return 1
  SEQ=$((SEQ+1))
  local out="$SCRATCH/$tag" tq ts td code exitc
  tq=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)
  touch "$MAIN/.loop/host-$host.lock" 2>/dev/null || true
  exec 9>"$MAIN/.loop/host-$host.lock"
  flock 9
  sleep "$DELAY"                                  # sleep is INSIDE the per-host lock
  ts=$(date +%s.%N)                               # t_sent: epoch, required by the brief
  code=$(curl -s --compressed --max-time 180 -A "$UA" -D "$out.h" -o "$out.b" \
              -w '%{http_code}' "https://$host$path" 2>>"$RUNLOG")
  exitc=$?
  td=$(date +%s.%N)
  flock -u 9
  exec 9>&-
  cp "$out.h" "$HERE/headers/$tag.h" 2>/dev/null || true
  python3 - "$LEDGER" "$out.h" "$out.b" "$SEQ" "$host" "$tag" "$path" "$role" \
           "$code" "$exitc" "$tq" "$ts" "$td" <<'PY'
import json, sys, os, hashlib
(L, hp, bp, seq, host, tag, path, role, code, exitc, tq, ts, td) = sys.argv[1:14]
KEEP = ('content-type','content-length','content-encoding','etag','last-modified',
        'server','vary','cache-control','access-control-allow-headers','x-cache')
hdrs = {}
if os.path.exists(hp):
    for line in open(hp, 'rb').read().decode('latin-1').splitlines():
        if ':' in line:
            k, v = line.split(':', 1)
            if k.strip().lower() in KEEP:
                hdrs[k.strip().lower()] = v.strip()
n = os.path.getsize(bp) if os.path.exists(bp) else 0
d = hashlib.sha256(open(bp,'rb').read()).hexdigest() if n else ''
mtime = f"{os.stat(bp).st_mtime:.6f}" if os.path.exists(bp) else ''
row = {"seq": int(seq), "host": host, "tag": tag, "method": "GET", "path": path,
       "role": role, "http_status": code, "curl_exit": int(exitc),
       "body_bytes": n, "body_sha256": d, "body_mtime_epoch": mtime,
       "content_type": hdrs.get('content-type','(none)'),
       "content_encoding": hdrs.get('content-encoding','(none)'),
       "etag": hdrs.get('etag','(none)'),
       "server": hdrs.get('server','(none)'),
       "headers": hdrs, "t_queued": tq, "t_sent": ts, "t_done": td}
open(L, 'a').write(json.dumps(row) + "\n")
print(f"seq={seq} GET {host}{path} -> {code} ctype={hdrs.get('content-type','-')} "
      f"bytes={n} sha256={d[:16]} t_sent={ts}")
PY
  log "seq=$SEQ GET https://$host$path status=$code exit=$exitc tag=$tag role=[$role]"
}

# assert_entry <tag> <expected_sha> — the control's own verdict
assert_entry() {
  local tag="$1" exp="$2"
  python3 - "$LEDGER" "$tag" "$exp" "$ENTRY_BYTES" <<'PY' || return 3
import json, sys
L, tag, exp, n_exp = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
r = [json.loads(l) for l in open(L) if l.strip() if json.loads(l)["tag"] == tag][-1]
ct = r["content_type"].split(';')[0].strip()
ok = r["http_status"] == "200" and r["body_bytes"] == n_exp and r["body_sha256"] == exp
print(f"CONTROL {tag}: 200={r['http_status']=='200'} {n_exp}B={r['body_bytes']==n_exp} "
      f"sha_match={r['body_sha256']==exp} ctype={ct} -> {'PASS' if ok else 'FAIL'}")
sys.exit(0 if ok else 3)
PY
}

# assert_asset <tag> <expected_sha> <expected_bytes> — PASS / MOVED, never silently accepted
assert_asset() {
  local tag="$1" exp="$2" n_exp="$3"
  python3 - "$LEDGER" "$tag" "$exp" "$n_exp" <<'PY'
import json, sys
L, tag, exp, n_exp = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
r = [json.loads(l) for l in open(L) if l.strip() if json.loads(l)["tag"] == tag][-1]
ct = r["content_type"].split(';')[0].strip()
same = (r["body_sha256"] == exp and r["body_bytes"] == n_exp)
real = (ct == "application/javascript")
print(f"ASSERT {tag}: status={r['http_status']} ctype={ct} bytes={r['body_bytes']} "
      f"sha256={r['body_sha256'][:16]} expected={exp[:16]}/{n_exp} "
      f"-> {'PASS' if same and real else ('MOVED' if real else 'NOT-AN-ASSET')}")
sys.exit(0 if (same and real) else 4)
PY
}

case "${1:-}" in
  control)
    req carelinkhp.minimed.eu "/" \
      "CONTROL entry document on the clinic host: pinned 5518 B sha256 0f2c5f62… (area G seq 2, area V seq 9). If this does not reproduce, the host family is not serving the artefact this lane's question is about and nothing below may be trusted" \
      "c-hp-entry"
    assert_entry c-hp-entry "$HP_ENTRY_SHA" || { echo "STOP: control failed" >&2; exit 3; }
    ;;
  assets)
    # five hosts, each on its OWN build's content-hashed asset name
    req carelinkhp.minimed.eu "$CLINIC_ASSET" \
      "DATA clinic pow build on its content-hashed name; pinned 3397615 B sha256 2a7fa8e7… (area G seq 3, area V seq 10)" "a-hp-main"
    assert_asset a-hp-main "$CLINIC_SHA" "$CLINIC_BYTES"
    req carelink.medtronic.com "$CLINIC_ASSET" \
      "DATA clinic build A on carelink.medtronic.com; pinned identical to hp (area A seq 8)" "a-cmc-main"
    assert_asset a-cmc-main "$CLINIC_SHA" "$CLINIC_BYTES"
    req carelink.medtronic.eu "$CLINIC_ASSET" \
      "DATA clinic build A on carelink.medtronic.eu; pinned identical to hp (area A seq 19)" "a-cme-main"
    assert_asset a-cme-main "$CLINIC_SHA" "$CLINIC_BYTES"
    req carelink-support.medtronic.eu "$SUPPORT_ASSET" \
      "DATA support cua build on its content-hashed name; pinned 3410666 B sha256 a054555a… (area G seq 6, area V seq 13)" "a-sup-main"
    assert_asset a-sup-main "$SUPPORT_SHA" "$SUPPORT_BYTES"
    req carelink-support.medtronic.com "$SUPPORT_ASSET" \
      "DATA support build B on carelink-support.medtronic.com; pinned identical to .eu (area A seq 20)" "a-supc-main"
    assert_asset a-supc-main "$SUPPORT_SHA" "$SUPPORT_BYTES"
    ;;
  entry)
    # reserve path, only if a digest MOVED: the entry document names today's asset
    req "$2" "/" "RESERVE entry document after a digest MOVED — names the current content-hashed asset so the deployment can be fetched on its own name" "r-$3-entry"
    ;;
  *) echo "usage: $0 control|assets|entry <host> <tag>" >&2; exit 2 ;;
esac

echo "ledger rows: $(ledger_len) of $CAP cap"
