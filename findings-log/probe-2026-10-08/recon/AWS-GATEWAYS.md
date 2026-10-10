# AWS API Gateways disclosed by the public patient config — bounded path enumeration

**Date:** 2026-10-10
**Targets:** the five `*.execute-api.*.amazonaws.com` endpoints published inside
`/patient/v2/configuration/public`, first recorded in
`CROSS-REGION-CONFIG-FINDINGS.md` §"Nine previously-unrecorded service endpoints".
**Scope:** unauthenticated, read-only, GET-only path enumeration. No POST, no
token exchange, no DNS work, no `*.medtronic.com` report brokers.

## 0. Headline, up front

The enumeration found **no new paths**. It did find that the *question* was
malformed: on AWS API Gateway REST APIs, `403 Missing Authentication Token` is
the **unmatched-route** error, not an auth-gate signal — so "403 = exists,
auth-gated" is inverted, and "404 = absent" is unreachable because these
gateways never emit 404. The genuinely new result is structural: **dialog-lite is
a single `ANY /{proxy+}` catch-all over the whole stage**, with a Lambda
integration that raises on every invocation, on both regions, with no CORS
configured at all.

## 1. Request accounting — cap and count

| | |
|---|---|
| Cap | **90 HTTP requests** |
| Requests actually sent | **90** (cap reached, never exceeded) |
| Distinct request shapes (url + method + headers) | 83 |
| Distinct URLs probed | 73 |
| Duplicate re-sends | 7 (identical url+method+headers already logged) |
| Per-host floor delay | 2.5 s (measured, not assumed) |
| Methods used | GET (85) + OPTIONS (5, one preflight per host) |

Breakdown of the 90:

| block | requests | what |
|---|---:|---|
| 0 | 5 | published root of each host, full headers |
| 1 | 5 | **control**: certainly-absent UUID under the published prefix |
| 2 | 10 | stage root **above** the published prefix, + control UUID there |
| 3 | 34 | dialog-lite: 15 vocabulary candidates + 1 composed shape, × 2 regions |
| 4 | 24 | patient-timeline: 7 vocabulary candidates, × 3 regions |
| 5 | 5 | dummy `X-Api-Key` header behaviour |
| 6 | 5 | OPTIONS preflight, one per host |
| *of which* | *7* | *duplicate re-sends (see §7)* |

> **Why the duplicate re-sends exist, stated plainly.** Requests 87–90 were an
> accidental re-run of the harness from BLOCK 0, which re-sent four root URLs
> already covered by #4–#7. The cap enforcement then raised `RuntimeError` at
> count 90 and stopped. The four duplicate records are **kept** in
> `gw-probe-results.jsonl`; deleting them would misrepresent the count. Net
> effect: BLOCK 7 (the adaptive second round) did not run — see §7.

Latency is the only region-correlated signal in the whole set:

| host | n | rtt min / mean / max |
|---|---:|---|
| dialog-lite EU | 25 | 73 / 79 / 93 ms |
| patient-timeline EU | 15 | 71 / 76 / 83 ms |
| dialog-lite US | 23 | 257 / 305 / 402 ms |
| patient-timeline US | 14 | 256 / 285 / 317 ms |
| patient-timeline trials | 13 | 283 / 304 / 398 ms |

## 2. The oracle: does 403-vs-404 tell you whether a path exists?

**No — and the control proves it in the first three requests of the run.**

The controls. `9f3c1d7e-2b48-4a6c-8e51-0c7d9a2b41f6` is a random UUID: not a
wordlist entry, not a term in `recon/JS-API-SURFACE.md` or
`CHUNK-CORPUS-FINDINGS.md`, and not a legal API-Gateway resource name. It is
certainly absent.

| gateway | control UUID | published root | published root + candidate |
|---|---|---|---|
| dialog-lite EU | **500** `InternalServerErrorException` | **500** | **500** |
| patient-timeline EU / US / trials | **403** `MissingAuthenticationTokenException` | **403** | **403** |

A certainly-absent path returns **byte-identical output** to the published root
on both gateways. So:

- **"403 = exists, auth-gated" is false.** On patient-timeline the UUID control
  403s. There is no response that distinguishes a real route from a fake one.
