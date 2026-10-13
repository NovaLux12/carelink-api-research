# Area D — is `commoncore-trials.medtronic.com` a real host?

**The `docs/10` §1 open row**, not a lettered `docs/11` area. Claim issue **#58**.
**Date:** 2026-10-13. **Method:** GET only, plus DNS resolution lookups.

**9 requests of a 10 cap.** GET only (6 HTTP GETs) and DNS `A` lookups (3), ≥2.5 s
declared and 2.5 s emitted **inside** a per-host `flock` on `.loop/host-<hostname>.lock`.
One request was held in reserve and **not** spent; §9 says why that reserve mattered.

**Verdict in one line: the host is REAL — it resolves, terminates TLS on a Medtronic
certificate, and answers — but the probe does not establish that it serves the
reports-broker route, because on this host family the `403` is the *unmatched-route*
oracle and a fabricated path is byte-identical to the real one.**

---

## 1. What the row actually asked, and what this pass can settle

The row was worth closing because the naming was OBSERVED and the existence was
INFERRED. The naming is now double-sourced from two independent passes, read off
the disk rather than re-fetched:

```
connect-src 'self' https://api-js.mixpanel.com https://*.amazonaws.com
wss://ws-mt1.pusher.com *.pusher.com cdn.jsdelivr.net google.com gstatic.com
fonts.googleapis.com fonts.gstatic.com https://clcloud-trials.minimed.com
https://commoncore-trials.minimed.com https://commoncore-trials.medtronic.com
```

Verbatim `connect-src`, from the header `carelink-trials.minimed.com` served:
[findings-log/2026-10-12-area-o-reports-namespace/headers/carelink-trials-minimed-com--c1-absent.h:18][source: findings-log/2026-10-12-area-o-reports-namespace/FINDINGS.md §6c]
and byte-for-byte the same line in a **different** pass on a **different** date —
[findings-log/2026-10-13-area-e-perkey-deployments/headers/carelink-trials.minimed.com--003-bulk-public.h:15].

So `https://commoncore-trials.medtronic.com` is in the vendor's own client allowlist.
That was already OBSERVED and this pass did not re-establish it. What this pass
attacks is the other half: **does the host exist, and does it serve?**

---

## 2. The host set, as measured this session

Nine requests. `*` marks a control. Every cell is OBSERVED 2026-10-13.

| seq | host | DNS | TLS | path | status | `x-amzn-errortype` | body sha256 |
|---|---|---|---|---|---|---|---|
| 1 | `commoncore-trials.medtronic.com` | **CNAME `d16wbx60y036c9.cloudfront.net`** → 4 A | — | — | — | — | — |
| 2* | `commoncore-trials.minimed.com` | — | DigiCert, SAN match, exp 2027-01-23 | `/reports-broker/v1/ocl` | **403** | `MissingAuthenticationTokenException` | `f249b63c…` |
| 3 | `commoncore.medtronic.com` | CNAME `d2te4je11hig0i.cloudfront.net` → 4 A | — | — | — | — | — |
| 4* | `commoncore.medtronic.com` | — | DigiCert, SAN match, exp 2027-04-03 | `/reports-broker/v1/ocl-probe-absent` | **403** | `MissingAuthenticationTokenException` | `f249b63c…` |
| 5 | `commoncore.medtronic.com` | — | DigiCert, SAN match | `/reports-broker/v1/ocl` | **403** | `MissingAuthenticationTokenException` | `f249b63c…` |
| 6 | `commoncore.medtronic.eu` | CNAME `d28ymzlhgkylij.cloudfront.net` → 4 A | — | — | — | — | — |
| 7 | `commoncore.medtronic.eu` | — | DigiCert, SAN match, exp 2027-04-03 | `/reports-broker/v1/ocl` | **403** | `MissingAuthenticationTokenException` | `f249b63c…` |
| 8* | `commoncore-trials.medtronic.com` | — | DigiCert, SAN match, exp 2027-01-23 | `/reports-broker/v1/ocl-probe-absent` | **403** | `MissingAuthenticationTokenException` | `f249b63c…` |
| 9 | `commoncore-trials.medtronic.com` | — | DigiCert, SAN match, exp 2027-01-23 | `/reports-broker/v1/ocl` | **403** | `MissingAuthenticationTokenException` | `f249b63c…` |

