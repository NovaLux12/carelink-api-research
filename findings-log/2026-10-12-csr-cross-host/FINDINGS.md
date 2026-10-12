# Area N — cross-host check of the two POST-only routes (2026-10-12)

Closes `docs/11-suggested-research-areas.md` area N. Claim: issue #8.

## Method

- Hosts: `clcloud.minimed.com`, `clcloud-trials.minimed.com`. **16 requests in
  the harness** (`probe.sh`, `results.jsonl`, `headers/`, `run.log` in this
  directory). **16 of a 16 cap**, ≥2.5 s between requests to the same host — the
  Area C spacing. GET and OPTIONS with an empty body only. No `Authorization`,
  no `Cookie`, no `x-api-key`, no POST, no token exchange, no DNS, no port
  scanning, no dev/stage host.
- Controls ran **before** the data cells on each host (requests 1–4 then 5–8 on
  `.com`; 9–12 then 13–16 on `-trials`), so the oracle verdict is not
  contaminated by the data it judges — the ordering `VERSION-AXIS.md` §1 was
  built on.
- The control set is **cell-for-cell the Area C set**
  ([findings-log/2026-10-11-pde-csr-oracle/probe.sh](../2026-10-11-pde-csr-oracle/probe.sh)),
  including the same fabricated UUID, so the two passes are comparable row by row.
- Candidate justification — no wordlist, no fuzzing, no new host:
  - `connect/csr/v2/display/message` and `connect/v2/display/message` are the two
    routes Area C recorded live-and-POST-only on `clcloud.minimed.eu` (its rows
    16 and 26). Both hosts are recorded cumulus hosts
    (`ORACLE-PROBE-MATRIX.md` rows 5–12). Area N's blocker was "four OPTIONS
    requests, never sent".
  - Both methods on both paths because the verdict rule in
    `docs/09-methodology-and-oracles.md` §2 needs both: `GET 403 + OPTIONS 403 →
    dead`, `GET 403 + OPTIONS 200 → live, POST-only`.

## Oracle re-validation (controls, OBSERVED)

| # | host | method | path | status | x-amzn-errortype | x-ca-err | CORS |
|---|---|---|---|---|---|---|---|
| 1 | `.com` | GET | `connect/carepartner/v13/display/message` | 401 | UnauthorizedException | 990 | absent |
| 2 | `.com` | GET | `connect/carepartner/v13/3f8a1c2e-…` (certainly absent) | 403 | MissingAuthenticationTokenException | absent | absent |
| 3 | `.com` | OPTIONS | `connect/carepartner/v13/display/message` | 200 | absent | absent | `*`, 0 B, `allow-methods: OPTIONS` |
| 4 | `.com` | OPTIONS | `connect/carepartner/v13/3f8a1c2e-…` | 403 | MissingAuthenticationTokenException | absent | absent |
| 9 | `-trials` | GET | `connect/carepartner/v13/display/message` | 401 | UnauthorizedException | 990 | absent |
| 10 | `-trials` | GET | `connect/carepartner/v13/3f8a1c2e-…` | 403 | MissingAuthenticationTokenException | absent | absent |
| 11 | `-trials` | OPTIONS | `connect/carepartner/v13/display/message` | 200 | absent | absent | `*`, 0 B, `allow-methods: OPTIONS` |
| 12 | `-trials` | OPTIONS | `connect/carepartner/v13/3f8a1c2e-…` | 403 | MissingAuthenticationTokenException | absent | absent |

Both hosts reproduce the `.eu` signature exactly (Area C rows 1–4). **Evidence
class: OBSERVED** — `results.jsonl` rows 1–4 and 9–12, `headers/01-*`–`04-*` and
`11-*`–`12-*`, `run.log`.

The 42 B router body (`{"message":"Missing Authentication Token"}`) and the 36 B
authorizer body (`{"message":"Authentication failure"}`) are byte-identical to
the recorded `.eu` responses; `Content-Type: application/json` throughout.

## Results — full table (OBSERVED)

| # | host | method | path | status | errortype | CORS / allow-methods | verdict |
|---|---|---|---|---|---|---|---|
| 5 | `.com` | GET | `connect/csr/v2/display/message` | 403 | MissingAuthToken | — | no GET route |
| 6 | `.com` | OPTIONS | `connect/csr/v2/display/message` | **200** | absent | `*`, `OPTIONS,POST`, 0 B | **LIVE, POST-only** |
| 7 | `.com` | GET | `connect/v2/display/message` | 403 | MissingAuthToken | — | no GET route |
| 8 | `.com` | OPTIONS | `connect/v2/display/message` | **200** | absent | `*`, `POST,OPTIONS`, 0 B | **LIVE, POST-only** |
| 13 | `-trials` | GET | `connect/csr/v2/display/message` | 403 | MissingAuthToken | — | no GET route |
| 14 | `-trials` | OPTIONS | `connect/csr/v2/display/message` | **200** | absent | `*`, `OPTIONS,POST`, 0 B | **LIVE, POST-only** |
| 15 | `-trials` | GET | `connect/v2/display/message` | 403 | MissingAuthToken | — | no GET route |
| 16 | `-trials` | OPTIONS | `connect/v2/display/message` | **200** | absent | `*`, `POST,OPTIONS`, 0 B | **LIVE, POST-only** |

