# Hosts and estate

What exists on the Medtronic CareLink network: the deployments, the host
families, what each host actually is, and the namespace/version map that goes
with them. All of it observed read-only and unauthenticated. This page extends
[`00-summary-the-map.md`](00-summary-the-map.md) — it does not contradict it.

**Dated 2026-10-10.** The full reasoning is in `findings-log/`.

Legend — **OBSERVED** = seen in a live response · **PUBLISHED** = in a vendor document
served without a login (live, or recovered from a public web archive) · **INFERRED** =
reasoned, not seen.

> **Navigation** — the map: [`00-summary-the-map.md`](00-summary-the-map.md) · → next:
> [`02-auth-tenants-and-flows.md`](02-auth-tenants-and-flows.md) · related:
> [`07-admin-portal-and-reporting.md`](07-admin-portal-and-reporting.md) ·
> [`09-methodology-and-oracles.md`](09-methodology-and-oracles.md)

Citations are `[source: findings-log/<file> §n]`. Inside tables the bare filename
is the same file: `PROBE-FINDINGS` = `findings-log/probe-2026-10-08/PROBE-FINDINGS.md`,
`RECON-SUBDOMAINS` = `findings-log/probe-2026-10-08/recon/RECON-SUBDOMAINS.md`,
`ARCHIVE-URLS` = `findings-log/probe-2026-10-08/recon/ARCHIVE-URLS.md`,
`PASSIVE-INFRA` = `findings-log/medtronic-carelink-2026-07-21/07-passive-infrastructure.md`.

---

## 1. Three patient deployments — and no fourth

| Deployment | Patient host | Cumulus host | Auth tenant | Country default |
|---|---|---|---|---|
| EU / OUS | `carelink.minimed.eu` | `clcloud.minimed.eu` | `carelink-login.minimed.eu` | `GB` |
| US | `carelink.minimed.com` | `clcloud.minimed.com` | `carelink-login.minimed.com` | `US` |
| Trials / clinical | `carelink-trials.minimed.com` | `clcloud-trials.minimed.com` | `carelink-login-trials.minimed.com` | `US` |

**OBSERVED.** Each host sends a given country to **its own** `clcloud` sibling —
`.eu → .eu`, `.com → .com`, symmetric, no anomaly. `GB` is `region: OUS` (Outside
US), not `EU` [source: findings-log/probe-2026-10-08/PROBE-FINDINGS.md §4,
CROSS-REGION-CONFIG-FINDINGS.md]. `CP[]` order in the discovery document is
`US, EU, CLINICAL` [source: PROBE-FINDINGS §3].

**No fourth patient deployment exists.** Every recorded `*trials*` host — 16 of
them across every name list on disk — is a `.com` host; there is no
`.eu` counterpart to `carelink-trials`. That answer was obtained from recorded
evidence with zero DNS and zero requests [source: recon/CONFIG-NAMESPACE-DEEP.md
TARGET 5]. The summary page records the same negative.

## 2. The shadow deployment (`.medtronic.eu` / `.medtronic.com`)

A parallel deployment that no tooling in this project knew about: `carelink.`,
`carelink-login.`, `carelink-support.`, `clcloud.`, `commoncore.` all exist on
`medtronic.eu`, and `carelink.medtronic.com` / `carelink-login.medtronic.com` /
`clcloud.medtronic.com` were found on `medtronic.com` by subfinder
[source: findings-log/probe-2026-10-08/SECURITY-FINDINGS.md;
recon/RECON-SUBDOMAINS.md §4]. The `minimed` discovery document never references
them [source: SECURITY-FINDINGS].

The two shadow Auth0 tenants are compared against the patient ones in
[`02-auth-tenants-and-flows.md`](02-auth-tenants-and-flows.md); the CT-log method that
surfaced these names is finding F5 in
[`08-security-findings.md`](08-security-findings.md).

