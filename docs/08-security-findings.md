# Security findings

A ranked, defensive summary of the security posture of Medtronic's public
CareLink surface — what the vendor exposes, and why it matters. Everything here
was observed **read-only and unauthenticated** during the 2026-10-08 → 2026-10-10
passes: no exploitation, no data retrieval, no writes, no credential guessing
[source: findings-log/probe-2026-10-08/SECURITY-FINDINGS.md §Scope]. Where a
source describes an attack surface, this page records the **observation and the
impact**, never a ready-to-run recipe. Extends
[`00-summary-the-map.md`](00-summary-the-map.md).

Legend — **OBSERVED** = seen in a live response · **PUBLISHED** = in a vendor
document served without a login (live, or recovered from a public archive) ·
**INFERRED** = reasoned, not seen. Citations are `[source: findings-log/<file>
§n]`; inside tables the bare filename is the same file, rooted at
`findings-log/probe-2026-10-08/` unless marked: `SECURITY-FINDINGS` ·
`CROSS-REGION` · `AUTH-TENANT` · `PUBLIC-CONFIG` · `CONFIG-NS` = `recon/CONFIG-NAMESPACE.md`
· `CONFIG-DEEP` = `recon/CONFIG-NAMESPACE-DEEP.md` · `ARCHIVE-URLS` = `recon/ARCHIVE-URLS.md`
· `COMMONCRAWL` = `recon/cc/COMMONCRAWL-URLS.md` · `HCP-SCHEMA` = `recon/HCP-CONFIG-SCHEMA.md`
· `RECON-SUBDOMAINS` = `recon/RECON-SUBDOMAINS.md` · `AWS-GATEWAYS` = `recon/AWS-GATEWAYS.md`
· `CLAIM-AUDIT` = `audit/CLAIM-AUDIT-2026-10-09.md` · `POSTURE-0721` =
`../medtronic-carelink-2026-07-21/11-public-security-posture.md` · `HURL-05` =
`regression/hurl/05-public-config.check.sh` (repo root).

## Bottom line

**No exploitable vulnerability was found.** No patient data is reachable without
a valid token, OAuth `redirect_uri` validation is strict, TLS is enforced
correctly, and the one leaked credential in the public JS bundle is **verified
not live** [source: SECURITY-FINDINGS §Bottom line]. What exists is a set of
**hardening gaps**, ranked below in the order a disclosure email would lead with.

| # | Finding | Class | Severity (per source) |
|---|---|---|---|
| F1 | Reports-broker API keys published **unauthenticated** on the US and trials patient hosts — EU ships a placeholder | OBSERVED | unrated; "same class as S3, but worse in two ways" [CROSS-REGION] |
| F2 | Hardcoded `x-api-key` in a public bundle, replicated on two hosts; prod API base points at a `dev.` host | OBSERVED | low — verified not live [SECURITY-FINDINGS S3] |
| F3 | Health-data portal ships **zero security headers** | OBSERVED | low-moderate [SECURITY-FINDINGS S1] |
| F4 | Pre-Auth0 authorize URLs in public archives carrying session material — one in plaintext | PUBLISHED | unrated [ARCHIVE-URLS §7] |
| F5 | Internal hostnames disclosed via certificate-transparency logs | OBSERVED | informational [SECURITY-FINDINGS S5] |
| F6 | `lhpro`/`lghpro` range typo — published bound exactly 2,000,000 too low | PUBLISHED | unrated (vendor data bug) [HCP-SCHEMA §6.1] |
| F7 | The single header gate that isn't — `pow.crm.settings` | OBSERVED | hygiene nit [AUTH-TENANT §9] |
| F8 | PKCE optional, `plain` accepted, custom-scheme redirect | OBSERVED | low-moderate [SECURITY-FINDINGS S2] |
| F9 | Vendor data-hygiene bugs + an unconditional-gzip protocol violation | OBSERVED | unrated [PUBLIC-CONFIG; README rule 6] |
| F10 | No `security.txt` anywhere in the public estate | OBSERVED | informational [SECURITY-FINDINGS S6] |

