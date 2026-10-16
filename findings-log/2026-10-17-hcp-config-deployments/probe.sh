#!/usr/bin/env bash
# Lane l2 — `hcp/configuration/public/*` existence verdicts across portal deployments.
# Claim: NovaLux12/carelink-api-research#144. Cap 85 HTTP requests, >=2.5 s per host.
#
# GET only. No POST, no -X, no -d, no token, no auth, no cookie, no port scan,
# no DNS brute force, no wordlist. Every request is one of three kinds, and the
# kind is written into the ledger's `role` field on every row:
#   CORPUS-CONTROL — a content-hashed asset name this repo already records at a
#                    named file:line, fetched so its recorded digest can be asserted
#                    BEFORE any key list taken from that build is used.
#   KEY            — a literal extracted offline from THAT host's own bundle route
#                    table. Never typed from memory, never inherited from another
#                    host, never from docs/07.
#   CONTROL        — one of the four standing controls named in the claim.
#
# The sleep goes INSIDE the per-host flock: four pool workers share one .loop, and
# four workers queueing on a lock and then firing together is worse than no
# serialisation at all.
#
# Usage:  probe.sh bundles      # batch 1 — the 4 corpus controls
#         plan.py               # 0 requests — digest assertions + route tables -> plan.json
#         probe.sh keys         # batch 2 — controls first per host, then that host's own keys
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
# Derived, never hardcoded: HERE is <main-clone>/.loop/worktrees/<w>/findings-log/<dir>,
# so five levels up is the main clone, where the shared per-host locks live.
REPO="$(cd "$HERE/../../../../.." && pwd)"
HDR="$HERE/headers"
RUNLOG="$HERE/run.log"
LEDGER="$HERE/results.jsonl"
# The 3.4 MB bundle assets must NOT be committed (research-checks.py fails any file
# > 1 MiB anywhere under findings-log/), so they are held outside it, in .loop/,
# which is gitignored. They are reproducible only by re-fetching, which is the point.
ASSETS="$REPO/.loop/l2-assets"
SCRATCH="$REPO/.loop/l2-scratch"
mkdir -p "$HDR" "$ASSETS" "$SCRATCH"
export L2_ASSETS="$ASSETS"

UA="carelink-bridge-research/1.0"
CAP=85
DELAY=2.5
PROWEB="X-System-ID: ProWeb"
PFX="/hcp/configuration/public"

: > "$RUNLOG"

log() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)" "$*" >> "$RUNLOG"; }
ledger_len() { [ -f "$LEDGER" ] && wc -l < "$LEDGER" | tr -d ' ' || echo 0; }

SEQ=0
[ -f "$LEDGER" ] && SEQ=$(ledger_len)

emit() { # emit seq hseq host tag path role senthdr code exit sz digest tq ts td ctype clen cenc vary xpid server hdrs
  python3 - "$LEDGER" "$@" <<'PY'
import json, sys
(L, seq, hseq, host, tag, path, role, sent, code, exit_, sz, digest,
 tq, ts, td, ctype, clen, cenc, vary, xpid, server, hdrs) = sys.argv[1:23]
row = {
    "seq": int(seq), "host_seq": int(hseq), "host": host, "tag": tag,
    "method": "GET", "path": path, "role": role, "sent_headers": sent,
    "http_status": code, "curl_exit": int(exit_),
    "content_type": ctype, "content_length_hdr": clen, "content_encoding": cenc,
    "vary": vary, "x_amz_cf_pop": xpid, "server": server,
    "body_bytes": int(sz), "body_sha256": digest, "headers": hdrs,
    "t_queued": tq, "t_sent": ts, "t_done": td,
}
open(L, "a").write(json.dumps(row) + "\n")
PY
}

hdrval() { [ -f "$1" ] || { echo "(none)"; return; }
  local v; v=$(grep -i "^$2:" "$1" | tail -1 | sed "s/^[^:]*:[[:space:]]*//" | tr -d '\r')
  [ -n "$v" ] && printf '%s' "$v" || echo "(none)"; }

