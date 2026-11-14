#!/usr/bin/env bash
# i18n display-strings pass, 2026-11-13. GET/HEAD only, no credential.
# One row per request in requests.tsv; bodies in bodies/.
set -uo pipefail
cd "$(dirname "$0")"
: > requests.tsv
printf '# n\tt_sent_utc\tmethod\turl\tstatus\tbytes\tcontent_type\tsha256\n' >> requests.tsv
mkdir -p bodies

n=0
req() { # method url slug
  local m="$1" u="$2" slug="$3"
  n=$((n+1))
  local ts; ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  local out="bodies/${slug}.bin"
  local meta
  meta=$(curl -sS -X "$m" -D "bodies/${slug}.h" -o "$out" \
    -w '%{http_code}\t%{size_download}\t%{content_type}' "$u")
  local dg="-"; [ -s "$out" ] && dg=$(sha256sum "$out" | cut -d' ' -f1)
  printf '%d\t%s\t%s\t%s\t%s\t%s\n' "$n" "$ts" "$m" "$u" "$meta" "$dg" >> requests.tsv
  echo "[$n] $m $u -> $meta"
  [ "$n" -lt 10 ] && sleep 2.2
}

EU=https://carelink.minimed.eu
COM=https://carelink.minimed.com

req GET  "$EU/crm/ocl/15.5/i18n/ui/app/en.json"                  eu-en
req GET  "$COM/crm/ocl/15.5/i18n/ui/app/en.json"                 com-en
req GET  "$EU/crm/ocl/15.5/i18n/ui/app/de.json"                  eu-de
req HEAD "$EU/crm/ocl/15.5/i18n/ui/app/en.json"                  eu-en-head
req GET  "$EU/crm/ocl/15.4/i18n/ui/app/en.json"                  ctl-version-15.4
req GET  "$EU/crm/ocl/15.6/i18n/ui/app/en.json"                  ctl-version-15.6
req GET  "$EU/crm/ocl/15.5/i18n/ui/app/zz.json"                  ctl-locale-zz
req GET  "$EU/crm/ocl/15.5/i18n/ui/app/zzz/does-not-exist.json"  ctl-absent-path
req GET  "$EU/crm/ocl/15.5/i18n/ui/zzz.json"                     ctl-absent-file
req GET  "$EU/patient/v2/configuration/public"                   public-config

echo "--- ledger ---"
cat requests.tsv