| Shadow host | What it is | Class |
|---|---|---|
| `carelink-login.medtronic.eu` | live OIDC document, 2753 B — **third Auth tenant** | OBSERVED |
| `carelink-login.medtronic.com` | live OIDC document, size not recorded in any source — **fourth Auth tenant** | OBSERVED |
| `clcloud.medtronic.com` | cumulus host, **gateway-gated** — 403 on the discovery path, unlike `clcloud.minimed.*` | OBSERVED |
| `carelink.medtronic.com` | **byte-identical** copy of the clinician portal bundle (sha256 `2a7fa8e7af519c2b` on both hosts) | OBSERVED |
| `carelink-support.medtronic.eu` | serves a **different** build of the portal — `main.759cddab23085086.js` (support/`cua`), not the clinic one | OBSERVED |
| `carelink-support.medtronic.com` | serves the **same different build** as `carelink-support.medtronic.eu` — it does **not** serve "the same document" as `carelinkhp`. **Corrected 2026-10-12** | OBSERVED |
| `carelink.medtronic.eu` | **does** serve the clinic bundle — byte-identical to `carelinkhp.minimed.eu`. **Corrected 2026-10-12; the "false positive" verdict below was wrong** | OBSERVED |
| `commoncore.medtronic.{eu,com}` | the reports backend (`/reports-broker`, `/reports-metadata`) | OBSERVED |

> ⚠ **Correction carried forward from the summary page:**
> `carelink.medtronic.com` is a second copy of the portal bundle.
> [source: docs/00-summary-the-map.md; recon/CONFIG-NAMESPACE-DEEP.md TARGET 5].

> ⚠ **CORRECTION — 2026-10-12 (area A), reversing the line above.** This page
> previously read: *"`carelink.medtronic.eu` is **not** — it is a false positive on any
> status-based check, because it answers 200 with the trap page. Do not treat the
> `.medtronic.eu` shadow as a second portal deployment."*
> **That verdict was wrong, and the md5 it rested on was right.** `carelink.medtronic.eu`
> serves an entry document byte-identical to `carelinkhp.minimed.eu`'s — md5
> `6aedf6c4004fbb29a298bc62128480be`, sha256 `0f2c5f6257a6fc6a…`, the value this repo
> has recorded since 2026-10-08 — and when asked for the chunk **its own document names**
> it returned `main.fb5f8cb7eb60c4d5.js` at **3,397,615 B, sha256
> `2a7fa8e7af519c2b`**: byte-identical to both other clinic-bundle hosts. **It is a
> portal deployment.** The host was called a false positive because only the *document*
> was ever measured, and on this family the document **is** the catch-all, so it cannot
> answer the question. The discriminator that works is an **asset path**
> (`Content-Type` + size + digest), not a document path
> [source: findings-log/2026-10-12-area-a-clinic-portal-region/FINDINGS.md §1;
> §Methodology correction]. That host also serves its fallback **gzipped** (2125 B on the wire for a 5518 B
> body), so a byte-size discriminator must be applied after decompression
> [source: recon/CONFIG-NAMESPACE-DEEP.md].

`clcloud.medtronic.com` behaving differently from `clcloud.medtronic.eu` is
recorded and **not diagnosed** [source: RECON-SUBDOMAINS §4.3].

## 3. Host families — what each one actually is