- **"404 = absent" is unreachable.** Zero `404` responses in 90 requests. AWS API
  Gateway **REST** APIs — which these are, on the evidence of the
  `x-amzn-errortype` / `x-amzn-requestid` / `x-amz-apigw-id` response triplet —
  answer an unmatched (resource, method) pair with `403` + body
  `{"message":"Missing Authentication Token"}` (42 bytes, always exactly). 404 is
  simply not in their response vocabulary, so there is no 404 branch to test.
- **The 403 body never varies.** All 44 of the 403s are the same 42-byte body.
  A usage-plan or Lambda-authorizer denial would read
  `{"message":"Forbidden"}` instead. We never saw that.

What **does** work, in exactly one direction:

> **On dialog-lite, `500 InternalServerErrorException` ⇒ the path is matched and
> routed.** `GET /prodous/` → 403 while `GET /prodous/<uuid>` → 500. If 403 meant
> "a real route exists but is auth-gated", the UUID would have been auth-gated
> too. It was not — it was routed. So 500-vs-403 is a real discriminator on that
> host, pointing the opposite way from the hypothesis in the brief.

Reliability, stated explicitly:

| | can positively confirm a route exists? | can positively confirm a route does not exist? |
|---|---|---|
| dialog-lite | **yes** (500 ⇒ routed) | no (everything is 500) |
| patient-timeline | **no** | **yes for GET and OPTIONS** (403 ⇒ no GET/OPTIONS route) |

That is a usable oracle in the weak direction only. It does **not** turn every
403 into a finding — it turns every 403 into a *negative*.

## 3. Headers and CORS

The complete observed response header set, confirmed against a full `curl -D -`
dump of one response per gateway, is six keys and nothing else:

```
date: <edge timestamp>
content-type: application/json
content-length: 36 (routed-and-failed) | 42 (no route)
x-amzn-errortype: InternalServerErrorException | MissingAuthenticationTokenException
x-amzn-requestid: <fresh UUID, 90/90 distinct>
x-amz-apigw-id: <varies per request>
```

- **No `Access-Control-*` header on any of the 90 responses** — including the
  five explicit preflights that carried `Origin: https://carelink.minimed.eu`
  plus `Access-Control-Request-Method: GET` and
  `Access-Control-Request-Headers: content-type,x-api-key`. Neither service has
  CORS configured. On dialog-lite the OPTIONS did not even fall through to a
  MOCK preflight responder — it was swallowed by the catch-all and returned 500.
  A service published in the patient-facing public config therefore **cannot be
  called from a browser**; it is server-side or native-app only.
- **No `Server`, `Via`, `X-Cache`, `X-Amz-Cf-Id`, `Set-Cookie` or `X-Powered-By`**
  anywhere. No `x-amzn-remapped-*`, no custom headers.
- `x-amzn-requestid` is a fresh UUID per request; it identifies the request, not
  the deployment. `x-amz-apigw-id` varies per request and does not decode to a
  stage name, region, mapping template or backend service name in plaintext.
  **Nothing in any response reveals stage, region, mapping template or backend
  service name.** (Region is already public from the hostname.)
- **Dummy `X-Api-Key` changed nothing.** `X-Api-Key: DUMMY-NOT-A-KEY-000000000000`
  is an obviously non-credential string. Sent once per host: dialog-lite stayed
  500, patient-timeline stayed 403, identical bodies and identical 36/42-byte
  lengths. So **no usage-plan API key is required** on any of the five gateways —
  which *weakens* the "auth-gated route" reading of the 403s, since a
  key-gated route would have flipped the body.

## 4. Cross-region

**No asymmetry anywhere.** Both services are structurally identical in every
region they are deployed to:

- **dialog-lite** (EU + US; `null` on trials): the same 20 distinct GET paths
  probed on each, the same 22 distinct request shapes, same statuses, same
  bodies, same header set. `/prodous/` → 403 but `/prodous/<x>` → 500; `/prod/`
  → 403 but `/prod/<x>` → 500. One gateway, one integration, mirrored.
- **patient-timeline** (EU + US + trials): the same 11 distinct GET paths on
  each, all 403, byte-identical. Three deployments of the same API id behaviour.
- The only region-correlated difference in the entire dataset is latency
  (§1), which matches eu-central-1 vs us-east-1 from this machine.
- Consistent with the config: `mmm.data.api.url` is `null` on trials, so the
  dialog service is not deployed there.

## 5. Genuinely new paths

