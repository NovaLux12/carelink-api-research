# The `commoncore-trials` pass — is `commoncore-trials.medtronic.com` a real host?

**The `docs/10` §1 open row**, not a lettered `docs/11` area. Claim issue **#58**.
**Date:** 2026-10-13. **Method:** GET only, plus DNS resolution lookups.

**9 requests of a 10 cap.** GET only (6 HTTP GETs) and DNS `A` lookups (3), ≥2.5 s
declared and 2.5 s emitted **inside** a per-host `flock` on `.loop/host-<hostname>.lock`.
One request was held in reserve and **not** spent; §9 says why that reserve mattered —
and, corrected 2026-10-13, what it cost.

> **Counting rule, stated so the ledger can be audited:** one request = one DNS lookup
> **or** one HTTP GET, counted where this harness invoked it. DNS is counted here
> though the repo's only precedent — area A — does not count it (§13e), so **under
> that rule this pass would account as **6 requests against the same 10 cap**. This
> direction is the conservative one; the divergence is recorded rather than hidden.

**Verdict in one line: the host is REAL — it resolves, terminates TLS on a Medtronic
certificate, and answers — but the probe does not establish that it serves the
reports-broker route, because on this host family the `403` is the *unmatched-route*
oracle and a fabricated path is byte-identical to the real one.**

> ⚠ **Run stopped 2026-10-13 (verifier round 1).** This pass's own committed
> artefacts contain **six 403s carrying `access-control-allow-origin: *`**, which
> bears on **closed area X**. That is a disclosure decision about a published closed
> area, not a research pass's to settle, so the `docs/` CORS prose is untouched here
> and the question is handed to **correction issue #61**. See the dated correction in
> §12 and the record fixes in §13.

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
[findings-log/2026-10-12-area-o-reports-namespace/headers/carelink-trials-minimed-com--c1-absent.h:12][source: findings-log/2026-10-12-area-o-reports-namespace/FINDINGS.md §6c]
and byte-for-byte the same line in **a second, independent pass** — area E's
`carelink-trials.minimed.com` sweep of 2026-10-13, the same day as this one:
[findings-log/2026-10-13-area-e-perkey-deployments/headers/carelink-trials.minimed.com--003-bulk-public.h:15].

> ⚠ **Corrected 2026-10-13 (verifier round 1):** the first cite read `:18`. **That
> file has 15 lines and the CSP header is on line 12.** Both reads of the CSP line are
> correct as values; only the anchor was wrong. `research-checks.py` validates cite
> *paths*, not line anchors, which is why this passed the gate.

So `https://commoncore-trials.medtronic.com` is in the vendor's own client allowlist.
That was already OBSERVED and this pass did not re-establish it. What this pass
attacks is the other half: **does the host exist, and does it serve?**

---

## 2. The host set, as measured this session

Nine requests. `*` marks a control. Every cell is OBSERVED 2026-10-13.

| seq | host | DNS | TLS | path | status | `x-amzn-errortype` | body sha256 | source |
|---|---|---|---|---|---|---|---|---|
| 1 | `commoncore-trials.medtronic.com` | **CNAME `d16wbx60y036c9.cloudfront.net`** → 4 A | — | — | — | — | — | `headers/01-ct-medtronic-cn.dns` |
| 2* | `commoncore-trials.minimed.com` | — | DigiCert, SAN match, exp 2027-01-23 | `/reports-broker/v1/ocl` | **403** | `MissingAuthenticationTokenException` | `f249b63c…` | `headers/02-ct-minimed-sibling.{h,v}` |
| 3 | `commoncore.medtronic.com` | CNAME `d2te4je11hig0i.cloudfront.net` → 4 A | — | — | — | — | — | `headers/03-cc-medtronic-com-cn.dns` |
| 4* | `commoncore.medtronic.com` | — | DigiCert, SAN match, exp 2027-04-03 | `/reports-broker/v1/ocl-probe-absent` | **403** | `MissingAuthenticationTokenException` | `f249b63c…` | `headers/04-cc-medtronic-com-absent.{h,v}` |
| 5 | `commoncore.medtronic.com` | — | DigiCert, SAN match | `/reports-broker/v1/ocl` | **403** | `MissingAuthenticationTokenException` | `f249b63c…` | `headers/05-cc-medtronic-com-ocl.{h,v}` |
| 6 | `commoncore.medtronic.eu` | CNAME `d28ymzlhgkylij.cloudfront.net` → 4 A | — | — | — | — | — | `headers/06-cc-medtronic-eu-cn.dns` |
| 7 | `commoncore.medtronic.eu` | — | DigiCert, SAN match, exp 2027-04-03 | `/reports-broker/v1/ocl` | **403** | `MissingAuthenticationTokenException` | `f249b63c…` | `headers/07-cc-medtronic-eu-ocl.{h,v}` |
| 8* | `commoncore-trials.medtronic.com` | — | DigiCert, SAN match, exp 2027-01-23 | `/reports-broker/v1/ocl-probe-absent` | **403** | `MissingAuthenticationTokenException` | `f249b63c…` | `headers/08-ct-medtronic-absent.{h,v}` |
| 9 | `commoncore-trials.medtronic.com` | — | DigiCert, SAN match, exp 2027-01-23 | `/reports-broker/v1/ocl` | **403** | `MissingAuthenticationTokenException` | `f249b63c…` | `headers/09-ct-medtronic-ocl.{h,v}` |

**All three DNS lookups returned `NOERROR`** (rcode `NOERROR`), each with a 5-line
answer section [the three `.dns` captures]. Recorded from the captures rather than
from the ledger's own fields, because those fields are defective — see §13i.

**Six GETs produced exactly one distinct response body.** Not "similar" — one
digest, `f249b63cb2fcb66b47e86f906c98f8fd912e82dd035b4e53d7e72fc1960cfd16`, 42 B,
`{"message":"Missing Authentication Token"}`.