## F1 — Reports-broker credentials published by the US and trials configs

`nutrino.cc.broker.service.config.security_headers["x-api-key"]`, and the same
key again in `nutrino.cc.metadata.service.config`, are served by
`GET /patient/v2/configuration/public` — **unauthenticated, on all three
deployments** [source: CROSS-REGION §SECURITY]:

| deployment | published value |
|---|---|
| EU | literal placeholder `%#$^&#GFFG@#*%&#$` (17 chars, starts `%#`) — not a credential |
| US | a real-looking base64 token, 18+ chars |
| trials | a **different** real-looking base64 token |

Two distinct 40-char tokens for the reports brokers were confirmed mechanically
[source: AWS-GATEWAYS §8]. These keys authenticate to
`commoncore.medtronic.{eu,com}/reports-broker/v1` and `/reports-metadata/v1` —
the CSV/PDF report backend over pump + CGM data, behind repo issue **#76**. The
values exist only in gitignored raw captures; per README rule 1 this page
records *that* they are exposed and *where*, never the values
[source: CROSS-REGION].

**Why it ranks first.** Same defect class as F2, worse in two ways: it is **on
the patient host**, unauthenticated, for any internet client; and **EU ships an
obviously-fake placeholder while US and trials ship working-looking secrets**, so
the EU value has passed internal review as fake and nobody noticed the other
two [source: CROSS-REGION]. Whether either key is live is **Unknown — not
tested, deliberately**: testing requires an authenticated call to a production
medical-data service, outside a read-only pass [source: CROSS-REGION]. A
known-dead key (F2) is a smaller problem than an untested one. Do **not**
conflate three separate values: the EU placeholder here, the bundle key in F2,
and the inert HCP-side placeholder in `pow.nutrino.cc.*.service.config`, which
is "the inert placeholder … *not* the live bundle credential" [source:
HCP-SCHEMA §6.4; PUBLIC-CONFIG §Config-integrity notes].

## F2 — Hardcoded `x-api-key` in the public bundle, on two hosts

`https://carelinkhp.minimed.eu/main.fb5f8cb7eb60c4d5.js` contains
`security_headers:{"x-api-key":"<redacted>"}` and
`host:"https://dev.commoncore.medtronic.eu/reports-broker/v1/ocl"` — a
credential shipped to every visitor, and a **production portal configured
against a development endpoint**; the two reports services share the key
[source: SECURITY-FINDINGS S3]. The key does **not** authenticate against
production: `commoncore.medtronic.eu` and `.com` return 403 `Missing
Authentication Token` with the key and 403 without; `dev.commoncore.medtronic.eu`
is 502 (backend down), and the gateway wants a different credential entirely
(AWS API Gateway error shape) [source: SECURITY-FINDINGS S3]. Severity low, but
permanent until the deployed bundle is rebuilt.

**It replicates.** `carelink.medtronic.com` serves the same file to the byte —
3397615 B, sha256 `2a7fa8e7af519c2b`, `cmp` identical — and
`carelink-support.medtronic.com` serves the same document [source:
SECURITY-FINDINGS addendum; RECON-SUBDOMAINS §4.2]. Any remediation conversation
must name both hosts; a fix scoped to `carelinkhp` fixes half of it. ⚠
Correction preserved: S3 was first recorded as one host's property and was
**widened to the bundle** on 2026-10-09 [SECURITY-FINDINGS addendum].

## F3 — Zero security headers on the health-data portal

**Observed** on both the HTML document and the 3.4 MB JS asset of
`carelinkhp.minimed.eu` — a diabetes health-data dashboard: no
`strict-transport-security`, no `content-security-policy`, no `x-frame-options`,
no `x-content-type-options`, no `referrer-policy`, no `permissions-policy`
[source: SECURITY-FINDINGS S1]. **Impact:** the portal is framable
(clickjacking), MIME-sniffable, and any successful content injection would run
unrestricted — unambiguously missing, on the highest-value host, and
`status.minimed.com` proves the vendor does this properly elsewhere. Severity
low-moderate.

