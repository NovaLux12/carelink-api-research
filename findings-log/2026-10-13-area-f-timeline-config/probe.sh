#!/usr/bin/env bash
# Area F probe — the timeline config key set, the two timeline-host keys, and the
# two dedicated-route config escapes off EU.
# Claim issue #55. CAP 26. GET only. curl --compressed on every request.
# Sleep 2.5 s INSIDE the per-host flock (shared machine, 4 concurrent workers).
#
# ORDER PER HOST — controls first, before any candidate, so the oracle verdict is
# not contaminated by the data it judges (AGENTS.md section 8, docs/09 section 3):
#   (1) 001-control-live    /patient/configuration/system/logbook.supported.entry.types
#       POSITIVE control. A per-key route inside the same namespace that is
#       recorded 200 on all three patient deployments (area E seq 2/78, pinned in
#       05-public-config.check.sh). It proves the /patient/configuration/ tree is
#       SERVING on this host, without which a 404 on any sibling is uninterpretable
#       (the whole tree could be absent on that deployment).
#   (2) 002-control-absent  /patient/configuration/version
#       NEGATIVE control, plausible-shaped: a real-looking flat config name.
#       Recorded 404 on .eu by no committed ledger -- see FINDINGS.md section 2,
#       where the claim's "recorded 404 on EU" premise is corrected. This pass
#       establishes it per host rather than inheriting it from another pass's prose.
#   (3) 003-control-root    /patient/configuration/
#       The namespace ROOT. Establishes whether the root itself serves a collection
#       on this host, which is what makes a child-404 interpretable.
#   (4) 004-bulk-public     /patient/v2/configuration/public
#       THE BULK DOCUMENT. Deliverable 1: one GET per host yields the full key set
#       of personal.patient.timeline.config, and settles deliverable 2 (whether a
#       second top-level key personal.patient.timeline.host exists) with zero
#       further requests. NOTE: the claim and the pool brief both name this
#       document "/patient/configuration/"; that path is the PER-KEY namespace,
#       not the bulk document. The repository is right: 05-public-config.check.sh
#       fetches /patient/v2/configuration/public, and CONFIG-NAMESPACE-DEEP.md
#       states the per-key form is a projection OF that document.
#   (5) 005-pkey-timeline-config  /patient/configuration/system/personal.patient.timeline.config
#   (6) 006-pkey-timeline-host    /patient/configuration/system/personal.patient.timeline.host
#       Deliverable 2's second side, and the source of the parsed value that
#       cell-digests.tsv hashes against the bulk subtree (deliverable 4).
#   (7) 007/008/009-dedicated     the two dedicated routes + messages/{lang}
#       Deliverable 3. Sent on .com and -trials ONLY: all three are already
#       recorded 200 on .eu (CONFIG-NAMESPACE-DEEP.md lines 86, 87, 90), and
#       re-probing them there would spend cap on a re-derivation of a cited fact.
#
# PER HOST: .eu 6 (.com 9, -trials 9) = 24 of a 26 cap.
#
# Response BODIES are transient (mktemp dir, never committed): only size,
# content-type, sha256 and the kernel body mtime enter results.jsonl. Headers are
# committed per request under headers/. analyse.py consumes the bodies while they
# are in hand and writes the committed digests, then TMPD is removed.
# This script is the record of what was sent.
#
# NOTE on paths: the lock dir and tmp parent are parameterised (same resolution
# area W/D/E's probe.sh uses) because a committed absolute path fails the gate's
# machine-path rule. The request sequence — URLs, order, sleeps, curl flags — is
# untouched.
set -uo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
_gitdir="$(git -C "$DIR" rev-parse --git-common-dir 2>/dev/null)"
if [ -n "$_gitdir" ]; then
  POOL_LOCK_DIR="${POOL_LOCK_DIR:-$(dirname "$_gitdir")/.loop}"
else
  POOL_LOCK_DIR="${POOL_LOCK_DIR:-$DIR/../../../.loop}"
fi
OUT="$DIR"
TMPD=$(mktemp -d)
CAP=26
UA="carelink-bridge-research/1.0"

mkdir -p "$OUT/headers"
SEQ=0
: > "$OUT/results.jsonl"
: > "$OUT/run.log"
date -u +%FT%T.%3NZ > "$OUT/run.log"