| Family | What it is | Class / source |
|---|---|---|
| `carelink.minimed.{eu,com}` | the patient host. `/patient/*` metadata + data, `/api/carepartner/v2/*`, all public config namespaces, and it fronts `/configs/v1/*.json` | OBSERVED — PROBE-FINDINGS §5, deep §4 |
| `clcloud.minimed.{eu,com}` | cumulus data/compute plane | OBSERVED — PROBE-FINDINGS §5 |
| `carelink-login.minimed.{eu,com}` | Auth0 login hosts; live OIDC + JWKS | OBSERVED — PROBE-FINDINGS §4 |
| `carelinkhp*.minimed.eu` | Angular **clinician portal** SPA. Returns HTML for every path; not an API. `carelinkhp.minimed.com` is NXDOMAIN — the bundle and its `hcp/*` surface are in [`07-admin-portal-and-reporting.md`](07-admin-portal-and-reporting.md) | OBSERVED — PROBE-FINDINGS §1, deep §6 |
| `commoncore.minimed.{eu,com}` | **502 on every path** — backend not serving. A *different* host from `commoncore.medtronic.*` | OBSERVED — PROBE-FINDINGS §1, deep §6 |
| `clcloudsnp*.minimed.{eu,com}` | **static-resource server** (Spring-style); 500 `No static resource …` | OBSERVED — PROBE-FINDINGS §1, deep §6 |
| `carelink-support*.minimed.{eu,com}` | 404 on the discovery path — not the patient API. Serves the CSR CRM at `/crm` (403) | OBSERVED — PROBE-FINDINGS §1; CROSS-REGION-CONFIG-FINDINGS |
| `carelink-content.medtronic.com` | S3 content bucket, version-directory-structured (`/carepartner/3-6-0/…`). 403 AccessDenied on the config JSONs | OBSERVED — PROBE-FINDINGS deep §4 |
| `status.minimed.com` | the advertised system-status page; `/__geo` → 200 `{"country":"GB"}` | OBSERVED — PROBE-FINDINGS §7 |
| `www.minimed.com` | marketing; carries an archived `/api/header-asset` | OBSERVED — ARCHIVE-URLS §2a |
| `carelink-subject.minimed.com` | 301 → `carelink-trials.minimed.com` — a marketing alias, not an API | OBSERVED — PROBE-FINDINGS deep §7 |
| `mypump.medtronic.com` | real host, 404 `text/html` (no root route) | OBSERVED — RECON-SUBDOMAINS §4.4 |
| *Minimed Outcomes* — `usminimedoutcomes`, `ousminimedoutcomes`, `minimedoutcomes-usapi` `.medtronic.com` | resolves, but every address is Medtronic-internal `144.15.x.x` → `http=000` from the public net. Logged, not probed | OBSERVED — RECON-SUBDOMAINS §4.4 |
| `mdtlogin.medtronic.com`, `mdtlogin-ocl.medtronic.com`, `mdts-ocl.medtronic.com` | the legacy Layer7 ("mag") auth edge and its resource server — see [page 2](02-auth-tenants-and-flows.md) | OBSERVED — AUTH-TENANT-FINDINGS §6; ARCHIVE-URLS §2c |
| `carelinkhp-test.minimed.eu` | the HCP portal's **test** deployment, build `3.2.339` vs prod `3.1.326` | PUBLISHED (archived) — ARCHIVE-URLS §2d |
| `carelink-connect.minimed.eu` | **RETIRED** — NXDOMAIN with a stale SOA serial. Some 2024–2025 third-party write-ups still mention it | OBSERVED (2026-07-21) — PASSIVE-INFRA |

## 4. Namespace → host map

Route-by-route detail for the patient namespaces is in
[`06-patient-api-surface.md`](06-patient-api-surface.md); the clinician portal's
`hcp/*` surface is in
[`07-admin-portal-and-reporting.md`](07-admin-portal-and-reporting.md).

