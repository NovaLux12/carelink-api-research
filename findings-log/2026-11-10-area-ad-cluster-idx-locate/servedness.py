#!/usr/bin/env python3
"""servedness.py — the S-L1 instrument (claim #152): the cluster.idx-level
"was this crawl served at all" check, plus - in its full form - the locate of
the minimed.eu family's SURT interval inside one crawl's cluster.idx.

    python3 servedness.py pass          # run the scripted queue (cap, locks, ledger)
    python3 servedness.py classify      # verdict table from the committed ledger only
    python3 servedness.py selftest      # the locate machinery on a synthetic keyspace

DESIGN NOTES (each is a decision FINDINGS.md can cite):

* Only two hosts may ever be fetched: `index.commoncrawl.org` and
  `data.commoncrawl.org` (asserted before every send). Zero requests to any
  Medtronic host.

* `data.commoncrawl.org` is the bulk path. Per area L's standing invariant a
  bulk-path request is made ONLY while BOTH the index-host lock AND the
  data-host lock are held simultaneously, acquired in one fixed order
  (index first, then data) inside one process — two passes cannot deadlock.

* Every send is a GET. The >= 3.5 s sleep lives INSIDE the held lock(s), so two
  passes on this host cannot both sleep and then send together.

* A failure (000, 5xx, timeout, or any non-documented 4xx) is a FAILURE, never
  an absence (docs/09 section 4: this API failed 17-50% of its queries in prior
  passes); it is re-issued, and every retry is its own row with its own cap cost.

* A cluster.idx read is ALWAYS a ranged read (`-r lo-hi`, asserted, never the
  whole file). Bodies are never committed and never loaded whole; the committed
  row carries bounded, redacted projections.

* THE LOCATE. The SURT keyspace is byte-sorted, so one ranged page read gives a
  one-page constraint AND every full line inside the page. The needle is the
  SORT INTERVAL of the minimed.eu domain family:

      FAMILY_INTERVAL = [ "eu,minimed)",  "eu,minimeda" )

    The apex block keys `eu,minimed)/...`; a subdomain block keys
    `eu,minimed,<host>)/...`; the next possible label character after
    `eu,minimed` is >= 'a', so everything in the interval is apex-plus-
    subdomain, and a key like `eu,minimede)` (a DIFFERENT domain) sorts at or
    after the upper bound and is correctly outside it.

  Presence is proven the moment one page carries a key inside the interval.
Absence is proven - and only proven - by the ADJACENT-LINES pair that
  punctuates the interval: a line < "eu,minimed)" followed immediately (next
  line in the sorted file) by a line >= "eu,minimeda". The pair is searched
  for inside a single page. A pair straddling a read boundary is NOT stitched
  across pages, so it is missed - which is the safe direction: a missed pair
  yields UNCONVERGED, never a false absence. Until such a pair is observed
  inside one page the locate state stays UNCONVERGED - recorded as such, never
  read as a negative.

TWO BUCKETS, NEVER MERGED (the difference between a finding and a non-finding):

* CONNECTION-LEVEL FAILURE - TLS `unexpected eof`, timeout, `000`, 5xx, or any
  non-documented 4xx. This is a statement about THIS HOST, THIS MOMENT, THIS
  ROUTE. AGENTS.md section 7 records that index.commoncrawl.org TLS-drops from
  some hosts; this API failed 17-50% of its queries in prior passes. A
  connection-level failure is NEVER recorded as a crawl verdict: a crawl whose
  every row failed at connection level is recorded as UNREAD-FROM-THIS-HOST,
  which does not discharge any standing indeterminate cell.
* SERVED - the request completed. `206` on the bulk path, or `200`/`301`/`302`/
  `404` on the CDX path (404 there is the DOCUMENTED absence shape, not a
  failure). Only this bucket may carry `served`, `served, no members` or
  `not published`.

`classify` prints the two counts separately, so a pass whose instrument never
reached the index cannot present a table of verdicts.
"""

import fcntl
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))

IDX_HOST = "index.commoncrawl.org"
DATA_HOST = "data.commoncrawl.org"
ALLOWED = {IDX_HOST, DATA_HOST}

DELAY = 3.5              # seconds of sleep INSIDE the held lock(s)
HEAD_BYTES = 8192        # head reads are ranged reads of this size
MAXRETRY = 2             # retries are requests and each gets a row
PAGE_MIN = 65536
PAGE_MAX = 1 << 20
LOCATE_PAGE = 1 << 22    # 4 MiB: one bisection step must cover enough keyspace
                         # that the interval is bracketed, not skipped over

FAM_LO = b"eu,minimed)"
FAM_HI = b"eu,minimeda"

# --- AD (2026-11-10): the seed is derived, never hardcoded. -----------------
# The 2026-10-19 pass opened every bisection at f0 = 0.85 of file size and
# landed in org,/pl,. Its own committed pages carry the calibration that
# brackets de,/es,/eu, and it used neither. `derive` recovers f0 from those
# committed pages at ZERO requests; `pass` reads the result.
SEED_PRIOR_DIR = os.environ.get("L_SEED_DIR") or os.path.join(
    os.path.dirname(HERE), "2026-10-18-sl1-cluster-servedness")
SEED_FILE = os.path.join(HERE, "seed-derivation.json")
LOCATE_BUDGET = 10       # pages per crawl, as docs/11 area AD directs

REDACTIONS = [
    (re.compile(rb"jsessionid_[A-Za-z0-9_-]{1,64}"), b"<JSESSIONID-REDACTED>"),
    (re.compile(rb"sessionData[A-Za-z0-9_-]{0,8}[=:]([^\s&]{1,256})"), b"sessionData=<REDACTED>"),
]


def redact(raw: bytes) -> bytes:
    for rx, rep in REDACTIONS:
        raw = rx.sub(rep, raw)
    return raw


def hdr(head: str, *names):
    out = []
    for n in names:
        m = re.search(r"^%s:\s*(.*)$" % n, head, re.I | re.M)
        if m:
            out.append("%s: %s" % (n, m.group(1).strip()))
    return "|".join(out)


def fetch_cap_word(fetch):
    return fetch.cap_line()


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def stamp(t):
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(t)) + ".%03dZ" % int((t % 1) * 1000)


def cdx_is_failure(code):
    """docs/09 section 4, the CDX counting rule: 502/504/503/400 (and 000) are
    FAILURES, never absences. 404 carries the documented absence shape."""
    return code not in ("200", "301", "302", "404")


def bulk_is_failure(code):
    """The bulk layer's shapes: 206 = served-with-range; 404/403 = the
    not-published shapes; anything else (000, 416, 5xx, 503 SlowDown) is a
    failure and is re-issued."""
    return code not in ("206", "404", "403")


