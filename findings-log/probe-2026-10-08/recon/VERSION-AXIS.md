# CareLink `carepartner` version axis — live/dead oracle test (2026-10-10)

**Question.** Which `carepartner` API versions are actually live on the
`clcloud.*` host family, and can an unauthenticated probe tell a live version
from a dead one?

**Method.** 70 HTTP requests — hard cap reached, 0 remaining. GET plus OPTIONS
only. Unauthenticated: no `Authorization`, no `Cookie`, no `x-api-key`, no POST,
no credential of any kind was used or written to disk. ≥2 s enforced between
requests to the same host (`last_hit[]` map in `vaxis-probe.sh`).
Hosts touched: `clcloud.minimed.eu`, `clcloud.minimed.com`,
`clcloud-trials.minimed.com`. No dev/stage/QA host was contacted.

Phase order was deliberate: **the fabricated-path controls ran first**, before
any version-sweep cell, so the oracle verdict is not contaminated by the data
it is used to judge.

Raw evidence: `vaxis.jsonl` (one line per request, with latency and header
signature), `vaxisbodies/*.{hdr,body}` (every response header and body).

---

## 1. The oracle — the caveat was half right, and the answer is *yes*

The earlier pass was correct that **status code alone carries no signal**, and
that finding reproduces exactly:

| control path | status | body |
|---|---|---|
| `/connect/carepartner/v13/be-periodic-data` (plausible, fabricated) | 403 | `{"message":"Missing Authentication Token"}` |
| `/connect/carepartner/v13/3f8a1c2e-…-1d2e3f4a5b6c` (random UUID) | 403 | identical |

…and both of those also come back 403 on `.com` and on `-trials`, and the live
`v13/display/message` returns 401 while the vendor-advertised
`v6/display/message` returns 403. So **403 ≠ dead and 401 ≠ live can be read
straight off the status line.** Anyone probing this family on status alone will
conclude nothing.

**But the response headers are a perfect, unambiguous oracle**, because this
host family is AWS API Gateway fronted by CloudFront. Every response carries an
`x-amzn-errortype` header, and Amazon uses *different* error types for "the
router found no route" versus "the request reached a backend authorizer":

| `x-amzn-errortype` | AWS meaning | Status here | Bytes | `x-cache` | CORS headers | Verdict |
|---|---|---|---|---|---|---|
| `MissingAuthenticationTokenException` | **no matching route in API Gateway** | 403 | 42 | `Error from cloudfront` | **absent** | **dead — path does not exist** |
| `UnauthorizedException` (+ `x-ca-err: 990`) | request **reached a backend authorizer**, denied for lack of a token | 401 | 36 | `Error from cloudfront` | absent | **live — route exists, token-gated** |
| *(none)* | — | 200/204 | 0+ | `Miss from cloudfront` | present on OPTIONS | **fully public, unauthenticated** |

The controls fire on every axis:

- All 7 fabricated controls (3 hosts × 2 paths on GET, plus `v13/be-periodic-data`
  on OPTIONS) → `MissingAuthenticationTokenException`, no CORS headers. **Zero
  false negatives.**
- All 13 `UnauthorizedException` responses are on `v11`/`v12`/`v13` of
  `display/message` and `discover`. **Zero false positives.**
- Cross-checks: the 6 responses that returned a body (200) all carry a
  previously-unrecorded **`x-cum-signature`** header — a distinct base64 value
  per document (6 distinct values across 6 docs), i.e. a per-document integrity
  signature. Every 403/401 lacks it.

**Two further header signals, ranked:**

1. **`access-control-allow-origin: *` + `access-control-allow-methods: OPTIONS`
   on an OPTIONS request is the cleanest liveness test for a resource that has
   no GET method.** `OPTIONS /connect/carepartner/v6/display/message` → 200,
   CORS present. `OPTIONS …/v99/display/message` → 403 no CORS.
   `OPTIONS /connect/carepartner/v13/3f8a1c2e-…` (UUID) → 403 no CORS.
   `OPTIONS /connect/carepartner/v13/be-periodic-data` (plausible) → 403 no CORS.
2. `x-cache: Miss from cloudfront` vs `Error from cloudfront` tracks the same
   split (9 Miss / 61 Error), but it is a weaker, derived signal — keep
   `x-amzn-errortype` as the authority.

### ⚠️ The oracle needs *both* methods, or it under-reports liveness