| Host family | Namespaces it serves |
|---|---|
| `carelink.minimed.{eu,com}` | `/patient/*` (metadata + data) · `/api/carepartner/v2/*` · `/patient/v2/configuration/public` · `/patient/v2/users/me` (401) · `/patient/v2/monitor/data` (405) · `/patient/configuration/system/<flat.key>` · `/patient/configuration/defaultCountry` · `/patient/configuration/recaptcha/key` · `/configs/v1/*.json` |
| `clcloud.minimed.{eu,com}`, `clcloud-trials.minimed.com` | `/connect/carepartner/v{6,10,11,12,13}/*` · `/connect/pde/*` · `/connect/csr/v2/*` · `/connect/v2/*` · `/connect/retina/v1/*` · `/patient/connect/data` · `/patient/m2m/connect/data/gc/patients/{username}` |
| `carelink-login.*` | `/authorize` · `/oauth/token` · `/oauth/revoke` (POST-only) · `/userinfo` · `/oidc/logout` · `/.well-known/openid-configuration` · `/.well-known/jwks.json` |
| `commoncore.medtronic.{eu,com}` | `/reports-broker/v1/ocl/*` · `/reports-metadata/v1/ocl/*` (403 unauthenticated on every route probed) |
| `clcloudsnp.*` | static resources only (500) |
| `carelinkhp.minimed.eu` | `/hcp/*` (29 `hcp/user/*`, 40 `hcp/clinics/*`, …) · `/connect/retina/*` |
| `carelink-support.*` | `/crm` (403) |
| `carelink-content.medtronic.com` | `/carepartner/<version>/…` (403 AccessDenied) |
| `www.minimed.com` | `/api/header-asset` |

Two live data endpoints have a **second** live host: `/patient/connect/data` and
`/patient/m2m/connect/data/gc/patients/{username}` answer 401 on **both**
`carelink.*` and `clcloud.*`; every other `/patient/*` path probed is 403 on
`clcloud` (gateway-level, no route) [source: APP-EMULATION-RESEARCH §2;
recon/CONFIG-NAMESPACE-DEEP.md TARGET 1].

## 5. DNS, CDN, PKI estate

- Every public CareLink consumer host fronts **AWS CloudFront**; the apex zone is
  delegated to Medtronic's own `ns2-ns5.medtronic.com`, so DNS changes go through
  Medtronic, not CloudFront [source: PASSIVE-INFRA].
- Edge observed as **LHR95-P3** (London) [source: PROBE-FINDINGS deep §7].
- Issuer is **DigiCert Global G2 TLS RSA SHA256 2020 CA1** for the whole prod
  estate; renewal cadence is ~6 months for `carelink-*`/`clcloud-*`, annual for
  `carelink-login-*` [source: PROBE-FINDINGS §2; PASSIVE-INFRA].
- All live prod hosts negotiate **TLS 1.3** with key exchange **`X25519MLKEM768`**
  (post-quantum hybrid KEM); TLS 1.0/1.1 are rejected [source: PROBE-FINDINGS §2;
  SECURITY-FINDINGS].
- **Mass cert rotation happened 2026-10-08** (nbf that day) for `clcloud.{eu,com}`,
  `carelink.{eu,com}`, `clcloudsnp.{eu,com}`, `carelink-trials-support`
  [source: PROBE-FINDINGS §2].
- **Renewal watch:** `clcloud-trials.minimed.com` expires **2026-10-28**;
  `status.minimed.com` expires 2026-12-02 [source: PROBE-FINDINGS §2].
- **INFERRED** — single-CDN and single-CA blast radius: one CloudFront or DigiCert
  event affects every consumer host at once [source: PASSIVE-INFRA].
- CNAME TTLs are 1800 s (apex) / 3386 s (`clcloud.minimed.eu`), so a resolver can
  pin a stale IP for up to ~56 minutes during a region incident
  [source: PASSIVE-INFRA].

## 6. Not publicly reachable — enumerated, deliberately not probed

- **NXDOMAIN, cert-only names:** `carelinkhp.minimed.com`,
  `carelinkhp-prod.minimed.com`, `clcloud-clinical.minimed.com`
  [source: PROBE-FINDINGS §1].
  **Re-confirmed NXDOMAIN 2026-10-12 (area A), and extended:** the resolver returns
  `NXDOMAIN` — not a timeout, not an empty NOERROR — for `carelinkhp.minimed.com`,
  `carelinkhp-prod.minimed.com`, `carelinkhp-trials.minimed.com` and
  `carelinkhp-prod.minimed.eu`. The last is the only `carelinkhp*` name the corpus
  named without ever probing; `carelinkhp-trials.minimed.com`'s recorded
  `000 / TCP connect failed` improves on this — there was never an address to connect
  to. **`carelinkhp` is therefore a single-deployment name**: no `.com` variant exists
  [source: findings-log/2026-10-12-area-a-clinic-portal-region/FINDINGS.md §What was
  searched and found empty; `dns.jsonl`].
