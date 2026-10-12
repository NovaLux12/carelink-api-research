# Area A — is `carelinkhp` the clinician portal for every region?

**Pass date:** 2026-10-12 · **Claim issue:** [#21](https://github.com/NovaLux12/carelink-api-research/issues/21)
**Branch:** `research/a-carelinkhp-region` · **Ledger:** `results.jsonl` (20 rows, one per HTTP request) · **DNS:** `dns.jsonl` (8 rows, recorded separately)

## Verdict

**Negative on the region's existence, and positive on what actually splits the family.**
There is no `.com` variant of `carelinkhp`. Every `carelinkhp*.minimed.{eu,com}` name
outside the baseline is **NXDOMAIN**. The clinician-portal bundle is deployed on
**five hosts across two TLDs**, and the split is **product role (clinic vs support),
not region** — every `.eu`/`.com` pair measured serves the *same* build.

Two builds exist:

| Build | Entry document (5518 B) sha256 | Main asset | Asset size |
|---|---|---|---|
| **A — clinic / `pow`** | `0f2c5f6257a6fc6a…` | `main.fb5f8cb7eb60c4d5.js` | 3,397,615 B |
| **B — support / `cua`** | `f637c8d0cd4ec6bc…` | `main.759cddab23085086.js` | 3,410,666 B |

| Host | Build | Ledger row |
|---|---|---|
| `carelinkhp.minimed.eu` | A | seq 4 |
| `carelink.medtronic.com` | A | seq 8 |
| `carelink.medtronic.eu` | **A** | seq 19 |
| `carelink-support.medtronic.eu` | B | seq 15 |
| `carelink-support.medtronic.com` | B | seq 20 |

`carelinkhp-prod.minimed.eu` — the only `carelinkhp*` name in the corpus that had
**never been probed** — is **NXDOMAIN**, so `recon/JS-API-SURFACE.md` Q2 ("does the same
bundle [serve] from `carelinkhp-prod.minimed.eu`") has no host to answer on.

## Request accounting

**20 of a 20 cap.** GET only throughout — no POST, no `-X`, no `-d`, no token, no
authentication, no port scan, no DNS brute force. 8 DNS lookups are recorded in
`dns.jsonl` and are **not** counted against the cap: they are resolver traffic, not
requests to a vendor host, and no HTTP request was issued to any host that failed to
resolve. **Limitation:** that boundary is stated rather than machine-checkable —
`dns.jsonl` records only `{host, resolver_status, a_records, probed, has_http_row}`,
with no resolver identity, no TTL and no timestamp of its own, so a reader cannot
re-derive from the artefact alone that eight separate lookups occurred. The count is
auditable only by reading `probe.sh`. **The two ledgers are also not symmetric, and
that is recorded rather than tidied away:** `dns.jsonl` holds **8 rows** covering
batch 1's host set plus the test host, while `results.jsonl` covers **5** hosts. Two
hosts that *were* probed over HTTP — `carelink-support.medtronic.eu` and
`carelink.medtronic.eu`, both added in batches 2 and 3 — have **no DNS row**, because
the resolver loop runs only in `probe.sh` and was not repeated. They resolved in
practice; the resolver status for them is simply unrecorded.

**Declared delay: 2.5 s, sleep inside the per-host `flock`.** Measured from
`run.log`: **minimum consecutive same-host gap 2 s over 15 gaps; all 15 are ≥ the
BRIEF's 2 s hard floor, 11 of 15 are ≥ 2.5 s.** Four gaps fall below the declared
2.5 s. **No cause is asserted for them**, per `docs/09` §4, which records this exact
signature as an open question and instructs that a pass report the floor and the
sub-declared gap *without* explaining it.

> **Denominator, stated so it is reproducible (`AGENTS.md` §6.7).** **15** = one gap per
> consecutive pair of requests to the same host, across all 5 responding hosts:
> `carelinkhp.minimed.eu` 3, `carelink.medtronic.com` 3,
> `carelink-support.medtronic.com` **4**, `carelink-support.medtronic.eu` 2,
> `carelink.medtronic.eu` 3. *(An earlier draft of this line said **14** — computed
> before `probe4.sh` added seq 20, which opens a fourth
> `carelink-support.medtronic.com` gap. The substantive figures are unaffected: that
> gap is 84 s, so the minimum, the "4 below 2.5 s" count and the "0 below 2 s" count
> are identical either way. The denominator was wrong.)*

**INFERRED, and not resolvable from the artefacts on disk.** `run.log` carries
whole-second timestamps only — no sub-second field, no monotonic clock — and the
timestamp is written by `log()` **after** the response returns, so it marks completion
rather than send. Nothing on disk distinguishes **three** candidates:

- whole-second truncation of a compliant 2.5 s sleep plus a fast request (which would
  read as either 2 or 3 depending on where the interval falls within the second);
- a transient backwards clock step of the kind area B suspected, which appears in one
  gap and then cancels against its neighbour;
- a post-hoc edit to `run.log`, which produces identical arithmetic.

All three fit the **15** recorded gaps. I am claiming the **counts**, which are
reproducible from `run.log` as committed, and **not** the explanation. What can be
said without inference: no gap fell below the 2 s floor, so the rule this repo
actually enforces was not breached.

> **How 15 is derived, and a definitional trap worth not repeating.** Per host, the
> gaps are the requests to that host **minus one**: 20 requests across 5 hosts gives
> **20 − 5 = 15**. Broken down: `carelinkhp.minimed.eu` **3**, `carelink.medtronic.com`
> **3**, `carelink-support.medtronic.com` **4**, `carelink-support.medtronic.eu` **2**,
> `carelink.medtronic.eu` **3**.
>
> The 4 matters because seqs **12 and 20 both go to `carelink-support.medtronic.com`**
> but seqs 13–19 sit between them. So **per-host grouping gives 15 and
> adjacent-in-time pairing gives 14** — two different quantities, and only the first
> answers "were any two requests to the same host closer than 2 s", which is the rule
> in question. `mtime.py`'s V3 test initially compared those two and reported a
> spurious cross-ledger disagreement; the test was wrong, not the ledgers, which agree
> on all 20 `(seq, host)` pairs.
>
> *(Two earlier drafts of this line said **14** — computed before `probe4.sh` added
> seq 20. The substantive figures were unaffected; the denominator was not.)*

### Cross-checked with a second oracle (area O's, 2026-10-12) — zero requests

Area O shipped a better timing oracle than a `run.log` timestamp: **prefer the
body-file mtime and cross-check it against `t0`**, because a `date` read before
`curl` can return later than the body curl then wrote, which makes `mtime - t0`
negative and manufactures a gap that never happened ([source: docs/09 §4,
sub-declared-gap row]).

Applied to **this pass's own committed artefacts** by `mtime.py` (offline, zero
requests; output in `mtime.txt`):

| Measure | Result |
|---|---|
| negative `mtime - t0` gaps (area O's corrupt-`t0` signature) | **0** |
| same-host gaps checkable | **10 of 15** |
| minimum `mtime` gap | **2.637 s** |
| `mtime` gaps ≥ the declared 2.5 s | **10 of 10** |
| the 4 pairs `run.log` logged as 2 s | **all 4 measure ≥ 2.5 s by mtime** — 2.637 / 2.841 / 2.839 / 2.652 s |

**This is OBSERVED for this pass and it is stronger than "no cause asserted":** an
oracle independent of `run.log`, at **sub-second** resolution, finds that **none of the
four short readings was actually a short interval** — all four real intervals exceed
the declared 2.5 s. What remains unestablished is *why `run.log` truncated them*, and
`docs/09`'s open question — which is about areas **B, X and Z**, whose artefacts this
pass does not touch — is **not** answered here.

**Three limits, stated rather than assumed:**

1. **Not reproducible from a clean clone.** **git does not preserve mtimes.** The bodies'
   *content* is committed; their filesystem timestamps are not. `mtime.py` re-run
   elsewhere yields different numbers or none. This is a property of the machine that
   ran the pass, not of the repository.
2. **10 of 15, not 15.** The five uncheckable gaps are those whose later request was a
   3.3–3.4 MB asset, whose bodies were deliberately not committed.
3. **A sub-2.5 s mtime gap would not have been conclusive on its own**, because an
   mtime marks body-write completion, so `gap = 2.5 s sleep + overhead +
   dur[n+1] − dur[n]` and a faster later request can shrink it. The finding above rests
   on gaps that came out *above* the threshold, which is the direction that is safe.

**A cross-check is only worth what its failure modes are worth, so two defects in
this file's first version are recorded rather than quietly repaired:**

1. **It printed a conclusion its own table falsified.** The CONCLUSION was a string
   literal that never read the measured values. On a `git archive` extract — where git
   collapses every body to one mtime — it printed *"no gap below the declared 2.5 s"*
   and *"all 4 measure ≥ 2.5 s by mtime"* directly above a table reading
   `mtime gaps >= 2.5s: 0 of 10` / `minimum 0.000s`, and **exited 0**. That is
   `AGENTS.md` §1 (a sentence that cannot be traced to a source) in the §6.5 shape
   (prose contradicting its own table), and the surrounding prose here does *not*
   over-claim, so the script was the counterweight to an otherwise-earned exoneration.
   **Fixed:** every reported figure is now computed, three validity tests (V1 collapse,
   V2 span agreement with `run.log`, V3 per-host denominator derived independently from
   `run.log`) gate the result, and an invalid series prints **NO RESULT** and exits 1.
   **A clean clone is now EXPECTED to exit 1**, because git does not preserve mtimes —
   which is the honest answer, not a broken check.
2. **It compared UTC logs against local mtimes.** `run.log` is written by `date -u`;
   `fromtimestamp()` renders an mtime in local time. The offset is constant across a
   run so it cancels out of every *difference*, which is why it stayed invisible here
   and would surface on a machine in another timezone or across a DST boundary.
   **Fixed:** mtimes are now converted to UTC explicitly before comparison.
   A third defect — the V3 denominator test as first written was a **tautology**
   (it compared the enumerated total to `len(rows) - n_hosts`, which is algebraically
   equal by construction) — was caught by deliberately dropping a ledger row and
   watching the test pass anyway. It now derives the denominator from `run.log`'s own
   `(seq, host)` stream, which is a genuinely separate record.

**I am in this class.** Area O excluded itself because its harness declared `DELAY=2.5`
but never emitted the `sleep`, so its sub-floor gaps are a rule breach rather than a
timing artefact. Mine are the opposite: `probe.sh:49-50`, `probe2.sh`, `probe3.sh` and
`probe4.sh` each run `sleep 2.5` **inside** the per-host `flock` and before `curl`.

> **Known-pending, deliberately not fixed here — and the base moved under round 2.**
> This pass contributes **1 pass and 4 occurrences** to the open question in `docs/09`
> §4. **On `main` as of `b6909d9` that row already reads `n = 4 passes, 9
> occurrences`** — area O rewrote it after this pass's round-1 note was written, which
> had quoted the older `3 passes / 7 occurrences`. Reconciling both branches' inputs is
> the merge queue's arithmetic, not this pass's, so **the row is left untouched**:
> sibling branches edit it from the same base with their own figures, and writing it
> here would race them and be overwritten. Recorded so the discrepancy is a known open
> item rather than silent drift. **The count in `docs/09` is not this pass's to
> change.**

## Controls, in the order they were sent

Controls were sent **first on every host**, before any candidate.

1. **Certainly-absent path** — `GET /a-control-this-path-cannot-exist-2026-10-12`.
   *The same fabricated string was used on all five responding hosts, deliberately:*
   the fallback body is the question, so the fallback bodies have to be
   byte-comparable to each other and to each host's own root. A per-host nonce would
   have produced five incomparable rows.
   **What it proved:** the SPA catch-all is live on all five hosts, and — the result
   that changed the pass — **the catch-all is byte-identical to the host's own entry
   document** (seq 1≡3, 5≡7, 9≡11, 13≡14, 16≡17). So a document-path probe cannot
   distinguish "real portal" from "fallback" on this host family. See §Methodology.
2. **Known-live published config key** — `GET /hcp/configuration/public/pow.crm.settings`
   with `X-System-ID: ProWeb`. Chosen because it is a **published vendor key already
   pinned** in the regression suite (`regression/hurl/05-public-config.check.sh:98`),
   so "live here" is a recorded fact and not an assumption.
   **What it proved:** all three `.com`/`.eu` portal hosts return `200` for it — a
   parked page cannot answer that. It also produced the per-host CRM base (§5).

Every host passed both controls. **No stop condition fired**: the absent-path control
returned the expected fallback on every host, no host turned out to be in a
parked-wildcard space (`carelink.medtronic.*` is a Medtronic apex, not `*.carelink.*`),
and nothing resembling a credential, session value, internal hostname or patient
identifier appeared in any response.

## Findings

### 1. `carelink.medtronic.eu` **does** serve the bundle — `docs/01` and `docs/10` said it did not

> **Correction (2026-10-12, applied in this same PR).** The two quotes below are
> quoted **as recorded on `main` before this pass's correction**, and they are how a
> reader of the *pre-merge* tree finds them — `docs/01-hosts-and-estate.md:69` and
> `docs/10-open-questions.md` §2. **This PR rewrote both sites in the same diff**, so
> on the merged tree the line numbers have moved and the sentences now read as
> corrections: `docs/01`'s `carelink.medtronic.eu` row says "**does** serve the clinic
> bundle … **Corrected 2026-10-12**", and `docs/10` §2 says "Was 'No — false
> positive.' That is now REFUTED." `docs/01` keeps the original sentence verbatim
> inside a dated `⚠ CORRECTION — 2026-10-12 (area A)` block, so the retraction history
> stays readable. **A line number in this log therefore points at `main`, not at the
> post-merge tree** — `AGENTS.md` §3's append-only rule for `findings-log/` versus the
> same-PR rewrite of `docs/`.

`docs/01-hosts-and-estate.md:69` records `carelink.medtronic.eu` as "**does not**
serve that bundle — it returns the 5518-byte SPA fallback, md5-identical to the
`carelinkhp` trap page", and `docs/10-open-questions.md` §2 closes the question "Is
`carelink.medtronic.eu` a second portal deployment?" with "**No — false positive.**"

**Both are refuted (OBSERVED, seq 16–19).** Its entry document is byte-identical to
`carelinkhp.minimed.eu`'s — md5 `6aedf6c4004fbb29a298bc62128480be`, sha256
`0f2c5f6257a6fc6af22e4b31309264df4c148e08016c196e1048bdc19a87e32d`, **the same value
the repo has recorded since 2026-10-08** — and when asked for the chunk **its own
document names**, it served `main.fb5f8cb7eb60c4d5.js` at **3,397,615 B,
sha256 `2a7fa8e7af519c2b`**, byte-identical to both other build-A hosts.

**The md5 half of the original claim was right and is re-anchored here** — I
independently reproduced `6aedf6c4004fbb29a298bc62128480be` from a live capture. It is
the **conclusion** drawn from it that was wrong.

The error is exactly §2 of this file: *the document **is** the catch-all*, so "returns
the 5518-byte fallback" was never evidence of absence. The host was classified as a
false positive because only the document was ever measured, and the document is
precisely the artefact that cannot answer the question. The `cmp`-identical evidence
that cleared `carelink.medtronic.com` existed on disk; the same test was never run on
`.eu`.

### 2. `carelink-support.medtronic.com` serves a **different build**, not "the same document"

> **Correction (2026-10-12, applied in this same PR).** Same marker as §1: the quotes
> below are **as recorded on `main` before this pass's correction**. This PR rewrote
> `docs/07-admin-portal-and-reporting.md`, `docs/01-hosts-and-estate.md` and
> `docs/08-security-findings.md` in the same diff, so on the merged tree the cited line
> numbers have moved and the sentences now carry dated correction blocks. The original
> wording is preserved verbatim inside those blocks rather than deleted.

`docs/07-admin-portal-and-reporting.md:24`, `docs/01-hosts-and-estate.md:68` and
`findings-log/probe-2026-10-08/SECURITY-FINDINGS.md` §S3 all record that
`carelink-support.medtronic.com` "serves the same document" as `carelinkhp.minimed.eu`.

**Refuted (OBSERVED, seq 9–12, 20).** Its entry document is a *different 5518-byte
document* — md5 `3e27b4df100cbc43ad6379d2517557fc`, sha256
`f637c8d0cd4ec6bc70944f7c9083ace6c205c5ecd22ce5da6ed533ece6d9a1bc` — and the only
difference from build A's document is the content-hashed chunk names:

```
build A: runtime.a752bb828cca4b2c.js   polyfills.e98da8d5da636e6e.js   main.fb5f8cb7eb60c4d5.js
build B: runtime.0c0212e340fbafc0.js   polyfills.e98da8d5da636e6e.js   main.759cddab23085086.js
```

Asking it for `main.fb5f8cb7eb60c4d5.js` returns the 5518 B catch-all (seq 12).
Asking it for `main.759cddab23085086.js` returns the real asset: **3,410,666 B,
sha256 `a054555a0f22176e`**, `content-type: application/javascript` (seq 20).

So `.com` support serves **build B**, and the host-name/labelling was right while the
"same document" claim was wrong.

### 3. `docs/08`'s digest is attached to the wrong artefact

`docs/08-security-findings.md` records that a host serves build B as
"`main.759cddab23085086.js`, sha256 `f637c8d0…`", and widens the S3 finding to "five
hosts".

**`f637c8d0…` is the sha256 of the 5518-byte entry document, not of the asset** (OBSERVED,
seq 11/14 vs seq 15/20). The asset `main.759cddab23085086.js` hashes to
`a054555a0f22176e…`. The build B *host* attribution in `docs/08` — `carelink-support.medtronic.eu`
— is **confirmed**: that host serves the identical document and the identical asset
(seq 13–15). But the digest recorded beside the asset name belongs to a different
file.

This is `AGENTS.md` §6.3 in the shape it warns about: a digest was carried forward
without asserting **which artefact was hashed**. The build-B host list in `docs/08` is
unchanged by this correction; only the digest's subject moves.

### 4. The region axis does nothing; the product axis is the split

Every `.eu`/`.com` pair measured serves the same build:

| Pair | `.eu` build | `.com` build |
|---|---|---|
| `carelink.medtronic.{eu,com}` | A (seq 19) | A (seq 8) |
| `carelink-support.medtronic.{eu,com}` | B (seq 15) | B (seq 20) |

So the answer to the area's title question — *is `carelinkhp` the clinician portal for
every region?* — is that **region is not a variable on this host family**. The one
thing that does vary is which product you are looking at (clinic `pow` vs support
`cua`), and both products are mirrored across both TLDs.

**INFERRED**, on the assumption that the bundle's published config names its own CRM
target correctly: the `base.uri` in `pow.crm.settings` tracks the **deployment**, not
the product (`.com` hosts, support included, all publish `carelink.medtronic.com/crm`).
This is one key on three hosts and no `cua.crm.settings` was probed, so it is offered as
a reading, not a finding.

### 5. `pow.crm.settings` differs by host — 96 B vs 97 B

| Host | Body |
|---|---|
| `carelinkhp.minimed.eu` (seq 2) | `{"base.uri":"https://carelink.medtronic.eu/crm","product":"pow","version":"4.5"}` — 96 B |
| `carelink.medtronic.com` (seq 6) | `{"base.uri":"https://carelink.medtronic.com/crm",…}` — 97 B |
| `carelink-support.medtronic.com` (seq 10) | `{"base.uri":"https://carelink.medtronic.com/crm",…}` — 97 B |

The single byte is `.eu` → `.com`. This is a **PUBLISHED** key served without a login,
and it is the only cell in this pass where the three hosts are *not* byte-identical —
which is itself the evidence that build A and build B are two deployments of one
product family rather than one deployment.

## Methodology correction — the 5518-byte discriminator does not work, for two separate reasons

`docs/09-methodology-and-oracles.md` §4 and `AGENTS.md` §7 both say to discriminate
the SPA fallback on `Content-Type`, "never on status", and `docs/09` adds "or the
exact 5518-byte size". **That advice is wrong in two ways this pass measured, and the
error is what produced Finding 1.**

1. **There is no document-path discriminator at all.** The catch-all *is* the entry
   document — seq 1≡3, 5≡7, 9≡11, 13≡14, 16≡17, all five pairs byte-identical. The
   fallback and the real portal root are the same 5518 bytes. Any probe that measures
   only a document path cannot distinguish them, and `Content-Type` cannot help because
   both are `text/html`.

   > **Counting rule, so "5 of 5" is reproducible rather than asserted.** One
   > comparison is counted per **responding host**: that host's certainly-absent-path
   > row against that host's own `/` row, compared by sha256 of the decompressed body.
   > The absent-path rows are `[1, 5, 9, 13, 16]` and the root rows are
   > `[3, 7, 11, 14, 17]`, paired in order — each pair verified to be the same host
   > before its digests were compared, so the ordering is not taken on trust. The
   > denominator is the **five** hosts with an HTTP row. It is explicitly **not** the
   > 8 rows in `dns.jsonl`: **3** of those rows are hosts that answered HTTP, the other
   > **5** are NXDOMAIN — and the test host `carelinkhp-test.minimed.eu` is *one of
   > those five*, not a sixth category, so the 8 rows partition as 3 + 5 with no row
   > counted twice. And it is **not per request** —
   > a host with three document paths would still contribute one pair.
   > *(An earlier draft of this line said "seven pairs", which was wrong in the way
   > `AGENTS.md` §6.7 forbids: the ledger contains five such pairs and no seventh.)*

2. **Size is not a discriminator either.** 5518 B maps to **at least two distinct
   digests** — `0f2c5f6257a6fc6a…` (builds A hosts) and `f637c8d0cd4ec6bc…`
   (build B hosts). A host serving build B satisfies "5518 bytes" and is not the
   `carelinkhp` page.

**The discriminator that does work is an asset path**, and it works on three axes at
once: the catch-all answers an asset path with `content-type: text/html` and 5518 B,
while a real asset answers with `content-type: application/javascript` and its own
size. Measured both ways on `carelink.medtronic.eu`: build A's chunk → 3,397,615 B
`application/javascript`; build B's chunk → 5518 B `text/html`.

So the rule becomes: **ask for a content-hashed chunk that the host's own document
names**, and discriminate on `Content-Type` + size + digest together. Naming a chunk in
HTML is not serving it — which is why seq 20 exists, to verify the build B `.com` host
*serves* the chunk its document names rather than inferring it from the string
(`AGENTS.md` §6.2).

## What was searched and found empty

- **`carelinkhp-prod.minimed.eu`** — NXDOMAIN. The only `carelinkhp*` name in the corpus
  never probed; it appears only in archive queries that returned 0 rows
  (`recon/ARCHIVE-URLS.md:39,369`) and as open Q2 in `recon/JS-API-SURFACE.md:1162`.
- **`carelinkhp.minimed.com`**, **`carelinkhp-prod.minimed.com`** — NXDOMAIN,
  re-confirming `PROBE-FINDINGS.md:29`. `carelinkhp-trials.minimed.com` — NXDOMAIN,
  improving on `CONFIG-NAMESPACE-DEEP.md:254`'s `000 / TCP connect failed`: the resolver
  returns **NXDOMAIN**, so there was never an address to connect to.
- **`carelinkhp-test.minimed.eu`** — a `test` deployment (`docs/01:103`). **Recorded
  and not probed**, per `docs/09` §1's bar on dev/stage/test contact. Resolver lookup
  only, and it returned **NXDOMAIN** — so the archived test deployment
  (`docs/01:103`, PUBLISHED from Wayback) has no DNS entry today. That is an
  observation about a name this pass deliberately never contacted; **no inference is
  drawn about whether the deployment still runs behind a name that is not in this
  corpus.**

No `.minimed.{eu,com}` host was probed that is not named in this repository before this
pass. No wordlist, no enumeration, no DNS brute force.

## Reproducing

```bash
bash findings-log/2026-10-12-area-a-clinic-portal-region/probe.sh    # batch 1, 12 requests
bash findings-log/2026-10-12-area-a-clinic-portal-region/probe2.sh   # batch 2, 6 requests
bash findings-log/2026-10-12-area-a-clinic-portal-region/probe3.sh   # batch 3, 1 request
bash findings-log/2026-10-12-area-a-clinic-portal-region/probe4.sh   # batch 4, 1 request
```

The four scripts exist because the pass changed shape mid-run: batch 2 was written after
batch 1 showed a `.com` host holding a digest `docs/08` attributed to a `.eu` host, and
batches 3 and 4 each test one inference the previous batch made. Bodies ≤ 100 KB are
committed under `headers/`; the two 3.4 MB bundle assets are deliberately **not**
committed, so their digests are reproducible only by re-fetching. `probe3.sh` exits
non-zero on an unset `RUNLOG` after its ledger row is written — the request and the row
are recorded; only the log append failed, and the row was appended by hand.

## Evidence table

| Claim | Class | Source |
|---|---|---|
| Build A served by `carelinkhp.minimed.eu` | OBSERVED | `results.jsonl` seq 4 |
| Build A served by `carelink.medtronic.com` | OBSERVED | `results.jsonl` seq 8 |
| **Build A served by `carelink.medtronic.eu`** — refutes `docs/01:69`, `docs/10` §2 (as recorded on `main`; both sites corrected in this same PR — see §1) | OBSERVED | `results.jsonl` seq 19 |
| Build B served by `carelink-support.medtronic.eu` | OBSERVED | `results.jsonl` seq 15 |
| Build B served by `carelink-support.medtronic.com` — refutes `docs/07:24`, `docs/01:68`, SECURITY-FINDINGS §S3 (as recorded on `main`; all corrected in this same PR — see §2) | OBSERVED | `results.jsonl` seq 20 |
| Catch-all ≡ host's own entry document, **5 of 5** host-pairs (counting rule below) | OBSERVED | `results.jsonl` seq 1≡3, 5≡7, 9≡11, 13≡14, 16≡17 |
| 5518 B maps to ≥ 2 distinct digests | OBSERVED | `results.jsonl` seq 3 vs seq 11 |
| `docs/08`'s `f637c8d0…` is the document, not the asset (`a054555a…` is the asset) — as recorded on `main`; `docs/08` corrected in this same PR (§3) | OBSERVED | `results.jsonl` seq 14 vs seq 15 |
| Build A asset digest `2a7fa8e7af519c2b` reproduces the value recorded 2026-10-08 | OBSERVED | `results.jsonl` seq 4; `AUTH-TENANT-FINDINGS.md:248` |
| `carelinkhp` entry doc md5 `6aedf6c4004fbb29a298bc62128480be` reproduces the recorded value | OBSERVED | `headers/carelinkhp-minimed-eu-root.b`; `CONFIG-NAMESPACE-DEEP.md:264` |
| 5 × `carelinkhp*.minimed.{eu,com}` names NXDOMAIN | OBSERVED (DNS) | `dns.jsonl` |
| `pow.crm.settings` `base.uri` tracks TLD, not product | OBSERVED | `results.jsonl` seq 2, 6, 10 |
| `pow.crm.settings` is unauthenticated on all three | OBSERVED | `results.jsonl` seq 2, 6, 10 |
| Region is not a variable on this host family | INFERRED from the two pairs above | assumption: nothing is injected per-region at the edge; a `Content-Length`/`Vary` split would falsify it, and none was seen |
| The CRM base tracks deployment rather than product | INFERRED | one key, three hosts, no `cua.crm.settings` probed |

## Correction to another pass's claim about this branch (area D, 2026-10-12)

Area D's counting-rule fix documents a KNOWN LIMIT that **names this branch**: it
states that my `for spec in ...` loop in `05-public-config.check.sh` would be
identified as a loop site and multiplied by 16, making `executed_05` **14 too high**.

**That is wrong, and this pass verified it by experiment rather than by argument.**
My loop contains **zero `check "` sites** — it is an inline `PASS=$((PASS + 1))`
branch — so `measure_assertions.py`'s `_loop_sites` counter, which is driven by
`^\s*check\s+"` with leading whitespace allowed, never sees it and never multiplies
it. Running that counter over this tree gives **41 check sites of which exactly 1 is
indented** — the pre-existing 16-family loop, not mine — so:

| `INLINE_05` | `executed_05` | runtime |
|---|---|---|
| 5 | 61 | **167 359** |
| 7 | 63 | **167 361** |

and the live suite prints `63 passed`, matching `INLINE_05 = 7`. The whole −2 versus
my `167 361` is `INLINE_05` 5 versus 7, nothing else; no ×16 multiplier is involved
and none could be.

Two consequences, stated so the next pass does not "fix" a correct number:

- **My `167 / 361` is correct and is not endangered by D's rule.** Do not restructure
  this addition to avoid a loop for D's benefit; there is nothing to avoid.
- **The misstatement is D's to correct, in D's script header.** Recorded here so the
  claim does not travel further unchallenged, and stated as a correction to another
  pass's *claim about my code* rather than as a change to their work.

**Not established, and deliberately not claimed:** whether build B's `hcp/*` surface
differs from build A's (not probed — the area is bundle identity, not route parity);
whether any host outside this list serves either build (no enumeration was performed);
and whether `docs/08`'s S3 finding's "five hosts" count is right in total — this pass
measured five hosts but the finding's host list was not re-derived.