**Six GETs produced exactly one distinct response body.** Not "similar" — one
digest, `f249b63cb2fcb66b47e86f906c98f8fd912e82dd035b4e53d7e72fc1960cfd16`, 42 B,
`{"message":"Missing Authentication Token"}`.

### 2a. The host exists — and is not a parked name

This is the half the row could not previously state. Three independent signals,
each of which a parking namespace fails (OBSERVED):

1. **Resolution.** `commoncore-trials.medtronic.com` is a **CNAME to a CloudFront
   distribution** (`d16wbx60y036c9.cloudfront.net`, 4 A records in
   `3.166.65.0/24`), not an A record at a parking operator. `medtronic.com` is not
   on the repo's wildcard-parking list — that list is `*.carelink.{eu,com}` and
   `*.clcloud.eu` [AGENTS.md §7] — but "not on the list" is an argument from
   absence, so the CNAME is what settles it, and it settles it positively.
2. **TLS.** A **DigiCert Global G2** leaf certificate whose SAN matches the host
   exactly, `start date: Jul 9 2026`, `expire date: Jan 23 2027`, TLS 1.3. A parked
   name gets a certificate from whoever operates the parking service; a
   host-specific certificate issued to this exact name is a deliberate act.
3. **A vendor-shaped HTTP answer**, not a redirect to a sales page: HTTP/2 403 with
   `x-amz-apigw-id`, `x-amzn-requestid`, `x-cache: Error from cloudfront`, and a
   `via` chain of two CloudFront hops.

**INFERRED, and stated as such:** that the certificate and distribution are
Medtronic-operated rather than third-party-hosted. The issuer chain and the SAN
are OBSERVED; the ownership of the distribution is an inference from the vendor
naming it in its own CSP plus the certificate matching.

### 2b. What the probe does **not** establish — and cannot

**The `403` here is not a route match.** `/reports-broker/v1/ocl` and
`/reports-broker/v1/ocl-probe-absent` return the **same status, the same error
type and the same body digest** on `commoncore-trials.medtronic.com` (seq 8 vs 9)
and on `commoncore.medtronic.com` (seq 4 vs 5). Under Oracle A — the AWS API
Gateway family — `MissingAuthenticationTokenException` **is** the unmatched-route
error, `404` is never emitted, and a certainly-absent control is byte-identical to
the published root [docs/09 §2; findings-log/probe-2026-10-08/recon/AWS-GATEWAYS.md §0, §2].

So the honest reading is the one the controls force:

> **The `403` on `commoncore-trials.medtronic.com` is indistinguishable from the
> `403` on a path I made up. It therefore proves the host answers HTTP; it does
> not prove `/reports-broker/v1/ocl` is routed there.**

Had I probed the one path and reported "403 = live, token-gated", that would have
been AGENTS.md §6 item 2 — a hit read as more than it proves. The controls are
what make the negative defensible.

**Consequence for `docs/07` and `docs/01`.** Both record
`commoncore.medtronic.{eu,com}` as **"403 unauthenticated on every route probed"**
and read that as the routes existing [docs/01-hosts-and-estate.md:134;
docs/07-admin-portal-and-reporting.md:209-215]. Seq 4 shows that reading does not
hold: a fabricated sibling path on that host returns the identical body. **The
`403` on `commoncore.medtronic.*` is the no-route error, so those pages' "all 403"
is a statement about the gateway, not about six endpoints.** This does not
contradict the pages' *values* — the six paths are still the paths the vendor's own
config names — but it changes what the `403` is evidence *of*, and `docs/07` uses
it as evidence of existence.

---

## 3. ⚠ Two recorded claims this pass contradicts — both readings retained

Per AGENTS.md §2, where sources disagree, **give both**. Neither original is deleted.

### 3a. The recorded `502` is gone — the sibling now answers `403`

