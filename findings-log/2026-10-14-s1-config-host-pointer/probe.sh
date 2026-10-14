#!/usr/bin/env bash
# Record of the harness actually sent. Re-running would repeat the vendor
# requests; the cap for this pass was 3 and is already spent.
# One request per host, so no same-host repeat and no same-host delay to
# enforce between repeats; a 3 s gap was held between different hosts anyway.
set -u
EU=carelink.minimed.eu
COM=carelink.minimed.com
TRI=carelink-trials.minimed.com
UA="carelink-bridge-research/1.0"

curl -sS --compressed -D "$WORK/headers/eu-pub.h" -o "$WORK/bodies/eu-pub.b" \
  -w '%{http_code}\n' -A "$UA" \
  "https://$EU/patient/v2/configuration/public"
sleep 3
curl -sS --compressed -D "$WORK/headers/com-pub.h" -o "$WORK/bodies/com-pub.b" \
  -w '%{http_code}\n' -A "$UA" \
  "https://$COM/patient/v2/configuration/public"
sleep 3
curl -sS --compressed -D "$WORK/headers/tri-pub.h" -o "$WORK/bodies/tri-pub.b" \
  -w '%{http_code}\n' -A "$UA" \
  "https://$TRI/patient/v2/configuration/public"