⚠ Two self-corrections preserved, because both were nearly published as
findings: TLS 1.0/1.1 were first recorded as "accepted" — that was a grep
matching error output, they are **rejected**; and `clcloud.minimed.eu` was first
recorded as header-less because `/` was probed on an API-only host — against
the discovery path it does send HSTS/CSP/XFO. `carelinkhp` remains genuinely
header-less, confirmed on both the HTML and the JS [source: SECURITY-FINDINGS
§Checked-and-clean].

## F4 — Pre-Auth0 authorize URLs carrying session material, in public archives

**Observed** in Wayback CDX results (PUBLISHED — archive records; nothing here
was fetched live) [source: ARCHIVE-URLS §7]:

- `mdtlogin.medtronic.com/…/authorize/login?action=display&sessionID=<uuid>&sessionData=<JWE>…`
  — `sessionData` is an **encrypted** JWE, so the payload is not readable, but
  the `sessionID` is a live-looking UUID in a public URL. 401 captures,
  2021-09-17 → 2025-12-09.
- `mdtlogin-ocl.medtronic.com/mmcl/…/authorize/login?…&sessionData=<JWS>…` —
  `sessionData` is an HS256 JWS whose payload is **plaintext base64url** and
  decodes to the whole authorization request (`sessionID`, `exp`,
  `current_username`, `client_name`, `scope_verified`, `client_id`,
  `redirect_uri`, `id_token_hint`, `nonce`, `acr_values`). 2 captures,
  2024-02-26 and 2024-09-12. "The whole authorization request is in the URL and
  is not confidential on this legacy edge."
- Separately, `wwwp.medtronic.com` URLs carry Java `;jsessionid_*=` values in
  the **path** (URL rewriting) — 8,058 markers in one CDX shard, 16,776 in
  another, 2024-10-03 → 2024-10-16 [source: COMMONCRAWL §9].

**Impact.** An authenticated session identifier sitting in a crawlable URL is a
public-archive property, not something this research caused — but it is a genuine
historical exposure, and a plausible contributor to why those URLs are archived
at all. The pre-Auth0 Layer7 flow put full authorization state in the URL by
construction; "a category of exposure the Auth0 track no longer has" [source:
ARCHIVE-URLS §7]. Mitigating context: the legacy edge is dead anyway — both
`mdtlogin*` hosts resolve but refuse TCP :443 [source: AUTH-TENANT §6; CONFIG-NS
E1/E2]. Per README rule 3 the raw captures are quarantined; only the redacted
shapes and the facts are published.

## F5 — Internal hostnames exposed by CT logs

`subfinder` + crt.sh surfaced 599 hostnames, 240 resolvable, including internal
infrastructure names — `grafana.<internal>.minimed.com`,
`k8s.<internal>.minimed.com`, `gitlab.<internal>.minimed.eu`,
`prometheus.<internal>.minimed.eu`, `db.<internal>.minimed.com` — plus ~400
dev/stage/test names [source: SECURITY-FINDINGS S5]. Names are redacted to
`<service>.<internal>` per README rule 2; the finding — that a vendor's CT logs
leak internal infrastructure names — survives the redaction, the names do not.
**Impact:** every one returns `HTTP 000` from a public network — the correct
posture; zero of 260 focus names resolved to an RFC1918/CGNAT address [source:
SECURITY-FINDINGS S5; RECON-SUBDOMAINS §8]. The exposure is informational: the
names are permanent public information, a free target list. ⚠ Standing caveat:
any CT-derived host list must first be filtered against the parked wildcard
namespaces (`*.carelink.{eu,com}`, `*.clcloud.eu`) — 49 collected names there
are false positives, and "seeding them as Medtronic domains is exactly how a
false positive would reach a disclosure" [source: SECURITY-FINDINGS addendum;
RECON-SUBDOMAINS §3].

## F6 — The `lhpro`/`lghpro` range typo (off by exactly 2,000,000)