### 2a. The host exists — and is not a parked name

This is the half the row could not previously state. Three independent signals,
each of which a parking namespace fails (OBSERVED). **Sources added 2026-10-13
(verifier round 1)** — the signals were originally stated with no `file:line` cite
at all, which in this repo is a deleted claim (§13h):

1. **Resolution.** `commoncore-trials.medtronic.com` is a **CNAME to a CloudFront
   distribution** (`d16wbx60y036c9.cloudfront.net`, 4 A records in
   `3.166.65.0/24`), not an A record at a parking operator
   [headers/01-ct-medtronic-cn.dns; `results.jsonl` seq 1]. `medtronic.com` is not
   on the repo's wildcard-parking list — that list is `*.carelink.{eu,com}` and
   `*.clcloud.eu` [AGENTS.md §7] — but "not on the list" is an argument from
   absence, so the CNAME is what settles it, and it settles it positively.
2. **TLS.** A **DigiCert Global G2** leaf certificate whose SAN matches the host
   exactly, `start date: Jul 9 2026`, `expire date: Jan 23 2027`, TLS 1.3
   [headers/09-ct-medtronic-ocl.v]. A parked name gets a certificate from whoever
   operates the parking service; a host-specific certificate issued to this exact
   name is a deliberate act.
3. **A vendor-shaped HTTP answer**, not a redirect to a sales page: HTTP/2 403 with
   `x-amz-apigw-id`, `x-amzn-requestid`, `x-cache: Error from cloudfront`, and a
   `via` chain of two CloudFront hops [headers/09-ct-medtronic-ocl.h].

> **The strongest anti-wildcard datum, added 2026-10-13 (verifier round 1):** the
> three names probed under `medtronic.{com,eu}` CNAME to **three *different* CloudFront
> distributions** — `d16wbx60y036c9` (trials `.medtronic.com`),
> `d2te4je11hig0i` (`.medtronic.com`), `d28ymzlhgkylij` (`.medtronic.eu`)
> [headers/01-ct-medtronic-cn.dns, headers/03-cc-medtronic-com-cn.dns,
> headers/06-cc-medtronic-eu-cn.dns]. **A wildcard-parked zone cannot do that**,
> because a wildcard resolves through one mechanism to one destination; three
> distinct, independently-issued distributions is what per-deployment provisioning
> looks like. This is a stronger argument than the single CNAME target it replaces:
> the single CNAME shows *a* CDN, the three show *per-deployment* CDN.

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

> ⚠ **Corrected 2026-10-13 (verifier round 1) — "404 is never emitted" is INFERRED by
> analogy, not observed here.** Oracle A is scoped in `docs/09` to `clcloud.*` and the
> five `*.execute-api.*.amazonaws.com` gateways, and `AWS-GATEWAYS.md` names **no
> `commoncore` host** (`grep -ni commoncore` → 0 hits), so that pass probed no
> `*.medtronic.com` report broker. **This pass observed no `404` in either direction**
> — all six requests answered `403`. The clause is INFERRED from the `clcloud.*`
> family. **Nothing in this pass's conclusion depends on it**: the finding rests on
> the byte-identical absent-path control, which needs no claim about the `404`
> vocabulary at all.

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

> ⚠ **Corrected 2026-10-13 (verifier round 1) — the cause of that gap was wrong.**
> As originally written this read "the cap did not allow a fourth pair", implying the
> cap forced it. **It did not.** The 10-cap could have covered a fourth pair — the
> arithmetic lands on exactly 10 of 10. What actually spent the slot was **my own
> self-imposed reserve**, held back to re-issue a gateway failure (§9), which was then
> never needed because no request returned one. §9 and this section did not connect,
> and the original sentence put the blame on the budget rather than on the choice.
> The gap is a **sequencing choice under an unused reserve**, not a cap constraint,
> and the correction matters because a future pass reading this should spend the slot
> on the EU control rather than assume it is unaffordable.
>
> The consequence is unchanged and still stands: **the no-route reading is adjudicated
> on `.com` only** (seq 4 vs 5). `commoncore.medtronic.eu`'s single `403` is
> corroboration, and any prose presenting the pair `commoncore.medtronic.{eu,com}` as
> one adjudicated unit over-reads the EU half. That limit is now carried into
> `docs/01` and `docs/07` rather than living only here.

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
request order across **all 9 captures that carry an mtime** (6 HTTP bodies + **3**
`dig` captures), giving **8 gaps**.

> ⚠ **Corrected 2026-10-13 (verifier round 1).** The original rule counted **7**
> captures and **6** gaps, because the same-host series in `spacing.py` iterated
> `bodies/*.b` only — so no DNS row could enter a pair. The three `dig` captures
> carry mtimes like any other capture and belong in the series. **The floor moved
> from 2.699 s to 2.638 s** and the series from 6 gaps to 8. Both series now derive
> from one mtime map, and the same-host counting rule is stated in the output the
> way the all-rows rule is.

| gap | seconds |
|---|---|
| seq 1 → 2 | 101.113 (the attempt-1 abort sits in this interval) |
| seq 2 → 3 | 2.678 |
| seq 3 → 4 | 2.833 |
| seq 4 → 5 | 2.840 |
| seq 5 → 6 | 2.780 |
| seq 6 → 7 | 2.638 |
| seq 7 → 8 | 2.757 |
| seq 8 → 9 | 2.699 |

**Floor 2.638 s · max 101.113 s · 0 gaps under 2.5 s · 0 under the repo's ≥2 s
floor · span 120.339 s.**

**Same-host gaps** — the rule is per host, and this series now includes DNS→GET pairs:

| host | pair | gap |
|---|---|---|
| `commoncore-trials.medtronic.com` | seq 1→8 (DNS→GET) | 117.640 s |
| `commoncore-trials.medtronic.com` | seq 8→9 (GET→GET) | 2.699 s |
| `commoncore.medtronic.com` | seq 3→4 (DNS→GET) | 2.833 s |
| `commoncore.medtronic.com` | seq 4→5 (GET→GET) | 2.840 s |
| `commoncore.medtronic.eu` | seq 6→7 (DNS→GET) | **2.638 s** |

**Same-host floor 2.638 s over 4 hosts** — every pair clears the ≥2 s floor.

> **Not re-derivable from a clean clone** (2026-10-13, verifier round 1).
> `results.jsonl` stores `body_mtime_epoch` as a **1-second integer**, and `docs/09`
> records that **git does not preserve mtimes**. A fresh clone therefore re-derives a
> floor of **3 s**, not 2.638 s. The nanosecond figure is measurable **only on the
> machine that ran the probe** — the same caveat the closed area-D country sweep
> records for its own mtime measurement. **Read 2.638 s as a fact about this machine
> at this time, not as a re-derivable property of the artefacts.**

**Two disclosures, because the instrument misbehaved and a reader deserves both:**

1. **`seq 6` has a negative duration** — `t_done` 0.668 s *before* `t_sent`, which
   is impossible. `seq 6` is the EU DNS lookup: `dig` had already exited when the
   `date` was read. This is the sixth occurrence of the defect `docs/09 §4` records.
   **It is why the `date` series is not the authority here.** In the `date` series
   the seq 6 → 7 gap reads **1.857 s** — apparently below the ≥2 s floor — while the
   mtime series for the same pair reads **2.638 s**, which passes. The apparent
   violation is an artefact of the broken row; the requests were correctly spaced.
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

> ⚠ **What this reserve actually cost (2026-10-13, verifier round 1).** The reserve
> is the **only** reason the EU absent-path control was not sent. Under the repo's
> own precedent — area A, which does **not** count DNS lookups against the cap
> [findings-log/2026-10-12-area-a-clinic-portal-region/FINDINGS.md:36] — this pass
> would have been **6 HTTP requests against the same 10 cap**, leaving room for the
> EU control and landing at **10 of 10**. **The two choices were coupled and §5 and §9
> did not say so.**
> Holding a reserve against a failure mode that never materialised is defensible in
> isolation; spending the slot on the pass's own weakest cell would have been the
> better trade, because the no-route reading is the pass's load-bearing negative and
> it is adjudicated on `.com` alone.

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

### Why this pass adds no regression pin

`AGENTS.md` §3 says a claim that should never rot gets a pin, and the verifier is
right that this pass's central negative — **the byte-identical fabricated-path control
on a `commoncore*` host** — is the kind of thing a pin is for. **It is deliberately
not pinned, and the reason is this pass's own finding:**

> **A pin would assert a status code whose meaning is unestablished on this host
> family.** What the control establishes is a *negative* — that the `403` fails to
> discriminate. Pinning `403 MissingAuthenticationTokenException` would encode a
> gateway artefact as a health check, and a vendor reconfiguration would then break
> the suite for a reason the pin's author does not believe in. The "404 is never
> emitted" half of the Oracle A reading this rests on is itself **INFERRED by analogy
> from `clcloud.*`** (§2b) and was never observed here.

**What *is* pinnable, and is not pinned here either:** the DNS fact — three names
under `medtronic.{com,eu}` CNAME to three distinct CloudFront distributions — is
stable, and a maintainer **can** pin it: `AGENTS.md` §11 requires that a new host
enter a workflow "only after a human added it to the suite", which is precisely the
step a maintainer would take. **This pass does not take it, because it cannot edit
`regression/` as a side effect of a research finding** — and because pinning three
new vendor hosts would change the weekly drift sweep's request budget, which is a
cost the maintainer should see before it is incurred, not after. That is a
disposition about *who* makes the call, not a claim that the call is forbidden.

So: **the negative is recorded, unpinnable as a status assertion, and the
maintainer may add a host-registration check deliberately.** Silence would have been
worse; this is the reason.

### The addendum

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

---

## Correction (2026-10-13, verifier round 1): six `403`s in this pass carry CORS, which bears on a **closed** area. Run stopped here.

**This is a stop condition, not a defect I can settle.** It is recorded here and
handed to **correction issue #61**; the `docs/` CORS prose is deliberately **not**
touched by this pass.

### What the verifier found, confirmed independently

Every one of this pass's six HTTP responses is a **403 carrying
`access-control-allow-origin: *`** — plus `access-control-allow-methods: *` and
`access-control-allow-headers: *`. **Four distinct hosts**, and **two of the six are
on the certainly-absent control path**:

| seq | host | path | role | CORS |
|---|---|---|---|---|
| 2 | `commoncore-trials.minimed.com` | `/reports-broker/v1/ocl` | CONTROL-b | `acao: *` · `acam: *` · `acah: *` |
| 4 | `commoncore.medtronic.com` | `/reports-broker/v1/ocl-probe-absent` | **CONTROL — certainly absent** | `acao: *` · `acam: *` · `acah: *` |
| 5 | `commoncore.medtronic.com` | `/reports-broker/v1/ocl` | CANDIDATE | `acao: *` · `acam: *` · `acah: *` |
| 7 | `commoncore.medtronic.eu` | `/reports-broker/v1/ocl` | CANDIDATE | `acao: *` · `acam: *` · `acah: *` |
| 8 | `commoncore-trials.medtronic.com` | `/reports-broker/v1/ocl-probe-absent` | **CONTROL — certainly absent** | `acao: *` · `acam: *` · `acah: *` |
| 9 | `commoncore-trials.medtronic.com` | `/reports-broker/v1/ocl` | CANDIDATE | `acao: *` · `acam: *` · `acah: *` |