**None.** All 15 dialog-lite candidates and all 7 patient-timeline candidates
returned byte-identical output to the certainly-absent control, on every region.
No candidate returned a status, content-type, body or header set that differs
from the control.

The candidates and their provenance (all traceable to
`recon/JS-API-SURFACE.md` / `CHUNK-CORPUS-FINDINGS.md`, or the service name):

| candidate | provenance |
|---|---|
| `insights` | `hcp/insights/v1/*` family, 8 endpoints (JS-API-SURFACE §2.1) |
| `gmi` | `gmi` / `glucoseManagementIndicator` call-site field (CHUNK-CORPUS) |
| `response` | reply noun for a conversational service |
| `recommendations` | `hcp/settings-calculator/recommendedValues` |
| `settings` | `hcp/patients/((patientId))/long-acting/settings` |
| `user` | `hcp/user/*` family, 29 endpoints (JS-API-SURFACE §7.6) |
| `session` | `session_valid_to`, `expireAllActiveSessions` (§5.2 / §6.1) |
| `config` | `hcp/configuration/*` family, 21 endpoints |
| `data` | the config key is literally `mmm.data.api.url` |
| `status` | `getReportStatus` / `report-status-enum` |
| `version` | conventional; no literal located in the corpus |
| `health` | conventional liveness endpoint |
| `ping` | `hcp/ping/ping`, the portal's own liveness probe (§7.5) |
| `dialog` | service name from the published URL path segment |
| `mmm` | config namespace `mmm.data.api.url` |
| `insights/v1/gmi` | composed shape a real client would build |
| `events`, `entries`, `items`, `list`, `query`, `range`, `params` | patient-timeline noun/verb vocabulary |

## 6. The actually-interesting finding: dialog-lite is a stage-wide catch-all

```
GET /prodous/                        -> 403 Missing Authentication Token   (#14)
GET /prodous/<random-uuid>           -> 500 Internal Server Error          (#19)
GET /prodous/dialog-lite/v1/         -> 500 Internal Server Error          (root, #1/#4/#87)
GET /prodous/dialog-lite/v1/gmi      -> 500 Internal Server Error          (#25)
```

Identical shape on the US deployment with `/prod/`. That is the signature of a
**single `ANY /{proxy+}` route at the stage root with a Lambda proxy
integration that raises on every invocation**. Three consequences:

1. **`dialog-lite/v1` in the published URL is not an API-Gateway resource.** It
   is opaque path data handed to the Lambda. The service has no route table to
   enumerate — "its path space" is the entire stage.
2. **Path enumeration on dialog-lite is informationally empty by construction**,
   and no amount of vocabulary refinement will change that. The task's framing
   ("the gateway is live and routing — it just needs a path") is correct about
   liveness and wrong about the payoff: it already has a path, for everything.
3. **The backend is failing open in the sense of being reachable but unusable.**
   `{"message": "Internal server error"}` with `x-amzn-errortype:
   InternalServerErrorException` is precisely what API Gateway emits when a
   Lambda proxy integration throws an unhandled exception. The same failure on
   GET and OPTIONS, with and without `X-Api-Key`, on two independent regions,
   across 22 distinct request shapes each. Most likely a broken/misconfigured
   deployment (missing env var or IAM permission) rather than a deliberate gate —
   but that cannot be settled from outside, and settling it is out of scope.

**patient-timeline is the mirror image.** `GET /prod/<random-uuid>` → 403 proves
there is **no `{proxy+}` at the stage root**. No GET or OPTIONS request reached
any backend on any of the three gateways. Three readings are consistent with the
evidence and cannot be separated with GET-only probing:

1. no routes are deployed in the `prod` stage at all;
2. routes exist but only for other verbs (e.g. a write-only ingest) — API
   Gateway's 403 conflates "no resource" with "resource exists, method not
   allowed";
3. the live stage is not `prod`.

The single test that would separate (1) from (2) is deliberately **not**
performed here: sending a dummy `Authorization: Bearer <not-a-token>` to see
whether the 403 becomes a `401 Unauthorized`. That is an authentication attempt,
which this brief excludes. It is the recommended first follow-up, with Jack's
sign-off.

## 7. What was not done, and why

