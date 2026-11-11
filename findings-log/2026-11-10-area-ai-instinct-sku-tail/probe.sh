#!/usr/bin/env bash
# Area AI — what do SKU-78961-01 … SKU-78968-01 map to, and are they in the
# patient document at all?  Claim: NovaLux12/carelink-api-research#181.
#
# Cap 16, `sleep 2.5` INSIDE the per-host flock, GET only.
#
# THE SINGLE SOURCE OF THE CAP. One assignment, here; `cap_guard` reads it, and
# FINDINGS.md's "N of a 16 cap" line must equal `wc -l results.jsonl`.
#
#   CAP=16  ==  3 hosts x (2 controls + 2 documents) = 12
#             + 4 unspent
#
# WHY TWO DOCUMENTS AND NOT EIGHT PER-SKU PROBES.
#   The question is "which of the 8 tail SKUs appear in the patient document,
#   and with what name". Both patient documents that carry SKU strings are
#   fetched WHOLE, at a key the record already names, and scanned locally:
#
#     /patient/configuration/system/personal.device.family.to.model.mapping
#         the 16-family map — area E seq 40, 200, 3470 B, sha256 ae70bde0… on
#         BOTH .com and -trials (`findings-log/2026-10-13-area-e-perkey-deployments/results.jsonl:40,116`)
#     /patient/configuration/system/personal.common.core.report.generation
#         the report-naming dict holding reportFileNamingSupportedPumpModels —
#         area E seq 29/105, 200, 10937 B, sha256 2f918b71… on both
#         (`…/results.jsonl:29,105`); area H located the 214-entry list here
#
#   A per-SKU GET would be `/patient/configuration/system/<key>.<SKU>` — a
#   sub-key grammar that is recorded NOWHERE in this repository. That is
#   wordlist fuzzing under another name, and it would burn 8 requests to
#   re-fetch bytes these two documents already contain. So the method is
#   one document fetch per host per document, then a local scan (extract.py,
#   zero requests). Which approach was taken, and why, is stated in FINDINGS.md.
#
# Controls FIRST on every host, before either document:
#   C1 absent  /patient/configuration/system/zzz.not.a.real.key.zzz  -> 404, 0 B
#              (area E seq 1/77; a genuine 404 on this namespace, so a 404 here
#               is an absence and not a catch-all)
#   C2 live    /patient/configuration/system/logbook.supported.entry.types
#              -> 200, 281 B, sha256 7f0a5bb4… (area E seq 2/78)
#
# Response BODIES are transient (kept in an uncommitted scratch dir): only
# size, content-type and sha256 enter results.jsonl. extract.py writes the
# EXTRACTED rows (the 16 family rows; the SKU/NNNNN-01 entries of the report
# list) into this log dir — the same thing area H committed as
# `family-map-verbatim.txt`, not the raw ~11 KB bodies.
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
# The main clone's `.loop/` holds the per-host locks and the scratch dir, and it
# is the SAME directory whichever worktree this runs from — resolved from git's
# common dir, not by counting `..` segments (a committed absolute path fails the
# gate's machine-path rule; a miscounted relative path would silently drop the
# locks into the wrong tree).
_gitdir="$(git -C "$HERE" rev-parse --git-common-dir 2>/dev/null)"
if [ -n "$_gitdir" ]; then
  REPO="$(cd "$(dirname "$(cd "$HERE" && cd "$_gitdir" && pwd)")" && pwd)"
else
  REPO="$(cd "$HERE/../../.." && pwd)"
fi
RUNLOG="$HERE/run.log"
LEDGER="$HERE/results.jsonl"
SCRATCH="$REPO/.loop/ai-scratch"
mkdir -p "$SCRATCH"
export AI_SCRATCH="$SCRATCH"

UA="carelink-bridge-research/1.0"
DELAY=2.5
CAP=16

HOSTS="carelink.minimed.com carelink.minimed.eu carelink-trials.minimed.com"
K_ABSENT="/patient/configuration/system/zzz.not.a.real.key.zzz"
K_LIVE="/patient/configuration/system/logbook.supported.entry.types"
D_FAMILY="/patient/configuration/system/personal.device.family.to.model.mapping"
D_REPORT="/patient/configuration/system/personal.common.core.report.generation"

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

