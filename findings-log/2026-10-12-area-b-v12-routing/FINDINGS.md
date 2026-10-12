# Area B — the `v11`/`v12`/`v13` routing picture under `/connect/carepartner`

**Claimed in #4. Run 2026-10-12. Area closed.** 17 of a 24 cap.

- **Method:** GET and OPTIONS with an **empty body**. No POST, no token exchange, no
  authentication, and **no auth-ish headers at all** — no `Authorization`, no `Cookie`, no
  `x-api-key`, not even a dummy. No port scanning, no DNS brute force, no wordlist, no new
  host, no dev/stage host.
- **17 of a 24 cap**: 11 on `clcloud.minimed.eu`, 3 on `clcloud.minimed.com`, 3 on
  `clcloud-trials.minimed.com`. Every candidate path was already recorded on disk by an
  earlier pass, plus one fabricated control and one fabricated version (`v99`) used only as
  controls.
- **Spacing.** The harness declares `sleep 2.5` between requests to the same host, and **15
  of 16 same-host gaps met it**. The measured floor from the client-side `run.log`
  timestamps is **2.033 s**, on one gap (`eu` → request 7). That satisfies the repo's own
  floor (`AGENTS.md` §8, ≥2 s between requests to the same host) and misses the harness's
  stricter self-declared 2.5 s. **The cause is not established** — `sleep 2.5` is the last
  statement in `req()` with no conditional path around it, and the timestamps are
  client-side `date -u` values taken before `curl`, so the Area U pass's explanation
  (CloudFront PoP clock skew) does not apply to this measurement. Recorded as an open
  discrepancy rather than explained away. **Measured floor: 2.033 s.**
- **Harness:** `probe.sh` — same HTTP discipline as
  [`../2026-10-12-pde-csr-cross-host/probe.sh`](../2026-10-12-pde-csr-cross-host/probe.sh).
  Machine log `run.log`, per-request record `results.jsonl`, every response head in
  `headers/`, verdict derivation `verdict.py` → `verdict.txt`. The harness refuses to run
  twice if `results.jsonl`/`run.log` exist, so the count cannot silently double, and it
  records **`curl_exit` per request** (the Area U harness did not) plus the **sha256 of
  every body**, so a transport failure can never be read as a vendor answer. All 17
  requests returned `curl_exit=0`.
- **Discriminator:** `x-amzn-errortype`, **never the status code**. On `clcloud.*` 403 is
  the *no-matching-route* error and a 404 is never emitted at all
  ([`docs/09`](../../docs/09-methodology-and-oracles.md) §2).

## The controls ran first on every host, and all eight passed

The data cells are only believable because the oracle reproduced **before** the data was
collected — otherwise the cells would be judged by a verdict established from the data they
exist to test. Verbatim from `results.jsonl` / `verdict.txt`:

| # | host | control | status | `x-amzn-errortype` | `x-ca-err` | `acao` |
|---|---|---|---|---|---|---|
| 1 | eu | GET `v13/display/message` | 401 | `UnauthorizedException` | `990` | (none) |
| 2 | eu | GET `v13/3f8a1c2e-…-1d2e3f4a5b6c` (fabricated) | 403 | `MissingAuthenticationTokenException` | (none) | (none) |
| 3 | eu | OPTIONS `v13/display/message` | 200 | (none) | (none) | `*` |
| 4 | eu | OPTIONS `v99/display/message` (fabricated) | 403 | `MissingAuthenticationTokenException` | (none) | (none) |
| 12 | com | GET `v13/display/message` | 401 | `UnauthorizedException` | `990` | (none) |
| 13 | com | GET `v13/3f8a1c2e-…` (fabricated) | 403 | `MissingAuthenticationTokenException` | (none) | (none) |
| 15 | trials | GET `v13/display/message` | 401 | `UnauthorizedException` | `990` | (none) |
| 16 | trials | GET `v13/3f8a1c2e-…` (fabricated) | 403 | `MissingAuthenticationTokenException` | (none) | (none) |

Controls 2/13/16 matter more than usual here, and the claim in #4 under-provisioned them:
it paired only a *live* control on `.com`/`-trials`. **The most likely finding in this area
was a negative** (a 403 on `.com`/`-trials` that would have split `v12` by region), and a
403 cannot be believed as "no route" on a host whose own no-route signature has not been
demonstrated. Both halves were therefore run on both hosts.

## Finding 1 — `v12/display/message` is 401 on all three hosts. The existing claim was right.

**OBSERVED, 3 hosts of 3.** `docs/03-discovery-and-versions.md` §6 and
`docs/06-patient-api-surface.md` both assert that `v12/display/message` is "401 on all three
hosts", and the only raw row behind that claim was row 52 of
`findings-log/probe-2026-10-08/recon/ORACLE-PROBE-MATRIX.md` — **`clcloud.minimed.eu`
only** (`AGENTS.md` §6 item 1: a claim stated without evidence). This pass supplies the
missing two rows. **The claim is confirmed, not corrected.**

| host | seq | status | `x-amzn-errortype` | `x-ca-err` | body |
|---|---|---|---|---|---|
| `clcloud.minimed.eu` | 6 | 401 | `UnauthorizedException` | `990` | `{"message":"Authentication failure"}` |
| `clcloud.minimed.com` | 14 | 401 | `UnauthorizedException` | `990` | same digest |
| `clcloud-trials.minimed.com` | 17 | 401 | `UnauthorizedException` | `990` | same digest |

