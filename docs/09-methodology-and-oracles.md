# Methodology and oracles

How this research was actually done, so it can be repeated or extended without
re-deriving the hard parts — or repeating the mistakes. Everything here comes
from the append-only logs; the method facts were re-verified three times
[source: findings-log/probe-2026-10-08/work/METHOD-FACTS.md]. Extends
[`00-summary-the-map.md`](00-summary-the-map.md).

Legend — **OBSERVED** = seen in a live response · **PUBLISHED** = in a vendor
document served without a login · **INFERRED** = reasoned, not seen.

Citations are `[source: findings-log/<file> §n]`; inside tables the bare
filename is the same file: `VERSION-AXIS` =
`findings-log/probe-2026-10-08/recon/VERSION-AXIS.md`, `AWS-GATEWAYS` =
`findings-log/probe-2026-10-08/recon/AWS-GATEWAYS.md`, `HCP-SCHEMA` =
`findings-log/probe-2026-10-08/recon/HCP-CONFIG-SCHEMA.md`, `METHOD-FACTS` =
`findings-log/probe-2026-10-08/work/METHOD-FACTS.md`, `CLAIM-AUDIT` =
`findings-log/probe-2026-10-08/audit/CLAIM-AUDIT-2026-10-09.md`, `CONFIG-DEEP` =
`findings-log/probe-2026-10-08/recon/CONFIG-NAMESPACE-DEEP.md`, `CONFIG-NS` =
`findings-log/probe-2026-10-08/recon/CONFIG-NAMESPACE.md`, `RECON-SUBDOMAINS` =
`findings-log/probe-2026-10-08/recon/RECON-SUBDOMAINS.md`, `CROSS-REGION` =
`findings-log/probe-2026-10-08/CROSS-REGION-CONFIG-FINDINGS.md`, `COMMONCRAWL` =
`findings-log/probe-2026-10-08/recon/cc/COMMONCRAWL-URLS.md`, `CHUNK-CORPUS` =
`findings-log/probe-2026-10-08/CHUNK-CORPUS-FINDINGS.md`, `JSMAP-HUNT` =
`findings-log/probe-2026-10-08/recon/JSMAP-HUNT.md`, `PROBE-FINDINGS` =
`findings-log/probe-2026-10-08/PROBE-FINDINGS.md`, `DRIFT-AND-NEW` =
`findings-log/probe-2026-10-08/recon/DRIFT-AND-NEW-2026-10-10.md`.

## 1. The constraints every pass ran under

| Constraint | How it was honoured |
|---|---|
| Read-only | GET and empty-body probes only; no `-X` overrides, no POST that writes. The one credential-adjacent act in the whole project was sending the published bundle key to the reports host to test validity — it returned 403 [source: findings-log/probe-2026-10-08/SECURITY-FINDINGS.md §Scope, S3] |
| Unauthenticated | no `Authorization`, no `Cookie`, no token, no api-key of the vendor's. A dummy `X-Api-Key: DUMMY-NOT-A-KEY-000000000000` was the only auth-ish header ever sent [AWS-GATEWAYS §8] |
| Low rate | ≥1.2 s spacing on probe rounds; ≥2 s per host enforced in-harness (`last_hit[]`); 2.5 s measured floor on the gateway sweep; ≥3 s on archive calls [VERSION-AXIS §Method; AWS-GATEWAYS §1; recon/ARCHIVE-URLS.md §0] |
| Hard request caps | per pass, and never exceeded: 30 (22 used), 60 (42 used), 80 (80), 70 (70), 90 (90), 26 archive, 41 Wayback, ~600 total across the day's passes [CONFIG-NS §Method; HCP-SCHEMA §1; CONFIG-DEEP §cap; VERSION-AXIS §Method; AWS-GATEWAYS §1; COMMONCRAWL §0; SECURITY-FINDINGS §Scope] |
| No dev/stage contact | dev/stage/test/load hosts are **enumerated passively and listed, never probed** [PROBE-FINDINGS §1; RECON-SUBDOMAINS §7.2] |
| No scanning | no port scans, no DNS bruteforce, no vhost fuzzing, no path enumeration beyond bounded, justified candidate lists [RECON-SUBDOMAINS §0; CONFIG-NS §Method] |
| Hosts that looked internal | recorded and left alone — every internal-looking name refuses the public network [RECON-SUBDOMAINS §4.5] |