**Recorded (OBSERVED, 2026-08):** `commoncore-trials.minimed.com` → **502**,
`text/html`, "backend down" [findings-log/probe-2026-10-08/recon/CONFIG-NAMESPACE-DEEP.md:252],
carried into [docs/01-hosts-and-estate.md:108] and into area O's CSP note
[findings-log/2026-10-12-area-o-reports-namespace/FINDINGS.md §6c].

**This session (OBSERVED, 2026-10-13):** the same host, the same path
`/reports-broker/v1/ocl` → **403**, `application/json`,
`MissingAuthenticationTokenException`, 42 B (seq 2).

Both stand as written. The 502 was real when recorded; **whether the change is
recovery or a gateway reconfiguration is INFERRED and unresolved.** The direction
that matters is the same either way: the host now reaches an API Gateway rather
than failing to resolve an origin, so **area O's reading of the 502 as "an
origin-side DNS failure, not absence" no longer describes this host today.**

`docs/00`'s row — `commoncore.medtronic.{eu,com}` "still live at path but
**CloudFront 502**" [docs/00-summary-the-map.md:98] — is contradicted the same way
and the same day: seq 5 and seq 7 return **403**, not 502, on the identical path.

### 3b. `docs/07`'s brace was missing a case

`docs/07` writes the bases as `https://commoncore.medtronic.{eu,com}/…`
[docs/07-admin-portal-and-reporting.md:209-210]. The trials deployment has its own
pair, and its **config names the `.minimed.com` half** —
`nutrino.cc.broker.service.config.host` =
`https://commoncore-trials.minimed.com/reports-broker/v1`
[findings-log/2026-10-12-published-pointers/enumeration-scrubbed.txt:217] — while
its **CSP names the `.medtronic.com` half**
[area O §6c, above].

So on the trials deployment the vendor names **two different hosts in two different
documents**: the config points at `commoncore-trials.minimed.com`, the CSP allows
`commoncore-trials.medtronic.com`. Both are real and both answer `403` (seq 2, seq 9).

**INFERRED:** that the config/CSP split is deliberate — a second reports host
reserved for a subset of deployments — rather than a stale config entry. Nothing
observed here distinguishes the two. The alternatives are not separable without a
request no pass is authorised to make.

---

## 4. Naming convention that justified the candidate list

Three hosts, one path, each with a source. Nothing was guessed and nothing was
brute-forced:

| candidate | where the name comes from |
|---|---|
| `commoncore-trials.medtronic.com` | the CSP `connect-src` served by `carelink-trials.minimed.com` (read, not derived) |
| `commoncore-trials.minimed.com` | the recorded sibling, and the trials deployment's own config value (§3b) |
| `commoncore.medtronic.{eu,com}` | the brace in `docs/07`, probed to check whether the trials case was missing |

Paths: `/reports-broker/v1/ocl` is **the path this repo already records for exactly
this host family** (`docs/01:134`, `docs/07:209-210`, and the trials config value
above), so it is a vendor-named path, not an invented one. The control path is that
value with `-probe-absent` appended — same prefix, guaranteed-absent tail.

---

## 5. Controls — sent, and what each one actually proved

Controls went **first on every host** (AGENTS.md §8), so no verdict is
contaminated by the data it judges.

| # | seq | control | what it proved |
|---|---|---|---|
| b | 2 | `commoncore-trials.minimed.com` on the identical path, **the first HTTP request sent** | anchored the recorded `502` to this session — and showed it has become a `403` (§3a) |
| a | 8 | `commoncore-trials.medtronic.com` → `/reports-broker/v1/ocl-probe-absent` | **the load-bearing one.** It showed this origin answers a fabricated path *identically* to the real one, so the real one's `403` is not evidence of a route |
| a' | 4 | `commoncore.medtronic.com` → same absent path | the same test on the sibling, confirming the no-route reading is a property of the family and not of one host |

**The EU cell (seq 7) has no absent-path control** — the cap did not allow a fourth
pair. So seq 7 is **corroboration, not an adjudicated reading**, and is labelled as
such wherever it is cited. This is the one gap in the pass and it is stated rather
than papered over.

---

## 6. Oracle discipline: is the status code an oracle here?