- **BLOCK 7 never ran** (`/prod/patient-timeline/v1/events` × 3 regions,
  `/prod/patient-timeline/logbook` × 1). Cause: the accidental re-run in §1
  consumed the last four budget slots. No request was sent beyond the cap.
- **No authorizer discrimination test.** See §6.
- **No POST, no DNS, no `*.medtronic.com` report brokers**, no host outside the
  five listed in the brief.
- **Blunt limitation:** this is 73 URLs against a path space of unbounded size.
  A negative result here is "none of these 73 exist", not "nothing exists".

## 8. Credential handling

No credential was written to any file. The only auth-ish header ever sent was
the literal string `DUMMY-NOT-A-KEY-000000000000`. Verified mechanically: the
real-looking `x-api-key` values that exist in `security/cfg-*.json` (three
distinct, one a 17-char literal placeholder, two 40-char tokens for the reports
brokers) appear in **zero** of the files written by this session. This file
follows the existing convention in `CROSS-REGION-CONFIG-FINDINGS.md`: report
*that* the keys are exposed and *where*, never the keys.

## 9. Files

| file | what |
|---|---|
| `recon/AWS-GATEWAYS.md` | this report |
| `recon/gw-probe-results.jsonl` | machine log, one record per request, 90 lines |
| `recon/gw-probe.log` | human-readable log with the provenance/correction notes |
| `recon/gw-probe-table.md` | the rendered request table, embedded below |
| `recon/aws-gw-probe.py` | harness: enforces the cap, the per-host delay, GET-only, body scrubbing |
| `recon/render-table.py` | renders §10 from the JSONL so the table cannot drift from the log |

## 10. Every URL probed

Statuses: **500** = routed to a backend that raised; **403** =
`MissingAuthenticationTokenException`, no route. Body heads are verbatim.


### dialog-lite EU — `0ptoikank6.execute-api.eu-central-1.amazonaws.com`

| # | method | path | status | `x-amzn-errortype` | content-type | body head | verdict |
|---|---|---|---|---|---|---|---|
| 1 | GET | `/prodous/dialog-lite/v1/` | **500** | `InternalServerErrorException` | application/json | *(not captured)* | ROUTED-BACKEND-ERROR |
| 2 | GET | `/prodous/dialog-lite/v1/9f3c1d7e-2b48-4a6c-8e51-0c7d9a2b41f6` | **500** | `InternalServerErrorException` | application/json | `{"message": "Internal server error"}` | ROUTED-BACKEND-ERROR |
| 14 | GET | `/prodous/` | **403** | `MissingAuthenticationTokenException` | application/json | `{"message":"Missing Authentication Token"}` | NO-ROUTE |
| 19 | GET | `/prodous/9f3c1d7e-2b48-4a6c-8e51-0c7d9a2b41f6` | **500** | `InternalServerErrorException` | application/json | `{"message": "Internal server error"}` | ROUTED-BACKEND-ERROR |
| 24 | GET | `/prodous/dialog-lite/v1/insights` | **500** | `InternalServerErrorException` | application/json | `{"message": "Internal server error"}` | ROUTED-BACKEND-ERROR |
| 25 | GET | `/prodous/dialog-lite/v1/gmi` | **500** | `InternalServerErrorException` | application/json | `{"message": "Internal server error"}` | ROUTED-BACKEND-ERROR |
| 26 | GET | `/prodous/dialog-lite/v1/response` | **500** | `InternalServerErrorException` | application/json | `{"message": "Internal server error"}` | ROUTED-BACKEND-ERROR |
| 27 | GET | `/prodous/dialog-lite/v1/recommendations` | **500** | `InternalServerErrorException` | application/json | `{"message": "Internal server error"}` | ROUTED-BACKEND-ERROR |
| 28 | GET | `/prodous/dialog-lite/v1/settings` | **500** | `InternalServerErrorException` | application/json | `{"message": "Internal server error"}` | ROUTED-BACKEND-ERROR |
| 29 | GET | `/prodous/dialog-lite/v1/user` | **500** | `InternalServerErrorException` | application/json | `{"message": "Internal server error"}` | ROUTED-BACKEND-ERROR |
| 30 | GET | `/prodous/dialog-lite/v1/session` | **500** | `InternalServerErrorException` | application/json | `{"message": "Internal server error"}` | ROUTED-BACKEND-ERROR |
| 31 | GET | `/prodous/dialog-lite/v1/config` | **500** | `InternalServerErrorException` | application/json | `{"message": "Internal server error"}` | ROUTED-BACKEND-ERROR |
| 32 | GET | `/prodous/dialog-lite/v1/data` | **500** | `InternalServerErrorException` | application/json | `{"message": "Internal server error"}` | ROUTED-BACKEND-ERROR |
| 33 | GET | `/prodous/dialog-lite/v1/status` | **500** | `InternalServerErrorException` | application/json | `{"message": "Internal server error"}` | ROUTED-BACKEND-ERROR |
| 34 | GET | `/prodous/dialog-lite/v1/version` | **500** | `InternalServerErrorException` | application/json | `{"message": "Internal server error"}` | ROUTED-BACKEND-ERROR |
| 35 | GET | `/prodous/dialog-lite/v1/health` | **500** | `InternalServerErrorException` | application/json | `{"message": "Internal server error"}` | ROUTED-BACKEND-ERROR |
| 36 | GET | `/prodous/dialog-lite/v1/ping` | **500** | `InternalServerErrorException` | application/json | `{"message": "Internal server error"}` | ROUTED-BACKEND-ERROR |
| 37 | GET | `/prodous/dialog-lite/v1/dialog` | **500** | `InternalServerErrorException` | application/json | `{"message": "Internal server error"}` | ROUTED-BACKEND-ERROR |
| 38 | GET | `/prodous/dialog-lite/v1/mmm` | **500** | `InternalServerErrorException` | application/json | `{"message": "Internal server error"}` | ROUTED-BACKEND-ERROR |
| 39 | GET | `/prodous/dialog-lite/v1/insights/v1/gmi` | **500** | `InternalServerErrorException` | application/json | `{"message": "Internal server error"}` | ROUTED-BACKEND-ERROR |
| 77 | GET | `/prodous/dialog-lite/v1/` / hdrs: X-Api-Key: DUMMY-NOT-A-KEY-000000000000 | **500** | `InternalServerErrorException` | application/json | `{"message": "Internal server error"}` | ROUTED-BACKEND-ERROR |
| 82 | OPTIONS | `/prodous/dialog-lite/v1/` / hdrs: Origin: https://carelink.minimed.eu Access-Control-Request-Method: GET Access-Control-Request-Headers: content-type,x-api-key | **500** | `InternalServerErrorException` | application/json | `{"message": "Internal server error"}` | ROUTED-BACKEND-ERROR |