req() { # req <host> <tag> <url>
  local host="$1" tag="$2" url="$3"
  if [ "$SEQ" -ge "$CAP" ]; then
    echo "REFUSED $host $tag $url — cap $CAP reached; NOT SENT" | tee -a "$OUT/run.log"
    return 0
  fi
  local lock="$POOL_LOCK_DIR/host-$host.lock"
  touch "$lock"
  SEQ=$((SEQ + 1))
  local d="$TMPD/$SEQ"
  mkdir -p "$d"
  local t_queued
  t_queued=$(date -u +%FT%T.%3NZ)
  flock "$lock" bash -c \
    'sleep 2.5; date -u +%FT%T.%3NZ > "$1/ts"; curl -s --compressed --max-time 30 -A "'"$UA"'" -D "$1/h" -o "$1/b" -w "%{http_code}" "$2" > "$1/code"; date -u +%FT%T.%3NZ > "$1/te"' \
    _ "$d" "$url"
  local t_sent t_done code size ctype sha mt_ms
  t_sent=$(cat "$d/ts"); t_done=$(cat "$d/te"); code=$(cat "$d/code")
  size=$(stat -c%s "$d/b")
  mt_ms=$(date -u -d "$(stat -c%y "$d/b")" +%s%3N 2>/dev/null || echo 0)
  ctype=$(grep -i '^content-type:' "$d/h" | tr -d '\r' | sed 's/^[Cc]ontent-[Tt]ype: *//' | head -n1)
  sha=$(sha256sum "$d/b" | cut -d' ' -f1)
  # discriminating headers, recorded verbatim
  local xamzn xcache acao
  xamzn=$(grep -i '^x-amzn-errortype:' "$d/h" | tr -d '\r' | sed 's/^[Xx]-[Aa]mzn-[Ee]rrortype: *//' | head -n1)
  xcache=$(grep -i '^x-cache:' "$d/h" | tr -d '\r' | sed 's/^[Xx]-[Cc]ache: *//' | head -n1)
  acao=$(grep -i '^access-control-allow-origin:' "$d/h" | tr -d '\r' | sed 's/^[Aa]ccess-[Cc]ontrol-[Aa]llow-[Oo]rigin: *//' | head -n1)
  cp "$d/h" "$OUT/headers/$host--$tag.h"
  printf '{"seq":%d,"host":"%s","tag":"%s","method":"GET","url":"%s","code":%s,"bytes":%d,"content_type":"%s","x_amzn_errortype":"%s","x_cache":"%s","acao":"%s","sha256":"%s","body_mtime_ms":%s,"t_queued":"%s","t_sent":"%s","t_done":"%s"}\n' \
    "$SEQ" "$host" "$tag" "$url" "$code" "$size" "$ctype" "$xamzn" "$xcache" "$acao" "$sha" "$mt_ms" "$t_queued" "$t_sent" "$t_done" \
    >> "$OUT/results.jsonl"
  printf '%d %s %s %s GET %s %s %s %s %s %s %s %s\n' \
    "$SEQ" "$host" "$tag" "$code" "$ctype" "$mt_ms" "$t_queued" "$t_sent" "$t_done" \
    >> "$OUT/run.log"
  echo "seq=$SEQ host=$host tag=$tag code=$code bytes=$size ctype=$ctype"
}

sweep_host() { # sweep_host <host> <with_dedicated: yes|no>
  local HOST="$1" DED="$2"
  local BASE="https://$HOST"
  # (1)(2)(3) controls FIRST, before any candidate
  req "$HOST" "001-control-live"        "$BASE/patient/configuration/system/logbook.supported.entry.types"
  req "$HOST" "002-control-absent"      "$BASE/patient/configuration/version"
  req "$HOST" "003-control-root"        "$BASE/patient/configuration/"
  # (4) the bulk document
  req "$HOST" "004-bulk-public"         "$BASE/patient/v2/configuration/public"
  cp "$TMPD/$SEQ/b" "$TMPD/bulk-$HOST.json"
  echo "BULK_SEQ[$HOST]=$SEQ"
  # (5)(6) the two timeline keys, per-key projection form
  req "$HOST" "005-pkey-timeline-config" "$BASE/patient/configuration/system/personal.patient.timeline.config"
  cp "$TMPD/$SEQ/b" "$TMPD/pkey-cfg-$HOST.json"
  req "$HOST" "006-pkey-timeline-host"   "$BASE/patient/configuration/system/personal.patient.timeline.host"
  cp "$TMPD/$SEQ/b" "$TMPD/pkey-host-$HOST.json"
  # (7) the dedicated-route escapes, off EU only
  if [ "$DED" = "yes" ]; then
    req "$HOST" "007-dedicated-defaultCountry" "$BASE/patient/configuration/defaultCountry"
    req "$HOST" "008-dedicated-recaptcha-key"    "$BASE/patient/configuration/recaptcha/key"
    req "$HOST" "009-dedicated-messages-en"      "$BASE/patient/configuration/messages/en"
  fi
  echo "swept $HOST: $SEQ requests so far"
}

sweep_host carelink.minimed.eu          no
sweep_host carelink.minimed.com        yes
sweep_host carelink-trials.minimed.com yes

echo "--- requests sent: $SEQ of a $CAP cap ---"

# Derivation runs WHILE THE BODIES ARE IN HAND — cell-digests.tsv is only
# writable during the sweep, which is the entire point of area E's verifier
# round-2 addendum.
python3 "$DIR/analyse.py" "$TMPD" "$OUT"

rm -rf "$TMPD"
echo "done: $SEQ requests. bodies removed (transient, not committed)"
wc -l "$OUT/results.jsonl" "$OUT/run.log"