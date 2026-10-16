#!/usr/bin/env python3
"""absorb-gate.py — lane l2. Zero vendor requests.

Appends the pinned suite's own requests to this pass's ledger.

The gate runs `regression/hurl/05-public-config.check.sh`, which issues real
vendor traffic — permitted by AGENTS.md §11 ("run the pinned suite and nothing
else") and permitted to nobody else. Those requests are part of this pass's cap,
so they belong in the accounting. A `curl` shim recorded them while the gate ran
(see `curl-shim.sh`); this turns those records into ledger rows in the same shape
as every other row, so `wc -l results.jsonl` is the whole traffic of the pass and
not only the part this pass's own harness issued.

Honest limits, stated on the row:

  - `t_sent` is the shim's *pre-exec* stamp, not a stamp taken inside a per-host
    lock. The suite does its own pacing (a 2 s `sleep` between its own requests)
    and is not under this pass's `sleep 2.5`-inside-flock harness. So these rows
    are counted but are **excluded from the measured spacing floor**, and the
    floor is stated over this pass's own harness rows only.
  - `content_type` / `body_bytes` / `body_sha256` are not captured: the shim does
    not intercept bodies, and re-fetching them would be additional vendor traffic
    charged to the same cap. The status and the URL are the evidence; the body
    evidence for the three `carelink.medtronic.eu` cells the suite already pins is
    the suite's own assertions.
"""
import json
import os
import sys
from urllib.parse import urlsplit

curllog, ledger, runlog = sys.argv[1:4]

if not os.path.exists(curllog):
    sys.exit(f"absorb-gate.py: no shim log at {curllog} — the gate issued nothing")

recs = [json.loads(l) for l in open(curllog, encoding="utf-8") if l.strip()]
if not recs:
    sys.exit("absorb-gate.py: shim log is empty — the gate issued no requests")

rows = [json.loads(l) for l in open(ledger, encoding="utf-8") if l.strip()]
seq = len(rows)
per_host = {}
for r in rows:
    per_host[r["host"]] = per_host.get(r["host"], 0) + 1

added = 0
with open(ledger, "a", encoding="utf-8") as f:
    for r in recs:
        host = urlsplit(r["url"]).netloc
        seq += 1
        per_host[host] = per_host.get(host, 0) + 1
        f.write(json.dumps({
            "seq": seq, "host_seq": per_host[host], "host": host,
            "tag": f"g{r['http_status']}-{host.replace('.', '-')}-"
                   f"suite-{seq}",
            "method": r["method"], "path": urlsplit(r["url"]).path
            + (("?" + urlsplit(r["url"]).query) if urlsplit(r["url"]).query else ""),
            "kind": "gate-suite",
            "role": "GATE-SUITE request issued by regression/hurl/05-public-config.check.sh "
                    "while `./scripts/research-gate.sh` ran, recorded by a curl shim that "
                    "exec'd the real curl unchanged. Counted against this pass's cap "
                    "(AGENTS.md §11). NOT part of this pass's sweep and NOT used as "
                    "evidence for any claim in FINDINGS.md except where the row's own "
                    "assertion is cited. " + r["issued_by"],
            "sent_headers": "(as the suite set them; not captured by the shim)",
            "http_status": r["http_status"], "curl_exit": r["curl_exit"],
            "content_type": "(not captured — the shim does not intercept bodies)",
            "content_length_hdr": "(not captured)",
            "content_encoding": "(not captured)", "vary": "(not captured)",
            "x_amz_cf_pop": "(not captured)", "server": "(not captured)",
            "body_bytes": -1, "body_sha256": "",
            "headers": "",
            "t_queued": r["t_queued"], "t_sent": r["t_queued"],
            "t_done": r["t_done"],
            "ledger_note": "t_sent is the shim's pre-exec stamp, NOT taken inside a "
                           "per-host lock; the suite carries its own pacing and is not "
                           "under this pass's sleep-inside-flock harness. Excluded from "
                           "the measured spacing floor for that reason. body_bytes -1 "
                           "means 'not captured', which is not the same as an empty body "
                           "(AGENTS.md §9's absent-vs-null class).",
        }) + "\n")
        added += 1

with open(runlog, "a", encoding="utf-8") as f:
    f.write(f"GATE_ABSORB rows_added={added} ledger={seq}\n")

print(f"absorb-gate.py: appended {added} gate-suite rows; ledger now {seq}")
for r in recs:
    print(f"  {r['http_status']:>3} {r['method']:<4} {r['url']}")