### dialog-lite US — `r5djbmetbb.execute-api.us-east-1.amazonaws.com`

| # | method | path | status | `x-amzn-errortype` | content-type | body head | verdict |
|---|---|---|---|---|---|---|---|
| 5 | GET | `/prod/dialog-lite/v1/` | **500** | `InternalServerErrorException` | application/json | `{"message": "Internal server error"}` | ROUTED-BACKEND-ERROR |
| 10 | GET | `/prod/dialog-lite/v1/9f3c1d7e-2b48-4a6c-8e51-0c7d9a2b41f6` | **500** | `InternalServerErrorException` | application/json | `{"message": "Internal server error"}` | ROUTED-BACKEND-ERROR |
| 15 | GET | `/prod/` | **403** | `MissingAuthenticationTokenException` | application/json | `{"message":"Missing Authentication Token"}` | NO-ROUTE |
| 20 | GET | `/prod/9f3c1d7e-2b48-4a6c-8e51-0c7d9a2b41f6` | **500** | `InternalServerErrorException` | application/json | `{"message": "Internal server error"}` | ROUTED-BACKEND-ERROR |
| 40 | GET | `/prod/dialog-lite/v1/insights` | **500** | `InternalServerErrorException` | application/json | `{"message": "Internal server error"}` | ROUTED-BACKEND-ERROR |
| 41 | GET | `/prod/dialog-lite/v1/gmi` | **500** | `InternalServerErrorException` | application/json | `{"message": "Internal server error"}` | ROUTED-BACKEND-ERROR |
| 42 | GET | `/prod/dialog-lite/v1/response` | **500** | `InternalServerErrorException` | application/json | `{"message": "Internal server error"}` | ROUTED-BACKEND-ERROR |
| 43 | GET | `/prod/dialog-lite/v1/recommendations` | **500** | `InternalServerErrorException` | application/json | `{"message": "Internal server error"}` | ROUTED-BACKEND-ERROR |
| 44 | GET | `/prod/dialog-lite/v1/settings` | **500** | `InternalServerErrorException` | application/json | `{"message": "Internal server error"}` | ROUTED-BACKEND-ERROR |
| 45 | GET | `/prod/dialog-lite/v1/user` | **500** | `InternalServerErrorException` | application/json | `{"message": "Internal server error"}` | ROUTED-BACKEND-ERROR |
| 46 | GET | `/prod/dialog-lite/v1/session` | **500** | `InternalServerErrorException` | application/json | `{"message": "Internal server error"}` | ROUTED-BACKEND-ERROR |
| 47 | GET | `/prod/dialog-lite/v1/config` | **500** | `InternalServerErrorException` | application/json | `{"message": "Internal server error"}` | ROUTED-BACKEND-ERROR |
| 48 | GET | `/prod/dialog-lite/v1/data` | **500** | `InternalServerErrorException` | application/json | `{"message": "Internal server error"}` | ROUTED-BACKEND-ERROR |
| 49 | GET | `/prod/dialog-lite/v1/status` | **500** | `InternalServerErrorException` | application/json | `{"message": "Internal server error"}` | ROUTED-BACKEND-ERROR |
| 50 | GET | `/prod/dialog-lite/v1/version` | **500** | `InternalServerErrorException` | application/json | `{"message": "Internal server error"}` | ROUTED-BACKEND-ERROR |
| 51 | GET | `/prod/dialog-lite/v1/health` | **500** | `InternalServerErrorException` | application/json | `{"message": "Internal server error"}` | ROUTED-BACKEND-ERROR |
| 52 | GET | `/prod/dialog-lite/v1/ping` | **500** | `InternalServerErrorException` | application/json | `{"message": "Internal server error"}` | ROUTED-BACKEND-ERROR |
| 53 | GET | `/prod/dialog-lite/v1/dialog` | **500** | `InternalServerErrorException` | application/json | `{"message": "Internal server error"}` | ROUTED-BACKEND-ERROR |
| 54 | GET | `/prod/dialog-lite/v1/mmm` | **500** | `InternalServerErrorException` | application/json | `{"message": "Internal server error"}` | ROUTED-BACKEND-ERROR |
| 55 | GET | `/prod/dialog-lite/v1/insights/v1/gmi` | **500** | `InternalServerErrorException` | application/json | `{"message": "Internal server error"}` | ROUTED-BACKEND-ERROR |
| 78 | GET | `/prod/dialog-lite/v1/` / hdrs: X-Api-Key: DUMMY-NOT-A-KEY-000000000000 | **500** | `InternalServerErrorException` | application/json | `{"message": "Internal server error"}` | ROUTED-BACKEND-ERROR |
| 83 | OPTIONS | `/prod/dialog-lite/v1/` / hdrs: Origin: https://carelink.minimed.eu Access-Control-Request-Method: GET Access-Control-Request-Headers: content-type,x-api-key | **500** | `InternalServerErrorException` | application/json | `{"message": "Internal server error"}` | ROUTED-BACKEND-ERROR |

