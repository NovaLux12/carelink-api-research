#!/usr/bin/env python3
"""Area M — derive HOST-ONLY facts from a Common Crawl response body.

WHY THIS EXISTS INSTEAD OF A BODY HEAD
--------------------------------------
Every response this pass fetches is either a CDX index-API JSON payload or a
slice of a CC CDX block, and both carry **third-party and vendor URLs in full**,
including URL paths. AGENTS.md section 7 records that CC captures contain live
Java session identifiers embedded in URL paths (and pre-Auth0 authorize URLs
whose sessionData is a plaintext-base64 JWS). A raw head is a raw capture.

So this pass stores **no response text at all**. What it stores per request is:

  * the response byte count and sha256 (so the capture is reproducible), and
  * the *distinct hostnames* the response mentions, plus a record count.

A hostname is the leftmost label of a URL. It cannot carry a path, a query
string or a session parameter, so deriving the host set is a safe projection of
a response that cannot itself be published. The counting rule is here, in code,
rather than in prose (AGENTS.md section 6 item 7).

Two response shapes are handled:

  CDX-JSON  one JSON object per line, carrying a "url" field
  CDX-TEXT  the plain block format, first field is the SURT urlkey
            (e.g. "com,medtronic)/some/path")
  JSON-ARRAY  collinfo.json — one document, a list of crawl objects

`--selftest` proves the projection is falsifiable: it asserts the host
extractor both FIRES on a known-positive control and stays quiet on
false-positive controls, including the two known trap shapes from this repo's
own history (a session parameter in the path, and a parked-wildcard name).
Exit 0 = the projection can be trusted; exit 1 = it cannot, and no finding
built on it should be published.
"""

from __future__ import annotations

import argparse
import json
import re
import sys


def surt_to_host(urlkey: str) -> str | None:
    """`com,medtronic,www)/x` -> `www.medtronic.com`; `com,example)/` -> `example.com`."""
    if ")/" not in urlkey:
        return None
    authority = urlkey.split(")/", 1)[0]
    if not authority:
        return None
    labels = [p for p in authority.split(",") if p not in ("", "port")]
    if not labels:
        return None
    host = ".".join(reversed(labels))
    return host.lower() if re.fullmatch(r"[a-z0-9.\-]+", host.lower()) else None


def host_from_url(url: str) -> str | None:
    m = re.match(r"^[a-z]+://([^/?#]+)", url, re.I)
    if not m:
        return None
    netloc = m.group(1).split("@")[-1].split(":")[0].lower()
    return netloc if re.fullmatch(r"[a-z0-9.\-]+", netloc) else None


