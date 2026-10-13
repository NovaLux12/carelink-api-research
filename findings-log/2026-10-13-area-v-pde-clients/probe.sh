#!/bin/bash
# Area V probe — "does any vendor client follow the published baseUrlPde?"
# Claim issue #42. Cap 24, GET only, curl --compressed, 2.5 s sleep INSIDE the
# per-host flock, t_sent emitted inside the lock immediately before curl execs.
#
# Order per host: (1) certainly-absent control, (2) entry document control,
# (3) only then the assets named by the entry document just captured — the
# asset paths are DERIVED from today's index, never from a note or a filename
# in this repo, because a bundle bump changes the hash in the name.
#
# Two controls with two different jobs, because the two host families differ:
#   carelinkhp.* / carelink-support.* return HTTP 200 + text/html + 5518 B for
#     EVERY unknown path (SPA fallback) -> status is useless, the fallback page
#     IS the index, so root and absent are expected to be byte-identical.
#   carelink.minimed.{eu,com} return a clean Apache 404 (196 B, iso-8859-1) for
#     an unknown path -> status IS an oracle here, and a 200 + application/
#     javascript is the only way an asset counts as real.
#
# Bodies (multi-MB main bundles) are written to $TMPBODIES and never committed;
# digests, sizes and the offline grep output are committed.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
# Derived, never hardcoded: probe.sh sits at <main>/.loop/worktrees/<w>/findings-log/<dir>/,
# so five levels up is the main clone, where the per-host locks live (pool brief).
MAIN="$(cd "$HERE/../../../../.." && pwd)"
LOGDIR=$HERE
OUT=$LOGDIR/headers
DELAY=${DELAY:-2.5}
TMPBODIES=${TMPBODIES:-$(mktemp -d)}
mkdir -p "$OUT" "$TMPBODIES"
chmod +x "$HERE/send.sh" 2>/dev/null || true
RUNLOG=$LOGDIR/run.log
JSONL=$LOGDIR/results.jsonl
: > "$RUNLOG"; : > "$JSONL"
echo "run start: $(date -u +%FT%T.%3NZ) tmpbodies=$TMPBODIES delay=${DELAY}" | tee -a "$RUNLOG"
SEQ=0

req() { # req <host> <path> <role> <tag>
  local host="$1" path="$2" role="$3" tag="$4"
  SEQ=$((SEQ+1)); local seq=$SEQ
  local lock="$MAIN/.loop/host-$host.lock"
  [ -e "$lock" ] || : > "$lock"
  local url="https://$host$path"
  local t_queued; t_queued=$(date -u +%FT%T.%3NZ)
  local out; out=$(flock "$lock" "$HERE/send.sh" "$DELAY" "$OUT/$tag.h" "$TMPBODIES/$tag.b" "$url" 2>&1)
  local t_done; t_done=$(date -u +%FT%T.%3NZ)
  # TS_SENT is emitted inside the lock, immediately before curl execs.
  local t_sent; t_sent=$(printf '%s\n' "$out" | sed -n 's/^TS_SENT //p' | head -1)
  local code; code=$(printf '%s\n' "$out" | sed -n 's/^HTTP_STATUS //p' | head -1)
  local curl_exit; curl_exit=$(printf '%s\n' "$out" | sed -n 's/^CURL_EXIT //p' | head -1)
  [ -n "$t_sent" ] || t_sent="(unrecorded)"
  [ -n "$code" ] || code="000"
  [ -n "$curl_exit" ] || curl_exit="-1"
  local ct="(none)"
  if [ -f "$OUT/$tag.h" ]; then
    ct=$(grep -i '^content-type:' "$OUT/$tag.h" | tail -1 | tr -d '\r' | sed 's/^[^:]*: *//')
  fi
  [ -n "$ct" ] || ct="(none)"
  local bytes=0 sha="(none)" mtime=""
  if [ -f "$TMPBODIES/$tag.b" ]; then
    bytes=$(stat -c%s "$TMPBODIES/$tag.b")
    sha=$(sha256sum "$TMPBODIES/$tag.b" | cut -d' ' -f1)
    mtime=$(stat -c%Y "$TMPBODIES/$tag.b")
  fi
  local ctype_full="(none)"
  if [ -f "$OUT/$tag.h" ]; then
    ctype_full=$(tr '\r' ' ' < "$OUT/$tag.h" | tr '\n' '|' | sed 's/|$//')
  fi
  local host_seq; host_seq=$(grep -c "\"host\": \"$host\"" "$JSONL" 2>/dev/null || true)
  host_seq=$((host_seq+1))
  # Row written through the environment, never through heredoc interpolation:
  # raw header bytes contain quotes, and area G's pass had to re-encode its
  # whole ledger because they leaked into the JSON.
  V_SEQ="$seq" V_HOSTSEQ="$host_seq" V_HOST="$host" V_TAG="$tag" V_PATH="$path" \
  V_ROLE="$role" V_URL="$url" V_CODE="$code" V_EXIT="$curl_exit" V_CT="$ct" \
  V_CFULL="$ctype_full" V_BYTES="$bytes" V_SHA="$sha" V_MTIME="$mtime" \
  V_DELAY="$DELAY" V_TQ="$t_queued" V_TS="$t_sent" V_TD="$t_done" \
  python3 -c '
import json, os, sys
e = os.environ
row = {
  "seq": int(e["V_SEQ"]), "host_seq": int(e["V_HOSTSEQ"]),
  "host": e["V_HOST"], "host_tag": e["V_TAG"],
  "method": "GET", "path": e["V_PATH"], "role": e["V_ROLE"], "url": e["V_URL"],
  "http_status": e["V_CODE"], "curl_exit": int(e["V_EXIT"]),
  "content_type": e["V_CT"], "ctype_full": e["V_CFULL"],
  "body_bytes": int(e["V_BYTES"]), "body_sha256": e["V_SHA"],
  "body_mtime_epoch": e["V_MTIME"], "delay_declared_s": e["V_DELAY"],
  "t_queued": e["V_TQ"], "t_sent": e["V_TS"], "t_done": e["V_TD"],
}
open(sys.argv[1], "a").write(json.dumps(row) + "\n")
' "$JSONL"
  printf '%s seq=%s host=%s tag=%s code=%s ctype=%s bytes=%s sha=%s\n' \
    "$t_sent" "$seq" "$host" "$tag" "$code" "$ct" "$bytes" "$sha" >> "$RUNLOG"
  echo "seq=$seq host=$host path=$path code=$code ctype=$ct bytes=$bytes sha=$sha" >&2
}