Tested, not assumed. On `clcloud.*` the `403` line is uniform and useless
[docs/09 §2]; the question for this family was whether the same is true here.

**Result: it is.** All six GETs — two hosts, real and fabricated paths — return one
body digest. The gateway headers (`x-amz-apigw-id`, `x-amzn-errortype`) place these
hosts in the **AWS API Gateway family**, where per Oracle A the `403` is the
inverted no-route error. So:

- the `403` **can** confirm a negative (no route, or no route reachable by GET);
- the `403` **cannot** confirm a positive — exactly the inversion `docs/09 §2`
  documents for `clcloud.*`, now shown to hold for the `commoncore.medtronic.*`
  family as well.

`content-type` was used to discriminate throughout (`application/json` + 42 B, never
the `text/html` SPA fallback), and `--compressed` was sent on every request.

---

## 7. Spacing — measured, with the oracle stated

**Declared 2.5 s, emitted inside the per-host lock. Measured floor: 2.699 s**, from
the **kernel-set body-file mtimes at nanosecond resolution** — the clock-independent
series `docs/09 §4` requires — cross-checked against the harness `date` series.

Counting rule (stated so the number is reproducible): one gap per consecutive pair in
request order across the 7 captures that have an mtime (6 HTTP bodies + the `dig`
capture), giving **6 gaps**.

| gap | seconds |
|---|---|
| seq 1 → 2 | 101.113 (the attempt-1 abort sits in this interval) |
| seq 2 → 4 | 5.511 |
| seq 4 → 5 | 2.840 |
| seq 5 → 7 | 5.418 |
| seq 7 → 8 | 2.757 |
| seq 8 → 9 | 2.699 |

**Floor 2.699 s · max 101.113 s · 0 gaps under 2.5 s · 0 under the repo's ≥2 s
floor · span 120.339 s.** Every same-host gap is larger still.

**Two disclosures, because the instrument misbehaved and a reader deserves both:**

1. **`seq 6` has a negative duration** — `t_done` 0.668 s *before* `t_sent`, which
   is impossible. `seq 6` is the EU DNS lookup: `dig` had already exited when the
   `date` was read. This is the sixth occurrence of the defect `docs/09 §4` records.
   **It is why the `date` series is not the authority here.** In the `date` series
   the seq 6 → 7 gap reads **1.857 s** — apparently below the ≥2 s floor — while the
   mtime series for the same pair reads **2.757 s**. The apparent violation is an
   artefact of the broken row; the requests were correctly spaced.
2. **The two series do not have equal spans** (harness 22.230 s over seq 2→9 vs
   mtime 19.226 s over the same range). I checked whether that is the "collapsed
   spread" signature of an untrustworthy series [docs/09 §4] and it is **not**:
   the 3.004 s difference is exactly the two endpoints that do not coincide
   (`t_queued` precedes the first body write by the in-lock sleep + connect, and the
   last `t_done` follows the last body write by curl teardown). Per-request,
   `mtime − t_sent` is **+0.108 s to +0.495 s** on all six HTTP rows — every one
   positive, every one in the band a real request takes. **The mtime series is
   consistent with the harness series, not in conflict with it.**

*A methodological note against myself:* an intermediate version of that check
printed a "residual unexplained: 0.000 s" line which was a **telescoping identity**
(`lead + tail` is algebraically the span difference) and therefore evidence of
nothing. It is not in this write-up. The per-request table above is the real check.

---

## 8. One request was spent by a harness abort, and is accounted for

The first run of `probe.sh` aborted on request 1 under `set -u`: `t_sent`/`t_done`
were assigned **inside a subshell**, so the parent saw them unset. That request —
the DNS lookup on `commoncore-trials.medtronic.com` — **was sent**, and its capture
is on disk.

It is **carried forward, not re-sent.** Re-issuing would have cost a second request
for an answer already captured, and would have put two rows in the ledger for one
fact. Its artefacts are preserved verbatim under `attempt1-aborted/`.