def derive(body: str) -> tuple[int | None, list[str], str, int]:
    """Return (record_count, sorted distinct hosts, shape, bytes_read_as_lines).

    `record_count` is `None` for any binary body. A gzip member decoded as
    UTF-8 yields byte-counts that LOOK like line counts — the two ranged CDX
    fetches in this pass recorded 38 112 and 16 284 "records" when the true
    counts were 15 000 and 6 000 — and a reader summing that column would add
    ~54 000 phantom records to a corpus. The field is `None` rather than a wrong
    number, and the byte count it would have been is returned separately so the
    mistake is still visible in the ledger.
    """
    hosts: set[str] = set()
    # ⚠ CORRECTED 2026-10-13 (verifier round 3). This comment previously read:
    #   "a NUL-sniff misses short payloads and would have let this pass's own
    #    two gzip fetches through as text"
    # The second clause was FALSE and is deleted. Every gzip member carries
    # FLG=0x00 at byte offset 3, so a NUL-sniff DOES catch a gzip payload —
    # verified on this pass's own seq 55 body: gzip magic at offset 0, first
    # NUL at index 3, inside the 4096-byte window. The first clause (a NUL
    # sniff misses short payloads) stands.
    #
    # So what does the magic check buy? On the real bodies, nothing — removing
    # the branch entirely leaves --selftest green and every published number
    # unchanged. It earns its place on a different shape, and the (binary, no
    # NUL) control in _selftest is the one that proves it: a payload carrying
    # the magic but no NUL byte is caught by the signature and missed by the
    # sniff. Deleting the magic branch kills that control; that is the claim.
    if body[:2] == "\x1f\x8b" or "\x00" in body[:4096]:
        # Binary (a gzip member, or anything else that is not text). Decompress
        # first and re-derive, so a binary body still yields its real facts.
        try:
            import gzip
            inner = gzip.decompress(body.encode("latin-1")).decode("utf-8", "replace")
        except Exception:
            return None, [], "binary", len(body.splitlines())
        n, h, shape, _ = derive(inner)
        return n, h, shape, len(body.splitlines())
    lines = [ln for ln in body.splitlines() if ln.strip()]

    # collinfo.json — a single JSON array document.
    stripped = body.lstrip()
    if stripped.startswith("["):
        try:
            doc = json.loads(body)
            return len(doc), [], "json-array", 0
        except ValueError:
            pass

    # An nginx/gateway error page is HTML, not records. It must never be
    # counted as captures: a 504 body has seven lines and zero URLs, and
    # reading it as "7 records" would manufacture a positive out of a server
    # failure. Recorded 2026-10-13 after the first absent-host control
    # answered 504 text/html.
    if stripped.lower().startswith(("<!doctype html", "<html")):
        return 0, [], "html-error", 0

    # An index-API "no captures" answer is a plain-text sentence, not JSON.
    if not stripped.startswith(("{", "[")):
        # CDX-TEXT block: first whitespace-separated field is the SURT urlkey.
        for ln in lines:
            key = ln.split(" ", 1)[0].strip()
            if key and key != "N" and key != "-":
                h = surt_to_host(key)
                if h:
                    hosts.add(h)
        if hosts:
            return len(lines), sorted(hosts), "cdx-text", 0
        return len(lines), [], "text", 0

    for ln in lines:
        try:
            obj = json.loads(ln)
        except ValueError:
            continue
        if not isinstance(obj, dict):
            continue
        h = None
        if isinstance(obj.get("url"), str):
            h = host_from_url(obj["url"]) or surt_to_host(obj["url"].split(" ")[0])
        elif isinstance(obj.get("urlkey"), str):
            h = surt_to_host(obj["urlkey"])
        if h:
            hosts.add(h)
    return len(lines), sorted(hosts), "cdx-json", 0


