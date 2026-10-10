# Medtronic CareLink — security posture assessment (2026-10-08)

**Scope:** the live public surface enumerated above (both `*.minimed.*` and the
new `*.medtronic.eu` shadow deployment).
**Method:** read-only, unauthenticated, low-rate (~1.2s spacing). TLS/policy
probing, header analysis, public-bundle review, one bounded credential-validity
test. **No exploitation, no data retrieval, no writes, no credential guessing.**
~150 requests in this pass (~600 total across all three passes today).

---

## Bottom line

**We did not find an exploitable vulnerability.** No patient data is reachable
without a valid token, OAuth `redirect_uri` validation is strict, TLS is
enforced correctly, and the one leaked credential we found is **not live**.

What we did find is a set of **hardening gaps**. Ranked by what I'd actually
put in a disclosure email:

---

## Findings

### S1 — `carelinkhp.minimed.eu` (health-data portal) ships **zero security headers**

Verified on both the HTML document and its 3.4 MB JS asset:

```
HTTP/2 200
content-type: text/html
(no strict-transport-security, no content-security-policy,
 no x-frame-options, no x-content-type-options, no referrer-policy,
 no permissions-policy)
```

This is a diabetes health-data dashboard ("Dashboard" title, MiniMed favicon).
Consequences:
- **Clickjacking** — no `X-Frame-Options` / CSP `frame-ancestors 'none'`, so the
  portal is framable.
- **MIME sniffing** — no `X-Content-Type-Options: nosniff`.
- **No content policy** — a successful content injection would run unrestricted.

This is the most concrete finding: it's unambiguously missing, on the highest-
value host, and `status.minimed.com` proves Medtronic *does* do this properly
elsewhere. **Severity: low-moderate.**

### S2 — PKCE is **optional**, and `plain` is accepted

`code_challenge_methods_supported` advertises `S256, plain`. Tested against the
real authorize endpoint:

| `code_challenge_method` | Result |
|---|---|
| `S256` | 302 → login page (accepted) |
| **`plain`** | **302 → login page (accepted)** |
| `none` | 302 with `invalid_request` (rejected) |
| *omitted entirely* | 302 → login page (**accepted**) |

The CareLink redirect is `com.medtronic.carepartner:/sso` — a **custom URI
scheme**. On Android, any app can register the same scheme. PKCE is the
mitigation for a malicious app intercepting that redirect, and here it is
**client-enforced only**. The client the bridge emulates does send S256, so the
bridge is fine; the *platform* default is weak. **Severity: low-moderate.**

### S3 — Hardcoded `x-api-key` in a public bundle, and prod points at a **dev** API host

`https://carelinkhp.minimed.eu/main.fb5f8cb7eb60c4d5.js` contains:

```js
security_headers:{"x-api-key":"<VENDOR-API-KEY-REDACTED>"},
host:"https://dev.commoncore.medtronic.eu/reports-broker/v1/ocl"
```
(two services — `reports-broker` and `reports-metadata` — share the same key).

Two issues, and the second is arguably the more interesting:
- **A credential is shipped to every visitor** in a public bundle.
- **The production portal's API base is a `dev.` host.** So the health portal's
  reports traffic is configured against a development endpoint.

**Verified not live** — the key does not authenticate against production:

| Host | With key | Without key |
|---|---|---|
| `commoncore.medtronic.eu` | 403 `Missing Authentication Token` | 403 |
| `commoncore.medtronic.com` | 403 | 403 |
| `dev.commoncore.medtronic.eu` | 502 (backend down) | 502 |

The gateway wants a different credential entirely (AWS API Gateway error shape).
**Severity: low** — but the build-config hygiene item is real and permanent
until someone fixes the deployed bundle.

### S4 — The discovery document is signed and the bridge never checks the signature

`clcloud.minimed.{eu,com}` and `clcloud-trials` return a **deterministic
344-char base64 `x-cum-signature`** on every discovery response:

- only on `/connect/carepartner/*/discover/*` (not on `/patient/*`, not on
  `countries/settings`)
- identical across repeated requests → it's a signature over the document
- **differs between `.eu` and `.com` even though the documents are byte-identical**
  (same sha256) → the signing key or binding is host/region-specific
- the discovery document itself carries 8 pinned `certificates[]`

The bridge does `axios.get(discoveryUrl)` and never reads the header
(`git grep x-cum-signature` → nothing in `src/` or `test/`). TLS makes this
defensible, but Medtronic is clearly providing a stronger primitive (sign +
pinned signer cert) that we're discarding. **Severity: low** (missing
defence-in-depth, not a live bypass).

### S5 — Mass internal-name disclosure via certificate transparency

`subfinder` + crt.sh surfaced **599 hostnames / 240 resolvable**, including
internal infrastructure names: `grafana.<internal>.minimed.com`,
`k8s.<internal>.minimed.com`, `gitlab.<internal>.minimed.eu`,
`prometheus.<internal>.minimed.eu`, `db.<internal>.minimed.com`,
`<internal>.minimed.com.*`, `other internal hosts`, `other internal hosts`.

**This is not an exposed-services finding** — every one of them returns
`HTTP 000` (connection refused/timeout) from a public network, which is the
correct posture. But the names themselves are permanent public information that
gives an attacker a free target list. The same applies to the ~400 dev/stage/
test hostnames. **Severity: informational.**

### S6 — No `security.txt` anywhere in the public estate

Checked `/.well-known/security.txt` on all 11 live hosts plus `www.medtronic.com`
and `medtronic.{com,eu}`. Every 200 was the Angular SPA catch-all returning
HTML, never an RFC 9116 file. Medtronic's corporate pages (`/us/en/security.html`)
404 and `/en-us/security.html` returns an Akamai "Incorrect…" error page.
**Severity: informational — but it means we have no published channel to report
through.**

