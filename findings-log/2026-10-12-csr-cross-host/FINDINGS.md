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
hosts (`.eu` Area C rows 1 and 3 + this pass rows 1/3 and 9/11 — the row number in
an earlier draft of this sentence was wrong; see §Correction).

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

**GET** registration is settled by the **GET probe**; the CORS header cannot
override it. (The original wording here read "method registration is settled by
the **GET probe alone**" — which contradicts §Limits below, since the *POST* half
cannot be settled that way. Narrowed; see §Correction.) This is `AGENTS.md` §6
item 2 in a new costume: a header read as meaning something it does not mean.

### Browser callability — ⚠ REFUTED 2026-10-12, original claim kept visible

> **Original claim, now known to be wrong.** "INFERRED, with the assumption
> stated: because a cross-origin request bearing an `Authorization` header
> triggers a preflight, and the `v13` preflight returns `allow-methods: OPTIONS`
> without `GET`, a browser-based client on another origin **could not complete a
> GET** to `v13/display/message`."

The label was honest; the **mechanism does not exist**. `GET` is a
CORS-safelisted method, so Fetch §4.8 never applies the `allow-methods` check to
it, and the CORS check itself (§4.10) reads only `Access-Control-Allow-Origin` and
`Access-Control-Allow-Credentials` — it never consults
`Access-Control-Allow-Methods`. A preflight advertising only `OPTIONS` therefore
**cannot** block a browser GET.

**Corrected statement:** a cross-origin browser GET to `v13` **passes the
preflight and the GET is sent**. It fails afterwards, because the `401`
`UnauthorizedException` response carries **no `Access-Control-*` header at all**
(OBSERVED — `headers/01-GET-connect_carepartner_v13_display_message.hdr`) and the
response is therefore unreadable by the page. Whether a **`200`** response carries
`Access-Control-Allow-Origin` is **token-gated and unobserved**; that is the
question now registered in `docs/10-open-questions.md` §1 and in the blocked table
at the top of `docs/11`.

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
  separate, cheap sweep — **successor area U** in `docs/11`, not assumed here.
  Bounded list, by design.
- No host other than the three recorded cumulus hosts was contacted.

## Requests

16 of a 16 cap, exactly as claimed in #8. ≥2.5 s spacing, same host. GET and
OPTIONS only, empty body. No auth headers, no cookies, no POST, no token
exchange.
---

## Correction (2026-10-12)

Independent verification of this PR's two flagged claims was delegated to two
agents running `CONTRIBUTING-research.md` Prompt D, one claim per run. Both read
the raw `.hdr` dumps rather than this prose. **Verdicts: CONFIRMS on the
methodology correction, CONTRADICTS on the browser-callability inference.** The
original claims are kept above; this section records what moved and why.

### 1. Refuted — browser callability (the substantive error)

The §"Browser callability" inference claimed a cross-origin browser GET to `v13`
would be blocked by the preflight advertising no `GET`. **The mechanism does not
exist.** `GET` is a CORS-safelisted method, so Fetch §4.8 never applies the
`allow-methods` test to it, and the CORS check (§4.10) reads only
`Access-Control-Allow-Origin` and `Access-Control-Allow-Credentials`.

Settled three ways: the spec text (PUBLISHED, fetched 2026-10-12); a local
headless-browser control where `allow-methods: OPTIONS` **plus** `ACAO: *` let the
GET through, while removing `ACAO` produced `MissingAllowOriginHeader` (OBSERVED,
local, zero vendor requests); and the vendor cell itself, where the preflight
**passed**, the GET **went to the wire**, and the failure was byte-for-byte the
no-`ACAO` signature (OBSERVED — 6 vendor requests, GET + its automatic preflight
OPTIONS, empty body, no credential headers, within the 10-request Prompt D cap).

**The real blocker was in a capture this pass already had:** the `401`
response carries no `Access-Control-*` header at all
(`headers/01-GET-connect_carepartner_v13_display_message.hdr`).

Corrected statement is in §"Browser callability" above. The residual question —
does a **200** carry `Access-Control-Allow-Origin`? — is token-gated and is now
registered in `docs/10-open-questions.md` §1 and in the blocked table at the top
of `docs/11`, replacing a pointer to successor area U, which was about something
else entirely.

**Why this happened.** The claim was INFERRED, labelled as such, with its
assumption stated — and still wrong, because the assumption was half-specified
behaviour that, checked, does not apply to the case it was applied to. A label
limits the damage of a wrong claim; it does not make the claim right.

### 2. Confirmed, with four defects around it

The core correction — `access-control-allow-methods` is not a register of a
route's methods — **holds, at the strength claimed**, with 3-of-3 host coverage
and each host carrying a captured GET+OPTIONS pair. The verifier's framing is
sharper than the original: the rule being corrected is *one-directional*
("a method absent from the list is absent from the route"), and `v13` is a
positive counterexample where absence in the list coexists with presence on the
route. One counterexample retires a one-directional inference rule outright.

It also declined to force a winner between the two readings of *why*: `v13`
carrying a misconfigured preflight, and the header being uninformative in
general. Both fit, nothing on disk discriminates, and the PR claims only the
weaker of the two. Four defects fixed:

1. **"settled by the GET probe alone"** contradicted §Limits 25 lines below,
   which correctly says the POST half rests on the routes *agreeing* with the
   header. Narrowed to **GET** registration.
2. **`docs/09`** asserted a mechanism — that the header "is gateway CORS
   configuration" — from n = 3 routes, two of which merely agree with it and
   whose agreement is only as strong as the header itself. Reworded to the
   non-overreaching form used in `docs/06` and here.
3. **The disclaimed clause was still live** in the `docs/06` oracle summary
   table — the one place a reader consults operationally. Flagged inline.
4. **Wrong citation.** This log cited "Area C row 13" for the `.eu` `v13`
   OPTIONS. Row 13 is `GET connect/csr/v1/display/message`; the `v13` OPTIONS is
   row **3**. `AGENTS.md` §6 item 6. The error also propagated into the
   verification brief, which repeated it — a second instance of prose errors
   travelling through the documents that cite them.

### 3. The pin was one-directional on exactly the axis of the finding

The suite asserted `allow-methods == "OPTIONS"` on the `v13` preflight but
**never pinned the GET half**. If Medtronic made `v13` POST-only, the header would
very likely still read `OPTIONS`, **nothing would fail**, and the documented claim
would have become false silently.

Closed: `GET` → 401 + `x-ca-err == "990"` is now pinned on all three hosts. The
suite did read CORS headers on the OPTIONS cells, so `docs/06`'s "asserts the
`x-amzn-errortype` on each 403 cell rather than reading the CORS header" was a
loose compression of a nuance stated correctly in the suite's own comment.

### 4. Negative result worth keeping

`x-amz-apigw-id` is **not** a route or API identity on this family. All 16 values
in this pass base64-decode to opaque binary and they differ between two requests
to the *same* route, so it cannot separate routes or APIs and cannot settle the
§Verdict 1 inference. Recorded so no future pass spends requests on it. The
§Verdict 1 inference about two separately-declared routes stays INFERRED and
unsettleable from outside: it needs the API Gateway export or the Layer7 policy,
both outside GET/OPTIONS-without-auth.