Source, verbatim: `headers/02-ct-minimed-sibling.h`, `headers/04-cc-medtronic-com-absent.h`,
`headers/05-cc-medtronic-com-ocl.h`, `headers/07-cc-medtronic-eu-ocl.h`,
`headers/08-ct-medtronic-absent.h`, `headers/09-ct-medtronic-ocl.h`; every ledger row
2–9 carries `"access_control_allow_origin": "*"`, and `probe.sh` captured the header
in the extraction list.

### Why it is not mine to settle

**Closed area X** is recorded at `docs/11` (Closed areas table), `docs/00`,
`docs/03` and `docs/10` as "**0 non-2xx responses carrying CORS anywhere**", and the
`docs/03` phrasing is "anywhere in the corpus". **This pass enlarges the corpus and
finds six.** Two readings are available and **neither is adopted here**:

1. **Area X was scoped to `clcloud.*`** — its own host family, AWS API Gateway behind
   CloudFront — and this is a different host family (`commoncore.medtronic.*`) that
   area X never swept. On that reading nothing is falsified.
2. **The claim was stated as absolute** ("anywhere"), and six non-2xx responses with
   CORS is a direct counterexample. On that reading a closed area is wrong.

Deciding between them is a **disclosure decision about a published, closed area**, and
`AGENTS.md` §11 puts correcting the record to humans. **This pass edits no CORS prose
in `docs/`.** Issue **#61** carries the full evidence table and both readings.

### Why the run stopped

A correction to a closed area that I cannot adjudicate, discovered in my own
committed artefacts, is exactly the kind of thing that must not ride into `main`
inside an unrelated PR. The science above stands; the record around it was fixed
(§13) and the open question is handed over.

### It bears directly on two open readings — and supplies the discriminating cell

- The two live readings are **`docs/10:56`** (whether a `clcloud.*` `200` carries
  `Access-Control-Allow-Origin`) and **area X's row in the `## Closed areas` table of
  `docs/11`** — the row beginning `X — why the two clcloud.* route families differ in
  their CORS headers`, evidence cell
  `findings-log/2026-10-12-area-x-cors-separation/FINDINGS.md`, issue cell `#15`, at
  `docs/11:1102` **as of this commit** — whose correction found a separating
  `200`-without-CORS cell in the corpus.
  **Six non-2xx responses carrying `acao: *` is a fact neither reading currently
  contains.**
- The unexcluded reading — that CORS on this gateway family is **emitted only on
  `OPTIONS`** — is exactly what these cells speak to, because **these six are bare
  `GET`s**: the request block in each `.v` trace sent exactly `Host`,
  `User-Agent`, `Accept` and `Accept-Encoding` and **no `Origin` header**
  [e.g. `headers/09-ct-medtronic-ocl.v`, request block lines 52-57]. So this is **not**
  a preflight artefact and not an origin-dependent reflection. **It is the
  discriminating cell that reading needs**, and it cuts against it.

Both readings are recorded; neither is adopted.

---

## 13. Corrections to this pass's own record (verifier round 1)

The science held: the verifier re-derived the CNAME, the certificate, the body digest
and **all six spacing gaps** from the artefacts independently, and every one held.
What it could not sign was the record around them. All are appended or corrected here
rather than edited away.

### 13a. A citation to a line that does not exist

The CSP was cited as `carelink-trials-minimed-com--c1-absent.h:18`. **That file has
15 lines; the `content-security-policy` header is on line 12.** Corrected to `:12`
here and in `docs/10`. The sibling cite `…003-bulk-public.h:15` was checked and is
correct as written. `AGENTS.md` §6 item 6.

**Why the gate went green:** `research-checks.py` resolves cite **paths**, not line
anchors, so a well-formed path with a wrong line number is invisible to it. Recorded
because the next reader will assume the checks cleared the anchor too.

### 13b. "Area D" collided with a closed area

Letter **D** was closed on 2026-10-12 — *"D — the 18-country sweep, completed"* — and
`docs/09` already attributes the body-mtime oracle discovery to that pass. Naming this
one D as well would have left one letter pointing at two different passes. The log
directory is renamed `2026-10-13-area-d-commoncore-trials` →
**`2026-10-13-commoncore-trials`**, and every self-reference uses the non-letter
handle **"the `commoncore-trials` pass"**, following the precedent `docs/11` already
sets for area O. The branch was unmerged, so the rename was free.

### 13c. `spacing.py` could not compute the same-host gaps it claimed to check

The same-host series iterated `bodies/*.b` only, so **no DNS row could ever enter a
pair** — and the EU host's pair is DNS→GET. It printed "these are all larger" on a
filtered subset, which is a false clean bill for anyone re-running it. **Both series
now derive from one mtime map** covering all 9 captures (6 HTTP bodies + 3 dig
captures), and the same-host counting rule is stated in the output the way the
all-rows rule is.

**Withdrawn — the verifier's inference from this was wrong.** It held that the
structurally-unprintable EU pair "is the one that violates the floor" at 1.857 s.
**It does not violate it.** The mtime series reads **2.638 s**, which passes the
≥2 s floor. The 1.857 s figure is the **corrupt seq-6 date row** (a negative
duration, already disclosed in §7), not the spacing. The structural defect was real
and is fixed; the conclusion drawn from it was not, and correcting the record means
saying so.

The all-rows series is now **8 gaps, not 6**, because the three dig captures enter it:
floor **2.638 s**, 0 under 2.5 s, 0 under 2 s.

### 13d. "404 is never emitted" is inherited, not observed here

That clause comes from Oracle A, which `docs/09` scopes to **`clcloud.*` and the five
`*.execute-api.*.amazonaws.com` gateways**. `AWS-GATEWAYS.md` names **no `commoncore`
host** (`grep -ni commoncore` → 0 hits), so that pass probed no `*.medtronic.com`
report broker. **This pass observed no `404` either way** — it requested six paths and
every one answered `403`. The clause is therefore **INFERRED by analogy from
`clcloud.*`**, and is now labelled as such at `FINDINGS.md` §2b, `docs/07` and
`docs/11`. **It is not needed for the pass's conclusion**, which rests on the
byte-identical control and needs no claim about the `404` vocabulary.