The patient config publishes `csr.control.codes.settings.ranges.lhpro.max =
.lghpro.max = 4292967295`. The correct uint32 maximum is `4294967295` (2³²−1);
the published value is exactly 2,000,000 too low and is wrong in **both**
ranges, so it is a consistent upstream typo rather than a per-field slip — the
HCP-side `cua.control.codes.settings` carries the correct `4294967295`, which is
how the two were compared [source: HCP-SCHEMA §6.1; HURL-05]. **Impact:** any
client validating a low-hypo / low-hypo-profile control code against the
published bound rejects 2,000,000 legitimate values [source: HURL-05]. The
regression suite asserts the **current (wrong)** value on purpose, so a vendor
fix fails loudly and updates the note rather than the fact going stale.

## F7 — The single header gate that isn't (`pow.crm.settings`)

Nine siblings under `/hcp/configuration/public/*` on `carelink.medtronic.eu`
return **412** without the client header (`X-System-ID: ProWeb`);
`pow.crm.settings` returns **200 `application/octet-stream`, 96 B,
unauthenticated**: `{"base.uri":"https://carelink.medtronic.eu/crm",
"product":"pow","version":"4.5"}` [source: AUTH-TENANT §9]. The header contract
itself is sound — the header is mandatory and its **value** is validated against
a vendor whitelist (`NotARealClient` → 412, empty → 412), though the value
comparison is case-insensitive while the key namespace is case-sensitive
[source: HCP-SCHEMA §2, §4]. **Impact:** low sensitivity — a CRM base URI and a
version string, no PII, no credential. The finding is the **inconsistency**: a
client-identity gate applied to nine siblings and not the tenth [source:
AUTH-TENANT §9]. It also corroborates that the shadow deployment's content
namespace is `pow` (version 4.5) where the patient deployments use `ocl`
[source: COMMONCRAWL §5]. Pinned by `HURL-05` so the drift is visible if the
gate is ever added or removed.

## F8 — PKCE is optional and `plain` is accepted

`code_challenge_methods_supported` advertises `S256, plain`. Against the real
authorize endpoint: `S256` → 302 (accepted), **`plain` → 302 (accepted)**,
`none` → 302 `invalid_request` (rejected), **omitted entirely → 302 (accepted)**
[source: SECURITY-FINDINGS S2; CLAIM-AUDIT second batch]. **Impact:** the
CareLink redirect is `com.medtronic.carepartner:/sso`, a custom URI scheme; on
Android any app can register the same scheme, and PKCE is the mitigation for a
malicious app intercepting that redirect — here it is **client-enforced only**
[source: SECURITY-FINDINGS S2]. The client the bridge emulates does send S256,
so the bridge is fine; the *platform* default is weak. Severity low-moderate.
Recorded so nobody "simplifies" it: the bridge correctly hardcodes S256
[source: AUTH-TENANT §2].

## F9 — Vendor data bugs and the unconditional-gzip protocol violation

Three parsing-level defects in vendor-published material:

- **Trailing-whitespace padding.** The `SIMPLERA` model list contains entries
  like `"MMT-5100       "`, `"MMT-5100J      "`, `"MMT-5100CLXP   "` — an
  exact-match parser silently misses them; the bridge's `normalise()` (uppercase
  + strip non-alphanumerics) handles it, a naive `===` would not (OBSERVED)
  [source: PUBLIC-CONFIG §#81; HURL-05].
- **Two unit keys that disagree.** `bgUnits` and `glucoseUnitsDefault` report
  different units in **BE, ES and IT** (`MG_DL` vs `MMOL_L` in the same
  response) — reading one and not the other mis-scales every value (OBSERVED)
  [source: CONFIG-DEEP NEW item 7; CLAIM-AUDIT third batch]. The bridge is
  unaffected: the transform reads the unit from the data payload, never from
  country settings [source: CLAIM-AUDIT third batch].
- **Unconditional gzip.** `carelink.minimed.eu` serves `Content-Encoding: gzip`
  ignoring `Accept-Encoding` entirely — verified against `identity`, `gzip` and
  `deflate` (magic `1f8b` in all three) — an RFC 9110 §8.4 violation that breaks
  any client that does not opt in (OBSERVED) [source: README rule 6; HURL-05
  header]. Use `curl --compressed`; a plain `curl -o` writes raw gzip and every
  later parse fails [source: PUBLIC-CONFIG §The endpoint].

A related trap in the same family: the per-key config envelope returns booleans
as the **strings** `"true"`/`"false"`, so `resp.value === false` silently never
fires [source: CONFIG-DEEP §HEADLINE].

## F10 — No `security.txt` anywhere

`/.well-known/security.txt` was checked on all 11 live hosts plus
`www.medtronic.com` and `medtronic.{com,eu}`. Every 200 was the Angular SPA
catch-all returning HTML, never an RFC 9116 file; the corporate security pages
404 or return an Akamai error page [source: SECURITY-FINDINGS S6]. Impact:
informational, but it means there is **no published channel to report
through** — a fact that shapes how any of the above would ever be disclosed.

## What was checked and found clean

Recorded so a future pass does not redo them (all OBSERVED unless noted)
[source: SECURITY-FINDINGS §Checked-and-clean; RECON-SUBDOMAINS §8;
ARCHIVE-URLS §8; CLAIM-AUDIT]:

| Check | Result |
|---|---|
| TLS protocol floors | TLS 1.0/1.1 **rejected** ("no protocols available"); 1.2/1.3 only — ⚠ first recorded wrong, see F3 |
| Negotiated cipher | `TLS_AES_128_GCM_SHA256`, X25519MLKEM768 post-quantum hybrid |
| OAuth `redirect_uri` | **strict allowlist** — attacker redirect → 403 `redirect_uri is not in the list of allowed callback URLs` |
| `device_code` grant | **disabled** for both client_ids — 403 `unauthorized_client` (answered an August open question) |
| CORS on `carelink-login` | `*` **with `credentials: false`** — the safe combination |
| HSTS on login hosts | `max-age=31536000; includeSubDomains` |
| PKCE `none` | rejected |
| Unauthenticated patient data | everything 401 `InvalidToken`; nothing readable |
| Internal infra reachability | all unreachable from the public internet |
| Mixpanel session recording | `record_sessions_percent: 0` — present, off |
| Secrets other than F1/F2 | none found |
| RFC1918 exposure | zero of 260 focus names resolved to a private address |
| Common Crawl coverage of the API surface | zero captures — a clean negative, not a gap in the sweep [COMMONCRAWL §1] |
| Cardiac CareLink CVE cluster (CVE-2025-12994/995/996/977, ICSMA-25-205-01) | **not applicable** — Medtronic's own bulletin states it does not affect diabetes CareLink Personal; do not cite as a vulnerability of this surface [POSTURE-0721 R8] |

## Untested, and the client side

**Untested:** whether any host would accept a token minted by one of the
**shadow** Auth0 tenants. Separate issuers plus completely disjoint JWKS kids
across all four tenants say it should not — so the exposure, if any, is a
verifier bug (accepting an arbitrary `kid` and skipping issuer/audience checks),
not a key leak [source: SECURITY-FINDINGS closing; AUTH-TENANT §8]. The archive
adds eight more named non-prod shadow login hosts whose JWKS kids remain
unknown — **12 candidate hostnames, 4 with known key material** [source:
COMMONCRAWL §4e]. Blocked on a token; not attempted.

**The client side** is not part of the vendor surface but belongs in the
picture, reviewed 2026-07-21 [source: POSTURE-0721]: plaintext `logindata.json`
holding full OAuth tokens (R1), `.env` carrying both the CareLink password and
the Nightscout `API_SECRET` (R2), verbose-mode logging of full CGM upload bodies
to journald (R9), and no signed tags or SLSA provenance (R6). All are fork-side
hardening items, not vendor findings — recorded so the two sides are never
conflated in a report.