# req <host> <path> <role> <tag> [header] [keep-asset]
req() {
  local host="$1" path="$2" role="$3" tag="$4" hdr="${5:-}" keep="${6:-}"
  SEQ=$((SEQ+1))
  local hseq out tq ts td code exit sz digest=""
  out="$SCRATCH/$tag"
  hseq=$(grep -c "\"host\": \"$host\"" "$LEDGER" 2>/dev/null | head -1)
  case "$hseq" in ''|*[!0-9]*) hseq=0 ;; esac
  hseq=$((hseq+1))
  tq=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)
  touch "$REPO/.loop/host-$host.lock" 2>/dev/null || true
  if [ -n "$hdr" ]; then
    code=$(flock "$REPO/.loop/host-$host.lock" -c "
      sleep $DELAY
      date -u +%Y-%m-%dT%H:%M:%S.%3NZ > '$out.ts'
      curl -s --compressed --max-time 120 -A '$UA' -H '$hdr' -D '$out.h' -o '$out.b' -w '%{http_code}' 'https://$host$path'" 2>>"$RUNLOG")
  else
    code=$(flock "$REPO/.loop/host-$host.lock" -c "
      sleep $DELAY
      date -u +%Y-%m-%dT%H:%M:%S.%3NZ > '$out.ts'
      curl -s --compressed --max-time 120 -A '$UA' -D '$out.h' -o '$out.b' -w '%{http_code}' 'https://$host$path'" 2>>"$RUNLOG")
  fi
  exit=$?
  td=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)
  ts=$(cat "$out.ts" 2>/dev/null || echo "$tq")
  cp "$out.h" "$HDR/$tag.h" 2>/dev/null || true
  sz=0
  if [ -f "$out.b" ]; then
    sz=$(stat -c%s "$out.b")
    digest=$(sha256sum "$out.b" | cut -d' ' -f1)
    # Bodies <= 100 kB are committed as evidence; the bundle assets are held
    # outside findings-log/ so the 1 MiB hygiene rule is not violated.
    if [ "$sz" -le 100000 ]; then cp "$out.b" "$HDR/$tag.b"
    elif [ "$keep" = "asset" ]; then cp "$out.b" "$ASSETS/$tag.b.assets"; fi
  fi
  local hdrs=""
  [ -f "$out.h" ] && hdrs=$(grep -v '^$' "$out.h" | tr -d '\r' | paste -sd'|' -)
  emit "$SEQ" "$hseq" "$host" "$tag" "$path" "$role" "${hdr:-(none)}" "$code" "$exit" "$sz" "$digest" \
       "$tq" "$ts" "$td" "$(hdrval "$out.h" content-type)" "$(hdrval "$out.h" content-length)" \
       "$(hdrval "$out.h" content-encoding)" "$(hdrval "$out.h" vary)" \
       "$(hdrval "$out.h" x-amz-cf-pop)" "$(hdrval "$out.h" server)" "$hdrs"
  log "seq=$SEQ host_seq=$hseq host=$host tag=$tag role=[$role] status=$code ctype=$(hdrval "$out.h" content-type) bytes=$sz sha256=${digest:0:16} path=$path"
}

cap_guard() {
  local n; n=$(ledger_len)
  if [ "$n" -ge "$CAP" ]; then
    log "CAP STOP at $n of $CAP — no further request issued"
    echo "CAP STOP: $n of $CAP" >&2; return 1
  fi
  return 0
}

case "${1:-}" in
bundles)
  # -------- corpus control ----------------------------------------------------
  # On this host family the catch-all IS the entry document (area A, "The
  # discriminator that does work is an asset path"), so only a content-hashed
  # chunk tells a deployment from a fallback. Each host is asked for the asset
  # name this repo already records for it; plan.py asserts the recorded digest
  # before batch 2 issues its first request.
  cap_guard || exit 0
  req carelinkhp.minimed.eu "/main.fb5f8cb7eb60c4d5.js" \
    "CORPUS-CONTROL clinic pow build asset; asset name recorded at AUTH-TENANT-FINDINGS.md:248-249, digest at 2026-10-14-area-k-clinic-controlflow/differential.py:142; expect sha256 2a7fa8e7af519c2b..." \
    b01-carelinkhp-minimed-eu-clinic-asset "" asset
  cap_guard || exit 0
  req carelink.medtronic.com "/main.fb5f8cb7eb60c4d5.js" \
    "CORPUS-CONTROL same clinic build asset on the .com clinic host; area A results.jsonl seq 8 recorded this host serving build A. Proves the catch-all is not answering and that this host serves the same build as carelinkhp" \
    b02-carelink-medtronic-com-clinic-asset "" asset
  cap_guard || exit 0
  req carelink.medtronic.eu "/main.fb5f8cb7eb60c4d5.js" \
    "CORPUS-CONTROL same clinic build asset on the shadow-portal .eu host; area A results.jsonl seq 19 refuted docs/01:69's 'does not serve that bundle'" \
    b03-carelink-medtronic-eu-clinic-asset "" asset
  cap_guard || exit 0
  req carelink-support.medtronic.com "/main.759cddab23085086.js" \
    "CORPUS-CONTROL support cua build asset; asset name and digest recorded at 2026-10-13-area-p-static-schema-recovery/FINDINGS.md:23; area A results.jsonl seq 20 recorded this host serving build B. The corpus control for the support key list" \
    b04-carelink-support-medtronic-com-support-asset "" asset
  ;;

