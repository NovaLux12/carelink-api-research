#!/usr/bin/env bash
# Record of the harness actually sent. Re-running would repeat the vendor
# requests; the cap for this pass was 6 and is already spent.
set -u
: "${REPO:?set REPO to the clone root}"
: "${WORK:?set WORK to a scratch directory for transient bodies}"
HOSTS_ROOT="$REPO/.loop"
EU=carelink.minimed.eu; COM=carelink.minimed.com; TRI=carelink-trials.minimed.com

req() {  # req <host> <url> <tag>
  local host="$1" url="$2" tag="$3"
  flock "$HOSTS_ROOT/host-$host.lock" -c \
    "sleep 2.5; curl -sS --compressed -D '$WORK/headers/$tag.h' -o '$WORK/bodies/$tag.b' -w '%{http_code}' '$url'" \
    > "$WORK/codes/$tag.code" 2>"$WORK/errs/$tag.err"
}

mkdir -p "$WORK/headers" "$WORK/bodies" "$WORK/codes" "$WORK/errs"

req "$EU"  "https://$EU/patient/v2/configuration/public"       "eu-pub"
req "$COM" "https://$COM/patient/v2/configuration/public"      "com-pub"
req "$TRI" "https://$TRI/patient/v2/configuration/public"      "tri-pub"

req "$EU"  "https://$EU/patient/configuration/messages/en"     "eu-msg"
req "$COM" "https://$COM/patient/configuration/messages/en"    "com-msg"
req "$TRI" "https://$TRI/patient/configuration/messages/en"   "tri-msg"
