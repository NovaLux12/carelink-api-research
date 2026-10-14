#!/usr/bin/env bash
# Area S2 (headliner) probe — messages/en shape and byte size, 3 deployments.
# Issue #91. CAP 6. GET only. curl --compressed on every request.
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
CAP=6
UA="carelink-bridge-research/1.0"

mkdir -p "$OUT/headers"
SEQ=0
: > "$OUT/results.jsonl"
: > "$OUT/run.log"
: > "$OUT/derived-parts.jsonl"
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
  local t_sent t_done code size ctype sha
  t_sent=$(cat "$d/ts"); t_done=$(cat "$d/te"); code=$(cat "$d/code")
  size=$(stat -c%s "$d/b")
  ctype=$(grep -i '^content-type:' "$d/h" | tr -d '\r' | sed 's/^[Cc]ontent-[Tt]ype: *//' | head -n1)
  sha=$(sha256sum "$d/b" | cut -d' ' -f1)
  cp "$d/h" "$OUT/headers/$host--$tag.h"
  if [[ "$tag" == *messages* ]]; then
    members=$(jq -c 'keys' "$d/b" 2>/dev/null)
    arrlen=$(jq -r 'if (.messages|type)=="array" then (.messages|length) else "NA" end' "$d/b" 2>/dev/null)
    firstkeys=$(jq -c 'if (.messages|type)=="array" and (.messages|length>0) then (.messages[0]|keys) else [] end' "$d/b" 2>/dev/null)
    printf '{"seq":%d,"host":"%s","tag":"%s","role":"CANDIDATE-messages-en-shape","path":"/patient/configuration/messages/en","messages_envelope_member_set":%s,"messages_array_length":%s,"first_entry_member_set":%s,"body_bytes":%d,"body_sha256":"%s"}\n' \
      "$SEQ" "$host" "$tag" "$members" "$arrlen" "$firstkeys" "$size" "$sha" >> "$OUT/derived-parts.jsonl"
  else
    topkeys=$(jq 'keys|length' "$d/b" 2>/dev/null)
    printf '{"seq":%d,"host":"%s","tag":"%s","role":"CONTROL-public-envelope","path":"/patient/v2/configuration/public","body_bytes":%d,"body_sha256":"%s","top_level_key_count":%s}\n' \
      "$SEQ" "$host" "$tag" "$size" "$sha" "${topkeys:-null}" >> "$OUT/derived-parts.jsonl"
  fi
  printf '{"seq":%d,"host":"%s","tag":"%s","method":"GET","url":"%s","code":%s,"bytes":%d,"content_type":"%s","content_length_header":"%s","sha256":"%s","t_queued":"%s","t_sent":"%s","t_done":"%s"}\n' \
    "$SEQ" "$host" "$tag" "$url" "$code" "$size" "$ctype" "$(grep -i '^content-length:' "$d/h" | tr -d '\r' | sed 's/^[Cc]ontent-[Ll]ength: *//' | head -n1)" "$sha" "$t_queued" "$t_sent" "$t_done" \
    >> "$OUT/results.jsonl"
  printf 'seq=%d host=%s tag=%s code=%s bytes=%d ctype=%s sha=%s t_queued=%s t_sent=%s t_done=%s\n' \
    "$SEQ" "$host" "$tag" "$code" "$size" "$ctype" "$sha" "$t_queued" "$t_sent" "$t_done" \
    >> "$OUT/run.log"
  echo "seq=$SEQ host=$host tag=$tag code=$code bytes=$size ctype=$ctype sha=$sha"
}

sweep_host() {
  local HOST="$1"
  local BASE="https://$HOST"
  req "$HOST" "001-control-public"   "$BASE/patient/v2/configuration/public"
  req "$HOST" "002-messages-en"       "$BASE/patient/configuration/messages/en"
  echo "swept $HOST"
}

sweep_host carelink.minimed.eu
sweep_host carelink.minimed.com
sweep_host carelink-trials.minimed.com

echo "--- requests sent: $SEQ of a $CAP cap ---"
rm -rf "$TMPD"
echo "done: $SEQ requests. bodies removed (transient, not committed)"