`/connect/carepartner/v6/display/message` — the exact URL the vendor's own
country-settings config hands out as `blePereodicDataEndpoint` — returns
**403 `MissingAuthenticationTokenException` on GET** yet **200 with CORS headers
on OPTIONS**. The resource exists in API Gateway; the **GET method is not
defined on it**. It is POST-only. This matches `work/METHOD-FACTS.md`'s
"POST → 401 `Authentication failure`" and is now proven independently from the
OPTIONS axis rather than inferred.

So the oracle in full: **GET 403 + OPTIONS 403 → dead. GET 403 + OPTIONS 200 →
live but POST-only. GET 401 → live with GET. GET 200/204 → public.**

**Correction to `METHOD-FACTS.md`.** Its table records "Unauth GET = 403 (HTML,
gateway)" for `clcloud.*/connect/carepartner/{v6,v11,v13}/display/message`.
Direct GET on all three hosts returns **401, not 403, for v11 and v13**; only v6
is 403. The 403 row is almost certainly the `curl -d`/forced-POST artifact that
file itself warns about two paragraphs earlier. The file's actual conclusion —
the bridge POSTs, and that is correct (`src/carelink/client.ts:272`) — is
unaffected.

**Latency is not an oracle.** Mean `t_total` by host: `.eu` 0.149 s (n=49),
`.com` 0.684 s (n=10), `-trials` 1.246 s (n=11). The host, not the version,
dominates. The four slowest cells (~4.6–5.9 s) were the unusual ones, but
`v11/discover` on `.eu` took 0.15 s, so it is not a per-version property either.

---

## 2. Every cell probed — 70 of 70

`x-cum-signature` marks responses carrying a signed discovery document.
Errortype abbreviated: `MissingAuthToken` = `MissingAuthenticationTokenException`.

66 of the 70 requests carry a body head of exactly one of two strings —
`{"message":"Missing Authentication Token"}` (43 × 403) or
`{"message":"Authentication failure"}` (13 × 401) — so the body head is
deliberately collapsed in the table to keep it readable. The verbatim bodies are
in `vaxisbodies/`.