keys)
  # -------- batch 2: read plan.json, then issue it in plan order -------------
  # plan.py has already asserted all four digests and refused to write plan.json
  # if any of them failed to reproduce, so reaching this point means the corpus
  # control passed. Controls come first per host inside the plan.
  python3 "$HERE/plan.py" --issue "$LEDGER" "$RUNLOG" "$HDR" "$SCRATCH" "$ASSETS" \
    "$REPO/.loop" "$DELAY" "$CAP" "$UA"
  ;;

gap)
  # -------- batch 3: the one cell batch 2 spent a slot on instead of measuring -
  # `logbook.supported.entry.types` is one of the build's 15 route literals, and
  # batch 2 used it as CONTROL-4 (header-ABSENT) on all three hosts. That is the
  # right control — docs/07:154-161 lists it among the nine siblings that return
  # 412 with no header — but it means its HEADERED verdict is unmeasured on
  # these three hosts, and a portability claim needs all 15 verdicts. Measured
  # here rather than written up as a gap, because 3 requests buy the cell and
  # the alternative is a 14-of-15 claim (AGENTS.md §6.1).
  #
  # A first attempt at this batch issued all three with a DOUBLED SLASH
  # (`…/public//logbook…`, ledger seq 56-58) because $PFX carried a trailing
  # slash. The vendor answered 200/226 B on all three, so the cell was in fact
  # measured — but the URL recorded in the ledger is not the URL this comment
  # claims was tested, and AGENTS.md §6.2 is exactly that mistake. The three
  # rows are left on the ledger and counted; the canonical cells are issued
  # here. The double-slash behaviour is recorded separately in FINDINGS §6.5.
  cap_guard || exit 0
  req carelink.medtronic.com "$PFX/logbook.supported.entry.types" \
    "KEY (gap cell) \`logbook.supported.entry.types\` WITH X-System-ID: ProWeb. One of the build's 15 route literals; batch 2 spent this URL as the header-ABSENT control (412), so the headered verdict is what is missing. Recorded for carelinkhp as 200/226 B (HCP-CONFIG-SCHEMA.md:159) — this cell is the portability comparison against that record." \
    g1-carelink-medtronic-com-logbook-supported-entry-types "$PROWEB"
  cap_guard || exit 0
  req carelink.medtronic.eu "$PFX/logbook.supported.entry.types" \
    "KEY (gap cell) \`logbook.supported.entry.types\` WITH X-System-ID: ProWeb. Same cell on the shadow-portal .eu host; batch 2 measured it header-absent at 412 (seq 14)." \
    g2-carelink-medtronic-eu-logbook-supported-entry-types "$PROWEB"
  cap_guard || exit 0
  req carelink-support.medtronic.com "$PFX/logbook.supported.entry.types" \
    "KEY (gap cell) \`logbook.supported.entry.types\` WITH X-System-ID: ProWeb. Same cell on the support deployment; batch 2 measured it header-absent at 412 (seq 19)." \
    g3-carelink-support-medtronic-com-logbook-supported-entry-types "$PROWEB"
  ;;

*)
  echo "usage: probe.sh bundles|keys|gap" >&2; exit 64;;
esac

echo "LEDGER_ROWS=$(ledger_len) CAP=$CAP"