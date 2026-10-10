# Area C — PDE / CSR / bare-carepartner oracle pass (2026-10-11)

Closes `docs/11-suggested-research-areas.md` area C. Claim: issue #2.

## Method

- Host: `clcloud.minimed.eu` only. Single-host scope is justified because the
  data leg shows no region split — OBSERVED in
  `findings-log/probe-2026-10-08/recon/VERSION-AXIS.md` §4 (v6/v11/v13
  byte-identical across all three hosts). Cross-host follow-up deferred unless
  something proved live.
- 26 requests in the harness (`probe.sh`, `results.jsonl`, `headers/`,
  `run.log` in this directory) + 4 confirmation re-probes of the two hits
  (same host, OPTIONS only, §4 below). **Total 30 of a 30 cap. ≥2.5 s between
  requests to the same host.** GET and OPTIONS only. No `Authorization`, no
  `Cookie`, no `x-api-key`, no POST, no token exchange.
- Controls ran first (requests 1–4), before any PDE/CSR cell, so the oracle
  verdict is not contaminated by the data it judges.
- Candidate justification (no wordlist, no fuzzing):
  - PDE versions {v1, v2, v3}: `baseUrlPde` in the live v13 discovery document
    is `…/connect/pde/v3` (PUBLISHED — served unauthenticated in the discovery
    doc, see `docs/03-discovery-and-versions.md`); the legacy `.com` v11 doc
    shows `…/connect/pde/v1` (PUBLISHED, same source). v2 completes the
    observed set.
  - PDE paths mirror the carepartner legs: `display/message` (data leg) and
    `discover/android/3.6` (discovery leg).
  - CSR: `connect/csr/v2/display/message` is the only observed CSR path
    (OBSERVED — `findings-log/probe-2026-10-08/recon/VERSION-AXIS.md` §5). v1/v3
    are version neighbours on the same axis as carepartner v11/v12/v13.
  - Bare `connect/carepartner/` root, `connect/carepartner/v13`,
    `connect/carepartner/v13/discover` are prefix parents of known-live leaves.
  - Bare `connect/v2/display/message` is the pre-carepartner cumulus path
    previously probed on GET only (OBSERVED — VERSION-AXIS §5).

## Oracle re-validation (controls, OBSERVED)

| # | method | path | status | x-amzn-errortype | x-ca-err | CORS |
|---|---|---|---|---|---|---|
| 1 | GET | `connect/carepartner/v13/display/message` | 401 | UnauthorizedException | 990 | absent |
| 2 | GET | `connect/carepartner/v13/3f8a1c2e-…` (UUID, certainly absent) | 403 | MissingAuthenticationTokenException | absent | absent |
| 3 | OPTIONS | `connect/carepartner/v13/display/message` | 200 | absent | absent | `*`, 0 B |
| 4 | OPTIONS | `connect/carepartner/v13/3f8a1c2e-…` | 403 | MissingAuthenticationTokenException | absent | absent |

The oracle from `docs/09-methodology-and-oracles.md` reproduces exactly:
GET 401 = live with GET; GET 403 + MissingAuthenticationTokenException = no
route; OPTIONS 200 + `access-control-allow-origin: *` = resource exists.
**Evidence class: OBSERVED** — `results.jsonl` rows 1–4, `headers/01-*` to
`headers/04-*`, `run.log` in this directory.

## Results — full table (OBSERVED)

Verdict rule (from `docs/09-methodology-and-oracles.md`): GET 403 + OPTIONS 403
→ dead; GET 403 + OPTIONS 200 → live but POST-only; GET 401 → live with GET;
GET 200/204 → public.

