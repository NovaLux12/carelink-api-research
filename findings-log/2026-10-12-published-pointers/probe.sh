#!/usr/bin/env bash
# Area T — does any published document point a client at csr/v2, or is it a
# namespace no config can address?
#
# Constraints, as claimed in #10:
#   - GET only. No POST, no token exchange, no authentication, no api-key.
#   - >=2.5 s between requests to the same host.
#   - Cap 12. Six document reads + up to six spares. A response that fails to
#     parse is NOT re-requested — decompress locally instead (carelink.* serves
#     gzip unconditionally; --compressed handles it, and a re-request is
#     forbidden for exactly the reason in docs/09 §4).
#   - Every candidate is a document already named in docs/ on disk. No
#     wordlist, no new host, no DNS, no dev/stage host.
#
# What is read, and why each one (all four distinct recorded discovery
# documents, not just the one the bridge pins):
#
#   clcloud.minimed.eu          /connect/carepartner/v13/discover/android/3.6
#       the Auth0/v13 patient doc, 20345 B. The cell the bridge pins.
#   clcloud.minimed.com         /connect/carepartner/v13/discover/android/3.6
#       same cell, US host. docs/03 §1 claims all three hosts serve the same
#       document; that claim is re-derived here rather than trusted.
#   clcloud.minimed.com         /connect/carepartner/v11/discover/android/3.6
#       the 18105 B LEGACY doc. The only recorded cell carrying
#       baseUrlPde = .../pde/v1 and no baseUrlCms/baseUrlAem.
#   clcloud-trials.minimed.com  /connect/carepartner/v6/discover/android/3.6
#       the 10053 B trials-only LEGACY doc, 403 on both patient hosts. The
#       third distinct document in the corpus.
#   carelink.minimed.{eu,com}   /patient/v2/configuration/public
#   carelink-trials.minimed.com /patient/v2/configuration/public
#       the 69-key public config. Carries csr.cumulus.periodic.data.endpoints,
#       whose VALUE no pass has ever read.
#   carelink.minimed.{eu,com}   /patient/countries/settings?countryCode=GB
#   carelink-trials.minimed.com /patient/countries/settings?countryCode=US
#       the 35-key country document. Publishes blePereodicDataEndpoint, a third
#       published pointer into the cumulus plane, swept here per deployment for
#       the first time.

set -uo pipefail
DIR="findings-log/2026-10-12-published-pointers"
DOCS="$DIR/docs"
mkdir -p "$DOCS"
: > "$DIR/requests.tsv"

n=0
last_host=""

# $1=host $2=path $3=outfile basename
get() {
  local host="$1" path="$2" name="$3"
  if [ "$host" != "$last_host" ]; then
    # new host: the >=2s rule is per host, so no sleep is owed across hosts,
    # but stay polite and add a short gap anyway.
    [ -n "$last_host" ] && sleep 2.5
    last_host="$host"
  else
    sleep 2.5
  fi
  n=$((n+1))
  local url="https://${host}/${path}"
  local out="$DOCS/${name}.json"
  local hdr="$DOCS/${name}.hdr"
  echo "[$n] GET $url"
  local code
  code=$(curl -s --compressed -D "$hdr" -o "$out" -w '%{http_code}' --max-time 25 "$url")
  local ctype;     ctype=$(grep -i '^content-type:' "$hdr" | tr -d '\r' | head -1)
  local enc;       enc=$(grep -i '^content-encoding:' "$hdr" | tr -d '\r' | head -1)
  local bytes;     bytes=$(wc -c < "$out" | tr -d ' ')
  local json_ok;   json_ok=$(python3 -c 'import json,sys
try:
    d=json.load(open(sys.argv[1]))
    print("parses:"+type(d).__name__)
except Exception as e:
    print("PARSE-FAIL:"+type(e).__name__)' "$out")
  printf '%d\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$n" "$host" "$path" "$code" "$bytes" "$ctype" "$json_ok" >> "$DIR/requests.tsv"
  echo "    $code | ${ctype:-content-type: (none)} | ${enc:-content-encoding: (none)} | ${bytes}B | $json_ok"
}

# --- the four distinct recorded discovery documents
get "clcloud.minimed.eu"         "connect/carepartner/v13/discover/android/3.6" "disc-eu-v13"
get "clcloud.minimed.com"        "connect/carepartner/v13/discover/android/3.6" "disc-com-v13"
get "clcloud.minimed.com"        "connect/carepartner/v11/discover/android/3.6" "disc-com-v11-legacy"
get "clcloud-trials.minimed.com" "connect/carepartner/v6/discover/android/3.6"  "disc-trials-v6-legacy"

# --- the 69-key public config, all three deployments
get "carelink.minimed.eu"         "patient/v2/configuration/public" "config-eu"
get "carelink.minimed.com"        "patient/v2/configuration/public" "config-com"
get "carelink-trials.minimed.com" "patient/v2/configuration/public" "config-trials"

# --- the 35-key country document, all three deployments (blePereodicDataEndpoint)
get "carelink.minimed.eu"         "patient/countries/settings?countryCode=GB" "countries-eu"
get "carelink.minimed.com"        "patient/countries/settings?countryCode=US" "countries-com"
get "carelink-trials.minimed.com" "patient/countries/settings?countryCode=US" "countries-trials"

echo "DONE n=$n (cap 12)"