`MissingAuthToken` = `MissingAuthenticationTokenException`. Every 200 carried
`x-cache: Miss from cloudfront`. **Evidence class: OBSERVED** — `results.jsonl`,
`headers/`, `run.log`.

## Verdict 1 — no region split (OBSERVED)

**Both routes are live and POST-only on all three cumulus hosts.** Every cell is
byte-identical across `clcloud.minimed.eu` (Area C), `clcloud.minimed.com` and
`clcloud-trials.minimed.com`, including the CORS header *ordering*, which differs
between the two routes and is stable:

| route | `access-control-allow-methods` | `access-control-allow-headers` |
|---|---|---|
| `connect/csr/v2/display/message` | `OPTIONS,POST` | `Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token` |
| `connect/v2/display/message` | `POST,OPTIONS` | the same, **plus** `x-amz-apigw-id,x-amzn-requestid,x-amzn-trace-id` |
| `connect/carepartner/v13/display/message` | `OPTIONS` | the shorter list |

Three routes, three distinct CORS configurations, identical on all three hosts
(OBSERVED — 3 hosts × 3 routes this pass and Area C's `.eu` rows). INFERRED
(assumption stated): two routes that differ in method-list *order* and in
allow-header breadth are most likely two separately-declared routes with different
gateway configuration, rather than one route answering twice. No vendor
document states this, and no pass has read the gateway configuration.

**This discharges the Area C limits inference.** The 2026-10-11 log recorded: *"INFERRED:
likely identical on `.com` and `-trials` because the data leg showed no region
split — but that is an inference from the carepartner leg, not an observation of
CSR/bare-v2."* It is now an observation, on the routes themselves. The original
line stays in that log; this is the superseding note.

## Verdict 2 — a methodology correction: `allow-methods` is not a method register

**This is the finding that outlives the area.**

`connect/carepartner/v13/display/message` advertises, on an OPTIONS request,
`access-control-allow-origin: *` and `access-control-allow-methods: OPTIONS` —
and on **GET returns `401` `UnauthorizedException` + `x-ca-err: 990`**, which this
repo's own oracle defines as *the request reached Medtronic's Layer7 authorizer*:
the route exists **and GET is a registered method on it**. Observed on all three
hosts (`.eu` Area C row 13 + this pass rows 3 and 11).

So the preflight advertises `OPTIONS` on a route that also serves GET. The
`allow-methods` list therefore **does not enumerate the route's registered
methods**, and cannot be read as evidence that a method is absent.

`docs/06-patient-api-surface.md` §"Existence oracles" currently presents this
exact signature as meaning the opposite:

> `access-control-allow-origin: *` + `access-control-allow-methods: OPTIONS` on
> an **OPTIONS** request proves the resource exists even when GET is undefined

The first half is right and is what found POST-only `v6`. The second half is
wrong as a general rule: that signature is carried by a GET-capable route.
**Corrected in place, original wording kept visible.**

What each signal can and cannot carry:

| signal | what it proves | what it does **not** prove |
|---|---|---|
| `OPTIONS` → 200 + `access-control-allow-origin: *` | the resource exists, even when no GET method is registered | which methods are registered |
| `GET` → 403 + `MissingAuthenticationTokenException` | no GET route | that nothing is registered — `v6`, `csr/v2` and bare `v2` are all 403 and all real |
| `GET` → 401 + `UnauthorizedException` + `x-ca-err: 990` | a GET route exists and reached the Layer7 authorizer | — |

Method registration is settled by the **GET probe alone**, never by the CORS
header. This is `AGENTS.md` §6 item 2 in a new costume: a header read as meaning
something it does not mean.

### Browser callability (INFERRED)

**INFERRED, with the assumption stated:** because a cross-origin request bearing
an `Authorization` header triggers a preflight, and the `v13` preflight returns
`allow-methods: OPTIONS` without `GET`, a browser-based client on another origin
could not complete a GET to `v13/display/message`. Assumption: the browser
enforces `allow-methods` on preflight, and no third-party client is
same-origin with `clcloud.*` — the first is specified behaviour (Fetch), the
second is not observed here and not tested. This does **not** affect server-side
clients, which do not preflight. It is recorded as a question, not a finding;
see successor area U.

## Limits (what this does NOT prove)

- **Route existence only.** Which of `{csr/v2, bare v2, v6, v11, v12, v13}`
  returns data with a real token is still token-gated
  (`docs/10-open-questions.md` §1). Unchanged by this pass.
- **"POST-only" still means "registered with a non-GET method, almost certainly
  POST"**, not "POST returns data". Unchanged inference from Area C, now
  reproduced on three hosts. Note that `v13` shows the `allow-methods` list
  cannot be trusted as the register, so the POST half rests on the two POST-only
  routes *agreeing* with it, not on the header alone.
- `csr/v1`/`v3` and the PDE namespace were **not re-probed on these two hosts**.
  They are dead on `.eu` on both methods; whether they are dead everywhere is a
  separate, cheap sweep and is named as successor area T's sibling below rather
  than assumed here. Bounded list, by design.
- No host other than the three recorded cumulus hosts was contacted.

## Requests

16 of a 16 cap, exactly as claimed in #8. ≥2.5 s spacing, same host. GET and
OPTIONS only, empty body. No auth headers, no cookies, no POST, no token
exchange.