- **Medtronic-internal IPs that hang on TLS:** `carelink-prod.minimed.com`
  (144.15.206.166), `carelink-clinical.minimed.com` (144.15.206.180),
  `carelink-support-prod` (.165), `origin.carelink.minimed.eu` and
  `www.minimed.eu` (144.15.107.20) — the real origins behind CloudFront
  [source: PROBE-FINDINGS deep §7].
- **Internal infrastructure names** resolved from CT logs and recorded, never
  touched: `grafana.*`, `k8s.*`, `gitlab.*`, `prometheus.*`, `db.*` and similar
  under `<internal>.minimed.{com,eu}` [source: SECURITY-FINDINGS S5;
  RECON-SUBDOMAINS §4.5]. Zero of 260 focus names resolved to an RFC1918 or CGNAT
  address [source: RECON-SUBDOMAINS §8].
- Everything else in the CT logs is dev/stage/test/uat/qa/loadlab — enumerated
  passively only, never probed [source: PROBE-FINDINGS §1, deep §7].

## 7. Traps — read before reporting any host

Each trap is restated with its fix in
[`09-methodology-and-oracles.md`](09-methodology-and-oracles.md).

### ⚠ `*.carelink.eu`, `*.carelink.com` and `*.clcloud.eu` are parked-domain wildcards

**This is the single most important line on this page.** `carelink.eu` is
wildcard DNS on a domain-parking operator (`ns1.abovedomains.com` /
`ns2.abovedomains.com`). *Every* name under it resolves — including randomly
generated, certainly-unregistered strings — and all of them **302 to the same
parking page** `https://ww38.carelink.eu/`.

The proof is a name that cannot exist:

```
zqxjkvwmpn987notarehost.carelink.eu   -> 103.224.182.253   (resolves)
zq7x-nonexistent-test-9137.carelink.eu -> 103.224.182.253  (resolves)
admin.carelink.eu                    -> 103.224.182.253 -> 302 https://ww38.carelink.eu/
```

`carelink.eu` carries a Let's Encrypt wildcard cert whose SANs include
`*.carelink.eu`, `*.medtronic.carelink.eu`, `*.minimed.carelink.eu` and several
**typosquats** (`medtrinic`, `medtronice`, `medtornic`, `cmedtronic`, …), reissued
on a ~90-day machine cadence. That cert is what injects the names into every
CT-log scraper. **All 49 names collected under `carelink.eu` / `carelink.com` /
`clcloud.eu` are false positives.** `clcloud.eu` is separately parked
(`ns1.dns-parking.com`) and is an unrelated Dutch company (`lamafurnish`,
`nextcloud`, `odoo`, …). Medtronic's cumulus host is `clcloud.minimed.{eu,com}`,
never `clcloud.eu`.

Reporting `superset.carelink.eu` as a Medtronic dashboard, or
`admin.carelink.eu` as an admin panel, would be a **demonstrably false positive
against a named vendor**. Treat the whole `*.carelink.{eu,com}` and `*.clcloud.eu`
space as unusable for attribution. This is also rule 4 of the README and a trap
row in the summary page — repeated here because a reader on *this* page must not
miss it.
[source: findings-log/probe-2026-10-08/PROBE-FINDINGS.md deep §8;
AUTH-TENANT-FINDINGS.md §8; recon/RECON-SUBDOMAINS.md §3, §5]

### The 200-for-everything portal trap