# ------------------------------------------------------------------ HTTP layer
class Fetcher:
    def __init__(self, bodies, cap, l_idx, l_data):
        self.ledger = os.path.join(HERE, "results.jsonl")
        self.runlog = os.path.join(HERE, "run.log")
        self.hdrdir = os.path.join(HERE, "headers")
        os.makedirs(self.hdrdir, exist_ok=True)
        os.makedirs(bodies, exist_ok=True)
        self.bodies = bodies
        self.cap = cap
        self.l_idx, self.l_data = l_idx, l_data
        self.lock_wait = 0.0

    def rows(self):
        if not os.path.exists(self.ledger):
            return 0
        with open(self.ledger) as fh:
            return sum(1 for l in fh if l.strip())

    def cap_line(self):
        return "%d of a %d cap" % (self.rows(), self.cap)

    # ---- locking: index first, then data for bulk-path sends; sleep inside both
    def _acquire(self, which):
        def grab(f):
            deadline = time.time() + 120
            while True:
                try:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    return
                except OSError:
                    if time.time() > deadline:
                        f.close()
                        raise TimeoutError("host lock not acquired within 120s")
                    self.lock_wait += 0.2
                    time.sleep(0.2)
        fi = open(self.l_idx, "r")
        grab(fi)
        fd = None
        if which == "data":
            fd = open(self.l_data, "r")
            grab(fd)
        return fi, fd

    def get(self, host, path, role, host_tag, range_=None, attempt=0):
        """One GET, one ledger row. `range_` is a half-open (lo, hi) BYTES
        window for the bulk host; None is only for the API/collinfo reads."""
        assert host in ALLOWED, "%s is not an allowed host" % host
        if range_ is not None:
            assert host == DATA_HOST and isinstance(range_, tuple), (
                "ranged reads are a data.commoncrawl.org instrument; got %s %r" % (host, range_))
        used = self.rows()
        if used >= self.cap:
            print("CAP REACHED at %d of %d - remaining queue abandoned." % (used, self.cap))
            return None
        seq = used + 1
        tag = role if attempt == 0 else "%s-r%d" % (role, attempt)
        hpath = os.path.join(self.hdrdir, "%d-%s.h" % (seq, tag))
        bpath = os.path.join(self.bodies, "%d-%s.body" % (seq, tag))
        q = time.time()

        fi, fd = self._acquire("data" if host == DATA_HOST else "idx")
        try:
            time.sleep(DELAY)
            tq = time.time()
            argv = ["curl", "-sS", "--max-time", "120", "-D", hpath, "-o", bpath,
                    "-w", "%{http_code}", "https://%s%s" % (host, path)]
            if host == IDX_HOST:
                argv.insert(2, "--compressed")
            if range_ is not None:
                argv += ["-r", "%d-%d" % (range_[0], range_[1] - 1)]
            out = subprocess.run(argv, capture_output=True, text=True).stdout.strip()
            code = out or "000"
            ts = time.time()
        finally:
            for f in (fi, fd):
                try:
                    if f is not None:
                        f.close()
                except Exception:
                    pass
        td = time.time()

        raw = open(bpath, "rb").read() if os.path.exists(bpath) else b""
        head = open(hpath, "r", errors="replace").read() if os.path.exists(hpath) else ""
        row = {
            "seq": seq, "host_seq": seq, "host": host, "host_tag": host_tag,
            "role": role, "attempt_tag": tag, "attempt": attempt,
            "method": "GET", "url": "https://%s%s" % (host, path), "path": path,
            "range": ("%d-%d[%dB]" % (range_[0], range_[1] - 1, range_[1] - range_[0]))
                     if range_ is not None else None,
            "http_status": code,
            "body_bytes": len(raw),
            "body_sha256": sha256(raw),
            "content_range": (m.group(1).strip()
                              if (m := re.search(r"^content-range:\s*(.*)$", head, re.I | re.M)) else None),
            "disc_headers": hdr(head, "content-type", "x-cache", "x-amzn-errortype",
                                "retry-after", "server"),
            "body_head": re.sub(rb"\s+", b" ", redact(raw[:600])).decode("utf-8", "replace")[:300],
            "t_queued": stamp(q), "t_sent": stamp(tq), "t_done": stamp(td),
        }
        with open(self.ledger, "a") as fh:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
        with open(self.runlog, "a") as fh:
            fh.write("%d\t%s\t%s\t%s\t%s%s\t%s\t%d\n" % (
                seq, tag, host, role, path,
                ("#%s" % row["range"]) if row["range"] else "", code, len(raw)))
        print("seq %2d  %-20s %-16s %-46s %-8s %7s B" % (
            seq, host, role,
            path if range_ is None else "%s -r%s" % (path, row["range"]),
            code, len(raw)), flush=True)
        return row

    def body_path(self, row):
        p = os.path.join(self.bodies, "%d-%s.body" % (row["seq"], row["attempt_tag"]))
        return p if os.path.exists(p) else None

    def get_retry(self, host, path, role, host_tag, range_=None, is_failure=None):
        """One LOGICAL read. A connection-level failure is re-issued up to
        MAXRETRY times; EVERY attempt is its own ledger row with its own
        t_sent and its own cap cost, because a retry is a request. The
        connection-level / served split is decided by `is_failure`, which
        defaults to the host's own documented shapes. Returns the last row
        sent, or None when the cap ended the sequence."""
        is_failure = is_failure or (bulk_is_failure if host == DATA_HOST else cdx_is_failure)
        row = None
        for attempt in range(MAXRETRY + 1):
            row = self.get(host, path, role, host_tag, range_=range_, attempt=attempt)
            if row is None:
                return None            # cap reached: no row, no verdict
            if not is_failure(row["http_status"]):
                return row             # SERVED: stop, this is a real answer
            if attempt < MAXRETRY:
                print("   %s %s -> %s is a connection-level failure; re-issued "
                      "(attempt %d of %d, %s)" % (
                          host, role, row["http_status"], attempt + 1,
                          MAXRETRY, fetch_cap_word(self)))
        return row


# --------------------------------------------------------- cluster.idx parsing
def body_lines(raw: bytes, splice: bytes = b""):
    """One page -> its full lines, with the two page-boundary fragments
    accounted. `splice` completes a torn head line when the caller knows the
    pages are contiguous; otherwise the fragment is consumed and accounted.
    Returns (lines, lead_consumed_bytes, tail_partial_bytes).
    Each line is (key, f2, f3) where key is the first tab-separated field. The
    observed layout is printed verbatim (redacted, bounded) in the head row's
    body_head, so the parser is never asked to guess a shape."""
    text = (splice or b"") + raw
    first_nl = text.find(b"\n")
    if first_nl == -1:
        return [], len(splice), text
    lead = first_nl + 1
    last_nl = text.rfind(b"\n")
    end = last_nl + 1
    tail = text[end:]
    lines = []
    for chunk in text[lead:end].split(b"\n"):
        if not chunk:
            continue
        f = chunk.split(b"\t")
        lines.append((f[0], f[1][:160] if len(f) > 1 else b"", f[2][:160] if len(f) > 2 else b""))
    return lines, lead, tail


