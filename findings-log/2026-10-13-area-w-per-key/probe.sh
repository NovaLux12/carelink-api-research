#!/usr/bin/env bash
# Area W probe — is the per-key projection a complete enumeration path?
# Claim issue #31. Cap 84. GET only. curl --compressed on every request.
# Sleep 2.5 s INSIDE the per-host flock (shared machine, 4 concurrent workers).
#
# Order: (1) 2 controls first; (2) bulk public config (derives the 69-name
# candidate list live — the cited config-eu.json is NOT on disk, raw captures
# are never committed, so the list is extracted from the same URL the pinned
# 05-public-config suite already fetches); (3) per-key GET for each of the 69
# names; (4) captcha's 4 subkeys in flat-name form (grammar INFERRED).
# Expected total: 2 + 1 + 69 + 4 = 76 of an 84 cap.
#
# Response BODIES are transient (mktemp dir, never committed): only size,
# content-type and sha256 enter results.jsonl. Headers are committed per
# request under headers/. This script is the record of what was sent.
#
# NOTE on paths: the run used absolute paths for the lock dir and tmp parent.
# They are parameterized here (same resolution area D's probe.sh uses) because
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
LOCK="$POOL_LOCK_DIR/host-carelink.minimed.eu.lock"
HOST=carelink.minimed.eu
BASE="https://$HOST"
TMPD=$(mktemp -d)

mkdir -p "$OUT/headers"
touch "$LOCK"
SEQ=0
: > "$OUT/results.jsonl"
: > "$OUT/run.log"
date -u +%FT%T.%3NZ > "$OUT/run.log"

req() { # req <tag> <url>
  local tag="$1" url="$2" d="$TMPD/$1"
  mkdir -p "$d"
  SEQ=$((SEQ + 1))
  local t_queued
  t_queued=$(date -u +%FT%T.%3NZ)
  flock "$LOCK" bash -c \
    'sleep 2.5; date -u +%FT%T.%3NZ > "$1/ts"; curl -s --compressed -D "$1/h" -o "$1/b" -w "%{http_code}" "$2" > "$1/code"; date -u +%FT%T.%3NZ > "$1/te"' \
    _ "$d" "$url"
  local t_sent t_done code size ctype sha
  t_sent=$(cat "$d/ts"); t_done=$(cat "$d/te"); code=$(cat "$d/code")
  size=$(stat -c%s "$d/b")
  ctype=$(grep -i '^content-type:' "$d/h" | tr -d '\r' | sed 's/^[Cc]ontent-[Tt]ype: *//' | head -n1)
  sha=$(sha256sum "$d/b" | cut -d' ' -f1)
  cp "$d/h" "$OUT/headers/$tag.h"
  printf '{"seq":%d,"host_seq":%d,"host":"%s","tag":"%s","method":"GET","url":"%s","code":%s,"bytes":%d,"content_type":"%s","sha256":"%s","t_queued":"%s","t_sent":"%s","t_done":"%s"}\n' \
    "$SEQ" "$SEQ" "$HOST" "$tag" "$url" "$code" "$size" "$ctype" "$sha" "$t_queued" "$t_sent" "$t_done" \
    >> "$OUT/results.jsonl"
  printf '%d %s %s %d %s %s %s %s\n' "$SEQ" "$tag" "$code" "$size" "$ctype" "$t_queued" "$t_sent" "$t_done" \
    >> "$OUT/run.log"
  echo "seq=$SEQ tag=$tag code=$code bytes=$size ctype=$ctype"
  cp "$d/b" "$TMPD/body-$tag.bin"
}

echo "TMPD=$TMPD"

# (1) controls first
req 001-control-absent "$BASE/patient/configuration/system/zzz.not.a.real.key.zzz"
req 002-control-live   "$BASE/patient/configuration/system/logbook.supported.entry.types"

# (2) bulk document — the candidate-list source
req 003-bulk-public "$BASE/patient/v2/configuration/public"

python3 - "$TMPD/body-003-bulk-public.bin" "$TMPD/keys.txt" <<'EOF'
import json,sys
bulk=json.load(open(sys.argv[1]))
keys=sorted(bulk.keys())
print("top-level keys:",len(keys))
assert len(keys)==69, f"expected 69, got {len(keys)}"
open(sys.argv[2],"w").write("\n".join(keys)+"\n")
nulls=[k for k in keys if bulk[k] is None]
print("null-valued:",len(nulls),nulls)
EOF
cp "$TMPD/keys.txt" "$OUT/keys.txt"

# (3) per-key sweep in sorted order
i=0
while IFS= read -r k; do
  i=$((i+1))
  tag=$(printf 'k%03d-%s' "$i" "$k" | tr -c 'A-Za-z0-9_.-' '_')
  req "$tag" "$BASE/patient/configuration/system/$k"
done < "$TMPD/keys.txt"

# (4) captcha subkeys, flat-name form (grammar INFERRED)
for s in enabled key type testKey; do
  req "c-captcha.$s" "$BASE/patient/configuration/system/captcha.$s"
done

echo "done: $SEQ requests. bodies in $TMPD (transient, not committed)"
wc -l "$OUT/results.jsonl" "$OUT/run.log"