### 13e. DNS accounting diverges from the repo's only precedent

This pass counts **DNS lookups against the cap**. Area A — the repo's precedent —
counts them the other way: *"8 DNS lookups are recorded in `dns.jsonl` and are **not**
counted against the cap: they are resolver traffic, not requests to a vendor host"*
[findings-log/2026-10-12-area-a-clinic-portal-region/FINDINGS.md:36].

**This direction is deliberate and conservative**, and the counting rule is stated at
the head of `probe.sh`, so it is not a breach — but it is a **divergence from the
repo's existing convention** and is recorded as one. Under area A's rule this pass
would account as **6 requests against the same 10 cap**.

### 13f. The `docs/11` successor overstated what the pass closed

The addendum said the pass "closed the whole unauthenticated half in 9 of a 10 cap".
That contradicts this log's own §5 and §11: the route question is **left open** and
the EU cell is **uncorroborated**. Reworded to "closed most of the unauthenticated
half". The successor is still sound — it is the *route* question it hands on, not the
host-existence question, which this pass did close.

### 13g. The 2.699 s floor is not re-derivable from a clean clone

`results.jsonl` stores `body_mtime_epoch` as a **1-second integer**, and `docs/09`
records that **git does not preserve mtimes**. So a clean clone re-derives a floor of
**3 s**, not 2.699 s. The nanosecond figure is measurable **only on the machine that
ran the probe** — the same caveat area D's closed sibling records for its own mtime
measurement. **Stated next to the number**, so nobody reads 2.699 s as re-derivable.

### 13h. The existence signals had no artefact cites; a stronger anti-wildcard fact was unused

§2a stated all three existence signals with **no `file:line` cite at all**, and the §2
table had no source column. The values were right — the verifier confirmed each — but
an uncited claim is a deleted claim in this repo. Cites added per signal.

**And the strongest anti-wildcard datum was not used.** Three names under
`medtronic.{com,eu}` CNAME to **three *different* CloudFront distributions** —
`d16wbx60y036c9`, `d2te4je11hig0i`, `d28ymzlhgkylij` — and a wildcard-parked zone
**cannot** do that, since a wildcard resolves through one mechanism. §2a argued from
the single CNAME target; the three-distribution fact is stronger and is now recorded
in both the log and `docs/01`.

### 13i. Four smaller record defects

- **`probe.sh` could not populate its own DNS fields.** `grep -m1 'status:'` matched
  the dig header line, so `dns_status` held `;; ->>HEADER<<- opcode: QUERY` and
  `dns_rcode` was **empty on all three DNS rows**. The field could never hold a
  status, so the prose outran the ledger meant to carry it. **Both are recorded from
  the captures directly** — `NOERROR` on all three, `rcode: NOERROR` — and the
  extraction is fixed.
- **"a different date" was ambiguous.** The second CSP source,
  `2026-10-13-area-e-perkey-deployments`, is **same-day as this pass**. Reworded to
  name both passes and their dates.
- **"retained above-by-below" described no structure** on the `docs/10` page; the
  superseded wording is now quoted **inline** in the row it supersedes.
- **The `.v` captures contain this machine's LAN address** (`192.168.8.133`) in
  curl's connection trace. It is a private RFC 1918 address, not a vendor asset, and
  it is **not on the `AGENTS.md` §7 scrub list** — but area I's captures carry the
  same class of value on `main`, so this is a known pattern rather than a new leak.
  Recorded rather than left unexplained.

### 13j. Two defects in §12, found by the round-2 verifier (2026-10-13)

Both in the CORS section added above; **the conclusion is unchanged and neither is
withdrawn** — only the support was wrong.

1. **A parenthetical that failed its own check.** §12 read *"no `Origin` header was
   sent at all (zero `Origin` occurrences across the `.v` traces)"*. **The claim is
   true; the parenthetical is not.** Each `.v` trace has **exactly one**
   case-insensitive `origin` hit — the response's own
   `< access-control-allow-origin: *` [e.g. `headers/09-ct-medtronic-ocl.v:69`]. The
   check as written could never have distinguished "no `Origin` sent" from "an
   `Origin` arrived and was reflected", because it matched the response header
   either way. That is `AGENTS.md` §6 item 2 — a check that reads as proof and is
   not. **Replaced with the evidence that actually discriminates**: the request block
   itself, which sent exactly `Host`, `User-Agent`, `Accept`, `Accept-Encoding`.
2. **Two `docs/09` attributions named the wrong document.** §12 credited `docs/09`
   with "the caution that CORS on an error is not the same as CORS on a success" and
   with a note that "a `200` carrying no preflight does exist on `clcloud.*`".
   **`docs/09` says "preflight" exactly once** (line 74, unrelated to CORS) and
   carries no such caution. **Both readings live in `docs/10:56` and in area X's
   `## Closed areas` row in `docs/11`** (the row beginning `X — why the two clcloud.*
   route families differ in their CORS headers`, evidence
   `findings-log/2026-10-12-area-x-cors-separation/FINDINGS.md`, issue cell **#15**;
   `docs/11:1102` as of this commit)
   and the citations now say so — `AGENTS.md` §6 item 6.

### 13k. One verifier claim upheld, one corrected (2026-10-13)

**Upheld — the EU same-host pair does not violate the floor.** Round 1 held it did,
at 1.857 s. Round 2 re-derived all three readings and upheld this pass's withdrawal:

| reading of seq 6→7 | value | verdict |
|---|---|---|
| mtime → mtime | **2.638 s** | PASS |
| `t_queued` → `t_queued` | **2.751 s** | PASS |
| `t_sent` → `t_sent` | 1.857 s | FAIL — corrupt row, artefact only |