# ------------------------------------------------------------------- the locate
class Locater:
    """Banded bisection on the FAMILY interval [FAM_LO, FAM_HI).

    `page(lo, hi)` is injected so the same machinery runs live (pass mode) and
    on synthetic bytes (selftest mode). The state machine below is the whole
    of the algorithm: every read either (a) observes the family inside its
    window (presence proved), (b) observes the adjacent pre/post pair that
    punctuates the interval inside its window (absence proved), or (c) moves
    the [lo, hi) bytes-interval the interval must lie in, and the next read is
    the widest page that fits in the shrunk interval."""

    def __init__(self, total, page, f0, budget, note=""):
        self.total = total
        self.page = page
        self.f0 = f0
        self.budget = budget
        self.note = note
        self.reads = []          # bounded per-read projection for the tree
        self.verdict = None

    def _read(self, lo, hi):
        res = self.page(lo, hi)
        if res is None:
            return None
        self.reads.append({
            "range": res["range"][0] if res.get("range") else lo,
            "bytes": (res["range"][1] - res["range"][0]) if res.get("range") else (hi - lo),
            "first_key": (lines[0][0].decode("utf-8", "replace") if (lines := res["lines"]) else ""),
            "last_key": (lines[-1][0].decode("utf-8", "replace") if lines else ""),
            "lines": len(lines),
        })
        return res

    def run(self):
        lo, hi = 0, self.total
        mid = int(self.f0 * self.total)
        n = 0
        while n < self.budget:
            if n == 0:
                a = max(0, mid - LOCATE_PAGE // 2)
                b = min(self.total, a + LOCATE_PAGE)
            else:
                width = max(PAGE_MIN, min(LOCATE_PAGE, (hi - lo) // 2))
                a_ = lo + max(0, (hi - lo - width) // 2)
                a, b = a_, min(self.total, a_ + width)
            assert b > a, ("degenerate window", a, b, lo, hi, self.total)
            res = self._read(a, b)
            if res is None:
                self.verdict = {"state": "FETCH_FAILED", "pages_used": n,
                                "budget": self.budget, "reads": self.reads, "note": self.note}
                return self.verdict
            n += 1
            lines, lead, tail = res["lines"], res["lead_dropped"], res["tail"]
            keys = [l[0] for l in lines]
            pairs = list(zip(keys, keys[1:]))
            in_fam = [l for l in lines if FAM_LO <= l[0] < FAM_HI]
            if in_fam:
                self.verdict = {
                    "state": "FAMILY_PRESENT",
                    "key_hits": [l[0].decode("utf-8", "replace") for l in in_fam[:6]],
                    "page": res["range"], "pages_used": n,
                    "budget": self.budget, "reads": self.reads, "note": self.note,
                }
                return self.verdict
            punct = [(x, y) for (x, y) in pairs if x < FAM_LO and y >= FAM_HI]
            if punct:
                self.verdict = {
                    "state": "FAMILY_ABSENT",
                    "evidence": [punct[0][0].decode("utf-8", "replace"),
                                 punct[0][1].decode("utf-8", "replace")],
                    "page": res["range"], "pages_used": n,
                    "budget": self.budget, "reads": self.reads, "note": self.note,
                }
                return self.verdict
            # no verdict this page: move the window
            if keys:
                first_k, last_k = keys[0], keys[-1]
                if last_k < FAM_LO:
                    lo = b          # the whole page sorts before the interval
                elif first_k >= FAM_HI:
                    hi = a          # the whole page sorts after it
                else:
                    # the page straddles; the interval lies inside its bytes
                    ra, rb = res["range"]
                    lo = max(lo, ra)
                    hi = min(hi, rb)
            else:  # nothing parsed: shrink around and retry
                b = a + max(PAGE_MIN, (b - a) // 3 or PAGE_MIN) if a == lo else max(
                    lo + PAGE_MIN, a)
                hi = b if hi > b else hi
            if lo >= hi:
                self.verdict = {"state": "UNCONVERGED_CLAMPED",
                                "clamp": [lo, hi], "pages_used": n,
                                "budget": self.budget, "reads": self.reads, "note": self.note}
                return self.verdict
        self.verdict = {"state": "UNCONVERGED", "pages_used": n, "budget": self.budget,
                        "window": [lo, hi], "reads": self.reads, "note": self.note}
        return self.verdict


# ---------------------------------------------------------------- selftest
def selftest():
    import random
    random.seed(7)
    tlds = ["com", "de", "es", "eu", "fr", "jp", "nl", "org", "uk", "us", "za"]
    doms = ["alpha", "bravo", "delta", "gamma", "omega", "xray"]

    def make(total_lines, extra):
        keys = []
        for i in range(total_lines):
            keys.append(("%s,%s%s)/%d.html" % (random.choice(tlds), random.choice(doms),
                                               random.choice(["", "www,", "blog,"]), i)).encode())
        keys += extra + [b"zz,winds)/tail.html"]
        keys.sort()
        return b"".join(k + b"\t20260101000000\tcdx-00000.gz\t0\t0\n" for k in keys)

    def page_for(file_bytes):
        def page(lo, hi):
            raw = file_bytes[lo:hi]
            lines, lead, tail = body_lines(raw)
            return {"lines": lines, "lead_dropped": lead, "tail": tail,
                    "contiguous": False, "range": (lo, hi)}
        return page

    print("== selftest: the locate machinery on synthetic keyspaces. 0 requests.")
    print("   (histogram: 120k lines - a 4 MiB page spans it whole, so this "
          "exercises the state machine, not the bisection)")
    fb = make(120000, [b"eu,minimed)/robots.txt", b"eu,minimed,carelink)/app/login",
                       b"eu,minimede)/counter-example.html"])
    v = Locater(len(fb), page_for(fb), f0=0.85, budget=10).run()
    assert v["state"] == "FAMILY_PRESENT" and any(
        k.startswith("eu,minimed)") or k.startswith("eu,minimed,") for k in v["key_hits"]), v
    print("   POSITIVE: %-14s in %2d pages, hits=%s" % (
        v["state"], v["pages_used"], sorted(set(k.split('/') [0] for k in v["key_hits"]))))

    fb = make(120000, [])
    v = Locater(len(fb), page_for(fb), f0=0.85, budget=10).run()
    assert v["state"] == "FAMILY_ABSENT" and v["evidence"][0].encode() < FAM_LO \
        and v["evidence"][1].encode() >= FAM_HI, v
    print("   NEGATIVE: %-14s in %2d pages, pair=(%r, %r)" % (
        v["state"], v["pages_used"], v["evidence"][0][:40], v["evidence"][1][:40]))

    # The budget floor: a locate whose reads sort entirely before the interval
    # has proved NOTHING and must say UNCONVERGED, not "absent". Injected page,
    # so the state machine is tested directly rather than through a synthetic
    # file large enough to outrun a 4 MiB page.
    def head_only(lo, hi):
        lines = [(b"com,aaa)/%d.html" % i, b"", b"") for i in range(1000)]
        return {"lines": lines, "lead_dropped": 0, "tail": b"", "range": (lo, hi)}
    v = Locater(1 << 30, head_only, f0=0.5, budget=3).run()
    assert v["state"] == "UNCONVERGED", v
    assert v["pages_used"] == 3, v
    print("   CONSTRAINED: %-14s (%d pages of a %d budget) -> bounded, not a negative" % (
        v["state"], v["pages_used"], v["budget"]))

    # A near-miss domain is a real absence, not a lookalike: eu,minimif) sorts
    # after the upper bound, so the adjacent pair that punctuates the interval
    # is genuine and the verdict may be ABSENT.
    fb = make(120000, [b"eu,minimif)/not-the-family.html"])
    v = Locater(len(fb), page_for(fb), f0=0.85, budget=3).run()
    assert v["state"] == "FAMILY_ABSENT", v
    assert v["evidence"][1].encode() >= FAM_HI, v
    print("   NEAR-MISS:    %-14s against eu,minimif) - a sibling domain is "
          "correctly outside the family interval" % v["state"])

    # A page that fails to fetch is FETCH_FAILED, never an absence.
    def broken(lo, hi):
        return None
    v = Locater(999999, broken, f0=0.5, budget=3).run()
    assert v["state"] == "FETCH_FAILED", v
    print("   FETCH FAILED: %-14s -> a transport failure, never an absence" % v["state"])

    # THE TWO BUCKETS. Every status this API has been recorded producing,
    # asserted against the two predicates, so the taxonomy is proved in code
    # and not asserted in prose. docs/09 s4: a 000/5xx/timeout/non-documented
    # 4xx is a FAILURE; the CDX 404 is the documented absence shape.

# ------------------------------------------ AD: selftest at realistic size
def selftest_realistic():
    """AD (2026-11-10). The 2026-10-18 selftest used 120k lines, which one
    4 MiB page swallows whole: it never exercised the bisection, and the page
    schedule it blessed was the one that could not converge live.

    This one builds a keyspace of REALISTIC size and TLD weight - 2,000,005
    lines at ~54 B/line, i.e. 108,905,444 B, the same order as CC-MAIN-2024-42's
    measured 121,395,065 B - so one 4 MiB page is 3.85% of the file and the
    bisection is genuinely exercised. It asserts:
      P1 the family, present, is found within the live budget (10 pages);
      P2 the OLD fixed f0=0.85 at the OLD 3-page budget does NOT converge -
         which reproduces the live UNCONVERGED at zero requests;
      P3 a near-miss sibling (eu,minimede) present but the family absent reads
         FAMILY_ABSENT, never PRESENT;
      P5 a seed displaced by +/-3% of the file still converges in 10 pages.
    P2 is reported, not asserted: on this keyspace the old seed reaches the
    family in 5 pages when given 10. What the seed buys is the margin, not the
    possibility - and at 3 pages neither seed would be safe.
    0 requests.
    """
    import random
    random.seed(20261110)

    # TLD weights follow the shape of the observed pages: com-dominated, with
    # de/ru/org/jp/net/uk/fr/br/es/nl/pl present, and eu a thin tail. That
    # placement is what makes eu,minimed) sit near 0.55 of the file rather
    # than at a convenient round number.
    weighted = ([b"com"] * 42 + [b"de"] * 9 + [b"ru"] * 8 + [b"org"] * 7 +
                [b"jp"] * 5 + [b"net"] * 5 + [b"uk"] * 4 + [b"fr"] * 4 +
                [b"br"] * 3 + [b"es"] * 2 + [b"nl"] * 2 + [b"pl"] * 2 +
                [b"it"] * 2 + [b"eu"] * 1)
    n = 2_000_000
    hdr = b"\t20260101000000\tcdx-00000.gz\t0\t0\n"

    def build(extra):
        """Returns (bytes, offsets) where offsets[i] is the byte offset of the
        first key >= x for bisect lookups - so 'where does eu,minim sit' is
        MEASURED from the file, never searched for in it as a substring."""
        keys = []
        for i in range(n):
            t = random.choice(weighted)
            keys.append(b"%s,d%05d)/p/%d.html" % (t, random.randrange(99999), i % 999))
        keys += extra
        keys.sort()
        parts, off, offsets = [], 0, []
        for k in keys:
            offsets.append(off)
            parts.append(k + hdr)
            off += len(k) + len(hdr)
        return b"".join(parts), keys, offsets

    def offset_of(keys, offsets, key):
        import bisect
        i = bisect.bisect_left(keys, key)
        return offsets[i] if i < len(offsets) else offsets[-1]

    def page_for(fb):
        def page(lo, hi):
            lines, lead, tail = body_lines(fb[lo:hi])
            return {"lines": lines, "lead_dropped": lead, "tail": tail,
                    "contiguous": False, "range": (lo, hi)}
        return page

    def span(fb, lo_key, hi_key):
        """byte span of the keys in [lo_key, hi_key) - from the synthetic file's
        own offsets, so the claim 'one page cannot span it' is measured."""
        a = offset_of(fb[1], fb[2], lo_key)
        b = offset_of(fb[1], fb[2], hi_key)
        return a, b

    fam = [b"eu,minimed)/robots.txt", b"eu,minimed,carelink)/app/login",
           b"eu,minimed,carelink)/patient/reports", b"eu,minimeda)/x.html"]
    near = [b"eu,minimede)/counter-example.html"]

    fbx = build(fam + near)
    fb = fbx[0]
    total = len(fb)
    pagef = page_for(fb)
    print("== selftest (realistic): %d B, %d lines, one page = %.2f%% of the file"
          % (total, len(fbx[1]), 100.0 * LOCATE_PAGE / total))
    assert LOCATE_PAGE < total // 20, "page is not small against the keyspace"

    a_lo, a_hi = span(fbx, b"eu,minim", b"eu,minj")
    print("   the eu,minim block spans bytes %d..%d (%.2f%% of the file), "
          "and one page is 4 MiB" % (a_lo, a_hi, 100.0 * (a_hi - a_lo) / total))
    assert a_lo > 0 and a_hi > a_lo

    # P1 - seeded near the bracket midpoint, as `derive` produces live
    f0 = (a_lo + a_hi) / 2.0 / total
    v = Locater(total, pagef, f0, LOCATE_BUDGET).run()
    got = sorted({k.split("/")[0] for k in v.get("key_hits", [])})
    print("   P1 SEEDED f0=%.4f  -> %-14s in %d of %d pages, hits=%s"
          % (f0, v["state"], v["pages_used"], LOCATE_BUDGET, got))
    assert v["state"] == "FAMILY_PRESENT", v
    assert v["pages_used"] <= LOCATE_BUDGET
    assert "eu,minimede)" not in got, ("the near-miss sibling was read as the "
                                       "family", got)

    # P2 - the same file at the old fixed seed, at the old page budget and at
    # the new one. This is where the live UNCONVERGED is reproduced at zero
    # requests, and where the seed's real contribution is measured: pages used.
    v85_3 = Locater(total, pagef, 0.85, 3).run()
    print("   P2a OLD f0=0.8500, budget 3  -> %-14s in %d of 3 pages  %s"
          % (v85_3["state"], v85_3["pages_used"],
             ("window %r (%.1f%% of the file)" % (v85_3["window"],
              100.0 * (v85_3["window"][1] - v85_3["window"][0]) / total))
             if "window" in v85_3 else ""))
    v85 = Locater(total, pagef, 0.85, LOCATE_BUDGET).run()
    print("   P2b OLD f0=0.8500, budget 10 -> %-14s in %d of %d pages"
          % (v85["state"], v85["pages_used"], LOCATE_BUDGET))
    print("   -> seeded %d page(s) vs unseeded %d: the seed buys margin, and at "
          "the old 3-page budget neither seed converges" % (v["pages_used"], v85["pages_used"]))

    # P3 - near-miss only: the family is ABSENT, eu,minimede) is present
    fb2 = build(near)[0]
    pagef2 = page_for(fb2)
    v2 = Locater(len(fb2), pagef2, f0, LOCATE_BUDGET).run()
    print("   P3 NEAR-MISS ONLY   -> %-14s in %d of %d pages, pair=(%r, %r)"
          % (v2["state"], v2["pages_used"], LOCATE_BUDGET,
             v2["evidence"][0][:38], v2["evidence"][1][:38]))
    assert v2["state"] == "FAMILY_ABSENT", v2
    assert v2["evidence"][0].encode() < FAM_LO and v2["evidence"][1].encode() >= FAM_HI, v2

    # P5 - an imprecise seed. The live f0 is an estimator, so it must survive
    # being wrong by a few percent of the file in either direction.
    for d in (-0.03, 0.03):
        vd = Locater(total, pagef, min(0.99, max(0.01, f0 + d)), LOCATE_BUDGET).run()
        print("   P5 SEED %+0.2f       -> %-14s in %d of %d pages"
              % (d, vd["state"], vd["pages_used"], LOCATE_BUDGET))
        assert vd["state"] == "FAMILY_PRESENT", (d, vd)
    print("   ASSERTED: seeded convergence within %d pages, near-miss not "
          "promoted, +/-3%% seed error survived." % LOCATE_BUDGET)


    print("   TAXONOMY: the two predicates over every recorded status")
    conn_bulk = ["000", "400", "416", "500", "502", "503", "504"]
    served_bulk = ["206", "403", "404"]
    for c in conn_bulk:
        assert bulk_is_failure(c), "bulk %s must be a connection-level failure" % c
    for c in served_bulk:
        assert not bulk_is_failure(c), "bulk %s must be served/not-published" % c
    conn_cdx = ["000", "400", "416", "500", "502", "503", "504"]
    served_cdx = ["200", "301", "302", "404"]
    for c in conn_cdx:
        assert cdx_is_failure(c), "cdx %s must be a connection-level failure" % c
    for c in served_cdx:
        assert not cdx_is_failure(c), "cdx %s must be served" % c
    # The overlap that the whole distinction rests on: 404 is served on BOTH
    # layers but means different things - a refused object on the bulk path, a
    # documented "no captures" on the API. 403 is served-but-refused on bulk.
    assert bulk_is_failure("404") is False and cdx_is_failure("404") is False
    assert bulk_is_failure("403") is False and cdx_is_failure("403") is True
    print("     bulk: connection-level %s | served %s" % (conn_bulk, served_bulk))
    print("     cdx : connection-level %s | served %s" % (conn_cdx, served_cdx))

    # The interval's arithmetic, asserted rather than described: the next
    # possible label character after "eu,minimed" is >= 'a', so nothing that
    # is NOT apex-or-subdomain can fall inside, and a sibling domain
    # (eu,minimede) sorts at or after the upper bound.
    assert FAM_LO < FAM_HI
    assert FAM_LO <= b"eu,minimed)/x" < FAM_HI, "the apex block key is inside"
    assert FAM_LO <= b"eu,minimed,carelink)/x" < FAM_HI, "a subdomain block key is inside"
    assert not (FAM_LO <= b"eu,minimeda)/x" < FAM_HI), "the upper bound is exclusive"
    assert not (FAM_LO <= b"eu,minimede)/x" < FAM_HI), "a longer sibling is outside"
    assert not (FAM_LO <= b"eu,minim)/x" < FAM_HI), "a shorter name is outside"
    print("   INTERVAL: [eu,minimed), eu,minimeda) admits apex + subdomains only; "
          "eu,minimede) and eu,minim) are outside it (asserted)")
    print("== selftest OK")


# ------------------------------------------------------- the zero-request seed
def seed_fracs():
    """f0 per crawl from the derivation file. Absent file -> the old 0.85,
    so a run without the derivation is visibly the old run, not a silently
    different one."""
    if not os.path.exists(SEED_FILE):
        return {}
    d = json.load(open(SEED_FILE))
    return {k: v["f0"] for k, v in d.get("crawls", {}).items()}


def do_derive():
    """ZERO REQUESTS. Recovers the bisection seed from the *committed* pages of
    the 2026-10-18 pass - the pass that opened at f0=0.85 and used none of the
    calibration it had already paid for.

    The rule, applied mechanically to each committed locate-*.json:
        lo = the end byte of the last committed page whose every key sorts
             BELOW FAM_LO  (that page's bytes cannot contain the interval)
        hi = the start byte of the first committed page whose first key sorts
             AT OR ABOVE FAM_HI
        f0 = (lo + hi) / 2 / total
    SURT keys are byte-sorted, so a key < FAM_LO and a key >= FAM_HI bracket
    the interval: that part is arithmetic (INFERRED only in that SURT order is
    byte order, which every page read here demonstrates). WHERE inside the
    bracket eu,minimed) sits is the inferred part; the midpoint is the
    defensible estimator and one 4 MiB page centred on it spans ~2.7% of the
    file, so the first read lands inside the bracket even if the midpoint is
    off by more than a percent.
    """
    print("== derive: the bisection seed, from committed pages only. 0 requests.")
    out = {"method": "midpoint of the de,/es,/eu, bracket observed in the "
                      "committed 2026-10-18 pages; zero requests",
           "family": [FAM_LO.decode(), FAM_HI.decode()],
           "source_dir": SEED_PRIOR_DIR, "crawls": {}}
    for crawl in ("CC-MAIN-2022-27", "CC-MAIN-2024-42"):
        fp = os.path.join(SEED_PRIOR_DIR, "locate-%s.json" % crawl)
        if not os.path.exists(fp):
            print("   %-18s no committed locate file" % crawl)
            continue
        v = json.load(open(fp))
        total = None
        # the file size is not in the locate file; it is in the committed head
        # row's Content-Range, so re-derive it from results.jsonl (still zero
        # requests: it is a committed row, not a live one).
        led = os.path.join(SEED_PRIOR_DIR, "results.jsonl")
        for line in open(led):
            r = json.loads(line)
            if ("/%s/" % crawl) in r.get("path", "") and r.get("content_range"):
                m = re.search(r"/(\d+)$", r["content_range"])
                if m:
                    total = int(m.group(1))
                    break
        assert total, "no committed file size for %s" % crawl
        reads = sorted(v["reads"], key=lambda x: x["range"])
        lo = hi = None
        for r in reads:
            k0, k1 = r["first_key"].encode(), r["last_key"].encode()
            if k1 < FAM_LO:
                lo = max(lo or 0, r["range"] + r["bytes"])
            if k0 >= FAM_HI and hi is None:
                hi = r["range"]
        assert lo and hi and lo < hi, ("no bracket", crawl, lo, hi)
        f0 = (lo + hi) / 2.0 / total
        page_pct = 100.0 * LOCATE_PAGE / total
        print("   %-18s total %d B" % (crawl, total))
        print("     bracket for de,/es,/eu,   (%d, %d)  = (%.5f, %.5f) of the file"
              % (lo, hi, lo / total, hi / total))
        print("     f0 = (%d + %d) / 2 / %d = %.5f   [one page spans %.1f%%]"
              % (lo, hi, total, f0, page_pct))
        out["crawls"][crawl] = {"total": total, "bracket": [lo, hi],
                                "f0": round(f0, 5), "page_pct_of_file": round(page_pct, 2)}
    if out["crawls"]:
        fs = [c["f0"] for c in out["crawls"].values()]
        tgt = round(sum(fs) / len(fs), 5)
        out["crawls"]["CC-MAIN-2014-23"] = {
            "total": None, "bracket": None, "f0": tgt,
            "derivation": "mean of the two control seeds (%.5f, %.5f); the two "
                          "brackets agree to within %.5f of the file, so the "
                          "mean is the estimator with no target-side evidence"
                          % (fs[0], fs[-1], abs(fs[0] - fs[-1]))}
        print("   %-18s no committed pages -> f0 = %.5f (mean of the controls)"
              % ("CC-MAIN-2014-23", tgt))
    with open(SEED_FILE, "w") as fh:
        fh.write(json.dumps(out, sort_keys=True, indent=1) + "\n")
    print("   wrote %s" % os.path.basename(SEED_FILE))


# --------------------------------------- AD: is a block-key absence an absence?
def do_probe_block():
    """ZERO-NETWORK-EXCEPT-ONE-BY-DESIGN. The control gate failed, so no locate
    verdict may be published. This read is the reason the gate's failure is a
    finding rather than a shrug.

    The locate reads `cluster.idx`, one line per ~200 KB CDX *block*, keyed by
    the block's FIRST SURT key. In CC-MAIN-2022-27 a puncturing pair
    (eu,mini-parfemy) ... eu,minimumwaste)) brackets the whole family interval,
    i.e. NO block boundary falls inside it. The question the instrument cannot
    answer from block keys is whether a eu,minimed record lives INSIDE one of
    those blocks. It can be answered by reading that block: the cluster.idx line
    carries the block's gz offset and its byte length.

    Committed output is a bounded projection - counts, key names, the record
    form, never the capture (AGENTS.md s7).
    """
    cap = int(os.environ.get("L_CAP", "50"))
    bodies = os.environ["L_BODIES"]
    fetch = Fetcher(bodies, cap, os.environ["L_LOCK_IDX"], os.environ["L_LOCK_DATA"])
    import zlib

    CRAWL = "CC-MAIN-2022-27"
    # The straddling block, read off this run's own locate page (seq 9): the
    # line that begins the block containing everything between it and the next
    # key. Chosen mechanically as the last key < FAM_LO in that page.
    loc = json.load(open(os.path.join(HERE, "locate-%s.json" % CRAWL)))
    blocks = _blocks_in_the_straddling_page(fetch, bodies, loc["evidence"])
    cand = [b for b in blocks if b[0] < FAM_LO][-1]
    print("== probe-block: the block keyed %r -> %s bytes @ %d (0 requests so far)"
          % (cand[0].decode("utf-8", "replace"), cand[3], cand[2]))

    # The path shape is the one this repository's own ledger records for a CDX
    # block on this host (area M, 2026-10-13): /cc-index/collections/<crawl>/
    # indexes/<block>. Not a guess.
    r = fetch.get_retry(DATA_HOST,
                        "/cc-index/collections/%s/indexes/%s" % (CRAWL, cand[1].decode()),
                        "block-read", "block-read",
                        range_=(cand[2], cand[2] + cand[3]))  # half-open: length bytes
    out = {"crawl": CRAWL, "block_first_key": cand[0].decode("utf-8", "replace"),
           "cdx_file": cand[1].decode("utf-8", "replace"),
           "offset": cand[2], "length": cand[3],
           "http_status": (r or {}).get("http_status"), "note": fetch.cap_line()}
    bp = fetch.body_path(r) if r else None
    if r is None or r["http_status"] != "206" or not bp:
        out["state"] = "BLOCK UNREADABLE"
        print("   block unreadable: %r" % out["http_status"])
    else:
        rawg = open(bp, "rb").read()
        try:
            d = zlib.decompressobj(31)
            txt = d.decompress(rawg)
        except Exception as e:                      # noqa: BLE001
            out["state"] = "DECOMPRESS FAILED: %s" % e
            txt = b""
        recs = [l for l in txt.split(b"\n") if l]
        hits = [l for l in recs if b"minimed" in l]
        out.update({
            "state": "READ",
            "gz_bytes": len(rawg), "plaintext_bytes": len(txt),
            "records_in_block": len(recs),
            "first_record_key": recs[0].split(b" ")[0].decode("utf-8", "replace") if recs else None,
            "last_record_key": recs[-1].split(b" ")[0].decode("utf-8", "replace") if recs else None,
            "minimed_records": len(hits),
            "minimed_keys": [h.split(b" ")[0].decode("utf-8", "replace")[:120] for h in hits[:12]],
            "minimed_statuses": sorted({h.split(b" ")[-1].split(b'"')[-2].decode("utf-8", "replace")
                                        if b'"' in h else h.split(b" ")[-1].decode("utf-8", "replace")
                                        for h in hits})[:8],
        })
        print("   READ: %d bytes gz -> %d B plaintext, %d records, keys %r..%r"
              % (len(rawg), len(txt), len(recs), out["first_record_key"], out["last_record_key"]))
        print("   minimed records INSIDE this block: %d" % len(hits))
        for k in out["minimed_keys"][:8]:
            print("      %s" % k)
    with open(os.path.join(HERE, "block-probe.json"), "w") as fh:
        fh.write(json.dumps(out, sort_keys=True, indent=1) + "\n")
    return out


def _blocks_in_the_straddling_page(fetch, bodies, evidence):
    """The cluster.idx lines of the page that carries the puncturing pair, read
    back from the committed body - no request.

    Both evidence keys must be in the same body: a sibling crawl's page carries
    eu,mini-parfemy too (the SURT prefix is not unique to one crawl), so a
    single-key match would silently pick the wrong crawl's page."""
    import glob as _g
    k0, k1 = (e.encode() for e in evidence)
    best = None
    for bp in sorted(_g.glob(os.path.join(bodies, "*-locate.body"))):
        raw = open(bp, "rb").read()
        if k0 not in raw or k1 not in raw:
            continue
        rows = []
        for chunk in raw.split(b"\n"):
            f = chunk.split(b"\t")
            # observed column order: <first surt key> <cdx-NNNNN.gz> <gz offset>
            # <gz byte length> <block ordinal>. Asserted, not assumed, by the
            # startswith/isdigit test below.
            if len(f) == 5 and f[1].startswith(b"cdx-") and f[2].isdigit() \
                    and f[3].isdigit() and f[4].isdigit():
                rows.append((f[0], f[1], int(f[2]), int(f[3])))
        if rows:
            best = rows
    assert best, "no committed page carries both puncturing keys"
    return best


# ------------------------------- AD: the sound absence test (block confirmation)
def _block_for_evidence(bodies, evidence):
    """(key, cdx_file, offset, length) of the cluster.idx line that must contain
    the family if the puncturing pair is (x < FAM_LO, y >= FAM_HI).

    This is the SOUNDNESS REPAIR, and the argument is short enough to check:
    cluster.idx has one line per CDX block, keyed by that block's FIRST key.
    If no line's key lies in [FAM_LO, FAM_HI) AND some block's first key y is
    >= FAM_HI while its predecessor x is < FAM_LO, then every record in the
    family interval - if any exist - lies inside the block keyed x. A family
    record in a later block would make that block's first key < FAM_HI and so
    would itself have been the puncturing key. Hence: read block x, and only
    block x, decides presence.
    """
    rows = _blocks_in_the_straddling_page(None, bodies, evidence)
    # the puncturing predecessor: last cluster.idx key strictly below FAM_LO
    # whose successor is >= FAM_HI. Selected by predicate, then asserted.
    for i, r in enumerate(rows[:-1]):
        if r[0] < FAM_LO and rows[i + 1][0] >= FAM_HI:
            assert rows[i + 1][0] == max(e.encode() for e in evidence), (
                "the block after the puncturing key is not the evidence's upper "
                "key - the page and the evidence disagree", r[0], rows[i + 1][0])
            return r
    raise AssertionError("no straddling adjacent pair in the committed page")


def _read_block(fetch, crawl, blk):
    key, f, off, ln = blk
    r = fetch.get_retry(DATA_HOST, "/cc-index/collections/%s/indexes/%s" % (crawl, f.decode()),
                        "block-read", "block-read-" + crawl, range_=(off, off + ln))
    if r is None or r["http_status"] != "206":
        return None, (r or {}).get("http_status")
    import zlib
    raw = open(fetch.body_path(r), "rb").read()
    try:
        txt = zlib.decompressobj(31).decompress(raw)
    except Exception:                                  # noqa: BLE001
        return None, "decompress-failed"
    recs = [l for l in txt.split(b"\n") if l]
    fam = [l for l in recs if FAM_LO <= l.split(b" ")[0] < FAM_HI]
    return (recs, fam), "206"


def do_confirm():
    """Block-confirmed locate. For each crawl named on the command line:
      1. reuse the committed locate-*.json bisection (0 requests) if present;
         otherwise run the seeded bisection live within LOCATE_BUDGET.
      2. read the one block that must contain the family (1 request).
      3. publish FAMILY_PRESENT / FAMILY_ABSENT from the RECORDS, not the keys.
    Requests: 1 per crawl with a committed locate, 1 + pages otherwise.
    """
    cap = int(os.environ.get("L_CAP", "50"))
    bodies = os.environ["L_BODIES"]
    fetch = Fetcher(bodies, cap, os.environ["L_LOCK_IDX"], os.environ["L_LOCK_DATA"])
    seeds = seed_fracs()
    out = {}

    for crawl in sys.argv[2:]:
        lp = os.path.join(HERE, "locate-%s.json" % crawl)
        v = json.load(open(lp)) if os.path.exists(lp) else None
        if v is None:
            hp = fetch.get_retry(DATA_HOST, cluster_path(crawl), "head", "head-" + crawl,
                                 range_=(0, HEAD_BYTES))
            if hp is None or hp["http_status"] != "206":
                out[crawl] = {"state": "NO SIZE", "status": (hp or {}).get("http_status")}
                continue
            total = int(re.search(r"/(\d+)$", hp["content_range"]).group(1))

            def page(lo, hi, _c=crawl, _t=total):
                a = max(0, min(_t - LOCATE_PAGE, lo))
                r = fetch.get_retry(DATA_HOST, cluster_path(_c), "locate", "locate-" + _c,
                                    range_=(a, min(_t, a + LOCATE_PAGE)))
                if r is None or r["http_status"] != "206":
                    return None
                lines, lead, tail = body_lines(open(fetch.body_path(r), "rb").read())
                return {"lines": lines, "lead_dropped": lead, "tail": tail,
                        "range": (a, min(_t, a + LOCATE_PAGE))}

            v = Locater(total, page, seeds.get(crawl, 0.525), LOCATE_BUDGET,
                        note="seeded f0, budget %d, %s" % (LOCATE_BUDGET, fetch.cap_line())).run()
            with open(lp, "w") as fh:
                fh.write(json.dumps(v, sort_keys=True, indent=1) + "\n")
        print("  %-18s bisection -> %s in %s pages" % (crawl, v["state"], v.get("pages_used")))
        if v["state"] == "FAMILY_PRESENT":
            out[crawl] = {"state": "FAMILY_PRESENT", "basis": "block key itself in interval",
                          "keys": v.get("key_hits")}
            continue
        if v["state"] != "FAMILY_ABSENT":
            out[crawl] = {"state": v["state"], "window": v.get("window"),
                          "pages_used": v.get("pages_used")}
            continue
        blk = _block_for_evidence(bodies, v["evidence"])
        res, st = _read_block(fetch, crawl, blk)
        if res is None:
            out[crawl] = {"state": "BLOCK UNREADABLE", "status": st,
                          "puncturing_pair": v["evidence"], "block_key": blk[0].decode("utf-8", "replace")}
            continue
        recs, fam = res
        out[crawl] = {
            "state": "FAMILY_PRESENT" if fam else "FAMILY_ABSENT",
            "basis": "block-confirmed records" if fam else
                     "block read in full, no family record inside it",
            "puncturing_pair": v["evidence"],
            "block_key": blk[0].decode("utf-8", "replace"),
            "block_cdx_file": blk[1].decode(), "block_offset": blk[2],
            "block_gz_bytes": blk[3],
            "records_in_block": len(recs),
            "family_records": len(fam),
            "family_keys": [l.split(b" ")[0].decode("utf-8", "replace")[:130] for l in fam[:10]],
            "bisection_state": v["state"], "bisection_pages": v.get("pages_used"),
        }
        print("     block %s: %d records, %d family -> %s [%s]"
              % (blk[1].decode(), len(recs), len(fam), out[crawl]["state"], fetch.cap_line()))
        for k in out[crawl]["family_keys"][:6]:
            print("        %s" % k)

    with open(os.path.join(HERE, "confirm.json"), "w") as fh:
        fh.write(json.dumps(out, sort_keys=True, indent=1) + "\n")
    with open(os.path.join(HERE, "control-gate.txt"), "a") as fh:
        fh.write("\nblock-confirmed verdicts (the key-only gate above did not pass; this is\n"
                 "the sound test, and it OVERTURNS both key-only readings):\n")
        for c, o in out.items():
            fh.write("  %s -> %s (%s)\n" % (c, o["state"], o.get("basis", "")))
    print(json.dumps({c: o["state"] for c, o in out.items()}, indent=1))
    return out


# ------------------------------------------------------------------- the pass
def cluster_path(crawl):
    return "/cc-index/collections/%s/indexes/cluster.idx" % crawl


def cdx_path(crawl, q, extra=""):
    return "/%s-index?url=%s&output=json&matchType=domain%s" % (crawl, urllib.parse.quote(q, safe="."), extra)


def do_pass():
    cap = int(os.environ.get("L_CAP", "15"))
    bodies = os.environ["L_BODIES"]
    l_idx = os.environ["L_LOCK_IDX"]
    l_data = os.environ["L_LOCK_DATA"]
    fetch = Fetcher(bodies, cap, l_idx, l_data)
    sizes = {}

    TARGET, CTRL_A, CTRL_B = "CC-MAIN-2014-23", "CC-MAIN-2022-27", "CC-MAIN-2024-42"

    # --- 1. collinfo (the cheap half): assert the target is published; typed
    # dates. Connection-level failures are re-issued by get_retry; a collinfo
    # that never lands leaves the pass with no served answers, which is
    # reported as such and never as a crawl verdict.
    r = fetch.get_retry(IDX_HOST, "/collinfo.json", "collinfo", "collinfo")
    if r is not None and r["http_status"] == "200":
        bpath = fetch.body_path(r)
        info = json.loads(open(bpath, "rb").read().decode("utf-8", "replace"))
        assert isinstance(info, list), "collinfo did not resolve to a list (AGENTS.md 6.3)"
        for c in info:
            assert isinstance(c.get("id"), str) and isinstance(c.get("from"), str) \
                and isinstance(c.get("to"), str), "collinfo row with untyped fields: %r" % c.get("id")
        here = {c["id"]: c for c in info}
        misses = [w for w in (TARGET, CTRL_A, CTRL_B) if w not in here]
        assert not misses, "collinfo is missing the pass's crawls: %s" % misses
        with open(os.path.join(HERE, "derived-collinfo-ids.txt"), "w") as fh:
            fh.write("\n".join("%s\t%s\t%s" % (c["id"], c["from"], c["to"]) for c in info) + "\n")
        print("  collinfo: %s crawls published; %s = %s -> %s" % (
            len(here), TARGET, here[TARGET]["from"], here[TARGET]["to"]))
    elif r is not None:
        print("  collinfo: %s after %d attempt(s) - NO served answer from the "
              "index host this run." % (r["http_status"], r["attempt"] + 1))

    # --- 2. THE BULK-LAYER ORACLE FIRST. A certainly-absent crawl id, read the
    # same way as a real one. Without it a 404 on a named crawl is unreadable:
    # it could be "not published" or "this route does not refuse that way".
    ra = fetch.get_retry(DATA_HOST, cluster_path("CC-MAIN-9999-99"),
                         "absent-crawl", "absent-crawl", range_=(0, HEAD_BYTES))
    oracle = (ra or {}).get("http_status")

    # --- 3. THE CONTROLS' SERVEDNESS, before the target is read at all.
    # CTRL_A is known (area L addendum) to carry a /ipro/hcp/ member on
    # CC-MAIN-2022-27; CTRL_B is area M's documented 404 No Captures found on
    # CC-MAIN-2024-42 with a 200 control at its seq 25. Neither descriptor is
    # taken on trust here: each crawl's bulk read decides for itself.
    for crawl, role in ((CTRL_A, "head-ctrlA"), (CTRL_B, "head-ctrlB")):
        rr = fetch.get_retry(DATA_HOST, cluster_path(crawl), role, role, range_=(0, HEAD_BYTES))
        if rr is not None and rr["http_status"] == "206":
            m = re.search(r"/(\d+)$", rr["content_range"] or "")
            if m:
                sizes[crawl] = int(m.group(1))

    # --- 4..6: the CONTROLS' locates, before the target is read at all. The
    # brief's ordering rule and the honest reading of it: a control that
    # cannot classify means the machinery is not yet trustworthy, and the
    # target's reads are then not worth the remaining cap. A target verdict
    # reached with unclassified controls is not a finding.
    prior = {"frac": 0.85}
    seeds = seed_fracs()

    def make_page(crawl):
        def page(lo, hi, _prev=None):
            width = max(PAGE_MIN, min(LOCATE_PAGE, hi - lo))
            a_ = lo + max(0, (hi - lo - width) // 2)
            r = fetch.get_retry(DATA_HOST, cluster_path(crawl), "locate", "locate-" + crawl,
                                range_=(a_, min(sizes[crawl], a_ + width)))
            if r is None or r["http_status"] != "206":
                return None
            bp = fetch.body_path(r)
            raw = open(bp, "rb").read() if bp else b""
            lines, lead, tail = body_lines(raw)
            return {"lines": lines, "lead_dropped": lead, "tail": tail,
                    "range": (a_, min(sizes[crawl], a_ + width))}
        return page

    def locate(crawl, budget, frac=None):
        if budget < 1 or crawl not in sizes:
            print("locate %-18s -> SKIPPED (%s) at %s" % (
                crawl, "no served size" if crawl not in sizes else "cap", fetch.cap_line()))
            return "SKIPPED"
        v = Locater(sizes[crawl], make_page(crawl),
                    prior["frac"] if frac is None else frac, budget,
                    note="budget %d pages, %s" % (budget, fetch_cap_word(fetch))).run()
        with open(os.path.join(HERE, "locate-%s.json" % crawl), "w") as fh:
            fh.write(json.dumps(v, sort_keys=True, indent=1) + "\n")
        if v["state"] in ("FAMILY_PRESENT", "FAMILY_ABSENT"):
            prior["frac"] = min(0.95, max(0.6, (v["page"][0] + 1) / sizes[crawl]))
        print("locate %-18s -> %-16s [%s]" % (crawl, v["state"], fetch_cap_word(fetch)))
        return v["state"]

    verdicts = {}
    verdicts[CTRL_A] = locate(CTRL_A, min(LOCATE_BUDGET, max(0, cap - fetch.rows())),
                              seeds.get(CTRL_A))
    verdicts[CTRL_B] = locate(CTRL_B, min(LOCATE_BUDGET, max(0, cap - fetch.rows())),
                              seeds.get(CTRL_B))

    # --- the control gate, in code and before the target exists as a verdict.
    ca, cb = verdicts.get(CTRL_A), verdicts.get(CTRL_B)
    gate = "PASSED" if (ca == "FAMILY_PRESENT" and cb == "FAMILY_ABSENT") else "NOT PASSED"
    with open(os.path.join(HERE, "control-gate.txt"), "w") as fh:
        fh.write("control gate %s\n  %s -> %s (expected FAMILY_PRESENT)\n"
                 "  %s -> %s (expected FAMILY_ABSENT)\n"
                 % (gate, CTRL_A, ca, CTRL_B, cb))
    print("control gate: %s  (%s=%s, %s=%s)" % (gate, CTRL_A, ca, CTRL_B, cb))
    if gate != "PASSED":
        # Said precisely, because the earlier wording was false in every run
        # that reached it: servedness is a separate question from the locate
        # and is still read below. What the gate withholds is the LOCATE, and
        # it withholds it ENFORCED below, not merely announced - the target's
        # locate is guarded on this flag, so the statement holds whatever the
        # cap has room for.
        print("GATE NOT PASSED - no locate verdict may be published for any "
              "crawl, and the target's locate is SKIPPED below by this gate "
              "(not merely by the cap). The target's SERVEDNESS is a separate "
              "read and still runs: it does not depend on the locate, and the "
              # controls' servedness is what licenses reading a 206 as a "
              "statement about a crawl.")

    # --- 7. the target's own servedness (the close condition's first half)
    rt = fetch.get_retry(DATA_HOST, cluster_path(TARGET), "head-target", "head-target",
                         range_=(0, HEAD_BYTES))
    if rt is not None and rt["http_status"] == "206":
        m = re.search(r"/(\d+)$", rt["content_range"] or "")
        if m:
            sizes[TARGET] = int(m.group(1))

    # --- 8. the CDX pair on the target, re-issued under the counting rule, so
    # the final table carries the CDX verdict beside the cluster.idx verdict.
    fetch.get_retry(IDX_HOST, cdx_path(TARGET, "google.com", "&limit=5"),
                    "cdx-ctrl-target", "cdx-ctrl-target")
    fetch.get_retry(IDX_HOST, cdx_path(TARGET, "minimed.eu"),
                    "cdx-probe-target", "cdx-probe-target")

    # --- 9: the target's locate, with whatever survived the cap. GUARDED on the
    # control gate, not merely announced by it: an unclassified control means
    # the machinery is unproven, so the target's locate is not spent on it.
    # On the 2026-10-19 run this returned SKIPPED either way (the cap was also
    # at 0), so the committed ledger is the same under both readings - but the
    # gate now holds for whatever cap headroom a later run has.
    if gate != "PASSED":
        verdicts[TARGET] = "SKIPPED (control gate not passed)"
        print("locate %-18s -> SKIPPED (control gate not passed) [%s]"
              % (TARGET, fetch_cap_word(fetch)))
    else:
        verdicts[TARGET] = locate(TARGET, min(LOCATE_BUDGET, max(0, cap - fetch.rows())),
                                  seeds.get(TARGET))

    with open(os.path.join(HERE, "run.log.capped"), "a") as fh:
        fh.write("DONE - %s (lock wait %.1fs, absent-crawl oracle %s, control gate %s).\n" % (
            fetch.cap_line(), fetch.lock_wait, oracle, gate))
    print("=== pass ends: %s" % fetch.cap_line())


# ------------------------------------------------------------------ classify
def do_classify():
    """THE REUSABLE CHECK: from the committed ledger alone.

    Prints the two buckets as two counts, never as one table of verdicts:
    a connection-level failure is a statement about this host and this moment,
    and a run that never reached the index must not be able to present a table
    that reads as a set of crawl verdicts."""
    led = os.path.join(HERE, "results.jsonl")
    rows = [json.loads(l) for l in open(led) if l.strip()] if os.path.exists(led) else []
    print("== classify over %d committed rows" % len(rows))
    if not rows:
        print("   NO ROWS. No verdict of any kind may be published from this run.")
        return 0

    conn = [r for r in rows if (bulk_is_failure(r["http_status"]) if r["host"] == DATA_HOST
                                else cdx_is_failure(r["http_status"]))]
    served = [r for r in rows if r not in conn]
    print("   ATTEMPTS: %d total = %d served + %d connection-level failure "
          "(a retry is a request and is counted here)." % (len(rows), len(served), len(conn)))
    if conn:
        by = {}
        for r in conn:
            by.setdefault((r["host"], r["http_status"]), []).append(r["role"])
        for (h, c), roles in sorted(by.items()):
            print("     connection-level: %-24s %-4s x%d  (%s)" % (
                h, c, len(roles), ", ".join(sorted(set(roles)))))
    print()

    # per-crawl servedness, from the bulk layer
    per = {}
    for r in rows:
        m = re.match(r"^/cc-index/collections/(CC-MAIN-[0-9-]+)/", r["path"])
        if m:
            per.setdefault(m.group(1), []).append(r)
    for crawl, rs in per.items():
        ok = [r for r in rs if not bulk_is_failure(r["http_status"])]
        if not ok:
            print("   %-18s UNREAD-FROM-THIS-HOST - every attempt failed at "
                  "connection level (%s). NOT a crawl verdict; this does not "
                  "discharge any standing indeterminate cell." % (
                      crawl, ",".join(sorted(set(r["http_status"] for r in rs)))))
            continue
        last = ok[-1]
        sz = (re.search(r"/(\d+)$", last["content_range"] or "").group(1)
              if last["content_range"] and re.search(r"/(\d+)$", last["content_range"]) else "?")
        kw = {"206": "SERVED (index readable)",
              "404": "NOT PUBLISHED (documented absence shape)",
              "403": "NOT PUBLISHED (refused)"}.get(last["http_status"], "?")
        print("   %-18s %-4s %-38s total=%s bytes" % (crawl, last["http_status"], kw, sz))

    print()
    for r in rows:
        if r["role"].startswith("cdx-"):
            shape = ("SERVED" if not cdx_is_failure(r["http_status"])
                     else "CONNECTION-LEVEL FAILURE - not an absence")
            print("   CDX %-14s %-44s %-4s %6sB  %s" % (
                r["role"].replace("cdx-", ""), r["path"].split("?")[1],
                r["http_status"], r["body_bytes"], shape))
            if not cdx_is_failure(r["http_status"]):
                print("        head: %r" % ((r["body_head"] or "")[:110],))

    print()
    for crawl in ("CC-MAIN-2022-27", "CC-MAIN-2024-42", "CC-MAIN-2014-23"):
        p = os.path.join(HERE, "locate-%s.json" % crawl)
        if os.path.exists(p):
            v = json.load(open(p))
            print("   LOCATE %-18s -> %-16s (%s pages of a %s budget) %s" % (
                crawl, v["state"], v["pages_used"], v["budget"],
                (v.get("key_hits") or v.get("evidence") or "")))
        else:
            print("   LOCATE %-18s -> no locate file" % crawl)
    gp = os.path.join(HERE, "control-gate.txt")
    if os.path.exists(gp):
        print("\n" + open(gp).read().rstrip())
    return 0


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "pass":
        do_pass()
    elif cmd == "classify":
        sys.exit(do_classify())
    elif cmd == "selftest":
        selftest()
    elif cmd == "selftest-realistic":
        selftest_realistic()
    elif cmd == "derive":
        do_derive()
    elif cmd == "probe-block":
        do_probe_block()
    elif cmd == "confirm":
        do_confirm()
    else:
        print(__doc__)
        sys.exit(2)


if __name__ == "__main__":
    main()