| # | namespace | host | ver | method | path | status | content-type | bytes | errortype | x-cache | CORS | t | body head |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | connect/carepartner | clcloud.minimed.eu | v13 | GET | `connect/carepartner/v13/be-periodic-data` | **403** | application/json | 42 | MissingAuthToken | Error | - | 0.07s | {message:Missing Authentication Token} |
| 2 | connect/carepartner | clcloud.minimed.eu | v13 | GET | `connect/carepartner/v13/3f8a1c2e-9b7d-4e5a-8c6b-1d2e3f4a5b6c` | **403** | application/json | 42 | MissingAuthToken | Error | - | 0.07s | {message:Missing Authentication Token} |
| 3 | connect/carepartner | clcloud.minimed.eu | v13 | GET | `connect/carepartner/v13/display/message` | **401** | application/json | 36 | Unauthorized | Error | - | 0.04s | {message:Authentication failure} |
| 4 | connect/carepartner | clcloud.minimed.eu | v6 | GET | `connect/carepartner/v6/display/message` | **403** | application/json | 42 | MissingAuthToken | Error | - | 0.05s | {message:Missing Authentication Token} |
| 5 | connect/carepartner | clcloud.minimed.com | v13 | GET | `connect/carepartner/v13/be-periodic-data` | **403** | application/json | 42 | MissingAuthToken | Error | - | 0.27s | {message:Missing Authentication Token} |
| 6 | connect/carepartner | clcloud.minimed.com | v13 | GET | `connect/carepartner/v13/3f8a1c2e-9b7d-4e5a-8c6b-1d2e3f4a5b6c` | **403** | application/json | 42 | MissingAuthToken | Error | - | 0.26s | {message:Missing Authentication Token} |
| 7 | connect/carepartner | clcloud.minimed.com | v13 | GET | `connect/carepartner/v13/display/message` | **401** | application/json | 36 | Unauthorized | Error | - | 0.11s | {message:Authentication failure} |
| 8 | connect/carepartner | clcloud.minimed.com | v6 | GET | `connect/carepartner/v6/display/message` | **403** | application/json | 42 | MissingAuthToken | Error | - | 0.26s | {message:Missing Authentication Token} |
| 9 | connect/carepartner | clcloud-trials.minimed.com | v13 | GET | `connect/carepartner/v13/be-periodic-data` | **403** | application/json | 42 | MissingAuthToken | Error | - | 0.38s | {message:Missing Authentication Token} |
| 10 | connect/carepartner | clcloud-trials.minimed.com | v13 | GET | `connect/carepartner/v13/3f8a1c2e-9b7d-4e5a-8c6b-1d2e3f4a5b6c` | **403** | application/json | 42 | MissingAuthToken | Error | - | 0.27s | {message:Missing Authentication Token} |
| 11 | connect/carepartner | clcloud-trials.minimed.com | v13 | GET | `connect/carepartner/v13/display/message` | **401** | application/json | 36 | Unauthorized | Error | - | 0.27s | {message:Authentication failure} |
| 12 | connect/carepartner | clcloud-trials.minimed.com | v6 | GET | `connect/carepartner/v6/display/message` | **403** | application/json | 42 | MissingAuthToken | Error | - | 0.26s | {message:Missing Authentication Token} |
| 13 | connect/carepartner | clcloud.minimed.eu | v13 | OPTIONS | `connect/carepartner/v13/display/message` | **200** | application/json | 0 | - | Miss | yes | 0.07s |  |
| 14 | connect/carepartner | clcloud.minimed.eu | v6 | OPTIONS | `connect/carepartner/v6/display/message` | **200** | application/json | 0 | - | Miss | yes | 0.04s |  |
| 15 | connect/carepartner | clcloud.minimed.eu | v99 | OPTIONS | `connect/carepartner/v99/display/message` | **403** | application/json | 42 | MissingAuthToken | Error | - | 0.04s | {message:Missing Authentication Token} |
| 16 | connect/carepartner | clcloud.minimed.eu | v13 | OPTIONS | `connect/carepartner/v13/discover/android/3.6` | **401** | application/json | 36 | Unauthorized | Error | - | 0.04s | {message:Authentication failure} |
| 17 | connect/carepartner | clcloud.minimed.eu | v99 | OPTIONS | `connect/carepartner/v99/discover/android/3.6` | **403** | application/json | 42 | MissingAuthToken | Error | - | 0.07s | {message:Missing Authentication Token} |
| 18 | connect/carepartner | clcloud.minimed.eu | v13 | OPTIONS | `connect/carepartner/v13/3f8a1c2e-9b7d-4e5a-8c6b-1d2e3f4a5b6c` | **403** | application/json | 42 | MissingAuthToken | Error | - | 0.04s | {message:Missing Authentication Token} |
| 19 | connect/carepartner | clcloud.minimed.eu | v1 | GET | `connect/carepartner/v1/discover/android/3.6` | **403** | application/json | 42 | MissingAuthToken | Error | - | 0.05s | {message:Missing Authentication Token} |
| 20 | connect/carepartner | clcloud.minimed.eu | v2 | GET | `connect/carepartner/v2/discover/android/3.6` | **403** | application/json | 42 | MissingAuthToken | Error | - | 0.04s | {message:Missing Authentication Token} |
| 21 | connect/carepartner | clcloud.minimed.eu | v3 | GET | `connect/carepartner/v3/discover/android/3.6` | **403** | application/json | 42 | MissingAuthToken | Error | - | 0.07s | {message:Missing Authentication Token} |
| 22 | connect/carepartner | clcloud.minimed.eu | v4 | GET | `connect/carepartner/v4/discover/android/3.6` | **403** | application/json | 42 | MissingAuthToken | Error | - | 0.07s | {message:Missing Authentication Token} |
| 23 | connect/carepartner | clcloud.minimed.eu | v5 | GET | `connect/carepartner/v5/discover/android/3.6` | **403** | application/json | 42 | MissingAuthToken | Error | - | 0.04s | {message:Missing Authentication Token} |
| 24 | connect/carepartner | clcloud.minimed.eu | v6 | GET | `connect/carepartner/v6/discover/android/3.6` | **403** | application/json | 42 | MissingAuthToken | Error | - | 0.06s | {message:Missing Authentication Token} |
| 25 | connect/carepartner | clcloud.minimed.eu | v7 | GET | `connect/carepartner/v7/discover/android/3.6` | **403** | application/json | 42 | MissingAuthToken | Error | - | 0.08s | {message:Missing Authentication Token} |
| 26 | connect/carepartner | clcloud.minimed.eu | v8 | GET | `connect/carepartner/v8/discover/android/3.6` | **403** | application/json | 42 | MissingAuthToken | Error | - | 0.04s | {message:Missing Authentication Token} |
| 27 | connect/carepartner | clcloud.minimed.eu | v9 | GET | `connect/carepartner/v9/discover/android/3.6` | **403** | application/json | 42 | MissingAuthToken | Error | - | 0.04s | {message:Missing Authentication Token} |
| 28 | connect/carepartner | clcloud.minimed.eu | v10 | GET | `connect/carepartner/v10/discover/android/3.6` | **204** | none | 0 | - | Miss | - | 4.56s |  |
| 29 | connect/carepartner | clcloud.minimed.eu | v11 | GET | `connect/carepartner/v11/discover/android/3.6` | **200** | application/json | 20345 | - | Miss | - | 0.15s | {config:android,3.6,supportedCountries:[{US:{region: **+x-cum-signature** |
| 30 | connect/carepartner | clcloud.minimed.eu | v12 | GET | `connect/carepartner/v12/discover/android/3.6` | **401** | application/json | 36 | Unauthorized | Error | - | 0.04s | {message:Authentication failure} |
| 31 | connect/carepartner | clcloud.minimed.eu | v13 | GET | `connect/carepartner/v13/discover/android/3.6` | **200** | application/json | 20256 | - | Miss | - | 0.10s | {config:android,3.6,supportedCountries:[{US:{region: **+x-cum-signature** |
| 32 | connect/carepartner | clcloud.minimed.eu | v14 | GET | `connect/carepartner/v14/discover/android/3.6` | **403** | application/json | 42 | MissingAuthToken | Error | - | 0.05s | {message:Missing Authentication Token} |
| 33 | connect/carepartner | clcloud.minimed.eu | v15 | GET | `connect/carepartner/v15/discover/android/3.6` | **403** | application/json | 42 | MissingAuthToken | Error | - | 0.07s | {message:Missing Authentication Token} |
| 34 | connect/carepartner | clcloud.minimed.eu | v16 | GET | `connect/carepartner/v16/discover/android/3.6` | **403** | application/json | 42 | MissingAuthToken | Error | - | 0.04s | {message:Missing Authentication Token} |
| 35 | connect/carepartner | clcloud.minimed.com | v6 | GET | `connect/carepartner/v6/discover/android/3.6` | **403** | application/json | 42 | MissingAuthToken | Error | - | 0.26s | {message:Missing Authentication Token} |
| 36 | connect/carepartner | clcloud-trials.minimed.com | v6 | GET | `connect/carepartner/v6/discover/android/3.6` | **200** | application/json | 10053 | - | Miss | - | 4.99s | {config:android,3.6,supportedCountries:[{US:{region: **+x-cum-signature** |
| 37 | connect/carepartner | clcloud.minimed.com | v11 | GET | `connect/carepartner/v11/discover/android/3.6` | **200** | application/json | 18105 | - | Miss | - | 4.76s | {config:android,3.6,supportedCountries:[{US:{region: **+x-cum-signature** |
| 38 | connect/carepartner | clcloud-trials.minimed.com | v11 | GET | `connect/carepartner/v11/discover/android/3.6` | **200** | application/json | 20345 | - | Miss | - | 5.91s | {config:android,3.6,supportedCountries:[{US:{region: **+x-cum-signature** |
| 39 | connect/carepartner | clcloud.minimed.com | v12 | GET | `connect/carepartner/v12/discover/android/3.6` | **401** | application/json | 36 | Unauthorized | Error | - | 0.26s | {message:Authentication failure} |
| 40 | connect/carepartner | clcloud-trials.minimed.com | v12 | GET | `connect/carepartner/v12/discover/android/3.6` | **401** | application/json | 36 | Unauthorized | Error | - | 0.27s | {message:Authentication failure} |
| 41 | connect/carepartner | clcloud.minimed.eu | v1 | GET | `connect/carepartner/v1/display/message` | **403** | application/json | 42 | MissingAuthToken | Error | - | 0.05s | {message:Missing Authentication Token} |
| 42 | connect/carepartner | clcloud.minimed.eu | v2 | GET | `connect/carepartner/v2/display/message` | **403** | application/json | 42 | MissingAuthToken | Error | - | 0.04s | {message:Missing Authentication Token} |
| 43 | connect/carepartner | clcloud.minimed.eu | v3 | GET | `connect/carepartner/v3/display/message` | **403** | application/json | 42 | MissingAuthToken | Error | - | 0.05s | {message:Missing Authentication Token} |
| 44 | connect/carepartner | clcloud.minimed.eu | v4 | GET | `connect/carepartner/v4/display/message` | **403** | application/json | 42 | MissingAuthToken | Error | - | 0.05s | {message:Missing Authentication Token} |
| 45 | connect/carepartner | clcloud.minimed.eu | v5 | GET | `connect/carepartner/v5/display/message` | **403** | application/json | 42 | MissingAuthToken | Error | - | 0.07s | {message:Missing Authentication Token} |
| 46 | connect/carepartner | clcloud.minimed.eu | v6 | GET | `connect/carepartner/v6/display/message` | **403** | application/json | 42 | MissingAuthToken | Error | - | 0.06s | {message:Missing Authentication Token} |
| 47 | connect/carepartner | clcloud.minimed.eu | v7 | GET | `connect/carepartner/v7/display/message` | **403** | application/json | 42 | MissingAuthToken | Error | - | 0.05s | {message:Missing Authentication Token} |
| 48 | connect/carepartner | clcloud.minimed.eu | v8 | GET | `connect/carepartner/v8/display/message` | **403** | application/json | 42 | MissingAuthToken | Error | - | 0.07s | {message:Missing Authentication Token} |
| 49 | connect/carepartner | clcloud.minimed.eu | v9 | GET | `connect/carepartner/v9/display/message` | **403** | application/json | 42 | MissingAuthToken | Error | - | 0.04s | {message:Missing Authentication Token} |
| 50 | connect/carepartner | clcloud.minimed.eu | v10 | GET | `connect/carepartner/v10/display/message` | **403** | application/json | 42 | MissingAuthToken | Error | - | 0.06s | {message:Missing Authentication Token} |
| 51 | connect/carepartner | clcloud.minimed.eu | v11 | GET | `connect/carepartner/v11/display/message` | **401** | application/json | 36 | Unauthorized | Error | - | 0.07s | {message:Authentication failure} |
| 52 | connect/carepartner | clcloud.minimed.eu | v12 | GET | `connect/carepartner/v12/display/message` | **401** | application/json | 36 | Unauthorized | Error | - | 0.04s | {message:Authentication failure} |
| 53 | connect/carepartner | clcloud.minimed.eu | v13 | GET | `connect/carepartner/v13/display/message` | **401** | application/json | 36 | Unauthorized | Error | - | 0.07s | {message:Authentication failure} |
| 54 | connect/carepartner | clcloud.minimed.eu | v14 | GET | `connect/carepartner/v14/display/message` | **403** | application/json | 42 | MissingAuthToken | Error | - | 0.07s | {message:Missing Authentication Token} |
| 55 | connect/carepartner | clcloud.minimed.eu | v15 | GET | `connect/carepartner/v15/display/message` | **403** | application/json | 42 | MissingAuthToken | Error | - | 0.04s | {message:Missing Authentication Token} |
| 56 | connect/carepartner | clcloud.minimed.eu | v16 | GET | `connect/carepartner/v16/display/message` | **403** | application/json | 42 | MissingAuthToken | Error | - | 0.04s | {message:Missing Authentication Token} |
| 57 | connect/carepartner | clcloud.minimed.com | v6 | GET | `connect/carepartner/v6/display/message` | **403** | application/json | 42 | MissingAuthToken | Error | - | 0.26s | {message:Missing Authentication Token} |
| 58 | connect/carepartner | clcloud-trials.minimed.com | v6 | GET | `connect/carepartner/v6/display/message` | **403** | application/json | 42 | MissingAuthToken | Error | - | 0.26s | {message:Missing Authentication Token} |
| 59 | connect/carepartner | clcloud.minimed.com | v11 | GET | `connect/carepartner/v11/display/message` | **401** | application/json | 36 | Unauthorized | Error | - | 0.27s | {message:Authentication failure} |
| 60 | connect/carepartner | clcloud-trials.minimed.com | v11 | GET | `connect/carepartner/v11/display/message` | **401** | application/json | 36 | Unauthorized | Error | - | 0.26s | {message:Authentication failure} |
| 61 | connect/carepartner | clcloud.minimed.com | v13 | GET | `connect/carepartner/v13/display/message` | **401** | application/json | 36 | Unauthorized | Error | - | 0.10s | {message:Authentication failure} |
| 62 | connect/carepartner | clcloud-trials.minimed.com | v13 | GET | `connect/carepartner/v13/display/message` | **401** | application/json | 36 | Unauthorized | Error | - | 0.27s | {message:Authentication failure} |
| 63 | connect/pde | clcloud.minimed.eu | v3 | GET | `connect/pde/v3/display/message` | **403** | application/json | 42 | MissingAuthToken | Error | - | 0.04s | {message:Missing Authentication Token} |
| 64 | connect/pde | clcloud.minimed.eu | v3 | GET | `connect/pde/v3/discover/android/3.6` | **403** | application/json | 42 | MissingAuthToken | Error | - | 0.07s | {message:Missing Authentication Token} |
| 65 | connect/pde | clcloud.minimed.eu | v1 | GET | `connect/pde/v1/display/message` | **403** | application/json | 42 | MissingAuthToken | Error | - | 0.05s | {message:Missing Authentication Token} |
| 66 | connect/pde | clcloud.minimed.eu | v2 | GET | `connect/pde/v2/display/message` | **403** | application/json | 42 | MissingAuthToken | Error | - | 0.04s | {message:Missing Authentication Token} |
| 67 | connect/csr | clcloud.minimed.eu | v2 | GET | `connect/csr/v2/display/message` | **403** | application/json | 42 | MissingAuthToken | Error | - | 0.04s | {message:Missing Authentication Token} |
| 68 | connect/v2 | clcloud.minimed.eu | v2 | GET | `connect/v2/display/message` | **403** | application/json | 42 | MissingAuthToken | Error | - | 0.07s | {message:Missing Authentication Token} |
| 69 | connect/carepartner | clcloud.minimed.eu | v13 | OPTIONS | `connect/carepartner/v13/be-periodic-data` | **403** | application/json | 42 | MissingAuthToken | Error | - | 0.07s | {"message":"Missing Authentication Token"} |
| 70 | connect/carepartner | clcloud-trials.minimed.com | v6 | GET | `connect/carepartner/v6/discover/android/3.8` | **200** | application/json | 10053 | - | Miss | - | 0.57s | {"config":"android,3.8","supportedCountries":[{"US": **+x-cum-signature** |

---

## 3. The version axis itself

### 3a. `discover` — base-path axis on `clcloud.minimed.eu`, `android/3.6`

| base version | status | oracle verdict | what it is |
|---|---|---|---|
| v1 – v9 | 403 | **no route** | dead |
| v10 | 204 | live, empty | exists, returns nothing |
| v11 | 200 | live, public | **trials-tenant** doc (see 3c) |
| v12 | 401 | live, token-gated | exists — body unreadable unauthenticated |
| v13 | 200 | live, public | **the patient API** doc — what the bridge uses |
| v14 – v16 | 403 | **no route** | dead |

`v13/discover/android/3.6` re-verified byte-identical to the doc already on disk
(`disc-eu.json`, 20256 B, sha `f8488626…`). The `204` on v10 comes back with a
distinctive `x-amzn-trace-id` carrying `Lineage=` and a security header set
(`strict-transport-security`, `x-frame-options: sameorigin`,
`content-security-policy: default-src 'self'`,
`x-permitted-cross-domain-policies: none`) that no other cell carries.

### 3b. `display/message` — version axis on `clcloud.minimed.eu`, GET

| version | GET | OPTIONS | verdict |
|---|---|---|---|
| v1 – v5 | 403 | not probed | **no GET route** |
| **v6** | 403 | **200 + CORS** | **exists, POST-only** — the vendor-advertised BLE endpoint |
| v7 – v10 | 403 | not probed | **no GET route** |
| **v11** | **401** | not probed | live, GET-capable, token-gated |
| **v12** | **401** | not probed | **live, GET-capable, token-gated — NEW** |
| **v13** | **401** | not probed | live, GET-capable, token-gated |
| v14 – v16 | 403 | not probed | **no GET route** |

### 3c. Auth0 + cumulus-v13 matrix

| cell | Auth0 | cumulus | CLINICAL | doc |
|---|---|---|---|---|
| `*/v13/discover/android/3.6` (all 3 hosts) | yes (`carepartner_auth0_{us,ous,cl}_…`) | **v13** | yes | patient doc — what the bridge uses |
| `.eu` + `-trials` `v11/discover/android/3.6` | yes (`…_cl_sso_config_v1.json`, the **clinical** config) | **v13** | yes | trials-tenant doc, Auth0 track |
| `.com` `v11/discover/android/3.6` | **no** | **v2** | **no** | legacy doc — see §4 |
| `-trials` `v6/discover/android/{3.6,3.8}` | **no** | **v2** | **no** | legacy doc — see §4 |
| `*/v12/discover/android/3.6` (all 3 hosts) | ? (401, unreadable) | ? | ? | token-gated — **worth a token** |

**Does any cell give a v13 cumulus base *and* survive a code path?** Two do:
`v13` (all three hosts) and `v11` (`.eu` and `-trials`). Both were already
known. **No new v13 cell exists.** The v6 and the `.com`-v11 cells are both
legacy: `SSOConfiguration` only, `baseUrlCumulus` at `/connect/carepartner/v2`,
`baseUrlPde` at `/connect/pde/v1`, `baseUrlCareLink` at
`/api/carepartner/v1`, no `baseUrlCms`, no `baseUrlAem`, regions `US,EU` only.

---

## 4. Cross-deployment asymmetry — two real findings

### ⚠️ The `v11` discovery document is **host-dependent** — this contradicts a recorded claim

PROBE-FINDINGS §3 states "the hostname does not select the region — the doc is
global and carries all three `CP` entries". That was derived from `v13` only,
and it still holds for v13. **It does not hold for v11:**

| host | `v11/discover/android/3.6` | size | content |
|---|---|---|---|
| `clcloud.minimed.eu` | 200 | **20345 B** | trials tenant: all three regions → `carelink-trials`/`clcloud-trials`, `baseUrlCumulus` = `…/connect/carepartner/**v13**`, `baseUrlPde` = `…/pde/**v3**`, Auth0 config = `carepartner_auth0_cl_sso_config_v1.json` (the **clinical** config, for all three regions), `US,EU,CLINICAL` |
| `clcloud-trials.minimed.com` | 200 | **20345 B** | byte-identical to the `.eu` doc (same sha `94b739dda478`) |
| `clcloud.minimed.com` | 200 | **18105 B** | **a different document**: legacy, `SSOConfiguration` only (no Auth0), `baseUrlCumulus` = `…/connect/carepartner/**v2**`, `baseUrlPde` = `…/pde/**v1**`, `baseUrlCareLink` = `/api/carepartner/**v1**`, **no `baseUrlCms`**, **no `baseUrlAem`**, regions `US,EU` only — no `CLINICAL` |

`certificates[]` is identical between the two (8 entries, same sha — consistent
with METHOD-FACTS' "not a tenant discriminator"). `supportedCountries` differs.

So `buildDiscoveryUrl(isUS)`'s eu/com split is **not** purely cosmetic after
all — for the `v11` base path it selects between two structurally different
documents. It remains cosmetic for v13.

### ⚠️ `v6/discover` exists on the trials deployment only

| host | `/connect/carepartner/v6/discover/android/3.6` |
|---|---|
| `clcloud.minimed.eu` | **403 `MissingAuthenticationTokenException`** — no route |
| `clcloud.minimed.com` | **403 `MissingAuthenticationTokenException`** — no route |
| `clcloud-trials.minimed.com` | **200**, 10053 B, `x-cum-signature` present |

A brand-new cell. It is the legacy doc: `SSOConfiguration` =
`https://carelink-trials.minimed.com/configs/v1/sso_cp_us_v6.json` — a **fourth**
SSO-config filename variant, alongside `oauth20_sso_carepartner_{us,eu}_v6.json`,
`sso_cp_us_v6.json` and `eu_sso_cp_eu_v6.json` — and it points every region at
`carelink-trials` hosts. It is **app-version-collapsed**: `android/3.8` returns
byte-identical content to `android/3.6`, differing only in the echoed
`"config":"android,3.8"`. That matches PROBE-FINDINGS §7's finding that the
main axis serves exactly two documents.

### What is *not* asymmetric

`display/message` at v6/v11/v13 gives byte-identical results on all three hosts
(v6 403, v11 401, v13 401). `v12/discover` is 401 on all three. There is no
region split on the data leg.

---

## 5. PDE / `csr` / bare-cumulus namespaces — refined, and a caveat

All six probed paths returned **403 `MissingAuthenticationTokenException`**, 42 B,
no CORS headers, no `x-cum-signature`:

| path | status | verdict |
|---|---|---|
| `/connect/pde/v3/display/message` | 403 | no GET route |
| `/connect/pde/v3/discover/android/3.6` | 403 | no GET route |
| `/connect/pde/v1/display/message` | 403 | no GET route |
| `/connect/pde/v2/display/message` | 403 | no GET route |
| `/connect/csr/v2/display/message` | 403 | no GET route |
| `/connect/v2/display/message` (pre-`carepartner` bare cumulus) | 403 | no GET route |

This refines two earlier notes. PROBE-FINDINGS §5 recorded
"`clcloud.minimed.{eu,com}/connect/pde/v3/*` → 403, PDE v3, untouched by us",
and AUTH-TENANT-FINDINGS carried `baseUrlPde` (`/connect/pde/v3`) forward as an
open question — "403, deliberately untouched". The 403 is the **router's**
no-route response, not a token gate: it is byte-identical to what a random UUID
returns. PDE v3 is *not* behind a token on the GET path — it is not on the GET
path at all.

**Caveat, stated because the v6 case proves it matters:** a 403 on GET does not
prove the resource is unregistered. `v6/display/message` is 403 on GET and
perfectly real. PDE v3 could equally be a POST-only route. I did not run OPTIONS
on the PDE namespace — the 70-request cap was exhausted. **PDE v3 needs an
OPTIONS probe (≲6 requests, ~12 s) before "does not exist" can be said.** Until
then the honest phrasing is "no GET route", not "absent".

---

## 6. NEW cells vs `PROBE-FINDINGS.md` §7

PROBE-FINDINGS §7 consolidated the `android/<app-version>` axis on the `v13`
base path. §7 does **not** record any of the following; none appeared in any
prior note except where marked:

1. **`/connect/carepartner/v12/display/message` — live, GET-capable, 401 on all
   three hosts.** Prior notes only ever probed `display/message` at v6/v11/v13.
   The live GET set is `{11, 12, 13}`, not `{11, 13}`.
2. **`/connect/carepartner/v6/discover/android/{3.6,3.8}` — live (200) on
   `clcloud-trials.minimed.com` only.** §7's base-path sweep never reached v6 on
   any host.
3. **`v11/discover` is host-dependent** — `.com` serves a 18105 B legacy doc
   while `.eu`/`-trials` serve a 20345 B Auth0/cumulus-v13 doc. A direct
   contradiction of PROBE-FINDINGS §3's "the doc is global".
4. **`x-cum-signature` response header** on every signed discovery document,
   distinct per document. Never recorded.
5. **`x-ca-err: 990`** on every 401 — the Broadcom/Layer7 CA-gateway error code,
   i.e. the `UnauthorizedException` 401s come from inside Medtronic's stack, not
   from API Gateway. Useful because it corroborates that 401 genuinely reached a
   backend.
6. **`x-amzn-errortype` as an existence oracle** for this host family. Recorded
   with 7 fabricated controls and 0 false results.
7. `v10/discover`'s 204 carries a security-header set and an `x-amzn-trace-id`
   `Lineage=` field that no other cell carries.

Confirmed, not new: `v10` → 204; `v12/discover` → 401 on all three hosts;
`v14`/`v15`/`v16` → no route; `v13/discover` byte-identical across all three
hosts and matching the on-disk capture.

---

## 7. What this means for the fork

`src/carelink/client.ts:767` — `const BLE_API_VERSIONS = [13, 11, 6, 5];`

Measured against the sweep above (the bridge POSTs to this path, `client.ts:272`):

| version | verdict | in the fork's list? |
|---|---|---|
| v13 | live, GET-capable | ✅ |
| v11 | live, GET-capable | ✅ |
| v12 | **live** — same shape as v11/v13 on all three hosts | ❌ **omitted** |
| v6 | exists, **POST-only** (no GET) — the version the vendor's own config hands out | ✅ (harmless, the bridge POSTs) |
| v5 | **no route at all — permanently dead, not auth-gated** | ✅ **dead weight** |

Two small, mechanical corrections available without a token: **v5 is a dead
entry that can never answer**, and **v12 is a live entry that is never tried**.
Neither changes behaviour today (v13 is tried first and is live) — but v5 should
not be in a fallback list, and v12 is a free extra candidate.

**And the honest limit:** everything here is about *route existence*. Which of
`{11, 12, 13}` returns the data the bridge wants, with a real token, is the
PROBE-FINDINGS §6 open question and cannot be answered without credentials.

---

## 8. Reproducing

```
recon/vaxis-probe.sh     # 68 requests, GET + OPTIONS, cap 70, prints a live table
recon/vaxis-extra.sh     # requests 69–70 (the OPTIONS control and the v13 hunt)
recon/vaxis.jsonl        # every request: status, ctype, bytes, latency, header sig
recon/vaxisbodies/       # *.hdr and *.body per request
```

Every claim in this file is a direct read of `vaxisbodies/`. The three 200-body
discovery documents are retained verbatim there for re-derivation.