**Round 1's own "mtime → mtime" figure of 2.757 s was the seq 7→8 gap** — a cell it
structurally could not compute, so it quoted a borrowed one. This pass's `spacing.py`
now *computes* the EU pair from one mtime map over all nine captures, which is the
difference between measuring it and filtering it out.

**Corrected — my §11 objection to the DNS pin was slightly overstated.** This pass
wrote that adding DNS to the suite "crosses `AGENTS.md` §11's boundary for
automation". More precisely: §11 says a new host enters a workflow **"only after a
human added it to the suite"**, which is exactly what a maintainer would do to pin
it. **The disposition is unchanged — a pass that cannot edit `regression/` should not
make that edit as a side effect — but the reasoning under it is tightened here**, and
the maintainer's route is named rather than implied to be forbidden.

### 13l. Two pointers the rebase moved, found by the round-3 verifier (2026-10-13)

Both are `AGENTS.md` §6 item 6 — **the evidence is right, the address of it is wrong.**
No claim in §1–§12 changes, and no finding is withdrawn. Only the coordinates change.

#### 13l-1. `docs/11:777` resolves to a sentence that has nothing to do with area X

§12 and §13j both sent the reader to the closed area X row at **`docs/11:777`**. On
this branch **line 777 is not area X at all** — it reads `Closes when: all 211 carry a
verdict for that token set…`, the tail of a *different* area's entry. The area X row
is **area X's row in the `## Closed areas` table of `docs/11`** — the row beginning
`X — why the two clcloud.* route families differ in their CORS headers`, evidence cell
`findings-log/2026-10-12-area-x-cors-separation/FINDINGS.md`, issue cell **#15** — at
`docs/11:1102` **as of this commit**.

Corrected in both places, and **to that content-addressed form rather than to another
line number**: §13m records that this is the *third* rottedness of the same anchor, so
the durable fix is the class, not the fourth coordinate.

The pointer was correct when written. It was correct against `8373169`; two commits
have since moved the row it names:

| ref | area X row |
|---|---|
| `8373169` (branch, pre-rebase) | `docs/11:777` |
| `614db77` (area F merge) | `docs/11:858` |
| `6a4ae46` (round-7 reviewed tip) | `docs/11:932` |
| this branch (`750bfca`, area L merged in) | `docs/11:1102` — **the fourth coordinate; §13m is why the pointer is now content-addressed** |

Every row above was verified against *its own* ref, not against this tree: all four
resolve to the same row. That is the whole problem in one table — a coordinate that was
true, then was not, then was true again, without the sentence it addresses changing.

`614db77` moved it **81** lines; this pass's own §12/§13 addendum moved it a further
**74**. A line anchor is a claim about a *line*, and both commits invalidated it
without changing a byte of the sentence that used it.

**Why the gate went green — the second time this pass has recorded it (§13a was the
first):** `research-checks.py` resolves `[source: findings-log/…]` **paths**, never
line anchors, so a well-formed path carrying a stale line number is invisible to it.
Nothing in CI would ever have caught this. Recorded because the next reader will
otherwise assume the checks cleared the anchors too.