Its `t_sent` and `t_done` are recorded as **bounds, not measurements**
(`t_sent ≥ t_queued + 2.5 s`; `t_done ≤` the kernel mtime), because the abort
destroyed the exact values and inventing them would be the fabrication this repo
exists to prevent. The row carries a `timestamp_note` saying so. **This is the only
row in the ledger whose timestamps are bounds, and it is the row whose timing nothing
depends on** — it is a DNS lookup on a host not otherwise probed in this pass, and
its gap to the next request on that host (seq 8, seq 9) is ≥2.6 s on the mtime series.

`probe.sh` as committed contains the fix and reproduces the whole 9-row ledger from
the attempt-1 capture plus 8 fresh requests.

---

## 9. The reserve, and why it was worth less than it cost

One request of the cap was **not** spent. It was held for re-issuing a gateway
failure, which `docs/09 §4` requires — a `502`/`503`/`504` from this family is a
failure and never an absence, and area M lost a whole re-measure to exactly that.
**It was not needed**, because no request in this pass returned a gateway error: all
six GETs returned a well-formed `403` and all three lookups returned `NOERROR`. The
reserve is recorded unused rather than quietly folded into the total.

---

## 10. Negatives, recorded as first-class results

- **No route was established on `commoncore-trials.medtronic.com`.** The `403` is
  indistinguishable from the fabricated-path control, so the pass produces
  **no evidence of existence for `/reports-broker/v1/ocl`** on any of the four
  hosts — including the two `commoncore.medtronic.{eu,com}` hosts `docs/07` lists six
  endpoints on.
- **The EU cell is uncorroborated by a control** (§5) and is the weakest cell here.
- **TLS ownership is INFERRED** (§2a), not established; no CT or PKI lookup was made.
- **Nothing was learned about the response bodies**, because no body was returned:
  all six GETs are the same 42-byte gateway error.
- **No POST, no OPTIONS, no authentication, no token exchange.** `commoncore`'s
  report *bodies* remain blocked on a clinician-scoped token, unchanged by this pass
  [docs/11 *Already blocked on a token*].

---

## 11. What "closed" means for this row

The claim issue offered two ways to close it, and said **both negatives count**:
"no trials host exists and the CSP entry is stale", or "a host exists but is
origin-side dead like its sibling".

**Neither is what the evidence shows.** The third possibility is the one that
happened: **the host exists, resolves, terminates TLS and answers — and the recorded
`sibling` is no longer origin-side dead.** So the row is closed on the *naming*
question it actually posed, with the route question explicitly left open:

- **`commoncore-trials.medtronic.com` is a real host.** INFERRED→**OBSERVED**:
  CNAME to CloudFront, host-specific DigiCert SAN match, gateway-shaped HTTP answer,
  three independent signals a parked name cannot produce.
- **`docs/07`'s `commoncore.medtronic.{eu,com}` brace is confirmed incomplete** — the
  trials case is real and is now named, alongside the finding that the trials
  deployment's *config* names a *different* trials host than its *CSP* does (§3b).
- **What is NOT closed:** whether `/reports-broker/v1/ocl` is routed on any of these
  four hosts. The `403` cannot answer that, and saying so is the pass's main
  negative.

---

## 12. Successor

Recorded as a **dated addendum** in `docs/11`'s *Already blocked on a token* section,
where area O's 2026-10-12 addendum already lives — **not** a new letter (A–Z are all
in use and the gate's area pattern would reject a two-letter heading twice). It is
carried in [docs/11-suggested-research-areas.md](../docs/11-suggested-research-areas.md).

---

## Files in this directory

| File | What |
|---|---|
| `FINDINGS.md` | this document |
| `probe.sh` | the harness as sent, carrying the attempt-1 reconstruction |
| `results.jsonl` | **9 rows, one per request**, three timestamps each |
| `run.log` | ordered request log, same three timestamp columns |
| `headers/` | per-request header, `-v` (TLS + wire trace) and DNS captures |
| `bodies/` | the 6 response bodies (42 B each — one digest) |
| `attempt1-aborted/` | the aborted run's capture, preserved verbatim |
| `spacing.txt` | the spacing measurement, its counting rule, and both series |

**Request accounting: 9 of a 10 cap.** `wc -l results.jsonl` = **9** = the number in
that line, in both directions.