# Area X — CORS separation, raw observations

Run date: 2026-10-12. Harness: `probe.sh` (unmodified, run once).
Corpus: `results.jsonl` (24 rows), request ledger: `run.log`, rendered table: `verdict.txt`.

This file records **only what came back off the wire**. It assigns no evidence
class, states no cause, and offers no explanation for any pattern below. Where a
value was absent, the word `absent` is written in place of the value.

---

## 1. Request accounting

- **25 of a 26 cap** — 24 from the harness, plus 1 hurl pin-validation request
  (see §7, and [`hurl-validation.txt`](hurl-validation.txt)). The harness's `CAP=26`
  guard refused nothing; request 24 was the last the harness issued and `run.log`
  ends `DONE n=24 (cap 26)`.
- `wc -l results.jsonl` = **25**. 24 header files + 24 body files were written by
  the harness. The 25th row was appended by hand in the same schema with `seq` 25,
  because hurl issued that request and does not write the ledger.
- All 24 requests were **GET** or **OPTIONS** with an empty body.
- No POST, no token exchange, no authentication. No `Authorization`, no `Cookie`,
  no `x-api-key` header was sent on any request. The only request headers the
  harness ever adds are `Origin` and `Access-Control-Request-Method`.
- The `Origin` literal used was `https://example.invalid` (RFC 2606 reserved). It
  was never resolved and is recorded here only as that literal string.
- Request 11 is an **OPTIONS** request that carries the header
  `Access-Control-Request-Method: POST`. The method on the wire is OPTIONS and
  the body is empty; the string `POST` appears only as a request-header value.

### Delay between requests

The harness's own stated spacing is **>=2.5 s between requests to the same host**
(`sleep 2.5` in `req()`). The repository rule it satisfies is `>=2s`.

Measured from the `run.log` timestamps (ISO-8601 with milliseconds, parsed with
`datetime`), the gap between the start of consecutive requests to the same host:

- same-host gaps measured: **21**
- gaps **>= 2.5 s**: **20**
- gaps **< 2.5 s**: **1**
- **single measured minimum same-host gap: 2.291 s** (`clcloud.minimed.eu`, between
  request 12 and request 13)
- maximum same-host gap: 8.550 s (`clcloud-trials.minimed.com`, before request 23)

**Stated plainly: one same-host gap in this run was 2.291 s, which is below the
harness's stated >=2.5 s and was not rounded away.** It remains above the
repository's `>=2s` floor. The other 20 gaps were between 2.613 s and 8.550 s.

The quantity measured is start-of-request to start-of-request. No cause for the
single sub-2.5 s gap is asserted here.

---

## 2. Control results

There are **7 control rows**, not 8. `results.jsonl` contains 7 rows whose `role`
begins with `CONTROL`, and `run.log` contains 7 lines carrying a `CONTROL` role.
Expectations are quoted from the comments in `probe.sh`.

