#!/usr/bin/env python3
"""Project one Common Crawl CDX response down to facts.

AGENTS.md §7: Common Crawl records carry live Java session identifiers in URL
paths, so no response body is committed anywhere in this directory. This script
reduces each body in code to a projection, and the ledger stores that plus the
body's byte count and sha256 so the capture stays reproducible.

Shapes handled, all established by the controls in §2 of FINDINGS.md:
  * record form   -- ndjson, one JSON object per line, `{"urlkey","timestamp",
                     "original","mimetype",...}` per capture
  * count form    -- a single ndjson line, `{"pages","pageSize","blocks"}`
  * absence form  -- `{"message": "No Captures found for: ..."}`
  * failure form  -- nginx/S3 gateway pages (text/html or text/plain)

Any `jsessionid` that survives into a committed projection is redacted to the
marker plus a count. The value is never written anywhere.
"""
import hashlib
import json
import re
import sys
from urllib.parse import urlsplit

# `jsessionid_` followed by the value; also bare `jsessionid=`.
SESSION_RE = re.compile(r"jsessionid(?:_|=)[^&;\s\"'/]*", re.IGNORECASE)


def redact(text):
    """Return (redacted_text, count_of_session_markers_found)."""
    hits = SESSION_RE.findall(text)
    return SESSION_RE.sub("jsessionid_<REDACTED>", text), len(hits)


def project(path):
    raw = open(path, "rb").read()
    try:
        text = raw.decode("utf-8", "replace")
    except Exception:
        text = ""

    out = {
        "shape": "unrecognised",
        "record_count": 0,
        "distinct_hosts": [],
        "distinct_host_count": 0,
        "jsession_markers": 0,
    }

    stripped = text.lstrip()
    if stripped.startswith("{") and '"message"' in text and '"pages"' not in text:
        try:
            obj = json.loads(stripped)
        except Exception:
            obj = None
        if isinstance(obj, dict) and "message" in obj:
            msg, n = redact(str(obj["message"]))
            out["shape"] = "absence-json"
            out["message"] = msg
            out["jsession_markers"] = n
            return out

    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        out["shape"] = "empty"
        return out

    # count form: exactly the three accounting keys, no captures
    try:
        first = json.loads(lines[0])
    except Exception:
        first = None
    if isinstance(first, dict) and "pages" in first and "urlkey" not in first:
        out["shape"] = "count-instrument"
        out["count_instrument"] = {k: first.get(k) for k in ("pages", "pageSize", "blocks")}
        return out

    records = []
    for ln in lines:
        try:
            rec = json.loads(ln)
        except Exception:
            continue
        if isinstance(rec, dict) and "urlkey" in rec:
            records.append(rec)

    if records:
        out["shape"] = "record-ndjson"
        out["record_count"] = len(records)
        members, markers = [], 0
        hosts, urlkeys = [], []
        for rec in records:
            u = str(rec.get("url", ""))
            parts = urlsplit(u)
            host = parts.netloc or ""
            clean = parts.path or "/"
            # a JSESSIONID rides in the path after a ';' -- drop the value
            clean, n = redact(clean)
            markers += n
            members.append(
                {
                    "ts": str(rec.get("timestamp", "")),
                    "code": str(rec.get("status", rec.get("original", ""))),
                    "host": host,
                    "path": clean,
                    "mimetype": str(rec.get("mimetype", ""))[:60],
                    "is_redirect": bool(rec.get("isredir", False)),
                }
            )
            hosts.append(host)
            # the SURT key carries the same ';jsessionid_…' suffix as the path
            uk, n_uk = redact(str(rec.get("urlkey", "")))
            markers += n_uk
            urlkeys.append(uk)
        out["members"] = members
        out["distinct_hosts"] = sorted(set(h for h in hosts if h))
        out["distinct_host_count"] = len(out["distinct_hosts"])
        out["jsession_markers"] = markers
        out["first_urlkey"] = urlkeys[0] if urlkeys else ""
        out["last_urlkey"] = urlkeys[-1] if urlkeys else ""
        out["ipro_hcp_members"] = [m for m in members if "/ipro/hcp" in m["path"]]
        out["ipro_hcp_count"] = len(out["ipro_hcp_members"])
        return out

    # gateway / error page
    out["shape"] = "error-page"
    out["error_text_head"], n = redact(text[:200])
    out["jsession_markers"] = n
    return out


if __name__ == "__main__":
    body = sys.argv[1]
    seq = sys.argv[2] if len(sys.argv) > 2 else "0"
    try:
        print(json.dumps(project(body)))
    except Exception as exc:  # a projection failure must not lose the request
        print(json.dumps({"shape": "projection-error", "error": str(exc)[:200]}))
