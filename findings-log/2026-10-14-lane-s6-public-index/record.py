#!/usr/bin/env python3
"""Append ONE results.jsonl row. Called from INSIDE the per-host flock.

This lives in its own file for a concrete reason. It was originally a heredoc
embedded in the `flock ... -c "..."` string, where every `"` in the Python had
to survive two layers of shell quoting; a missed escape made the whole critical
section exit 127 and the request was correctly refused. Splitting it out means
the row schema is readable as Python and is not re-quoted per shell.

Usage (all positional, all required):
  record.py <results.jsonl> <seq> <host_seq> <host> <tag> <role> <path> \
            <http_status> <body_bytes> <sha256> <t_queued> <t_sent> <t_done>

The derived facts are read from <results_dir>/ts/<tag>.facts, which derive.py
wrote from the body while the lock was still held. If that file is missing or
unparseable the row records record_count 0 with shape "none" -- never a guess.

Ordering guarantee: t_sent is written before the curl and t_done after it, both
inside this same critical section, and the row is written before the lock is
released. So a row cannot carry another request's timestamps, which is the
defect five rows in the previous pass carry (t_done before t_sent).
"""

from __future__ import annotations

import json
import os
import sys

# Response text is never committed: CC captures carry jsessionid_* values in URL
# paths and pre-Auth0 authorize URLs whose sessionData is a base64 JWS
# (AGENTS.md section 7). This marker is the record that the withholding was
# deliberate, not a placeholder for a value that was lost.
WITHHELD = ("<withheld-by-policy: raw CDX/JSON text carries session material; "
            "see derive.py>")


def main(argv: list[str]) -> int:
    if len(argv) != 14:
        print(f"record.py: expected 13 args, got {len(argv) - 1}", file=sys.stderr)
        return 2
    (_, results, seq, host_seq, host, tag, role, path,
     status, nbytes, sha, t_queued, t_sent, t_done) = argv

    # derive.py wrote <tag>.facts and the header projection <tag>.cf into the
    # scratch tree while the lock was held. That tree lives OUTSIDE the
    # repository (see probe.sh SCRATCH): raw CC responses reach 1.86 MB and the
    # gate's hygiene check globs findings-log/ for anything over 1 MiB.
    scratch = os.environ.get("S6_SCRATCH", "").strip()
    ts_dir = os.path.join(scratch, "ts") if scratch else os.path.join(
        os.path.dirname(results) or ".", "ts")
    try:
        with open(os.path.join(ts_dir, f"{tag}.facts"), encoding="utf-8") as fh:
            facts = json.load(fh)
        if not isinstance(facts, dict):
            raise ValueError("facts is not an object")
    except Exception:
        facts = {"record_count": 0, "distinct_hosts": [],
                 "distinct_host_count": 0, "shape": "none"}

    # The discriminating header set (docs/09 section 4). Recorded as
    # "(none)" when absent, which is a fact about the response rather than a
    # missing value -- some answers genuinely carry no header we track.
    try:
        with open(os.path.join(ts_dir, f"{tag}.cf"), encoding="utf-8") as fh:
            disc = fh.read().strip() or "(none)"
    except Exception:
        disc = "(none)"

    row = {
        "seq": int(seq),
        "host_seq": int(host_seq),
        "host": host,
        "host_tag": tag,
        "method": "GET",
        "path": path,
        "role": role,
        "http_status": status,
        "curl_exit": 0,
        "body_bytes": int(nbytes),
        "body_sha256": sha,
        "disc_headers": disc,
        "body_head": WITHHELD,
        **facts,
        "t_queued": t_queued,
        "t_sent": t_sent,
        "t_done": t_done,
    }
    # Append-mode write of one line: a single write() of a single object, so a
    # concurrent writer cannot interleave a partial row.
    with open(results, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))