| seq | host | method | path | status | x-amzn-errortype (token) | x-ca-err | expectation in probe.sh | result |
|---:|---|---|---|---:|---|---|---|---|
| 1 | `clcloud.minimed.eu` | GET | `connect/carepartner/v13/display/message` | 401 | `UnauthorizedException` | 990 | `CONTROL-live-token-gated` — the route is token-gated, so the answer is the authz error, not the no-route error | **PASS** |
| 2 | `clcloud.minimed.eu` | GET | `connect/carepartner/v13/3f8a1c2e-9b7d-4e5a-8c6b-1d2e3f4a5b6c` | 403 | `MissingAuthenticationTokenException` | absent | `CONTROL-dead-fabricated-uuid` — a fabricated UUID does not match a route | **PASS** |
| 3 | `clcloud.minimed.eu` | OPTIONS | `connect/carepartner/v99/display/message` | 403 | `MissingAuthenticationTokenException` | absent | `CONTROL-dead-preflight-fabricated-version` — a fabricated version does not match a route | **PASS** |
| 15 | `clcloud.minimed.com` | GET | `connect/carepartner/v13/display/message` | 401 | `UnauthorizedException` | 990 | `CONTROL-live-token-gated` — same shape as seq 1, included because a 403 cannot be believed on a host whose no-route signature is unshown | **PASS** |
| 16 | `clcloud.minimed.com` | GET | `connect/carepartner/v13/3f8a1c2e-9b7d-4e5a-8c6b-1d2e3f4a5b6c` | 403 | `MissingAuthenticationTokenException` | absent | `CONTROL-dead-fabricated-uuid` | **PASS** |
| 20 | `clcloud-trials.minimed.com` | GET | `connect/carepartner/v13/display/message` | 401 | `UnauthorizedException` | 990 | `CONTROL-live-token-gated` | **PASS** |
| 21 | `clcloud-trials.minimed.com` | GET | `connect/carepartner/v13/3f8a1c2e-9b7d-4e5a-8c6b-1d2e3f4a5b6c` | 403 | `MissingAuthenticationTokenException` | absent | `CONTROL-dead-fabricated-uuid` | **PASS** |

All 7 controls ran before any data row on their host, and all 7 reproduced the
signature their label names.

---

## 3. Every request, one table per host

`sent_headers` reads `none sent` when no request header was added, otherwise the
two headers the harness sent. `ACAO` is `access-control-allow-origin`. The family
column is the full set of `access-control-*` header names seen on the wire, any
case, unanchored.

### `clcloud.minimed.eu` — 14 requests

| seq | method | path | sent_headers | status | ACAO | access-control family seen |
|---:|---|---|---|---:|---|---|
| 1 | GET | `connect/carepartner/v13/display/message` | none sent | 401 | absent | absent |
| 2 | GET | `connect/carepartner/v13/3f8a1c2e-9b7d-4e5a-8c6b-1d2e3f4a5b6c` | none sent | 403 | absent | absent |
| 3 | OPTIONS | `connect/carepartner/v99/display/message` | none sent | 403 | absent | absent |
| 4 | GET | `connect/carepartner/v13/discover/android/3.6` | none sent | 200 | absent | absent |
| 5 | GET | `connect/carepartner/v13/discover/android/3.6` | Origin: https://example.invalid \| Access-Control-Request-Method: GET | 200 | absent | absent |
| 6 | GET | `connect/carepartner/v13/discover/android/3.6` | Origin: https://example.invalid \| Access-Control-Request-Method: GET | 200 | absent | absent |
| 7 | OPTIONS | `connect/carepartner/v13/discover/android/3.6` | none sent | 401 | absent | absent |
| 8 | OPTIONS | `connect/carepartner/v13/discover/android/3.6` | Origin: https://example.invalid \| Access-Control-Request-Method: GET | 401 | absent | absent |
| 9 | OPTIONS | `connect/carepartner/v13/display/message` | none sent | 200 | `*` | access-control-allow-origin, access-control-allow-methods, access-control-allow-headers |
| 10 | OPTIONS | `connect/carepartner/v13/display/message` | Origin: https://example.invalid \| Access-Control-Request-Method: GET | 200 | `*` | access-control-allow-origin, access-control-allow-methods, access-control-allow-headers |
| 11 | OPTIONS | `connect/carepartner/v13/display/message` | Origin: https://example.invalid \| Access-Control-Request-Method: POST | 200 | `*` | access-control-allow-origin, access-control-allow-methods, access-control-allow-headers |
| 12 | GET | `connect/carepartner/v13/display/message` | Origin: https://example.invalid \| Access-Control-Request-Method: GET | 401 | absent | absent |
| 13 | GET | `connect/carepartner/v11/discover/android/3.6` | none sent | 200 | absent | absent |
| 14 | GET | `connect/carepartner/v11/discover/android/3.6` | Origin: https://example.invalid \| Access-Control-Request-Method: GET | 200 | absent | absent |