### patient-timeline EU — `d4mwt26mmi.execute-api.eu-central-1.amazonaws.com`

| # | method | path | status | `x-amzn-errortype` | content-type | body head | verdict |
|---|---|---|---|---|---|---|---|
| 3 | GET | `/prod/patient-timeline/9f3c1d7e-2b48-4a6c-8e51-0c7d9a2b41f6` | **403** | `MissingAuthenticationTokenException` | application/json | `{"message":"Missing Authentication Token"}` | NO-ROUTE |
| 6 | GET | `/prod/patient-timeline/` | **403** | `MissingAuthenticationTokenException` | application/json | `{"message":"Missing Authentication Token"}` | NO-ROUTE |
| 16 | GET | `/prod/` | **403** | `MissingAuthenticationTokenException` | application/json | `{"message":"Missing Authentication Token"}` | NO-ROUTE |
| 21 | GET | `/prod/9f3c1d7e-2b48-4a6c-8e51-0c7d9a2b41f6` | **403** | `MissingAuthenticationTokenException` | application/json | `{"message":"Missing Authentication Token"}` | NO-ROUTE |
| 56 | GET | `/prod/patient-timeline/events` | **403** | `MissingAuthenticationTokenException` | application/json | `{"message":"Missing Authentication Token"}` | NO-ROUTE |
| 57 | GET | `/prod/patient-timeline/entries` | **403** | `MissingAuthenticationTokenException` | application/json | `{"message":"Missing Authentication Token"}` | NO-ROUTE |
| 58 | GET | `/prod/patient-timeline/items` | **403** | `MissingAuthenticationTokenException` | application/json | `{"message":"Missing Authentication Token"}` | NO-ROUTE |
| 59 | GET | `/prod/patient-timeline/list` | **403** | `MissingAuthenticationTokenException` | application/json | `{"message":"Missing Authentication Token"}` | NO-ROUTE |
| 60 | GET | `/prod/patient-timeline/query` | **403** | `MissingAuthenticationTokenException` | application/json | `{"message":"Missing Authentication Token"}` | NO-ROUTE |
| 61 | GET | `/prod/patient-timeline/range` | **403** | `MissingAuthenticationTokenException` | application/json | `{"message":"Missing Authentication Token"}` | NO-ROUTE |
| 62 | GET | `/prod/patient-timeline/params` | **403** | `MissingAuthenticationTokenException` | application/json | `{"message":"Missing Authentication Token"}` | NO-ROUTE |
| 79 | GET | `/prod/patient-timeline/` / hdrs: X-Api-Key: DUMMY-NOT-A-KEY-000000000000 | **403** | `MissingAuthenticationTokenException` | application/json | `{"message":"Missing Authentication Token"}` | NO-ROUTE |
| 84 | OPTIONS | `/prod/patient-timeline/` / hdrs: Origin: https://carelink.minimed.eu Access-Control-Request-Method: GET Access-Control-Request-Headers: content-type,x-api-key | **403** | `MissingAuthenticationTokenException` | application/json | `{"message":"Missing Authentication Token"}` | NO-ROUTE |