## 2. Oracle A — the AWS API-Gateway family (inverted)

On `clcloud.*` and the five `*.execute-api.*.amazonaws.com` gateways the
surface is AWS API Gateway behind CloudFront, so every response carries
`x-amzn-errortype` — and Amazon uses **different error types for "no route"
versus "reached a backend authorizer"** [source: VERSION-AXIS §1].

| Signal | Meaning | Verdict |
|---|---|---|
| `x-amzn-errortype: MissingAuthenticationTokenException` (403, 42 B) | **no matching route** | dead — path does not exist |
| `UnauthorizedException` + `x-ca-err: 990` (401) | request reached Medtronic's Layer7 authorizer | live — route exists, token-gated |
| no errortype (200/204) | public | live, unauthenticated |

**The inversion, stated plainly:** on these gateways **403 is the unmatched-route
error**, a 404 is never emitted (it is simply not in the gateway's response
vocabulary — zero 404s in 90 requests), so "403 = exists, auth-gated" is false
and "404 = absent" is unreachable. A certainly-absent control UUID returns
byte-identical output to the published root. **403 can never positively confirm a
route; it only ever confirms a negative** [source: AWS-GATEWAYS §0, §2].

The full oracle needs **both** methods, or it under-reports liveness:

```
GET 403 + OPTIONS 403 → dead
GET 403 + OPTIONS 200 → live, POST-only      (CORS headers present)
GET 401              → live with GET
GET 200/204          → public
```

`access-control-allow-origin: *` on an OPTIONS request is the cleanest proof that
a resource exists with no GET method — that is how POST-only
`v6/display/message` was found [source: VERSION-AXIS §1]. **But
`access-control-allow-methods` is not a register of the route's methods:**
`carepartner/v13/display/message` advertises `OPTIONS` on its preflight and is
GET-capable (`GET` → 401 `UnauthorizedException` + `x-ca-err: 990`) on all three
hosts (OBSERVED, 3-of-3 with a captured GET+OPTIONS pair each,
[findings-log/2026-10-12-csr-cross-host/FINDINGS.md]). The list therefore
**cannot be read as evidence that a method is absent**. Settle **GET**
registration from the GET probe and treat the CORS method list as corroboration
only; the header's *mechanism* is not established (n = 3 routes, two of which
merely agree with it). The one positive
direction on the bare gateways: on `dialog-lite`, `500
InternalServerErrorException` proves a path **is** matched (the Lambda raised),
which is how the stage-wide catch-all was identified; on `patient-timeline` 403
positively confirms *no* GET/OPTIONS route [source: AWS-GATEWAYS §2, §11].
`x-cache: Miss/Error from cloudfront` tracks the same split but is a weaker,
derived signal — keep `x-amzn-errortype` as the authority. **Latency is not an
oracle**: host dominates, not version [source: VERSION-AXIS §1].

## 3. Oracle B — the portal family (reliable)

On `carelinkhp.*` / `/hcp/*` the status set **is** reliable, because the SPA
fallback is distinguishable by content-type and the namespace is case-sensitive
[source: HCP-SCHEMA §3, §4]:

| Response | Meaning |
|---|---|
| `200` + `application/json` | key exists, published unauthenticated |
| `401` + `InvalidToken` | **key exists but is token-gated** |
| `404`, 0 bytes | **key does not exist** |
| `412`, 0 bytes | header check failed (missing/invalid `X-System-ID`) |
| `405` | exists, POST-only |
| `200` + `text/html` + 5518 B | SPA fallback — says nothing about existence |