# req <host> <path> <role> <tag>
# The body always lands at $SCRATCH/<tag>.b (curl -o); nothing is copied, and the
# scratch dir is gitignored, so bodies stay transient by construction.
req() {
  local host="$1" path="$2" role="$3" tag="$4"
  cap_guard || return 1
  SEQ=$((SEQ+1))
  local out="$SCRATCH/$tag" tq ts td code exitc
  tq=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)
  touch "$REPO/.loop/host-$host.lock" 2>/dev/null || true
  exec 9>"$REPO/.loop/host-$host.lock"
  flock 9
  sleep "$DELAY"                       # the sleep is INSIDE the per-host lock
  ts=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)
  code=$(curl -s --compressed --max-time 120 -A "$UA" \
              -D "$out.h" -o "$out.b" -w '%{http_code}' \
              "https://$host$path" 2>>"$RUNLOG")
  exitc=$?
  flock -u 9
  exec 9>&-
  td=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)
  # The body is ALREADY at $out.b in the gitignored scratch dir — no copy needed,
  # and a copy would be `cp f f`.
  python3 - "$LEDGER" "$out.h" "$out.b" "$SEQ" "$host" "$path" "$role" "$tag" \
            "$code" "$exitc" "$tq" "$ts" "$td" <<'PY'
import json, sys, os, hashlib
(L, hp, bp, seq, host, path, role, tag, code, exitc, tq, ts, td) = sys.argv[1:14]
KEEP = ('content-type','content-length','content-encoding','server','vary',
        'cache-control','date','etag','last-modified')
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
       "server": hdrs.get('server','(none)'),
       "headers": hdrs, "t_queued": tq, "t_sent": ts, "t_done": td}
open(L, "a").write(json.dumps(row) + "\n")
print(f"seq={seq} GET {host}{path} -> {code} ctype={hdrs.get('content-type','-')} "
      f"bytes={n} sha256={d[:16]}")
PY
  log "seq=$SEQ GET https://$host$path status=$code exit=$exitc bytes=$(stat -c%s "$out.b" 2>/dev/null || echo 0) tag=$tag role=[$role]"
}

sweep() {
  local h
  for h in $HOSTS; do
    local s; s=$(echo "$h" | tr . -)
    # ---- controls first, on THIS host, before any document (2) --------------
    req "$h" "$K_ABSENT" \
      "CONTROL-1 certainly-absent dotted key: 404 recorded on .com/.trials (area E seq 1,77; 0 B, text/vnd.a). Proves a 404 on this namespace is a genuine absence, not a catch-all, so the liveness reading below is not a fallback artefact" \
      "c1-$s-absent" || return 0
    req "$h" "$K_LIVE" \
      "CONTROL-2 known-live dotted key: 200 281 B sha256 7f0a5bb4… recorded (area E seq 2,78). Proves this route family is live on this host and the 200 below is a document, not a shell" \
      "c2-$s-live" || return 0
    # ---- the two documents (2) ---------------------------------------------
    req "$h" "$D_FAMILY" \
      "DOCUMENT-1 the 16-family map. Carries the INSTINCT row verbatim — the only patient-document source of SKU strings by family. Recorded 200/3470 B/sha ae70bde0… on .com and -trials (area E seq 40,116)" \
      "d1-$s-family-map" || return 0
    req "$h" "$D_REPORT" \
      "DOCUMENT-2 reportFileNamingSupportedPumpModels dict. The other patient-document source of SKU strings; recorded 200/10937 B/sha 2f918b71… on .com and -trials (area E seq 29,105), and the later 236-entry reading is committed at findings-log/2026-11-03-report-list-drift/list-verbatim-2026-11-03.txt:110-139" \
      "d2-$s-report-gen" || return 0
  done
}

case "${1:-all}" in
  all)   sweep ;;
  *) echo "usage: probe.sh [all]" >&2; exit 64 ;;
esac
echo "LEDGER_ROWS=$(ledger_len) CAP=$CAP"