### patient-timeline US — `7r9xxd72kk.execute-api.us-east-1.amazonaws.com`

| # | method | path | status | `x-amzn-errortype` | content-type | body head | verdict |
|---|---|---|---|---|---|---|---|
| 7 | GET | `/prod/patient-timeline/` | **403** | `MissingAuthenticationTokenException` | application/json | `{"message":"Missing Authentication Token"}` | NO-ROUTE |
| 12 | GET | `/prod/patient-timeline/9f3c1d7e-2b48-4a6c-8e51-0c7d9a2b41f6` | **403** | `MissingAuthenticationTokenException` | application/json | `{"message":"Missing Authentication Token"}` | NO-ROUTE |
| 17 | GET | `/prod/` | **403** | `MissingAuthenticationTokenException` | application/json | `{"message":"Missing Authentication Token"}` | NO-ROUTE |
| 22 | GET | `/prod/9f3c1d7e-2b48-4a6c-8e51-0c7d9a2b41f6` | **403** | `MissingAuthenticationTokenException` | application/json | `{"message":"Missing Authentication Token"}` | NO-ROUTE |
| 63 | GET | `/prod/patient-timeline/events` | **403** | `MissingAuthenticationTokenException` | application/json | `{"message":"Missing Authentication Token"}` | NO-ROUTE |
| 64 | GET | `/prod/patient-timeline/entries` | **403** | `MissingAuthenticationTokenException` | application/json | `{"message":"Missing Authentication Token"}` | NO-ROUTE |
| 65 | GET | `/prod/patient-timeline/items` | **403** | `MissingAuthenticationTokenException` | application/json | `{"message":"Missing Authentication Token"}` | NO-ROUTE |
| 66 | GET | `/prod/patient-timeline/list` | **403** | `MissingAuthenticationTokenException` | application/json | `{"message":"Missing Authentication Token"}` | NO-ROUTE |
| 67 | GET | `/prod/patient-timeline/query` | **403** | `MissingAuthenticationTokenException` | application/json | `{"message":"Missing Authentication Token"}` | NO-ROUTE |
| 68 | GET | `/prod/patient-timeline/range` | **403** | `MissingAuthenticationTokenException` | application/json | `{"message":"Missing Authentication Token"}` | NO-ROUTE |
| 69 | GET | `/prod/patient-timeline/params` | **403** | `MissingAuthenticationTokenException` | application/json | `{"message":"Missing Authentication Token"}` | NO-ROUTE |
| 80 | GET | `/prod/patient-timeline/` / hdrs: X-Api-Key: DUMMY-NOT-A-KEY-000000000000 | **403** | `MissingAuthenticationTokenException` | application/json | `{"message":"Missing Authentication Token"}` | NO-ROUTE |
| 85 | OPTIONS | `/prod/patient-timeline/` / hdrs: Origin: https://carelink.minimed.eu Access-Control-Request-Method: GET Access-Control-Request-Headers: content-type,x-api-key | **403** | `MissingAuthenticationTokenException` | application/json | `{"message":"Missing Authentication Token"}` | NO-ROUTE |