Validated with a positive control: `…/public/personal/media/config/eu` → 401
(exists, gated) versus `…/public/personal/media/config` → 404 and a fabricated
key → 404. And with a case control: `CSU.CONTROL.CODES.SETTINGS` → 404 while
`cua.control.codes.settings` → 200, so a lower-case 404 is a true absence. Two
controls convert 28 "not found" verdicts into a defensible negative
[source: HCP-SCHEMA §4, §7].

**What neither oracle can prove:** content behind a gate; and on the `configs/v1`
S3 bucket, `AccessDenied` is returned for absent keys too — a 403 there is
indistinguishable from "exists but unreadable", so the honest phrasing is "no
evidence of existence", never "confirmed absent" [source: CONFIG-NS TARGET 3;
AUTH-TENANT-FINDINGS §6].

### Oracle C — the Auth0 tenant family (two 404s, not one)

Added 2026-10-12 from area I's controls. The `carelink-login.*` hosts are
Auth0's tenant front door, and they answer a `404` in **two structurally
different ways**. Discriminating on status alone — the advice everywhere else on
this page — collapses both into "not found" and loses the distinction.

| Signal | Meaning | Verdict |
|---|---|---|
| `404` + `content-type: text/plain; charset=utf-8`, 10 B, **`x-auth0-not-found: 1`** | the tenant's front door **does not know this path** | absent — unrouted |
| `404` + `content-type: application/json; charset=utf-8`, 60 B, `cache-control: no-cache`, **no** `x-auth0-not-found` | reached Auth0's API layer and a handler had nothing to return | **routed, resource absent** — a different claim, and for an endpoint a document advertises, the one worth making |
| `200` + `application/json` | the document exists | live, public |

`x-auth0-not-found: 1` is the better oracle on this host family: it appears on
the unrecognised path and on **nothing else** across area I's 19 responses, so
it identifies "this path is unknown to the tenant" where a status code cannot.

**INFERRED, and it matters that it is labelled:** that the two signatures
correspond to two different *routing states*. Observed is the separation; the
meaning assigned to it is not. Nothing in area I depends on the reading — only on
the fact that the two shapes are distinguishable, which lets a sweep say "absent"
and "advertised-but-absent" as different verdicts rather than one.

**Establish it per host.** One host's 404 proves nothing about the next host's
front door, which is why area I spent a second control on a differently
configured tenant and recorded both digests rather than assuming
[source: findings-log/2026-10-12-area-i-auth0-tenant-behaviour/FINDINGS.md §4].

## 4. The trap list

