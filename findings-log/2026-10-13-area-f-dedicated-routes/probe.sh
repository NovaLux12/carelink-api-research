#!/usr/bin/env bash
# Area F (successor) probe — dedicated config-escape routes on .com and -trials.
# Issue #77. CAP 14. GET only. curl --compressed on every request.
# Sleep 2.5 s INSIDE the per-host flock. Per-host lock files are NOT removed.
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
CAP=14
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
  local xamzn xcache acao xpow
  xamzn=$(grep -i '^x-amzn-errortype:' "$d/h" | tr -d '\r' | sed 's/^[Xx]-[Aa]mzn-[Ee]rrortype: *//' | head -n1)
  xcache=$(grep -i '^x-cache:' "$d/h" | tr -d '\r' | sed 's/^[Xx]-[Cc]ache: *//' | head -n1)
  acao=$(grep -i '^access-control-allow-origin:' "$d/h" | tr -d '\r' | sed 's/^[Aa]ccess-[Cc]ontrol-[Aa]llow-[Oo]rigin: *//' | head -n1)
  xpow=$(grep -i '^x-powered-by:' "$d/h" | tr -d '\r' | sed 's/^[Xx]-[Pp]owered-[Bb]y: *//' | head -n1)
  cp "$d/h" "$OUT/headers/$host--$tag.h"
  printf '{"seq":%d,"host":"%s","tag":"%s","method":"GET","url":"%s","code":%s,"bytes":%d,"content_type":"%s","content_length_header":"%s","x_amzn_errortype":"%s","x_cache":"%s","acao":"%s","x_powered_by":"%s","sha256":"%s","body_mtime_ms":%s,"t_queued":"%s","t_sent":"%s","t_done":"%s"}\n' \
    "$SEQ" "$host" "$tag" "$url" "$code" "$size" "$ctype" "$(grep -i '^content-length:' "$d/h" | tr -d '\r' | sed 's/^[Cc]ontent-[Ll]ength: *//' | head -n1)" "$xamzn" "$xcache" "$acao" "$xpow" "$sha" "$mt_ms" "$t_queued" "$t_sent" "$t_done" \
    >> "$OUT/results.jsonl"
  printf 'seq=%d host=%s tag=%s code=%s bytes=%d ctype=%s sha=%s t_queued=%s t_sent=%s t_done=%s\n' \
    "$SEQ" "$host" "$tag" "$code" "$size" "$ctype" "$sha" "$t_queued" "$t_sent" "$t_done" \
    >> "$OUT/run.log"
  echo "seq=$SEQ host=$host tag=$tag code=$code bytes=$size ctype=$ctype"
}

sweep_host() {
  local HOST="$1"
  local BASE="https://$HOST"
  # controls first
  req "$HOST" "001-control-version"     "$BASE/patient/configuration/version"
  req "$HOST" "002-control-root"        "$BASE/patient/configuration/"
  # dedicated routes
  req "$HOST" "003-dedicated-defaultCountry" "$BASE/patient/configuration/defaultCountry"
  req "$HOST" "004-dedicated-recaptcha-key"    "$BASE/patient/configuration/recaptcha/key"
  req "$HOST" "005-dedicated-messages-en"      "$BASE/patient/configuration/messages/en"
  echo "swept $HOST"
}

sweep_host carelink.minimed.com
sweep_host carelink-trials.minimed.com

echo "--- requests sent: $SEQ of a $CAP cap ---"
rm -rf "$TMPD"
echo "done: $SEQ requests. bodies removed (transient, not committed)"
wc -l "$OUT/results.jsonl" "$OUT/run.log"