# Name the asset out of an entry document already captured to disk. Zero requests.
asset_from_index() { # asset_from_index <tag> <regex-ish basename prefix>
  local tag="$1" want="$2"
  [ -f "$TMPBODIES/$tag.b" ] || return 1
  grep -o "$want\.[0-9a-f]\{16\}\.js" "$TMPBODIES/$tag.b" | head -1
}

echo "== host 1: patient EU ==" >&2
req carelink.minimed.eu "/main.deadbeefdeadbeef.js" "CONTROL-certainly-absent-proves-status-is-an-oracle-here" "eu-absent"
req carelink.minimed.eu "/" "CONTROL-entry-anchors-build-identity-and-names-assets" "eu-root"
EU_MAIN=$(asset_from_index eu-root 'main'); EU_RUNTIME=$(asset_from_index eu-root 'runtime')
echo "eu index names: main=${EU_MAIN:-none} runtime=${EU_RUNTIME:-none}" >&2
[ -n "$EU_MAIN" ] && req carelink.minimed.eu "/$EU_MAIN" "CANDIDATE-patient-eu-main-bundle" "eu-main"
[ -n "$EU_RUNTIME" ] && req carelink.minimed.eu "/$EU_RUNTIME" "CANDIDATE-patient-eu-runtime-chunkmap" "eu-runtime"

echo "== host 2: patient US (.com) ==" >&2
req carelink.minimed.com "/main.deadbeefdeadbeef.js" "CONTROL-certainly-absent-proves-status-is-an-oracle-here" "us-absent"
req carelink.minimed.com "/" "CONTROL-entry-anchors-build-identity-and-names-assets" "us-root"
US_MAIN=$(asset_from_index us-root 'main')
echo "us index names: main=${US_MAIN:-none}" >&2
[ -n "$US_MAIN" ] && req carelink.minimed.com "/$US_MAIN" "CANDIDATE-patient-us-main-bundle" "us-main"

echo "== host 3: clinician portal, clinic build ==" >&2
req carelinkhp.minimed.eu "/main.deadbeefdeadbeef.js" "CONTROL-certainly-absent-proves-spa-fallback-live" "hp-absent"
req carelinkhp.minimed.eu "/" "CONTROL-entry-anchors-build-identity-and-names-assets" "hp-root"
HP_MAIN=$(asset_from_index hp-root 'main')
echo "hp index names: main=${HP_MAIN:-none}" >&2
[ -n "$HP_MAIN" ] && req carelinkhp.minimed.eu "/$HP_MAIN" "CANDIDATE-clinic-portal-main-bundle" "hp-main"

echo "== host 4: support portal build ==" >&2
req carelink-support.medtronic.eu "/main.deadbeefdeadbeef.js" "CONTROL-certainly-absent-proves-spa-fallback-live" "sup-absent"
req carelink-support.medtronic.eu "/" "CONTROL-entry-anchors-build-identity-and-names-assets" "sup-root"
SUP_MAIN=$(asset_from_index sup-root 'main')
echo "sup index names: main=${SUP_MAIN:-none}" >&2
[ -n "$SUP_MAIN" ] && req carelink-support.medtronic.eu "/$SUP_MAIN" "CANDIDATE-support-portal-main-bundle" "sup-main"

echo "run end: $(date -u +%FT%T.%3NZ)" | tee -a "$RUNLOG"
echo "TMPBODIES=$TMPBODIES"