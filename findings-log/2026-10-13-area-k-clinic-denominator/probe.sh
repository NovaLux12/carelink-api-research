#!/usr/bin/env bash
# Area K clinic 225 chunk denominator — GET-only probe.
# Each request acquires the host lock, sleeps, curls, releases.
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$DIR/../../.." && pwd)"
LOGDIR="$DIR"
BODYDIR="${TMPDIR:-/tmp}/carelink-clinic-bodies"
LOCK="$ROOT/.loop/host-carelinkhp.minimed.eu.lock"
HOST="https://carelinkhp.minimed.eu"
MAP="$LOGDIR/runtime-map.txt"
META="$LOGDIR/meta.tsv"

mkdir -p "$LOGDIR/headers" "$BODYDIR"
rm -f "$META" "$LOGDIR/results.jsonl"

cp /tmp/clinic-map.txt "$MAP"

seq=0
while read -r id name hash; do
  [[ -z "${id:-}" ]] && continue
  seq=$((seq+1))
  path="/${name}.${hash}.js"
  url="${HOST}${path}"
  body="${BODYDIR}/body-${seq}.js"
  hdr="${LOGDIR}/headers/$(printf '%03d' "$seq").txt"
  metafile="${LOGDIR}/.meta-${seq}.tmp"
  t_queued=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)
  flock "$LOCK" bash -c "
    sleep 2.5
    tsent=\$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)
    status=\$(curl --compressed -sS -o '$body' -D '$hdr' -w '%{http_code}' '$url')
    tdone=\$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)
    printf '%s\\t%s\\t%s\\n' \"\$tsent\" \"\$tdone\" \"\$status\" > '$metafile'
  "
  read -r tsent tdone status < "$metafile"
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$seq" "$id" "$name" "$hash" "$path" "$t_queued" "$tsent" "$tdone" "$status" >> "$META"
  rm -f "$metafile"
  echo "seq=$seq id=$id emitted=$name.$hash status=$status queued=$t_queued" >&2
done < "$MAP"
echo "done total=$seq" >&2