| # | method | path | status | errortype | CORS | verdict |
|---|---|---|---|---|---|---|
| 5 | GET | `connect/pde/v1/display/message` | 403 | MissingAuthToken | — | no GET route |
| 6 | OPTIONS | `connect/pde/v1/display/message` | 403 | MissingAuthToken | — | **dead** |
| 7 | GET | `connect/pde/v2/display/message` | 403 | MissingAuthToken | — | no GET route |
| 8 | OPTIONS | `connect/pde/v2/display/message` | 403 | MissingAuthToken | — | **dead** |
| 9 | GET | `connect/pde/v3/display/message` | 403 | MissingAuthToken | — | no GET route |
| 10 | OPTIONS | `connect/pde/v3/display/message` | 403 | MissingAuthToken | — | **dead** |
| 11 | GET | `connect/pde/v3/discover/android/3.6` | 403 | MissingAuthToken | — | no GET route |
| 12 | OPTIONS | `connect/pde/v3/discover/android/3.6` | 403 | MissingAuthToken | — | **dead** |
| 13 | GET | `connect/csr/v1/display/message` | 403 | MissingAuthToken | — | no GET route |
| 14 | OPTIONS | `connect/csr/v1/display/message` | 403 | MissingAuthToken | — | **dead** |
| 15 | GET | `connect/csr/v2/display/message` | 403 | MissingAuthToken | — | no GET route |
| 16 | OPTIONS | `connect/csr/v2/display/message` | **200** | absent | `*`, 0 B | **LIVE, POST-only — NEW** |
| 17 | GET | `connect/csr/v3/display/message` | 403 | MissingAuthToken | — | no GET route |
| 18 | OPTIONS | `connect/csr/v3/display/message` | 403 | MissingAuthToken | — | **dead** |
| 19 | GET | `connect/carepartner/` | 403 | MissingAuthToken | — | no GET route |
| 20 | OPTIONS | `connect/carepartner/` | 403 | MissingAuthToken | — | **dead** |
| 21 | GET | `connect/carepartner/v13` | 403 | MissingAuthToken | — | no GET route |
| 22 | OPTIONS | `connect/carepartner/v13` | 403 | MissingAuthToken | — | **dead** |
| 23 | GET | `connect/carepartner/v13/discover` | 403 | MissingAuthToken | — | no GET route |
| 24 | OPTIONS | `connect/carepartner/v13/discover` | 403 | MissingAuthToken | — | **dead** |
| 25 | GET | `connect/v2/display/message` | 403 | MissingAuthToken | — | no GET route |
| 26 | OPTIONS | `connect/v2/display/message` | **200** | absent | `*`, 0 B | **LIVE, POST-only — NEW** |

`MissingAuthToken` = `MissingAuthenticationTokenException`. All 403 bodies are
the 42 B `{"message":"Missing Authentication Token"}` router response; the 401
control body is the 36 B `{"message":"Authentication failure"}` authoriser
response. Response `Content-Type` is `application/json` throughout.
**Evidence class: OBSERVED** — `results.jsonl`, `headers/`, `run.log`.

## The two hits (OBSERVED, confirmed 3×)

**Hit 1 — `connect/csr/v2/display/message` is live, POST-only.**

- GET → 403 MissingAuthenticationTokenException, 42 B, no CORS (request 15).
- OPTIONS → 200, `access-control-allow-origin: *`,
  `access-control-allow-methods: OPTIONS,POST`, 0 B, `x-cache: Miss from
  cloudfront` (request 16), reproduced twice more on re-probe (4 OPTIONS
  confirmations total across the two hits, §4 of the claim).
- This is the same signature by which POST-only `v6/display/message` was found
  (GET 403 + OPTIONS 200 + CORS). No prior note records any live CSR route.

**Hit 2 — `connect/v2/display/message` (bare pre-carepartner cumulus) is live,
POST-only.**

- GET → 403 MissingAuthenticationTokenException, 42 B, no CORS (request 25).
- OPTIONS → 200, `access-control-allow-origin: *`,
  `access-control-allow-methods: POST,OPTIONS`, 0 B, `x-cache: Miss from
  cloudfront` (request 26), reproduced twice more on re-probe.
- Prior verdict was "no GET route" (VERSION-AXIS §5); the honest phrasing is now
  "exists, POST-only", same class as `v6/display/message`.

INFERRED (assumptions shown): both hits list POST in `Allow`/`CORS` methods,
so the live method is most likely POST — the same inference that held for v6,
whose POST → 401 was later confirmed independently. Without a token the body
behind POST cannot be observed, so "POST-only" means "registered with a
non-GET method, almost certainly POST", not "POST returns data".

## Negatives closed (OBSERVED)

- PDE: all of v1/v2/v3 `display/message` plus v3 `discover/android/3.6` are
  GET-403 + OPTIONS-403 with MissingAuthenticationTokenException and no CORS.
  The v6 caveat ("403 on GET does not prove unregistered") is now discharged
  for PDE on this host: **no route on any tested method**, not merely "no GET
  route". This supersedes the VERSION-AXIS §5 caveat for PDE.
- CSR v1/v3: dead on both methods. Only v2 is live.
- Bare `connect/carepartner/` prefixes (root, `v13`, `v13/discover`): dead on
  both methods. The router answers at leaves, not at prefix parents.

## Limits (what this does NOT prove)

- Single host (`clcloud.minimed.eu`). INFERRED: likely identical on `.com` and
  `-trials` because the data leg showed no region split — but that is an
  inference from the carepartner leg, not an observation of CSR/bare-v2. **Needs
  a cross-host OPTIONS check (4 requests) before claiming global.**
- Route existence only. Which of {csr/v2, bare v2, v6, v11, v12, v13} returns
  data with a real token is still token-gated, same as the
  `docs/06-patient-api-surface.md` open question.
- `csr/v1`/`v3` and PDE neighbours beyond the probed set (e.g. other CSR
  versions, `pde/v3` siblings) remain unprobed by design — bounded list, no
  fuzzing.

## Requests

30 of a 30 cap. 26 harness + 4 confirmations. ≥2.5 s spacing, same host.
GET + OPTIONS only. No auth headers, no cookies, no POST, no token exchange.
