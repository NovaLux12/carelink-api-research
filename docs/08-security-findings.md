# Security findings

A ranked, defensive summary of the security posture of Medtronic's public
CareLink surface — what the vendor exposes, and why it matters. Everything here
was observed **read-only and unauthenticated** during the 2026-10-08 → 10-10
passes: no exploitation, no data retrieval, no writes, no credential guessing
[source: findings-log/probe-2026-10-08/SECURITY-FINDINGS.md §Scope]. Where a
source describes an attack surface this page records the **observation and the
impact**, never a recipe. Extends [`00-summary-the-map.md`](00-summary-the-map.md).

> **To report an exposure, or a vulnerability in a client.** An exposure in
> Medtronic's own surface belongs here, reported **redacted** — never the value —
> via this repo's [`SECURITY.md`](../SECURITY.md). A vulnerability in client code is
> a different repo: [NovaLux12/carelink-bridge](https://github.com/NovaLux12/carelink-bridge/security/advisories/new),
> whose own [`SECURITY.md`](https://github.com/NovaLux12/carelink-bridge/blob/main/SECURITY.md)
> is its private-advisory channel. The findings below are the vendor-side posture a
> client inherits; the client's own hardening is that repo's business.

Legend — **OBSERVED** = seen in a live response · **PUBLISHED** = in a vendor
document served without a login (live, or recovered from a public archive) ·
**INFERRED** = reasoned, not seen. Citations are `[source: findings-log/<file> §n]`;
in tables the bare name is that same file under `findings-log/probe-2026-10-08/`
(subdirs as named; `DRIFT-AND-NEW` = `recon/DRIFT-AND-NEW-2026-10-10.md`), except
`POSTURE-0721` =
`../medtronic-carelink-2026-07-21/11-public-security-posture.md` and `HURL-05` =
`regression/hurl/05-public-config.check.sh` (repo root).

**No exploitable vulnerability was found.** No patient data is reachable without
a valid token, `redirect_uri` validation is strict, TLS is enforced correctly,
and the one leaked credential in the public JS bundle is **verified not live**
[source: SECURITY-FINDINGS §Bottom line]. What exists is a set of **hardening
gaps**, ranked below in disclosure order.

| # | Finding | Class | Severity (per source) |
|---|---|---|---|
| F1 | Reports-broker API keys published **unauthenticated** on the US and trials patient hosts — EU ships a placeholder | OBSERVED | unrated; "same class as S3, but worse in two ways" [CROSS-REGION] |
| F2 | Hardcoded `x-api-key` in a public bundle, replicated beyond one host; prod API base points at a `dev.` host | **see correction below** — the host count and evidence class are corrected | low — verified not live [SECURITY-FINDINGS §S3] |

> **⚠ Corrected 2026-10-12 by area Y.** This row previously read *"replicated across **five
> hosts** (drift-swept)"* and was labelled **OBSERVED**. Two defects, either sufficient alone:
>
> 1. **The count outran its own citation.** This row cites `SECURITY-FINDINGS.md` §S3, whose
>    section is titled *"S3 is replicated across a second host"* and which says the bundle is
>    deployed **"at least twice" — including on the `.medtronic.com` shadow**. Two, not five.
> 2. **The evidence class is the one the source forbids.** The corroborating drift file opens
>    *"**Provenance:** this file is a **reconstruction from the agent's report** … Re-verify
>    before treating any row as **OBSERVED**"*.
>
> **The later paragraph in this section, which carries the same count, is separately correct and is NOT changed.** It cites
> `DRIFT-AND-NEW`, which has a section headed *"Five hosts, not two"*, and it already carries
> the caveat *"recorded as reported; the sweep's own caveat is that its evidence table was never
> written to disk and must be re-verified before being treated as OBSERVED"*. An earlier draft of
> this correction wrongly extended to it on the strength of this row's citation; the two cite
> **different sources**, and the retraction is preserved here rather than deleted.
>
> **Not a disclosure change.** The key is redacted, the finding is "verified not live", and no
> new host is named.
| F3 | Health-data portal ships **zero security headers** | OBSERVED | low-moderate [SECURITY-FINDINGS S1] |
| F4 | Pre-Auth0 authorize URLs in public archives carrying session material — one in plaintext | PUBLISHED | unrated [ARCHIVE-URLS §7] |
| F5 | Internal hostnames disclosed via certificate-transparency logs | OBSERVED | informational [SECURITY-FINDINGS S5] |
| F6 | `lhpro`/`lghpro` range typo — published bound exactly 2,000,000 too low | PUBLISHED | unrated (vendor data bug) [HCP-SCHEMA §6.1] |
| F7 | The single header gate that isn't — `pow.crm.settings` | OBSERVED | hygiene nit [AUTH-TENANT §9] |
| F8 | PKCE optional, `plain` accepted, custom-scheme redirect | OBSERVED | low-moderate [SECURITY-FINDINGS S2] |
| F9 | Vendor data-hygiene bugs + an unconditional-gzip protocol violation | OBSERVED | unrated [PUBLIC-CONFIG; README rule 6] |
| F10 | No `security.txt` anywhere in the public estate | OBSERVED | informational [SECURITY-FINDINGS S6] |

## F1 — **Held back — not published**

A ranking of severity is deliberately absent, because the finding it would rank
is not published.

What was found, in one sentence with no values: **two of the three deployments
publish service credentials in their unauthenticated public configuration, while
the third ships an obvious placeholder.** The credentials home to the reports
backend discussed under #76.

What is withheld:

- **The values, everywhere.** Never in this repo.
- **The comparison between deployments.** That is the finding that makes it
  reportable, and it is held for a disclosure decision.
- **Whether any credential involved is live.** Deliberately never tested — that
  would need an authenticated call to a production medical-data service, well
  outside a read-only pass. Nothing here should be read as a claim that anything
  works.

The one half that **is** published: the EU deployment ships a 17-character literal
placeholder. That is published because it explains the bug class and exposes
nothing.

> Recorded so a future reader knows something was removed on purpose, rather than
> never looked for.

## F2 — Hardcoded `x-api-key` in the public bundle, replicated

`https://carelinkhp.minimed.eu/main.fb5f8cb7eb60c4d5.js` contains
`security_headers:{"x-api-key":"<redacted>"}` and
`host:"https://dev.commoncore.medtronic.eu/reports-broker/v1/ocl"` — a
credential shipped to every visitor, and a **production portal configured
against a development endpoint**. The key does **not** authenticate against
production: `commoncore.medtronic.eu` and
`.com` return 403 `Missing Authentication Token` with the key and 403 without;
`dev.commoncore.medtronic.eu` is 502 (backend down), and the gateway wants a
different credential entirely (AWS API Gateway error shape) [source:
SECURITY-FINDINGS S3]. **It replicates.** `carelink.medtronic.com` serves the same
file to the byte — 3397615 B, sha256 `2a7fa8e7af519c2b`, `cmp` identical — so S3 was
**widened from one host to the bundle** on 2026-10-09 [source: SECURITY-FINDINGS
addendum; RECON-SUBDOMAINS §4.2]. The 2026-10-10 drift sweep then found
`carelink-support.medtronic.eu` serving the same document in a **different
build** (`main.759cddab23085086.js`, sha256 `f637c8d0…`) carrying the identical
key material and the same dev-host bug, so the finding spans **five hosts** —
recorded as reported; the sweep's own caveat is that its evidence table was
never written to disk and must be re-verified before being treated as OBSERVED
[source: DRIFT-AND-NEW; docs/00-summary-the-map.md].

## F3 — Zero security headers on the health-data portal

**Observed** on `carelinkhp.minimed.eu`'s HTML document and its 3.4 MB JS asset
— a diabetes health-data dashboard: no
`strict-transport-security`, no `content-security-policy`, no `x-frame-options`,
no `x-content-type-options`, no `referrer-policy`, no `permissions-policy`
[source: SECURITY-FINDINGS S1]. **Impact:** the portal is framable
(clickjacking), MIME-sniffable, and any successful content injection would run
unrestricted — unambiguously missing, on the highest-value host, and
`status.minimed.com` proves the vendor does this properly elsewhere. ⚠ Two
self-corrections preserved: TLS 1.0/1.1 were first recorded
as "accepted" — that was a grep matching error output, they are **rejected**; and
`clcloud.minimed.eu` was
first recorded as header-less because `/` was probed on an API-only host — against
the discovery path it does send HSTS/CSP/XFO. `carelinkhp` remains genuinely
header-less [source: SECURITY-FINDINGS §Checked-and-clean].

## F4 — Pre-Auth0 authorize URLs carrying session material, in public archives

**Observed** in Wayback CDX results (archive records; nothing fetched live)
[source: ARCHIVE-URLS §7]:

- `mdtlogin.medtronic.com/…/authorize/login?action=display&sessionID=<uuid>&sessionData=<JWE>…`
  — an **encrypted** JWE payload (not readable), but a live-looking `sessionID`
  UUID in a public URL. 401 captures, 2021-09-17 → 2025-12-09.
- `mdtlogin-ocl.medtronic.com/mmcl/…/authorize/login?…&sessionData=<JWS>…` — an
  HS256 JWS whose payload is **plaintext base64url** and decodes to the whole
  authorization request (`sessionID`, `exp`, `current_username`, `client_id`,
  `redirect_uri`, `id_token_hint`, `nonce`, …). 2 captures, 2024-02-26 and
  2024-09-12: "the whole authorization request is in the URL and is not
  confidential on this legacy edge."
- Separately, `wwwp.medtronic.com` URLs carry Java `;jsessionid_*=` values in the
  **path** — 8,058 markers in one CDX shard, 16,776 in a second, 2024-10-03 →
  2024-10-16 [source: COMMONCRAWL §9].

**Impact.** An authenticated session identifier sitting in a crawlable URL is a
public-archive property, not something this research caused — but a genuine
historical exposure: the pre-Auth0 Layer7 flow put full authorization state in the
URL by construction, "a category of exposure the Auth0 track no longer has"
[source: ARCHIVE-URLS §7]. The legacy edge is dead anyway — both `mdtlogin*`
hosts refuse TCP :443 [AUTH-TENANT §6; CONFIG-NS E1/E2] — and the raw captures
are quarantined per README rule 3.

## F5 — Internal hostnames exposed by CT logs

`subfinder` + crt.sh surfaced 599 hostnames, 240 resolvable, including
`grafana.<internal>.minimed.com`, `k8s.<internal>.minimed.com`,
`gitlab.<internal>.minimed.eu`, `prometheus.<internal>.minimed.eu`,
`db.<internal>.minimed.com`, plus ~400 dev/stage/test names [source:
SECURITY-FINDINGS S5] — names redacted to `<service>.<internal>` per README rule
2, so the finding survives and the names do not. **Impact:** every one returns
`HTTP 000` (correct posture) and zero of 260 focus names resolved to
RFC1918/CGNAT [SECURITY-FINDINGS S5; RECON-SUBDOMAINS §8]. ⚠ Any CT-derived
host list must first be
filtered against the parked wildcard namespaces (`*.carelink.{eu,com}`,
`*.clcloud.eu`): 49 collected names there are false positives, and "seeding them
as Medtronic domains is exactly how a false positive would reach a disclosure"
[SECURITY-FINDINGS addendum].

## F6 — The `lhpro`/`lghpro` range typo (off by exactly 2,000,000)

The patient config publishes `csr.control.codes.settings.ranges.lhpro.max =
.lghpro.max = 4292967295`; the correct uint32 maximum is `4294967295` (2³²−1), so
the published bound is exactly 2,000,000 too low and is wrong in **both** ranges —
a consistent upstream typo, not a per-field slip. The HCP-side
`cua.control.codes.settings` carries the correct `4294967295`, which is how the
two were compared [source: HCP-SCHEMA §6.1; HURL-05]. **Impact:** a client
validating a low-hypo / low-hypo-profile control code against the published bound
rejects 2,000,000 legitimate values [source: HURL-05]. The regression suite
asserts the **current (wrong)** value on purpose, so a vendor fix fails loudly;
still unfixed upstream on 2026-10-10, tracked as issue **#97** [DRIFT-AND-NEW].

## F7 — The single header gate that isn't (`pow.crm.settings`)

Nine siblings under `/hcp/configuration/public/*` on `carelink.medtronic.eu`
return **412** without the client header (`X-System-ID: ProWeb`);
`pow.crm.settings` returns **200 `application/octet-stream`, 96 B,
unauthenticated**: `{"base.uri":"https://carelink.medtronic.eu/crm",
"product":"pow","version":"4.5"}` [source: AUTH-TENANT §9]. The header contract
itself is sound — mandatory, value-whitelisted (`NotARealClient` → 412)
[source: HCP-SCHEMA §2]. **Impact:** low
sensitivity — a CRM base URI and a version string, no PII, no credential; the
finding is the
**inconsistency**, a client-identity gate applied to nine siblings and not the
tenth [source: AUTH-TENANT §9], and is pinned by `HURL-05`.

## F8 — PKCE is optional and `plain` is accepted

`code_challenge_methods_supported` advertises `S256, plain`. Against the real
authorize endpoint: `S256` → 302 (accepted), **`plain` → 302 (accepted)**,
`none` → 302 `invalid_request` (rejected), **omitted entirely → 302 (accepted)**
[source: SECURITY-FINDINGS S2; CLAIM-AUDIT second batch]. **Impact:** the
redirect is `com.medtronic.carepartner:/sso`, a custom URI scheme; on Android
any app can register the same scheme, and PKCE is the mitigation for a malicious
app intercepting that redirect — here it is **client-enforced only** [source:
SECURITY-FINDINGS S2]. The bridge's client ([NovaLux12/carelink-bridge](https://github.com/NovaLux12/carelink-bridge)) does send S256 [AUTH-TENANT §2]; the
platform default is weak.

## F9 — Vendor data bugs and the unconditional-gzip protocol violation

Three parsing-level defects in vendor-published material:

- **Trailing-whitespace padding.** The `SIMPLERA` model list contains entries
  like `"MMT-5100       "` — an exact-match parser silently misses them;
  `normalise()` handles it, a naive `===` would not (OBSERVED) [source:
  PUBLIC-CONFIG §#81; HURL-05].
- **Two unit keys that disagree.** `bgUnits` and `glucoseUnitsDefault` report
  different units in **BE and CH** (`MG_DL` vs `MMOL_L` in the same
  response) — reading one and not the other mis-scales every value (OBSERVED)
  [source: CONFIG-DEEP NEW item 7; CLAIM-AUDIT third batch].
- **Unconditional gzip.** `carelink.minimed.eu` serves `Content-Encoding: gzip`
  ignoring `Accept-Encoding` entirely — verified against `identity`, `gzip` and
  `deflate` (magic `1f8b` in all three) — an RFC 9110 §8.4 violation that breaks
  any client that does not opt in; use `curl --compressed`, or a plain `curl -o`
  writes raw gzip and every later parse fails (OBSERVED) [source: README rule 6;
  HURL-05; PUBLIC-CONFIG].

## F10 — No `security.txt` anywhere

`/.well-known/security.txt` was checked on all 11 live hosts plus
`www.medtronic.com` and `medtronic.{com,eu}`: every 200 was the Angular SPA
catch-all returning HTML, never an RFC 9116 file; the corporate pages 404 or
Akamai-error [source: SECURITY-FINDINGS S6] — informational, but there is **no
published channel to report through**.

## What was checked and found clean

Recorded so a future pass does not redo them [source: SECURITY-FINDINGS
§Checked-and-clean; RECON-SUBDOMAINS §8] (all OBSERVED):

| Check | Result |
|---|---|
| TLS floors + cipher | 1.0/1.1 **rejected** ("no protocols available"), 1.2/1.3 only (⚠ first recorded wrong — see F3); `TLS_AES_128_GCM_SHA256`, X25519MLKEM768 post-quantum hybrid |
| OAuth `redirect_uri` | **strict allowlist** — attacker redirect → 403 `redirect_uri is not in the list of allowed callback URLs` |
| `device_code` grant | **disabled** for both client_ids — 403 `unauthorized_client` (answered an August open question) |
| Login-host posture | CORS `*` **with `credentials: false`** (the safe combination); HSTS `max-age=31536000; includeSubDomains`; PKCE `none` rejected |
| Unauthenticated patient data | everything 401 `InvalidToken`; nothing readable |
| Internal infra + telemetry | all unreachable from the public internet; Mixpanel session recording `record_sessions_percent: 0` — present, off; no secrets other than F1/F2 |
| Common Crawl coverage of the API surface | zero captures — a clean negative, not a gap in the sweep [COMMONCRAWL §1] |
| Cardiac CareLink CVE cluster (CVE-2025-12994/995/996/977, ICSMA-25-205-01) | **not applicable** — Medtronic's own bulletin states it does not affect diabetes CareLink Personal; do not cite as a vulnerability of this surface [POSTURE-0721 R8] |

## Untested, and the client side

**Untested:** whether any host would accept a token minted by one of the
**shadow** Auth0 tenants. Separate issuers plus completely disjoint JWKS kids
across all **five** tenants say it should not; the exposure, if any, is a
verifier bug (arbitrary `kid`, skipped issuer/audience checks), not a key leak
[source: SECURITY-FINDINGS closing; AUTH-TENANT §8;
findings-log/2026-10-12-area-i-auth0-tenant-behaviour/FINDINGS.md §5]. Blocked
on a token.

**The client side** is not part of the vendor surface but belongs in the
picture, reviewed 2026-07-21 [source: POSTURE-0721]: plaintext `logindata.json`
holding full OAuth tokens (R1), `.env` carrying both the CareLink password and
the Nightscout `API_SECRET` (R2), verbose-mode logging of full CGM upload bodies
to journald (R9), no signed tags or SLSA provenance (R6) — all fork-side items,
recorded so the two sides are never conflated in a report.