| Trap | Detail | Fix |
|---|---|---|
| Parked wildcard namespaces | `*.carelink.{eu,com}` and `*.clcloud.eu` are wildcard DNS on parking operators — a random, certainly-unregistered string resolves and 302s to a parked page; a Let's Encrypt wildcard reissued on a ~90-day cadence injects the names into every CT scraper. 49 collected names are false positives | never attribute a name from this space to Medtronic; the proof is a name that cannot exist [RECON-SUBDOMAINS §3; PROBE-FINDINGS deep §8] |
| 5518-byte SPA fallback | `carelinkhp.minimed.eu` returns 200 `text/html`, exactly 5518 B, for **every** unknown path — including fabricated chunk names. Nearly stored 225 copies of `index.html` in the chunk sweep | discriminate on `Content-Type`, never on status; `carelink.medtronic.eu` serves the same page gzipped, so compare sizes after decompression [CHUNK-CORPUS; CONFIG-DEEP TARGET 5] |
| Unconditional gzip | `carelink.minimed.eu` serves gzip ignoring `Accept-Encoding` (RFC 9110 §8.4); hurl's jsonpath returns `none` because hurl only decodes what it asked for — which is why the config regression is a shell script, not a `.hurl` file | `curl --compressed`, or decompress locally; do not re-request [HURL-05 header; README rule 6] |
| `index.commoncrawl.org` unreachable | both attempts failed (`curl (56)` / `(52)`) while `data.commoncrawl.org` over the identical TLS path worked — a host-level failure, not rate limiting | used the bulk path (binary-search `cluster.idx`, ranged `cdx-NNNNN.gz` fetches); coverage capped to two crawls instead of ~100, and that cap is stated rather than papered over [COMMONCRAWL §0–§1] |
| `curl -d` forcing POST | an earlier "GET vs POST" matrix was wrong because `-d` forces POST — cases labelled "GET with body" were actually POSTs | re-probe with a clean GET and discriminate on `x-amzn-errortype`, **not** the status. There is no `Allow` header to fall back on: across all 42 captured `clcloud.*` responses on disk (26 from 2026-10-11, 16 from 2026-10-12) **not one carried `Allow`**, so the GET probe is the only method authority this host family offers [METHOD-FACTS §Correction]. **That is a fact about `clcloud.*`, not about the vendor's edge, and must not be generalised:** on the `carelink.*` **patient** plane `Allow` is common — `/patient/monitor/data` carries `Allow: HEAD, GET, OPTIONS` and `/patient/dataUpload/recentUploads` carries `Allow: POST, OPTIONS` ([`06-patient-api-surface.md`](06-patient-api-surface.md)), though `/patient/connect/data` carries none. Area O found it is **per-route** there too: across 24 responses on `/patient/reports/*` it appears on **9 of 24**, exactly the POST-only `405`s, and on no `401`, `400` or `404` [findings-log/2026-10-12-area-o-reports-namespace/FINDINGS.md §6a] |
| CORS `allow-methods` read as a method register | `access-control-allow-methods` is gateway CORS configuration, not the route's registered methods. `carepartner/v13/display/message` advertises `OPTIONS` and is GET-capable (`GET` → 401 `UnauthorizedException` + `x-ca-err: 990`) on all three hosts | settle method registration from the **GET probe**; treat `allow-methods` as corroboration. The header is also not canonicalised: two routes that are *both* GET-403 and OPTIONS-200 advertise different lists, in different orders, with different allow-headers (OBSERVED: `csr/v2` → `OPTIONS,POST`, bare `v2` → `POST,OPTIONS` + three extra allow-headers) [findings-log/2026-10-12-csr-cross-host/FINDINGS.md]. Area Z then showed the header is a **per-route constant** — 9 of 9 cells per route across 3 hosts × 3 `Origin` conditions, never varying by request — while `ACAO` itself is the literal `*` in **45 of 45** cells and is **not** an echo of `Origin` [findings-log/2026-10-12-area-z-origin-reflection/FINDINGS.md §4–§5] | pin the **exact** value, not `contains "POST"`: a reordering of the same method set is a change this header makes and a `contains` assertion cannot see. The two orderings are now pinned verbatim in `04-deep-surface.hurl`, and `Allow: POST, OPTIONS` on a report route is pinned verbatim in `03-patient-api.hurl` |
| jq `//` swallowing `false` | a country sweep conflated "key absent" with "value false" | re-derive with `has()` [PROBE-FINDINGS deep §8] |
| Mis-offset CDX fetches | an earlier pass's computed byte ranges landed on alphabetical neighbours; the `raw-*.cdx` artefacts look like results and are not | corrected fetches kept; wrong artefacts labelled misleading on disk [COMMONCRAWL §1] |
| Self-measurement artefact | `deep-matrix.jsonl`'s `x-api-key: "len=10"` is the length of the scrubber's own `[REDACTED]` placeholder — the pass measured itself | length column ignored; further scrubbing added [CONFIG-DEEP §Measurement artifact] |
| A gap below the harness's own declared `sleep` | **Observed in four passes, same signature, and area Z makes it five occurrences in one run — but area O breaks the pattern's premise, because its harness never called the sleep at all.** In areas B, X and Z each `req()` ends with an unconditional `sleep 2.5` and timestamps with `date` *before* `curl`, so a same-host gap **cannot** be under 2.5 s — yet area B measured 2.033 s, area X measured **2.291 s** (`clcloud.minimed.eu`, req 12→13), and **area Z measured 5 such gaps out of 48, minimum 2.042 s** (2.044 / 2.449 / 2.042 s on `.eu`, 2.470 s on `.com`, 2.449 s on `-trials`). All satisfy the repo's real `>=2 s` floor, so none is a rule breach. **Area O is not in this class and must not be counted as if it were:** it *declared* `DELAY=2.5` and the `sleep` was never emitted, so all 21 of its same-host gaps are sub-floor by construction — a **rule breach**, not a timing artefact | Record the measured floor and the sub-declared gap in the pass's own accounting, **never rounded away**, and do not assert a cause. Area B's INFERRED reading was a transient backwards clock step (the error appears then cancels against its neighbour); that is **not** established, and a post-hoc edit to `run.log` would produce the same arithmetic, so neither candidate is excluded. Open: *why does a sub-declared gap appear at all?* — **n = 4 passes, 9 occurrences as of area O (B, X, Z and O). Area D's own run adds 14 more, so across five passes the figure is 23 — see the next row, which carries D's 14. Zero requests needed, answerable entirely from timestamps already on disk.** ⚠ **Area O showed the in-band timestamps are not always trustworthy**, and shipped a better oracle: `date` read before curl can come back **later** than the body curl then wrote, which makes `mtime - t0` negative and manufactures a gap that never happened. **Prefer the body-file mtimes and cross-check against `t0`; if `mtime - t0` is negative, the `t0` is corrupt, not the request concurrent** [findings-log/2026-10-12-area-o-reports-namespace/FINDINGS.md §1a]. Not filed as a `docs/11` area because **every letter A–Z is now in use** and a two-letter heading is invisible to the gate's area checks (verified against its own regexes), so adding one would leave the priorities page's stated count disagreeing with its own contents ⚠ **ANSWERED 2026-10-12 by area D, and not the way it was framed:** the gaps were not sub-declared at all — the `date` series is the faulty instrument (that pass recorded 11 negative request durations, which is impossible), while the kernel mtime series shows **0 of 118 gaps under 2.5 s**. The mechanism by which `date` misreports is still **not** established and no cause is asserted; a post-hoc edit to `run.log` remains indistinguishable. **See the next row for the method and its counting rule.** |
| **The `date` series itself is the suspect** — use body-file mtimes instead | **Area D answered the open question above, and the answer was that the instrument is the problem.** That pass made the same finding four passes running (14 gaps under 2.5 s, min 1.642 s) **and recorded 11 of 119 requests with a NEGATIVE duration** — `t_done` earlier than `t_sent`, which is impossible — so those timestamps cannot all be faithful. **The settling evidence was on disk the whole time and nobody looked:** `curl -o bodies/cc-XX.json` makes the **kernel** set each body's mtime at write time, and that series is independent of the harness's clock. Measured: **118 gaps, min 2.575 s, max 2.636 s, 0 under 2.5 s and 0 under the `>=2 s` floor** (OBSERVED, [findings-log/2026-10-12-area-d-country-sweep/spacing.txt](../findings-log/2026-10-12-area-d-country-sweep/spacing.txt)). **So the answer is: the requests were spaced correctly and the `date` readings are what moved** — which does **not** explain the mechanism, and no cause is asserted for it | **When the harness writes response bodies, measure spacing from their mtimes, not from `date`.** **Counting rule:** one gap per consecutive pair **in request order** (from `run.log`), measured `mtime[n+1] − mtime[n]`, including error envelopes; N bodies give N−1 gaps. **Validate the series before trusting it** — git does **not** preserve mtimes, so on a fresh clone or `git archive` every body carries the checkout time and the spread collapses to 0.0 s; a trustworthy run's mtime span **equals the harness span** (area D: 304.9 s both ways). Report the `date` series alongside, never instead |
| A count the gate's regex cannot see | `README.md` stated **two** assertion counts. Line 440 reads `147 pinned assertions` and the gate reads it. Line 384-385 reads `` `regression/hurl/` holds **147⏎pinned assertions** `` — **wrapped across a line break inside a bold span**, so the gate's pattern `(\d+) pinned assertions` does not match it, the site was already satisfied by line 440, and the numbers check reported `ok`. It was reporting green about a value it had never seen | the numbers check is **not** evidence that every count site agrees — it only sees counts on one line with a single space before the phrase. Verify counts by re-running `scripts/measure_assertions.py` and grepping for the number yourself. **Not fixed here**: changing the gate's own pattern in the same PR the gate passed is a decision for a maintainer, not a side effect of a research pass |
| A corpus count scoped to one host family | The CORS confound stood for two passes on a count that was right and a scope that was not: of 24 captured `200` heads, 14 carried `access-control-allow-origin` and the 10 that did not were labelled "on a different host surface" — **4 of them are `clcloud.*` discovery documents, across the three cumulus hosts (two on `.com`)**. The false premise propagated into five pages | before scoping any corpus count to a host family, resolve each counted item to its host **from the committed harness that fetched it**, not from the filename prefix. `disc-*` meant `clcloud.*`; `config-*`/`countries-*` meant `carelink.*`. The 4-of-10 table is in [`2026-10-12-area-b-v12-routing/FINDINGS.md`](../findings-log/2026-10-12-area-b-v12-routing/FINDINGS.md) §Correction — **not** in `2026-10-12-area-x-cors-separation/FINDINGS.md` §4, which covers only that pass's own 25 rows and names no capture. Separately: those four heads are **gitignored** (`published-pointers/.gitignore` lists `docs/`), so the 24/14/10 split cannot be re-derived from a clean clone |
| A ledger that cannot resolve the delay it claims | Area I's ledger timestamps at **1-second resolution**, so the 12 same-host gaps quantise onto 2.000 s and 3.000 s and the declared 2.5 s sleep is **unmeasurable from the ledger**. The measured floor of 2.000 s is a **lower bound**, not a measurement — the same class of defect as the sub-declared gap above, but quieter: that one produced gaps *below* the declared delay and looked like a clock fault, this one produces plausible-looking numbers that simply cannot answer the question asked | state the resolution next to the number ("measured floor 2.000 s **at 1-second ledger resolution**, which cannot resolve the declared 2.5 s") and point at the harness as the authority for the delay itself. Emit **millisecond** timestamps (`date -u +%FT%T.%3NZ`) in new harnesses. Do not report a 2.000 s floor as though it evidenced 2.5 s of spacing [findings-log/2026-10-12-area-i-auth0-tenant-behaviour/FINDINGS.md §Method] |
| A transcribed identifier mistaken for a disagreement | `carelink-login.minimed.com`'s second JWKS `kid` was recorded **20 characters long where the live string is 21** — one `Q` dropped, in two files at once. The companion defect on another tenant was a transposition, which `docs/02` §8 had already caught by holding both readings open; a **deletion** leaves only one reading, so no amount of cross-file comparison finds it | compare identifiers **in code** against a named `file:line`, never by eye — `findings-log/2026-10-12-area-i-auth0-tenant-behaviour/corpus-audit.py` prints observed-vs-corpus token matches with their locations. A recorded identifier that appears in no capture is not evidence of agreement. Both of area I's corrections were found this way, and **both were against the more thorough earlier pass** [findings-log/2026-10-12-area-i-auth0-tenant-behaviour/FINDINGS.md §6] |