def _selftest() -> int:
    fails: list[str] = []

    # (1) The extractor must FIRE. A selftest that cannot fail is the defect
    # area Y's addendum names, so these positives are asserted first.
    n, hosts, _shape, _b = derive('{"url": "http://example.com/a", "timestamp": "2026"}\n'
                                  '{"url": "https://www.example.org/b"}\n')
    if n != 2 or hosts != ["example.com", "www.example.org"]:
        fails.append(f"positive cdx-json control: got n={n} hosts={hosts}")

    n, hosts, _shape, _b = derive('com,medtronic,www)/a 20260101 text/html 200 SHA - 1234 0 warc\n'
                                  'com,medtronic)/b 20260101 text/html 200 SHA - 1234 0 warc\n')
    if n != 2 or hosts != ["medtronic.com", "www.medtronic.com"]:
        fails.append(f"positive cdx-text control: got n={n} hosts={hosts}")

    if derive('[{"id":"CC-MAIN-2026-39"}]')[0] != 1:
        fails.append("json-array control: expected 1 record")

    # A gateway error page has lines and no URLs. Counting it as records is
    # how a server failure becomes a positive finding.
    n, hosts, shape, _b = derive("<html>\n<head><title>504 Gateway Time-out</title></head>\n"
                             "<body>\n<center><h1>504 Gateway Time-out</h1></center>\n"
                             "<hr><center>nginx/1.31.6</center>\n</body>\n</html>\n")
    if n != 0 or hosts != [] or shape != "html-error":
        fails.append(f"html-error control: got n={n} hosts={hosts} shape={shape}")

    # (2) FALSE-POSITIVE controls. The host projection must not invent hosts,
    # and it must not be fooled by the shapes that have cost this repo time.
    n, hosts, _s, _b = derive('No Captures found for: minimed.eu/*\n')
    if hosts != []:
        fails.append(f"false positive: extracted hosts from a no-captures sentence: {hosts}")

    # A parked-wildcard name from the spaces AGENTS.md section 7 names must
    # still project to a host — that is a fact about the response, not an
    # assertion that the host is real. Recorded so the two are not confused.
    n, hosts, _s, _b = derive('{"url": "http://zz-random-9f2a.carelink.eu/"}\n')
    if hosts != ["zz-random-9f2a.carelink.eu"]:
        fails.append(f"parked-wildcard control did not project its host: {hosts}")

    # A session parameter in the PATH must not survive the projection. The
    # value below is synthetic and is a control, not a capture.
    n, hosts, _s, _b = derive('{"url": "http://wwwp.medtronic.com/a/b;jsessionid_XYZZY=ABCDEF123456/c.html"}\n')
    if hosts != ["wwwp.medtronic.com"]:
        fails.append(f"session-in-path control leaked path material: {hosts}")

    # The projection must be a pure syntactic transformation, not a filter:
    # a host it has never seen, and a single-label one, still project. (The
    # name that used to stand in for "an internal-looking host" was removed —
    # scripts/scrub-patterns.txt scans every diff for that shape, and a
    # *control* that trips the leak scan is not a control, it is a defect.)
    n, hosts, _s, _b = derive('{"url": "http://a-host-nobody-has-seen.example/x"}\n')
    if hosts != ["a-host-nobody-has-seen.example"]:
        fails.append(f"unseen-host control did not project: {hosts}")

    n, hosts, _s, _b = derive('{"url": "http://single-label/x"}\n')
    if hosts != ["single-label"]:
        fails.append(f"single-label control did not project: {hosts}")

    # A BINARY body must never report a record count. This is the defect that
    # made two ranged gzip fetches record 38 112 and 16 284 phantom "records"
    # where the true counts were 15 000 and 6 000 — a reader summing that
    # column would add ~54 000 phantom records to the corpus.
    import gzip as _gz
    _payload = _gz.compress(
        "com,medtronic)/a 20260101 text/html 200 S - 1 0 w\n"
        "com,medtronic)/b 20260101 text/html 200 S - 1 0 w\n".encode())
    _blob = _payload.decode("latin-1")
    n, hosts, shape, binlines = derive(_blob)
    # The count must be the TRUE record count (2), not the phantom byte-line
    # count a UTF-8 decode of the member would produce, and the phantom is
    # quarantined in its own field rather than discarded.
    if n != 2:
        fails.append(f"binary control: count was {n}, expected the true 2 — a "
                     "gzip body is reporting a byte count as a record count")
    if binlines <= 0:
        fails.append("binary control: the phantom byte-line count was not "
                     "recorded separately, so it cannot be told apart from a count")

    # (6) A binary payload with the gzip MAGIC but NO NUL byte in the sniff
    # window. This is the only shape that exercises the signature branch: the
    # NUL-sniff alone misses it. Added 2026-10-13 after verifier round 3
    # established that the magic check bought nothing on the real bodies (a
    # gzip member always has FLG=0x00 at offset 3), which made the previous
    # justification a mechanism claim no test supported. Deleting the magic
    # branch must kill this control.
    _nomagic = "\x1f\x8b" + "\xff" * 64
    n, hosts, shape, _b = derive(_nomagic)
    if shape != "binary":
        fails.append(f"a payload carrying the gzip magic but no NUL byte was "
                     f"classified {shape!r}, not 'binary' — the signature branch "
                     f"is not exercised by anything, so it cannot be justified")

    if fails:
        for f in fails:
            print(f"  !! {f}")
        print("SELFTEST FAIL — the host projection cannot be trusted; "
              "publish nothing built on it.")
        return 1
    print("SELFTEST PASS — the host projection fires on every positive control "
          "and stays quiet on every recorded false-positive control "
          "(the controls are the assertions above; no count is printed here "
          "because a self-test that quotes its own tally drifts when one is "
          "added).")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("body", nargs="?")
    a = ap.parse_args()
    if a.selftest:
        return _selftest()
    if not a.body:
        ap.error("need a body file or --selftest")
    with open(a.body, "rb") as fh:
        raw = fh.read()
    n, hosts, shape, binbytes = derive(raw.decode("latin-1"))
    print(json.dumps({"record_count": n, "distinct_hosts": hosts,
                      "distinct_host_count": len(hosts), "shape": shape,
                      "bytes_read_as_lines": binbytes}))
    return 0


if __name__ == "__main__":
    sys.exit(main())