### `clcloud.minimed.com` — 5 requests

| seq | method | path | sent_headers | status | ACAO | access-control family seen |
|---:|---|---|---|---:|---|---|
| 15 | GET | `connect/carepartner/v13/display/message` | none sent | 401 | absent | absent |
| 16 | GET | `connect/carepartner/v13/3f8a1c2e-9b7d-4e5a-8c6b-1d2e3f4a5b6c` | none sent | 403 | absent | absent |
| 17 | GET | `connect/carepartner/v13/discover/android/3.6` | none sent | 200 | absent | absent |
| 18 | GET | `connect/carepartner/v13/discover/android/3.6` | Origin: https://example.invalid \| Access-Control-Request-Method: GET | 200 | absent | absent |
| 19 | OPTIONS | `connect/carepartner/v13/discover/android/3.6` | none sent | 401 | absent | absent |

### `clcloud-trials.minimed.com` — 5 requests

| seq | method | path | sent_headers | status | ACAO | access-control family seen |
|---:|---|---|---|---:|---|---|
| 20 | GET | `connect/carepartner/v13/display/message` | none sent | 401 | absent | absent |
| 21 | GET | `connect/carepartner/v13/3f8a1c2e-9b7d-4e5a-8c6b-1d2e3f4a5b6c` | none sent | 403 | absent | absent |
| 22 | GET | `connect/carepartner/v13/discover/android/3.6` | none sent | 200 | absent | absent |
| 23 | GET | `connect/carepartner/v13/discover/android/3.6` | Origin: https://example.invalid \| Access-Control-Request-Method: GET | 200 | absent | absent |
| 24 | OPTIONS | `connect/carepartner/v13/discover/android/3.6` | none sent | 401 | absent | absent |

### The full `access-control-*` values on the three rows that carried any

Only seq 9, 10 and 11 sent any header from this family. On all three the values
were identical:

| header | value on seq 9, 10, 11 |
|---|---|
| `access-control-allow-origin` | `*` |
| `access-control-allow-methods` | `OPTIONS` |
| `access-control-allow-headers` | `Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token` |
| `access-control-allow-credentials` | absent |
| `access-control-max-age` | absent |
| `vary` | absent |

All three returned `content-type: application/json`, `content-length: 0`, and a
zero-byte body. On all three the value of `access-control-allow-methods` was the
literal `OPTIONS`, including seq 10 and seq 11, which were sent with an
`Origin` and an `Access-Control-Request-Method` header.

---

## 4. Every row whose status is 200, and whether it carried ACAO

12 rows returned `200`. Grouped by whether an `Origin` was sent on that request:

**Origin NOT sent — 5 rows**

| seq | host | method | path | ACAO |
|---:|---|---|---|---|
| 4 | `clcloud.minimed.eu` | GET | `connect/carepartner/v13/discover/android/3.6` | absent |
| 9 | `clcloud.minimed.eu` | OPTIONS | `connect/carepartner/v13/display/message` | `*` |
| 13 | `clcloud.minimed.eu` | GET | `connect/carepartner/v11/discover/android/3.6` | absent |
| 17 | `clcloud.minimed.com` | GET | `connect/carepartner/v13/discover/android/3.6` | absent |
| 22 | `clcloud-trials.minimed.com` | GET | `connect/carepartner/v13/discover/android/3.6` | absent |

**Origin SENT — 7 rows**

| seq | host | method | path | ACAO |
|---:|---|---|---|---|
| 5 | `clcloud.minimed.eu` | GET | `connect/carepartner/v13/discover/android/3.6` | absent |
| 6 | `clcloud.minimed.eu` | GET | `connect/carepartner/v13/discover/android/3.6` | absent |
| 10 | `clcloud.minimed.eu` | OPTIONS | `connect/carepartner/v13/display/message` | `*` |
| 11 | `clcloud.minimed.eu` | OPTIONS | `connect/carepartner/v13/display/message` | `*` |
| 14 | `clcloud.minimed.eu` | GET | `connect/carepartner/v11/discover/android/3.6` | absent |
| 18 | `clcloud.minimed.com` | GET | `connect/carepartner/v13/discover/android/3.6` | absent |
| 23 | `clcloud-trials.minimed.com` | GET | `connect/carepartner/v13/discover/android/3.6` | absent |