## 5. Verification discipline — the four ways this project has been wrong

Each of these actually happened. Each produced a mechanism, not an apology.

**1. A claim without evidence.** The `pde/v3` status was recorded as 401 in the
notes when the live probe returned 403; a review round then "corrected" the
architecture doc from 403 to 401, and a later round marked it VERIFIED — four
rounds, all trusting the previous hop. Re-probed twice: **403**. The distinction
matters: on `clcloud.*` that body is a gateway-level rejection (the host does
not route the path at all), not an app-level token gate. **Fix:** re-probe the
numbers, don't re-read the notes; the correction-of-a-correction is recorded as
such [source: CLAIM-AUDIT §FOUND WRONG]. Same class: the METHOD-FACTS `curl -d`
artifact, and the S3-bucket 403 that was never evidence of non-existence even
though the conclusion it supported held [source: METHOD-FACTS; CONFIG-NS].

**2. A grep that hit without proving.** "Neither `main.js` nor `runtime.js`
contains a `sourceMappingURL` comment" was false — `hp-main.js` contains the
token at byte offset 1791807, as a `worker-loader` string literal, not a
directive. The conclusion (no source maps) survived; the stated reason did not.
Same class twice more: the apparent `ngp`/`guardian` matches in the clinic bundle
were zxcvbn dictionary noise (case-sensitive grep: 0 hits), and the patient
bundle's three "NGP" hits were Samsung user-agent strings. And once more in the
2026-10-10 drift sweep: a prose note quoted the family-map hash as `215e6671de09`
when it actually hashes to `8ce419a22fd3` on every artefact on disk and live —
the pinned regression assertion had been right all along and the hand-written
note was wrong, which is how it surfaced [source: DRIFT-AND-NEW §Documented
defect]. **Fix:** prove what a hit *is* — literal vs directive, byte offset,
case-sensitive control — and replace sampling with an exhaustive offline grep
plus 62 live probes and written reopen conditions; "values quoted in prose notes
are not evidence. The pinned assertion is" [source: CHUNK-CORPUS §source maps;
HCP-SCHEMA §4; recov/PATIENT-APP-VOCABULARY.md; JSMAP-HUNT §7; DRIFT-AND-NEW].

