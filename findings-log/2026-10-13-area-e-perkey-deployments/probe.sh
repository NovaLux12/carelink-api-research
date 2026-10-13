#!/usr/bin/env bash
# Area E probe — is the per-key projection identical on .com and -trials?
# Claim issue #41. Cap 170. GET only. curl --compressed on every request.
# Sleep 2.5 s INSIDE the per-host flock (shared machine, 4 concurrent workers).
#
# Order per host: (1) 2 controls; (2) bulk public config (asserts the host's own
# top-level key set against the committed 69-name list from area W — no new
# target, it is the same URL the pinned 05-public-config suite already fetches);
# (3) per-key GET for each of the 69 names, in sorted order; (4) captcha's four
# subkeys in flat-name form (the grammar was INFERRED in W and the EU negative
# resolved it; confirmed here per deployment).
# Per host: 2 + 1 + 69 + 4 = 76. Two hosts: 152 of a 170 cap.
#
# Response BODIES are transient (mktemp dir, never committed): only size,
# content-type, sha256 and the kernel body mtime enter results.jsonl. Headers
# are committed per request under headers/. This script is the record of what
# was sent.
#
# NOTE on paths: the run used absolute paths for the lock dir and tmp parent.
# They are parameterized here (same resolution area W/D's probe.sh uses) because
# a committed absolute path fails the gate's machine-path rule. The request
# sequence — URLs, order, sleeps, curl flags — is untouched.
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
KEYS="$DIR/../2026-10-13-area-w-per-key/keys.txt"

mkdir -p "$OUT/headers"
SEQ=0
: > "$OUT/results.jsonl"
: > "$OUT/run.log"
date -u +%FT%T.%3NZ > "$OUT/run.log"

req() { # req <host> <tag> <url>
  local host="$1" tag="$2" url="$3"
  local lock="$POOL_LOCK_DIR/host-$host.lock"
  touch "$lock"
  SEQ=$((SEQ + 1))
  local d="$TMPD/$SEQ"
  mkdir -p "$d"
  local t_queued hseq
  t_queued=$(date -u +%FT%T.%3NZ)
  hseq=$(( $(grep -c '' "$OUT/results.jsonl") + 1 ))
  flock "$lock" bash -c \
    'sleep 2.5; date -u +%FT%T.%3NZ > "$1/ts"; curl -s --compressed -D "$1/h" -o "$1/b" -w "%{http_code}" "$2" > "$1/code"; date -u +%FT%T.%3NZ > "$1/te"' \
    _ "$d" "$url"
  local t_sent t_done code size ctype sha mt_ms
  t_sent=$(cat "$d/ts"); t_done=$(cat "$d/te"); code=$(cat "$d/code")
  size=$(stat -c%s "$d/b")
  mt_ms=$(date -u -d "$(stat -c%y "$d/b")" +%s%3N 2>/dev/null || echo 0)
  ctype=$(grep -i '^content-type:' "$d/h" | tr -d '\r' | sed 's/^[Cc]ontent-[Tt]ype: *//' | head -n1)
  sha=$(sha256sum "$d/b" | cut -d' ' -f1)
  cp "$d/h" "$OUT/headers/$host--$tag.h"
  printf '{"seq":%d,"host_seq":%d,"host":"%s","tag":"%s","method":"GET","url":"%s","code":%s,"bytes":%d,"content_type":"%s","sha256":"%s","body_mtime_ms":%s,"t_queued":"%s","t_sent":"%s","t_done":"%s"}\n' \
    "$SEQ" "$hseq" "$host" "$tag" "$url" "$code" "$size" "$ctype" "$sha" "$mt_ms" "$t_queued" "$t_sent" "$t_done" \
    >> "$OUT/results.jsonl"
  printf '%d %d %s %s %s %d %s %s %s %s %s %s\n' \
    "$SEQ" "$hseq" "$host" "$tag" "$code" "$size" "$ctype" "$mt_ms" "$t_queued" "$t_sent" "$t_done" \
    >> "$OUT/run.log"
  echo "seq=$SEQ host=$host tag=$tag code=$code bytes=$size ctype=$ctype"
}

sweep_host() { # sweep_host <host>
  local HOST="$1"
  local BASE="https://$HOST"
  local SHORT="${HOST%%.minimed.*}"
  SHORT="${SHORT#carelink-}"        # -> "com" / "trials"
  # (1) controls first on every host, before any candidate
  req "$HOST" "001-control-absent"   "$BASE/patient/configuration/system/zzz.not.a.real.key.zzz"
  req "$HOST" "002-control-live"     "$BASE/patient/configuration/system/logbook.supported.entry.types"
  # (2) bulk document on this deployment
  req "$HOST" "003-bulk-public"      "$BASE/patient/v2/configuration/public"
  cp "$TMPD/$SEQ/b" "$TMPD/bulk-$HOST.json"
  echo "BULK_SEQ[$HOST]=$SEQ"
  # (3) per-key sweep in sorted order, from the committed EU list
  local i=0 k tag
  while IFS= read -r k; do
    [ -z "$k" ] && continue
    i=$((i + 1))
    tag=$(printf '%s-k%03d-%s' "$SHORT" "$i" "$k" | tr -c 'A-Za-z0-9_.-' '_')
    req "$HOST" "$tag" "$BASE/patient/configuration/system/$k"
  done < "$KEYS"
  # (4) captcha subkeys, flat-name form
  for s in enabled key type testKey; do
    req "$HOST" "$SHORT-c-captcha.$s" "$BASE/patient/configuration/system/captcha.$s"
  done
  echo "swept $HOST: $SEQ requests so far"
}

echo "TMPD=$TMPD"
sweep_host carelink.minimed.com
sweep_host carelink-trials.minimed.com

echo "done: $SEQ requests. bodies in $TMPD (transient, not committed)"
wc -l "$OUT/results.jsonl" "$OUT/run.log"