**Because `docs/11` moved twice, the whole log was swept for the same failure.** Every
line anchor in this file was re-resolved against this tree — **14 distinct
`file:line` targets**, including the three written in prose form ("line 12", "line
12", "line 74"):

| sweep | result |
|---|---|
| 14 distinct `file:line` targets | **13 resolve. Exactly one did not: `docs/11:777`, cited twice — corrected above** |
| `docs/10:56`, the *other* live reading | resolves; it did **not** drift |
| `c1-absent.h:18` (§13a) | the one deliberate non-resolution — it is the *wrong* cite §13a quotes in order to document the error. Left as written. |

**No `docs/` or `README.md` page carries a line anchor into this log** — of the **11**
citations `docs/` and `README.md` make to this file, **0** are followed by a line
number; all 11 name a `§` instead — so the drift is confined to this file and **no
`docs/` repair was needed**. **Counting rule, because the number is meaningless
without one: a citation is one markdown link or bracket-quoted path pointing at this
log, counted once even where it spells the path twice.** The path occurs **12** times
across **10** lines; exactly **one** of those — `docs/10:45` — is the URL half of a
link whose link text already carries it, so 12 − 1 = **11**. The anchor half is
measured separately and is the load-bearing one:
`grep -rnE 'commoncore-trials/FINDINGS\.md[:#]*[0-9]+' docs/ README.md` returns
**nothing**. Nine of the 11 name a `§` straight after the path; `docs/11:36` names
`§2a` on the following line (the line wrapped) and `docs/11:97` names it in the link
text rather than after the path. Corrected 2026-10-13 — the derivation and the
superseded wording are in §13l-4.

#### 13l-2. "request block lines 1-7" pointed at the DNS/TLS preamble

§12/§13j cited *"[e.g. `headers/09-ct-medtronic-ocl.v`, request block **lines 1-7**]"*
as the evidence that the six bare `GET`s sent no `Origin`. **Lines 1-7 are the DNS and
TLS preamble** — `"* Host commoncore-trials.medtronic.com:443 was resolved."` through
`"* TLSv1.3 (OUT), TLS handshake, Client hello (1):"` — and carry **zero** request
headers: `awk 'NR<=7 && /^> /'` returns **0** lines. **The request block is lines
52-57**, corrected in place.

**The corrected range is not file-specific — it is identical in all six captures.**
Every `.v` trace in `headers/` (`02`, `04`, `05`, `07`, `08`, `09`) has exactly six
`> ` lines, and in each they sit at **52-57**. So the reader may check *any* of the
six at the same address, and the union of header names sent across all six request
blocks is exactly **`Host`, `User-Agent`, `Accept`, `Accept-Encoding`** — the four
names §12 lists — with `grep -ci origin` over lines 52-57 of all six returning **0**.

**The claim §12 made is CONFIRMED; only its address moved.** These six are bare
`GET`s, so they are not a preflight artefact and not an origin-dependent reflection —
which is exactly the disposition §12 took, and it stands.

#### 13l-3. The rebase left the five disputed CORS sites byte-unchanged

The pointer drift above is a merge artefact, so the sites the merge was *supposed* to
leave alone were re-checked rather than assumed: **`docs/00:166`, `docs/03:341`,
`docs/10:56`, `docs/06:156`, and the area X row** are byte-identical to `614db77` (md5
per site — and for the area X row that comparison is `614db77:858` against this
branch's area X `## Closed areas` row (`docs/11:1102` as of this commit), since the
rebase is what moved it). `docs/06:156` was added
to this inventory on 2026-10-13 after the round-5 verifier found it carrying the same
CORS wording — "a \`GET\` of a discovery payload; 0 non-2xx responses carrying CORS
anywhere" (md5 `863b149c2170ec6ad769534f75be8b08` at both refs) — it was simply missed
the first time, so the inventory now names five byte-checked sites rather than four.
The merge is provably correct — `git merge-tree --write-tree 8373169 614db77` yields
`63a595a6…`, which is **byte-identical to the merge commit `7872a1c9`'s tree**, so the
merge introduced nothing beyond `614db77` — and **no pin crept into `regression/`**. What
moved was a line number, not a byte of CORS prose. (Stated against the merge commit
rather than against "this branch's" tree, which stopped being true the moment the next
correction was committed — §13m.)

#### 13l-4. "12 citations" counted string occurrences, not citations (2026-10-13)

§13l-1's closing paragraph said *"of the **12** citations `docs/` and `README.md` make
to this file, **0** are followed by a line number; all 12 name a `§` instead"*. **The
superseded wording is quoted here rather than deleted.** `12` is the number of
**occurrences of the log path as a string**, which is not the number of citations. The
round-5 verifier counted the same 12 occurrences across the same 10 lines and found
the discrepancy: **one of them is the URL of a markdown link whose link text already
carries the path** — `docs/10:45`, `[findings-log/2026-10-13-commoncore-trials/FINDINGS.md §12](https://…/findings-log/2026-10-13-commoncore-trials/FINDINGS.md)`.
Counted per citation it is **11**, and the corrected number is what §13l-1 now states.
This is `AGENTS.md` §6 item 7 — a count generalised from a subset, with no counting
rule recorded — except that here the subset was the whole corpus and the *unit* was
wrong, which is the same failure wearing a different hat.

**The counting rule, so the number can be re-derived rather than believed.** A
**citation** is one markdown link or bracket-quoted path that points at this log, and
it is counted **once** even where it spells the path twice (once in the link text,
once in the URL). Both halves are checkable with no vendor request:

```bash
# 12 — occurrences of the path as a string, across 10 lines
grep -rnoE 'commoncore-trials/FINDINGS\.md' docs/ README.md | wc -l
# 1 — links that spell it twice; the single instance is docs/10:45
grep -rnoE '\[[^][]*commoncore-trials/FINDINGS\.md[^][]*\]\([^)]*commoncore-trials/FINDINGS\.md[^)]*\)' \
  docs/ README.md | wc -l
# 0 — line anchors into this log: the load-bearing half, and it was already right
grep -rnE 'commoncore-trials/FINDINGS\.md[:#]*[0-9]+' docs/ README.md   # no output
```

12 − 1 = **11 citations**. Enumerated, all 11 and each one's `§`:

| site | `§` named |
|---|---|
| `docs/00:98` | after the path (`§3a, §2b`) |
| `docs/01:71` | after the path (`§2a`) |
| `docs/01:108` | after the path (`§3a`) |
| `docs/01:109` | after the path (`§2a, §2b, §3b`) |
| `docs/01:134` | after the path (`§2b, §5`) |
| `docs/07:240` | after the path (`§2b, §5`) |
| `docs/07:248` | after the path (`§2b, §3b`) |
| `docs/10:45` (twice) | after the path (`§12`), and after the path (`§2a, §2b`) |
| `docs/11:36` | **on the following line** — the line wraps, `§2a` sits at `:37` |
| `docs/11:97` | **in the link text** — `[§12](…)`, the path appears only in the URL |

**What did not change, and is the reason no `docs/` page was touched.** The two
halves of the old sentence had different luck: the **"0 are followed by a line
number"** half was already true and is independently CONFIRMED — the third command
above returns nothing, so **no `docs/` page carries a stale line anchor into this
log** and **no `docs/` repair was needed**; the **"all 12 name a `§`"** half was true
of the set and wrong only about its size. Every one of the 11 names a `§`, which is
why the conclusion the sentence exists to support stands unchanged.

**Why the two non-obvious rows are spelled out rather than smoothed over.** A reader
re-deriving "all 11 name a `§`" with a naive "does a `§` follow the path *on the same
line*" test gets **9**, not 11, and would wrongly conclude the claim is false. `docs/11:36`
wraps its `§2a` onto `:37`, and `docs/11:97` puts its `§12` in the link *text* with
the path only in the URL. Both are recorded here so the next re-derivation does not
have to rediscover them.

**This correction moved no claim, no host, no status and no request.** The pass's
9 of a 10 cap is untouched: `wc -l results.jsonl` = **9**, one live accounting line
at `:505`, and §13f's `:654` still quotes the superseded wording it superseded.

### 13m. The same anchor rotted a third time, so the pointer is now content-addressed (2026-10-13)

**This is an address defect. No claim, host, status, request count or evidence label
below this heading changed.**

Area L (#63) merged into `main` as `c521083` and this branch merged it forward to
`750bfca`: **92 files, 1965 insertions, 2 deletions.** The insert
`@@ -833,0 +834,170 @@` in `docs/11` moved area X's `## Closed areas` row from
**`docs/11:932`** to **`docs/11:1102`**. The merge's only two deleted lines are two
area M Common Crawl rows replaced in place at `docs/08:275` and `docs/10:64` — area L's
wording, touching no CORS site.

That left five live pointers in this log naming a line that is now `**Also INFERRED, and
it was previously left in an OBSERVED sentence here rather**` — a mid-sentence
continuation of an unrelated area's note:

| was | now |
|---|---|
| `:565` (§12) | content-addressed |
| `:719` (§13j) | content-addressed |
| `:756` (§13l-1) | content-addressed |
| `:765` (§13l-1 table) | `6a4ae46` row added as history; "this branch" row now content-addressed |
| `:829` (§13l-3) | content-addressed |

**Why this one is fixed as a class, and not as a fourth coordinate.** It is the third
line-anchor correction in this one file: §13a fixed `…c1-absent.h:18` (a 15-line file),
§13l-1 fixed `docs/11:777` → `932` **for exactly this reason**, and `932` has now rotted
again. Every one of those fixes was correct when written and every one was invalidated by
a later insert. Three correct-and-still-wrong coordinates is the evidence that the line
number was never the right key.

**The durable form.** What identifies the row is its table and its content, not its
position:

> **area X's row in the `## Closed areas` table of `docs/11-suggested-research-areas.md`**
> — the row beginning ``X — why the two `clcloud.*` route families differ in their CORS
> headers``, whose evidence cell names
> `findings-log/2026-10-12-area-x-cors-separation/FINDINGS.md` and whose issue cell reads
> `#15`. Currently at `docs/11:1102` **as of this commit** — a convenience, not the key.

All five sites now carry that form. The `## Closed areas` heading is at `docs/11:1090` and
the row at `docs/11:1102` on this tree; both are re-derivable by `grep -n`.

**The general rule, recorded so the next pass does not rediscover it.** *A line anchor
into `docs/11` rots on every insert to that file, and `docs/11` is inserted into several
times a week in this repo.* Cite by **table and row content**; treat a line number as a
convenience that expires, and mark it "as of this commit" when you carry one. This is
`AGENTS.md` §6 item 6 — the evidence is right and the address of it is wrong — but the
generalisation matters more than the instance: **do not write a `docs/11` line anchor as
a live pointer at all.**

**The sweep, re-resolved against this tree.** Counting rule: one distinct
`file:line` target, repo shorthand expanded (`docs/11` → `docs/11-*.md`, bare
`*.h`/`*.b` → the single matching capture), each resolved to a string and asserted
non-blank before it is called a resolution — `AGENTS.md` §6 item 3, and the reason a
first pass at this sweep reported **21** "unresolved" targets that were in fact shorthand
expansions never attempted.

| sweep | result |
|---|---|
| **30** distinct `file:line` targets | **28 resolve in range and non-blank. Zero resolve to the wrong content** |
| `docs/11` targets, **before** this correction | **3** resolved in range but not to area X: `932` (**live, 5 citations — rotted**), plus `777` and `858`, which are *historical* statements about refs `8373169` and `614db77` and are correct as such |
| `docs/11` targets, **after** | **0** rotted. `777`, `858`, `932`, `1102` are each checked **at their own ref** — all four resolve to the area X row, which is the whole problem stated in one line: true, then not, then true again |
| `carelink-trials-minimed-com--c1-absent.h:18` (`:594`, §13a) | out of range — the file has **15** lines. The one deliberate non-resolution: it is the *wrong* cite §13a quotes to document the error. Left as written |
| `c1-absent.h:18` (`:806`) | not a pointer — it is the sweep table *naming* §13a's deliberate non-resolution |

**What did not change, and was re-checked rather than assumed.** All five CORS-wording
sites are byte-identical to `origin/main` on this tree (`docs/00:166`,
`docs/03:341`, `docs/10:56`, `docs/06:156`, and the area X row, md5 per site);
`docs/09` still says `preflight` **exactly once**, at `:74`, which §13j depends on; no
disputed-wording line was added to `docs/`; `regression/` untouched; `216 / 430` and
`research-checks.py` exit 0. `docs/00:170` — the seventh carrier of the disputed wording,
found by the round-6 review — remains byte-unchanged and is **not** contradicted: it reads
*"…is **not excluded**"*, asserts nothing about `clcloud.*`, and this pass's six cells are
on a different host family. That hedge is in fact the strongest evidence that the disputed
wording has already been qualified once on `main`, which is material to the #61 ruling.

**The rule caught this file's author committing the bug one last time, which is why it
is worth stating as a rule rather than a fix.** While re-confirming the five CORS sites
against the *current* `origin/main`, the check was written as a fixed-line comparison —
`origin/main:858` vs this branch's `:1102` — and reported **`DIFFERS`**. It did not.
`origin/main` is now `c521083`, area L's merge, where the row sits at **`:1028`**, not
`:858`; resolved there, the two digests are both `a5c5343312ba3886dab31bbba1c06319` and
the row is byte-unchanged. The stale coordinate had survived **four** separate commits
(`614db77` → `6a4ae46` → `750bfca` → `c521083`) while still being quoted as current. The
first two rotted live pointers in this log were fixed to a coordinate that was already
dying; only the content-addressed form survives that.

**One further correction, made here rather than left standing.** §13l-3 said
`git merge-tree --write-tree 8373169 614db77` "yields a tree byte-identical to **this
branch's**". Re-run: it yields `63a595a6…`, which is **byte-identical to the merge commit
`7872a1c9`'s tree** — so the merge claim is CONFIRMED on its proper target. The old
wording named a target that stopped being true the moment the next correction was
committed, which is §13m's own failure mode in miniature; it is now stated against the
merge commit.