Of the 12 rows that returned 200, **3 carried ACAO and 9 did not**. The 3 that
carried it were all OPTIONS on `clcloud.minimed.eu`. The 9 that did not were all
GET requests for a `discover` payload.

**Rows where ACAO and status 200 disagree: 9**, all of the form *200 with no
ACAO* — seq 4, 5, 6, 13, 14, 17, 18, 22, 23. Every one is a GET for a `discover`
payload. **No row returned a non-200 status while carrying ACAO**: the three rows
carrying ACAO all returned 200.

---

## 5. Body digests, grouped

The all-zero digest `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
is the digest of an empty body. It is recorded here as an empty-body marker, not
as a shared body value.

| body sha256 | bytes | count | seq | hosts |
|---|---:|---:|---|---|
| `e3b0c442…b855` (empty-body marker) | 0 | 3 | 9, 10, 11 | `clcloud.minimed.eu` |
| `d551247201fc8fc27dee1ae62538455ea04258855f1880443176930399875a7a` | 36 | 8 | 1, 7, 8, 12, 15, 19, 20, 24 | all three |
| `f84886265667b1b685ad0d362793c0478354f2ec30d7c81e30a52ca86a3b1609` | 20256 | 7 | 4, 5, 6, 17, 18, 22, 23 | all three |
| `f249b63cb2fcb66b47e86f906c98f8fd912e82dd035b4e53d7e72fc1960cfd16` | 42 | 4 | 2, 3, 16, 21 | all three |
| `94b739dda4784c7b49564cc059b6760b24d60822e87d34a0d3dfa676a6420615` | 20345 | 2 | 13, 14 | `clcloud.minimed.eu` |

Counts sum to 24. The 36-byte, 42-byte and 20256-byte bodies each returned a
byte-identical payload on all three hosts. The 20345-byte body appeared only on
`clcloud.minimed.eu`.

---

## 6. Transport health

- `curl_exit` was **0 on all 24 harness rows**. Rows with a non-zero exit: 0.
- Every `http_status` resolved to a digit string. Rows with no response head: 0.
- **Zero empty header files** and zero empty body files across all 24 header and
  24 body files. No request needed the harness's transport-failure fallback.
- No digest was the empty string.

There is no transport failure to report in this run. The 25th request (§7) was not
issued by curl; its transport result is hurl's, recorded on its row.

---

## 7. The 25th request — hurl validation of the two new assertions

**Recorded here so the ledger and this file agree.** The harness issued 24; one
further request was issued by `hurl 8.0.1 --test` to execute two assertions added
to `regression/hurl/01-discovery-pin.hurl` before they were committed, because this
repo records shipping an unexecuted assertion as a defect.

| # | host | method | path | issued by | status | ACAO | acam |
|---:|---|---|---|---|---:|---|---|
| 25 | `clcloud.minimed.eu` | GET | `connect/carepartner/v13/discover/android/3.6` | hurl 8.0.1 (not curl) | 200 | **absent** | **absent** |

That is the **10th** row of the form *200 with no ACAO*, and the third of them to
be produced by a tool other than `probe.sh` — an independent confirmation of the
same cell by a second harness, not a re-count of one measurement.

Verbatim command, output, exit code and the exact limits of what the two predicates
prove are in [`hurl-validation.txt`](hurl-validation.txt). One request, not three:
a single-cell harness was used so validation could not push the pass over its cap.

**This section states no cause.** What the 25 rows establish is recorded as
observations in §4; the reading of them belongs in `docs/`, and the limits of that
reading are stated there rather than here.