**3. A hash comparison over a lookup that silently returned null.** The
cross-region config comparison reported four "SAME" rows where only three were
same: the walker looked up dotted-nested paths with a single
`dict.get("a.b.c")`, got `None`, and hashed `None` — two genuinely different
values produced identical digests and looked like agreement. **Fix:** walk the
path segment-by-segment and assert the resolved type; `HURL-05` treats an
all-zero digest (`e3b0c442…`, the sha256 of the empty string) as a failure
rather than a comparison. "A hash check over a lookup that can silently return
`null` will manufacture consensus" [source: CROSS-REGION §Verification note;
HURL-05].

**4. A dead test-file typecheck.** In the bridge repo, neither `npx tsc
--noEmit` nor CI could see a type error in any test file — the base tsconfig
excludes `test/` — which is how a TS2322 in a test went unnoticed. **Fix:**
`tsconfig.test.json`, which has to restate both `include` and `exclude` (the
base excludes `test/`) and set `rootDir: "."` (the base sets `rootDir: "src"`);
verified by injecting a type error and watching CI's new step fail. Recorded
downstream in the consumer repo:
[source: [NovaLux12/carelink-bridge CHANGELOG #87](https://github.com/NovaLux12/carelink-bridge/blob/main/CHANGELOG.md)].

The generalisation behind all four: a check that *looks* like it ran is worse
than no check, because it converts a gap into a green tick.

## 6. The append-only log / canonical-docs split

`docs/` is canonical, synthesised, dated. `findings-log/` is append-only,
verbatim, dated — the audit trail. **`docs/` supersedes `findings-log/` where
they disagree**, and the logs are kept anyway, because conclusions were retracted
and re-derived and that history is itself evidence (a retraction you cannot see
is a claim you cannot audit) [source: README].

Practical consequences, all visible in this repo:

- Corrections are **appended, never edited away**: the `pde/v3` 403→401→403
  chain, the S3 scope widening, the source-map claim's wrong reason, and the
  four-tenant upgrade all live in the logs with their reasoning intact
  [source: CLAIM-AUDIT; SECURITY-FINDINGS addendum; CHUNK-CORPUS;
  AUTH-TENANT-FINDINGS §8].
- Claims are pinned by a regression suite so they fail loudly rather than rot:
  `regression/hurl/` holds 199 assertions (413 execute per run, counting the
  16-family loop expansion and hurl's status-line checks); exit 0 = the public
  surface has not drifted *past the pinned values* since 2026-10-08
  [source: docs/00-summary-the-map.md;
  findings-log/probe-2026-10-08/work/VALIDATION-RUNBOOK.md Tier 5].
- **⚠ Corrected 2026-10-12 — the counting rule counted INDENTATION as "inside
  the loop", and said 423 where 363 was right.** Area D added four checks
  inside an `if`/`else` in `05-public-config.check.sh`; they are indented, and
  the rule read indentation as loop membership, so it multiplied four
  once-executed checks by 16. `executed_05` went **61 → 125** and the derived
  runtime **359 → 423**, against the **363** the live suite printed. **Both
  numbers stood in prose** until the owner ruled it a rule bug rather than a
  prose bug. The rule is now **structural** — a check site is a loop site iff a
  `for`/`while`/`until` lexically encloses it — and measures loop structure, not
  layout. **The pre-fix figures (171/363) are stated here rather than at the count
  site above, which the merge corrected to 176/378 — so the retraction history
  stays visible**, and the evidence that the fix discriminates rather than merely
  differing: the old rule returns **1** loop site at base `b275e2b` and **5** on
  area D's branch, while the corrected rule returns **1** on **both**, and
  `executed_05_derived` (65) now equals the live `N passed` (65) without being
  told it. `scripts/measure_assertions.py --self-test` exercises the rule
  against 16 synthetic shell shapes and exits non-zero on any regression
  [source: scripts/measure_assertions.py header + `_loop_sites()`;
  findings-log/2026-10-12-area-d-country-sweep/FINDINGS.md §11]. The config
  checks deliberately pin the vendor's *current wrong* `lhpro` bound so a vendor
  fix breaks the test and updates the note [source: HURL-05].
- Where a pass's own evidence could not be written to disk, the log says so
  instead of implying it exists: the 2026-10-10 drift sweep is explicitly a
  **reconstruction from the agent's report**, "re-verify before treating any row
  as OBSERVED" — a provenance caveat, not a finding [source: DRIFT-AND-NEW
  §Provenance].
- Redaction rules (six of them in the README) exist because breaking them
  leaked something: never commit a credential, never publish internal hostnames,
  never publish raw archive captures, never report a parked-namespace name,
  discriminate on content-type not status, use `curl --compressed`
  [source: README §Rules].

## 7. Reproducing

The pass harnesses and machine logs are named in each source file and are the
authoritative artefacts: `vaxis-probe.sh` / `vaxis.jsonl` (oracle + 70-cell
sweep), `aws-gw-probe.py` / `gw-probe-results.jsonl` (cap + delay + scrub),
`hcp2probe.sh` / `hcp2-matrix.jsonl`, `deep-probe.sh` / `deep-matrix.jsonl`,
`cdx/q.sh` + `request-log.tsv` (archive passes), `locate.py` / `qr.sh` /
`ccparse.py` (Common Crawl bulk path), and `hurl/run.sh` + `05-public-config.check.sh`
(drift detection) [source: VERSION-AXIS §8; AWS-GATEWAYS §9; HCP-SCHEMA §1;
CONFIG-DEEP §cap; COMMONCRAWL §10; HURL-05]. Re-derive the oracle controls
before trusting any future 404 or 403 from these hosts [source: HCP-SCHEMA
§10].