Every one is `UnauthorizedException` + `x-ca-err: 990` — the request reached Medtronic's
Layer7 authorizer, i.e. the route exists and is token-gated. **There is no region split on
this cell.**

## Finding 2 — `v12` *does* carry a CORS preflight, exactly like `v13`. The area's question is answered "no difference".

**OBSERVED.** The area asked whether `v12` has an OPTIONS route where `v13` does not. **It
does not differ** — `v11`, `v12` and `v13` are identical on this axis, all three answering
`200` with `access-control-allow-origin: *`,
`access-control-allow-methods: OPTIONS`, and the same `allow-headers` list.

| path (`.eu`) | seq | status | `x-amzn-errortype` | `acao` | `acam` |
|---|---|---|---|---|---|
| `v11/display/message` OPTIONS | 7 | 200 | (none) | `*` | `OPTIONS` |
| `v12/display/message` OPTIONS | 8 | 200 | (none) | `*` | `OPTIONS` |
| `v13/display/message` OPTIONS | 3 | 200 | (none) | `*` | `OPTIONS` |

`docs/06` §"display/message, version axis" carries **`OPTIONS` = "not probed"** for `v11`,
`v12` **and** `v13`. All three are now probed; all three answer `200` with CORS.

**What this does *not* say.** `access-control-allow-methods` is **not** a register of a
route's methods — the repo has a recorded correction on exactly that mistake, from
`v13/display/message` advertising `OPTIONS` on a route that is GET-capable
([`docs/09`](../../docs/09-methodology-and-oracles.md) §2, trap table). Method registration
is settled by the **GET** probe (the `401` + `990` above), and the header is corroboration
only. And a passing preflight does **not** make the route browser-callable: the `401`
response itself carries **no `Access-Control-*` header at all**, which is the recorded
`MissingAllowOriginHeader` failure
([`docs/10`](../../docs/10-open-questions.md) §1). That open question is untouched by this
pass.

## Finding 3 — CORS preflight presence is decided per **route**, not per version or host

**OBSERVED, a clean 3 × 2 on `clcloud.minimed.eu`.** This is the pass's real structural
result. `display/message` carries a CORS preflight at every version; `discover/android/3.6`
carries none at any version.

| route | `v11` | `v12` | `v13` |
|---|---|---|---|
| `…/display/message` OPTIONS | 200, `acao: *` | 200, `acao: *` | 200, `acao: *` |
| `…/discover/android/3.6` OPTIONS | **401**, `x-ca-err: 990`, **no `Access-Control-*`** | **401**, `990`, none | **401**, `990`, none |

So "the gateway adds CORS to `clcloud.*`" is **false as a rule**: the same host, the same
method, the same session, one path apart, differ. Preflight configuration is a per-route
property. (INFERRED, and only as far as these 6 cells go: nothing on disk states the rule,
and n = 6 is one host and two route families. The successor area below exists because of
this.)

## Finding 4 — the response bodies collapse to two artefacts, and one digest cross-confirms an earlier pass

**OBSERVED.** Across 17 responses there are only **two** non-empty body digests plus the
empty string:

- `sha256:d5512472…` — 36 B, **10 bodies**: every `401` in the pass, across `v11`, `v12`
  and `v13`, across `display/message` **and** `discover/android/3.6`, on **all three hosts**
  (seq 1, 5, 6, 9, 10, 11, 12, 14, 15, 17). The auth failure is byte-identical everywhere.
- `sha256:f249b63c…` — 42 B, **4 bodies**: every no-route `403` (seq 2, 4, 13, 16).

The `42 B / sha256:f249b63cb2fc` digest **independently reproduces** the no-route artefact
digest recorded by the Area U pass on the two other hosts
([`../2026-10-12-pde-csr-cross-host/FINDINGS.md`](../2026-10-12-pde-csr-cross-host/FINDINGS.md);
also `docs/10` §2). Two passes, different hosts, same digest: the router's no-route
response is **one artefact shared across the three cumulus hosts**, and this pass's
controls on all three agree with it.

`verdict.py` asserts the resolved body type **before** hashing, and treats an all-zero
digest as a failure rather than a comparison — the defence against `AGENTS.md` §6 item 3,
where hashing a silently-`null` lookup manufactured consensus.

## `x-ca-err` does not vary by version

**OBSERVED.** Every `401` in the pass carries `x-ca-err: 990` — `v11`, `v12`, `v13`,
`display/message`, `discover/android/3.6`, all three hosts. There is **no version-specific
error code** to distinguish these routes. Read from this pass's captured headers only, not
from older captures on a different date.

## What this pass does NOT settle

- **Response bodies remain unreadable.** Every live cell is token-gated; the comparison of
  what `v11`/`v12`/`v13` actually return stays in `docs/10` §1.
- **Browser callability is still open, in both directions.** See Finding 2's caveat.
- **`v12` outside the three hosts**, and any `v14`+ behaviour, were not probed and are not
  claimed.
- The `x-ca-err: 990` reading follows `docs/09` §2: `990` distinguishes "reached the Layer7
  authorizer" from any other 401. The mechanism behind `990` itself is **not** established
  (INFERRED from the header's behaviour, n = 10 responses).

## Reproduction

```bash
bash findings-log/2026-10-12-area-b-v12-routing/probe.sh   # refuses to run twice
python3 findings-log/2026-10-12-area-b-v12-routing/verdict.py \
        findings-log/2026-10-12-area-b-v12-routing/results.jsonl
```