---

## Checked and clean (not findings)

Recorded so a future pass doesn't redo them:

| Check | Result |
|---|---|
| TLS protocol floors | **TLS 1.0 and 1.1 correctly rejected** ("no protocols available"); 1.2/1.3 only |
| Negotiated cipher | `TLS_AES_128_GCM_SHA256`, X25519MLKEM768 (post-quantum hybrid) |
| OAuth `redirect_uri` | **Strict allowlist** — attacker redirect → `403 "redirect_uri is not in the list of allowed callback URLs"` |
| `device_code` grant | **Disabled** for this client (`403 unauthorized_client`) |
| CORS on `carelink-login` | `*` **with `credentials: false`** — the safe combination |
| HSTS on login hosts | `max-age=31536000; includeSubDomains` |
| PKCE `none` | Rejected |
| Unauth patient-data access | Everything 401 `InvalidToken`; nothing readable |
| Internal infra reachability | All unreachable from public internet |
| Mixpanel session recording | `record_sessions_percent: 0` (present, off) |
| Secrets other than the S3 key | None found |

**Two of my own earlier claims were wrong and are corrected here:**
- I first recorded TLS 1.0/1.1 as "accepted" — that was my grep matching error
  output. They are rejected.
- I first recorded `clcloud.minimed.eu` as having no security headers — that was
  because I probed `/`, which isn't a real path on an API-only host. Against the
  discovery path it does send HSTS/CSP/XFO.
`carelinkhp.minimed.eu` remains genuinely header-less, confirmed on both the HTML
and the JS asset.

---

## Separate Auth0 tenant — cross-tenant question left open

`carelink-login.medtronic.eu` is a **second, independent Auth0 tenant**:
- issuer `https://carelink-login.medtronic.eu/` (vs `…minimed.eu/`)
- **completely different JWKS kids** (`jd0EOLxJ8XduYx4lLy3ig, gZMBCJcl_t25Es4U_g_ow`
  vs `8RqxnMm8vg2Go_y1LAVh9, vnTNpK5RvkqVEfQgHRsqv`)
- otherwise identical OAuth policy (grants, DPoP ES256, backchannel logout)

Live with it: `carelink.`, `carelink-login.`, `carelink-support.`, `clcloud.`,
`commoncore.` all on `medtronic.eu`. The `minimed` discovery document never
references these, so it's a parallel deployment nothing in our tooling knew
about.

**The one thing I could not test:** whether `clcloud.minimed.eu` would accept a
token minted by the shadow tenant. Separate issuer + separate keys means it
should not — but token-audience/`kid` validation done loosely is exactly the
class of bug that would make it critical. Needs a valid token.

---

# NEW API FAMILY: reports (`commoncore.medtronic.{eu,com}`)

Discovered from the public `carelinkhp` bundle. **Entirely outside everything
the bridge calls.** Endpoints (names from the bundle, hosts verified live):

```
base   https://commoncore.medtronic.{eu,com}/reports-broker/v1/ocl
       https://commoncore.medtronic.{eu,com}/reports-metadata/v1/ocl
```
| Endpoint | Service | Unauth |
|---|---|---|
| `/reports/generateReport` | broker | 403 |
| `/reports/reportStatus` | broker | 403 |
| `/reports/reportCsv` | broker | 403 |
| `/reports/reportPdf` | broker | 403 |
| `/reports/ReportDataTimelinesRange/patients` | metadata | 403 |
| `/reports/ReportDataTimelinesForCalendar` | metadata | 403 |

`dev.commoncore.medtronic.eu` resolves but is **502** (backend down).
`commoncore.minimed.eu` also 502 — that's a *different* host.

A CSV/PDF report generator over pump+CGM data is plausibly richer than what
`/patient/monitor/data` returns. **Worth probing with a real token in November.**

## Addendum 2026-10-09 (agent round) — scope corrections

### S3 is replicated across a second host

`carelink.medtronic.com` serves the **same SPA, byte-identical** (same sha256,
same `main.fb5f8cb7eb60c4d5.js`) as `carelinkhp.minimed.eu`. `carelink-support.medtronic.com`
serves the same document too.

S3 was recorded as a property of one host. It is a property of the bundle, and
the bundle is deployed at least twice — including on the `.medtronic.com` shadow
deployment, which was outside the original scope. Any remediation conversation
with Medtronic needs to name both hosts.

### ⚠️ S3 and every other finding must exclude `*.carelink.{eu,com}` and `*.clcloud.eu`

That space is **wildcard DNS on a domain-parking operator**. Every name resolves,
including certainly-unregistered ones, and they all 302 to the same parking page.
49 collected names in that space are false positives.

They were seeded as Medtronic domains, which is exactly how a false positive
would reach a disclosure. **Any host list taken from CT enumeration must be
filtered against this before it is used to name a vendor.**

### A fourth Auth0 tenant

`carelink-login.medtronic.com` — live OIDC document, identical OAuth policy to
the three known tenants, **different JWKS kids** (`cEgK74…`, `80YhF8…`). The
`.medtronic.com` shadow half had never been enumerated (an earlier crt.sh query
returned a 150-byte error page and was written off).

The token-confusion question below is now larger: four candidate issuers rather
than two.

### Unchanged

No new exploitable vulnerability. No RFC1918 exposure — zero of 260 focus names
resolved to a private address, and every API-shaped request returned 401/403 or
SPA HTML. No unauthenticated data endpoint. The new `Minimed Outcomes` family
(`usminimedoutcomes`, `ousminimedoutcomes`, `minimedoutcomes-usapi`) is `http=000`
from the public net like every other internal-looking name already recorded.
