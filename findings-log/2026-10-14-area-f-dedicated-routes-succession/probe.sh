#!/usr/bin/env bash
# Area F succession probe — dedicated config-escape routes envelope behavior on .com and -trials.
# Issue #102. CAP 14. GET only. curl --compressed on every request.
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

shape() { # shape <bodyfile>
  python3 - "$1" <<'PY'
import json,sys
p=sys.argv[1]
b=open(p,"rb").read()
try:
    o=json.loads(b)
except Exception:
    print("non-json")
    raise SystemExit
if isinstance(o,dict):
    parts=["dict:"+",".join(sorted(o.keys()))]
    for k,v in o.items():
        if isinstance(v,list):
            parts.append(f"arrlen:{k}:{len(v)}")
        elif isinstance(v,str):
            parts.append(f"strlen:{k}:{len(v)}")
        elif isinstance(v,bool):
            parts.append(f"bool:{k}:{str(v).lower()}")
        elif v is None:
            parts.append(f"null:{k}")
        else:
            parts.append(f"type:{k}:{type(v).__name__}")
    print("|".join(parts))
else:
    print(type(o).__name__)
PY
}

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
  local cl xcache acao
  cl=$(grep -i '^content-length:' "$d/h" | tr -d '\r' | sed 's/^[Cc]ontent-[Ll]ength: *//' | head -n1)
  xcache=$(grep -i '^x-cache:' "$d/h" | tr -d '\r' | sed 's/^[Xx]-[Cc]ache: *//' | head -n1)
  acao=$(grep -i '^access-control-allow-origin:' "$d/h" | tr -d '\r' | sed 's/^[Aa]ccess-[Cc]ontrol-[Aa]llow-[Oo]rigin: *//' | head -n1)
  local sh
  sh=$(shape "$d/b")
  cp "$d/h" "$OUT/headers/$host--$tag.h"
  printf '%s\n' "{\"seq\":$SEQ,\"host\":\"$host\",\"tag\":\"$tag\",\"method\":\"GET\",\"url\":\"$url\",\"http_status\":$code,\"curl_exit\":0,\"body_bytes\":$size,\"content_type\":\"$ctype\",\"content_length_header\":\"$cl\",\"x_cache\":\"$xcache\",\"acao\":\"$acao\",\"body_sha256\":\"$sha\",\"body_shape\":\"$sh\",\"t_queued\":\"$t_queued\",\"t_sent\":\"$t_sent\",\"t_done\":\"$t_done\"}" \
    >> "$OUT/results.jsonl"
  printf 'seq=%d host=%s tag=%s code=%s bytes=%d ctype=%s sha=%s shape=%s t_queued=%s t_sent=%s t_done=%s\n' \
    "$SEQ" "$host" "$tag" "$code" "$size" "$ctype" "$sha" "$sh" "$t_queued" "$t_sent" "$t_done" \
    >> "$OUT/run.log"
  echo "seq=$SEQ host=$host tag=$tag code=$code bytes=$size ctype=$ctype shape=$sh"
}

sweep_host() {
  local HOST="$1"
  local BASE="https://$HOST"
  req "$HOST" "001-control-version"     "$BASE/patient/configuration/version"
  req "$HOST" "002-control-root"        "$BASE/patient/configuration/"
  req "$HOST" "003-dedicated-defaultCountry" "$BASE/patient/configuration/defaultCountry"
  req "$HOST" "004-dedicated-recaptcha-key"  "$BASE/patient/configuration/recaptcha/key"
  req "$HOST" "005-dedicated-messages-en"    "$BASE/patient/configuration/messages/en"
  req "$HOST" "006-dedicated-messages-fr"    "$BASE/patient/configuration/messages/fr"
  req "$HOST" "007-dedicated-messages-de"    "$BASE/patient/configuration/messages/de"
  echo "swept $HOST"
}

sweep_host carelink.minimed.com
sweep_host carelink-trials.minimed.com

echo "--- requests sent: $SEQ of a $CAP cap ---"
rm -rf "$TMPD"
echo "done: $SEQ requests. bodies removed (transient, not committed)"
wc -l "$OUT/results.jsonl" "$OUT/run.log"
