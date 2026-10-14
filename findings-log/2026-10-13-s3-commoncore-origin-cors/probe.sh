#!/usr/bin/env bash
set -euo pipefail
LOG="$(cd "$(dirname "$0")" && pwd)"
: "${LOOP:?set LOOP to the shared .loop directory}"
DELAY=2.5
UA='carelink-bridge-research/1.0'
CAP=12
SEQ=0
[ -f "$LOG/results.jsonl" ] && SEQ="$(wc -l < "$LOG/results.jsonl" | tr -d ' ')"
REC="$(mktemp -d)"
mkdir -p "$LOG/headers" "$LOG/bodies"
trap 'rm -rf "$REC"' EXIT
now(){ date -u +%FT%T.%3NZ; }
out(){
  local host="$1" cell="$2" method="$3" path="$4" role="$5" origin="${6:-}"
  case "$method" in GET|OPTIONS) ;; *) echo "ABORT"; exit 2 ;; esac
  case "$path" in /*) ;; *) echo "ABORT"; exit 2 ;; esac
  SEQ=$((SEQ+1))
  local n; n="$(printf '%02d' "$SEQ")"
  local tag; tag="$(printf '%s' "$host" | cut -d. -f1)-$(printf '%s' "$cell" | tr 'A-Z' 'a-z' | tr '_' '-')"
  local h="$LOG/headers/$n-$tag.h" b="$LOG/bodies/$n-$tag.b"
  local s="$LOG/headers/$n-$tag.sent.h" r="$REC/$n"; mkdir -p "$r"
  local kvs="$r/kv"; : > "$kvs"
  local tq ts td code cexit errline connected upload
  tq="$(now)"
  (
    set +e
    flock -x 9
    sleep "$DELAY"
    now > "$r/ts"
    if [ "$method" = OPTIONS ]; then
      if [ -n "$origin" ]; then
        curl -sS --compressed -v -X OPTIONS -A "$UA" -H "Origin: $origin" --connect-timeout 10 --max-time 40 -o "$b" -D "$h" -w '%{http_code}' "https://$host$path" > "$r/code" 2>"$r/v"
      else
        curl -sS --compressed -v -X OPTIONS -A "$UA" --connect-timeout 10 --max-time 40 -o "$b" -D "$h" -w '%{http_code}' "https://$host$path" > "$r/code" 2>"$r/v"
      fi
    else
      if [ -n "$origin" ]; then
        curl -sS --compressed -v -A "$UA" -H "Origin: $origin" --connect-timeout 10 --max-time 40 -o "$b" -D "$h" -w '%{http_code}' "https://$host$path" > "$r/code" 2>"$r/v"
      else
        curl -sS --compressed -v -A "$UA" --connect-timeout 10 --max-time 40 -o "$b" -D "$h" -w '%{http_code}' "https://$host$path" > "$r/code" 2>"$r/v"
      fi
    fi
    echo $? > "$r/exit"
    now > "$r/td"
  ) 9>"$LOOP/host-$host.lock"
  ts="$(cat "$r/ts")"; td="$(cat "$r/td")"; code="$(cat "$r/code")"; cexit="$(cat "$r/exit")"
  sed -n 's/^> //p' "$r/v" > "$s"
  errline="$(grep -m1 '^curl: ' "$r/v" || true)"
  upload="$(grep -m1 -e '^\* no upload' -e '^\* upload' "$r/v" || true)"
  connected="$(grep -c 'Connected to' "$r/v" || true)"
  printf 'seq\t%s\nhost\t%s\nhost_tag\t%s\ncell\t%s\nmethod\t%s\npath\t%s\nrole\t%s\nsent_headers\t%s\norigin_sent\t%s\ncurl_error_line\t%s\ncurl_upload_line\t%s\ncurl_connected_lines\t%s\ndelay_declared_s\t%s\nt_queued\t%s\nt_sent\t%s\nt_done\t%s\nhttp_status\t%s\ncurl_exit\t%s\ncontent_type\t%s\ncontent_encoding\t%s\nx_amzn_errortype\t%s\nx_ca_err\t%s\nallow\t%s\nvary\t%s\naccess_control_allow_origin\t%s\naccess_control_allow_methods\t%s\naccess_control_allow_headers\t%s\naccess_control_allow_credentials\t%s\nx_cache\t%s\nserver\t%s\nresponse_cors_header_count\t%s\nbody_bytes\t%s\nbody_sha256\t%s\nbody_mtime_epoch\t%s\nbody_mtime_iso\t%s\nbody_head256\t%s\n' \
    "$SEQ" "$host" "$tag" "$cell" "$method" "$path" "$role" \
    "User-Agent: $UA${origin:+; (Origin: $origin)}" "${origin:-<none>}" "${errline:-<none>}" "${upload:-<none>}" "$connected" "$DELAY" "$tq" "$ts" "$td" "${code:-000}" "$cexit" \
    "$(grep -im1 '^content-type:' "$h" | cut -d' ' -f2- | tr -d '\r')" \
    "$(grep -im1 '^content-encoding:' "$h" | cut -d' ' -f2- | tr -d '\r')" \
    "$(grep -im1 '^x-amzn-errortype:' "$h" | cut -d' ' -f2- | tr -d '\r')" \
    "$(grep -im1 '^x-ca-err:' "$h" | cut -d' ' -f2- | tr -d '\r')" \
    "$(grep -im1 '^allow:' "$h" | cut -d' ' -f2- | tr -d '\r')" \
    "$(grep -im1 '^vary:' "$h" | cut -d' ' -f2- | tr -d '\r')" \
    "$(grep -im1 '^access-control-allow-origin:' "$h" | cut -d' ' -f2- | tr -d '\r')" \
    "$(grep -im1 '^access-control-allow-methods:' "$h" | cut -d' ' -f2- | tr -d '\r')" \
    "$(grep -im1 '^access-control-allow-headers:' "$h" | cut -d' ' -f2- | tr -d '\r')" \
    "$(grep -im1 '^access-control-allow-credentials:' "$h" | cut -d' ' -f2- | tr -d '\r')" \
    "$(grep -im1 '^x-cache:' "$h" | cut -d' ' -f2- | tr -d '\r')" \
    "$(grep -im1 '^server:' "$h" | cut -d' ' -f2- | tr -d '\r')" \
    "$(grep -ic '^access-control-' "$h" || true)" \
    "$(wc -c < "$b" | tr -d ' ')" "$(sha256sum "$b" | cut -d' ' -f1)" \
    "$(stat -c %Y "$b")" "$(date -u -d "@$(stat -c %Y "$b")" +%FT%T.%3NZ)" \
    "$(head -c 256 "$b" | tr -d '\0' | tr '\n' ' ' | cut -c1-256)" >> "$kvs"
  python3 - "$kvs" "$LOG/results.jsonl" <<'PY'
import json,sys
kv,d,o=sys.argv[1],{},[]
for line in open(kv):
    line=line.rstrip('\n')
    if '\t' in line:
        k,v=line.split('\t',1)
        if k not in d: o.append(k)
        d[k]=v
r=json.dumps({k:d[k] for k in o}); json.loads(r)
open(sys.argv[2],'a').write(r+'\n')
PY
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$SEQ" "$host" "$method" "$path" "$tq" "$ts" "$td" >> "$LOG/run.log"
  printf '[%s] %-7s %-5s %-28s origin=%-6s -> %s\n' "$host" "$method" "${code:-000}" "$path" "${origin:-bare}" "$ts"
}
H_T='commoncore-trials.minimed.com'
H_O='commoncore.medtronic.com'
ORIG='https://example.invalid'
echo "cap $CAP requests | delay ${DELAY}s | GET + empty-body OPTIONS | Origin on $H_O"

# breadth
out "$H_T" T-rec-get   GET     /reports-broker/v1/ocl               recorded-path-not-control  ''
out "$H_T" T-abs-get   GET     /reports-broker/v1/ocl-probe-absent certainly-absent            ''
out "$H_T" T-abs-opt   OPTIONS /reports-broker/v1/ocl-probe-absent deciding-cell              ''
out "$H_T" T-rec-opt   OPTIONS /reports-broker/v1/ocl               matched-pair               ''

# Origin axis bare
out "$H_O" O-rec-get-bare GET     /reports-broker/v1/ocl               recorded-path-bare           ''
out "$H_O" O-abs-get-bare GET     /reports-broker/v1/ocl-probe-absent certainly-absent-bare        ''
out "$H_O" O-abs-opt-bare OPTIONS /reports-broker/v1/ocl-probe-absent deciding-cell-bare          ''
out "$H_O" O-rec-opt-bare OPTIONS /reports-broker/v1/ocl               matched-pair-bare           ''

# Origin axis with Origin header
out "$H_O" O-rec-get-orig GET     /reports-broker/v1/ocl               recorded-path-origin         "$ORIG"
out "$H_O" O-abs-get-orig GET     /reports-broker/v1/ocl-probe-absent certainly-absent-origin      "$ORIG"
out "$H_O" O-abs-opt-orig OPTIONS /reports-broker/v1/ocl-probe-absent deciding-cell-origin         "$ORIG"
out "$H_O" O-rec-opt-orig OPTIONS /reports-broker/v1/ocl               matched-pair-origin          "$ORIG"

echo "12 invocations complete"