`carelinkhp.minimed.eu` returns **HTTP 200 `text/html` with a 5518-byte body for
every path that does not exist** — including fabricated chunk names such as
`<id>.deadbeefdeadbeef.js` and `99999999.ffffffffffffffff.js.map`. Discriminate
on **`Content-Type`**, never on status code. `carelink.medtronic.com`,
`carelink-support.medtronic.com` and `carelink.medtronic.eu` return the same
document (the `.eu` one gzipped, ~2125 B on the wire). This trap caused three
near-misses in one session and nearly stored 225 copies of `index.html` during
the chunk sweep.
[source: findings-log/probe-2026-10-08/CHUNK-CORPUS-FINDINGS.md;
recon/JSMAP-HUNT.md §2; recon/CONFIG-NAMESPACE-DEEP.md TARGET 5; README rule 5]

> ⚠ **Correction — 2026-10-12 (area A): the discriminator above is wrong for document
> paths, and the wrongness produced a refuted claim.** Two measurements, both
> byte-level:
>
> 1. **The catch-all *is* the entry document.** On all five responding hosts the body
>    for a fabricated path and the body for `/` are the **same bytes**. So a
>    document-path probe cannot distinguish "real portal" from "fallback", and
>    `Content-Type` cannot rescue it — both are `text/html`.
> 2. **5518 B is not one document.** The size maps to **at least two digests**:
>    `0f2c5f6257a6fc6a…` (clinic hosts) and `f637c8d0cd4ec6bc…`
>    (`carelink-support.medtronic.{eu,com}`, a different build).
>
> **The fix that works: ask for a content-hashed chunk the host's own document names,
> and discriminate on `Content-Type` + size + digest together.** Measured both ways on
> one host: its own build's chunk → `application/javascript`, 3,397,615 B; the other
> build's chunk name → `text/html`, 5518 B. Naming a chunk in HTML is not serving it.
> [source: findings-log/2026-10-12-area-a-clinic-portal-region/FINDINGS.md §Methodology
> correction; `results.jsonl` seq 1≡3, 5≡7, 9≡11, 13≡14, 16≡17, 3 vs 11, 18 vs 19]

### Other traps

| Trap | Detail | Source |
|---|---|---|
| **Unconditional gzip** | `carelink.minimed.eu` serves `Content-Encoding: gzip` ignoring `Accept-Encoding` entirely (verified against `identity`, `gzip`, `deflate`) — an RFC 9110 §8.4 violation. Use `curl --compressed`. A plain `curl -o` writes raw gzip and every later parse fails | README rule 6; PUBLIC-CONFIG-FINDINGS |
| **403 is byte-identical everywhere** | a fabricated path, a random UUID and a dead version all return the same 403 `{"message":"Missing Authentication Token"}`. **Latency is not an oracle** either: the host dominates, not the version | recon/VERSION-AXIS.md §1 |
| **404 content-type oddity** | the per-key config namespace's 404 carries `content-type: text/vnd.a` — do not discriminate on it | recon/CONFIG-NAMESPACE-DEEP.md |
| **Raw archive captures** | Common Crawl/Wayback contain live `jsessionid_*` values in URL paths and pre-Auth0 authorize URLs whose `sessionData` is a plaintext-base64 JWS. Facts only — never copy the captures | README rule 3; ARCHIVE-URLS §7 |
| **Published credentials** | Two vendor `x-api-key` values and one reCAPTCHA site key are known to be published. Record *that* they are exposed and *where*, never the values | README rule 1; CROSS-REGION-CONFIG-FINDINGS |

## 8. What we still do not know

The consolidated list, with what would settle each, is in
[`10-open-questions.md`](10-open-questions.md).

| Question | Status |
|---|---|
| Why `clcloud.medtronic.com` gateway-gates discovery while `clcloud.medtronic.eu` does not | **Unknown** — not in any source; recorded, not diagnosed [source: RECON-SUBDOMAINS §4.3] |
| Whether any `dev`/`stage` host behaves differently from prod | **Unknown** — deliberately never probed |
| The true origins behind CloudFront (`144.15.x.x`) | **Unknown** — refusal to handshake, left alone |
| Report bodies from `commoncore` | blocked on a token; **never archived in any crawl** — the largest unarchived surface in the project |