### patient-timeline trials — `oflhmnvbe6.execute-api.us-east-1.amazonaws.com`

| # | method | path | status | `x-amzn-errortype` | content-type | body head | verdict |
|---|---|---|---|---|---|---|---|
| 8 | GET | `/prod/patient-timeline/` | **403** | `MissingAuthenticationTokenException` | application/json | `{"message":"Missing Authentication Token"}` | NO-ROUTE |
| 13 | GET | `/prod/patient-timeline/9f3c1d7e-2b48-4a6c-8e51-0c7d9a2b41f6` | **403** | `MissingAuthenticationTokenException` | application/json | `{"message":"Missing Authentication Token"}` | NO-ROUTE |
| 18 | GET | `/prod/` | **403** | `MissingAuthenticationTokenException` | application/json | `{"message":"Missing Authentication Token"}` | NO-ROUTE |
| 23 | GET | `/prod/9f3c1d7e-2b48-4a6c-8e51-0c7d9a2b41f6` | **403** | `MissingAuthenticationTokenException` | application/json | `{"message":"Missing Authentication Token"}` | NO-ROUTE |
| 70 | GET | `/prod/patient-timeline/events` | **403** | `MissingAuthenticationTokenException` | application/json | `{"message":"Missing Authentication Token"}` | NO-ROUTE |
| 71 | GET | `/prod/patient-timeline/entries` | **403** | `MissingAuthenticationTokenException` | application/json | `{"message":"Missing Authentication Token"}` | NO-ROUTE |
| 72 | GET | `/prod/patient-timeline/items` | **403** | `MissingAuthenticationTokenException` | application/json | `{"message":"Missing Authentication Token"}` | NO-ROUTE |
| 73 | GET | `/prod/patient-timeline/list` | **403** | `MissingAuthenticationTokenException` | application/json | `{"message":"Missing Authentication Token"}` | NO-ROUTE |
| 74 | GET | `/prod/patient-timeline/query` | **403** | `MissingAuthenticationTokenException` | application/json | `{"message":"Missing Authentication Token"}` | NO-ROUTE |
| 75 | GET | `/prod/patient-timeline/range` | **403** | `MissingAuthenticationTokenException` | application/json | `{"message":"Missing Authentication Token"}` | NO-ROUTE |
| 76 | GET | `/prod/patient-timeline/params` | **403** | `MissingAuthenticationTokenException` | application/json | `{"message":"Missing Authentication Token"}` | NO-ROUTE |
| 81 | GET | `/prod/patient-timeline/` / hdrs: X-Api-Key: DUMMY-NOT-A-KEY-000000000000 | **403** | `MissingAuthenticationTokenException` | application/json | `{"message":"Missing Authentication Token"}` | NO-ROUTE |
| 86 | OPTIONS | `/prod/patient-timeline/` / hdrs: Origin: https://carelink.minimed.eu Access-Control-Request-Method: GET Access-Control-Request-Headers: content-type,x-api-key | **403** | `MissingAuthenticationTokenException` | application/json | `{"message":"Missing Authentication Token"}` | NO-ROUTE |

---

## 11. Bottom line

**Zero new paths.** The oracle as hypothesised in the brief does not work —
a certainly-absent UUID returns the same `403 Missing Authentication Token` as
the published root, and no 404 is ever emitted, so 403 is an unmatched-route
error rather than an auth-gate and 404 is unreachable. The one useful discriminator
runs the other way: on dialog-lite, `500 InternalServerErrorException` proves a
path *is* matched, which reveals that both deployments are a single stage-wide
`ANY /{proxy+}` catch-all to a Lambda that throws on every request — including
the OPTIONS preflight, meaning no CORS is configured and the service cannot be
called from a browser at all.
