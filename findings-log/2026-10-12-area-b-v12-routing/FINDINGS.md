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
- **Plus 4 further requests, to 21 of 24**, re-issued through `hurl 8.0.1 --test` to
  validate the four new assertions added to `regression/hurl/04-deep-surface.hurl` before
  they were committed. These are **re-probes of cells already counted above** (seq 14, 17,
  8, 9) — they produce no new evidence, only a check that the pin syntax passes. Output:
  `Success ... (4 request(s) in 8665 ms) / Executed requests: 4`, `Failed files: 0`,
  exit 0.
- **Plus 1 further request, to 22 of 24**, re-validating the `discover` pin after review
  added `access-control-allow-origin not exists` + `access-control-allow-methods not
  exists` to it. Those two assertions had never been executed, and shipping an unexecuted
  assertion is a failure this repo keeps recording, so the changed cell was re-run rather
  than trusted: `Success ... (1 request(s) in 2075 ms)`, `Failed files: 0`, exit 0.
- **22 of a 24 cap in total.** GET + OPTIONS with empty bodies only; no POST, no token
  exchange, no authentication, no auth headers.
- **Spacing.** The harness declares `sleep 2.5` between requests to the same host. Of the
  **14 same-host gaps** in `run.log`, **13 are ≥2.5 s** and one (`eu` → request 7) is
  **2.033 s**, which is below both the harness's own 2.5 s and arithmetically below what
  the committed harness can produce — see §"The one spacing anomaly" below. The measured
  floor is **2.033 s**, which satisfies the repo's own floor (`AGENTS.md` §8, ≥2 s between
  requests to the same host). *(Corrected 2026-10-12 after review: an earlier draft of this
  file said "15 of 16 same-host gaps". There are 14 same-host gaps, not 16 — 16 is the count
  of all gaps including the two cross-host transitions.)*
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

## Finding 3 — the two route families differ observably in their CORS headers — **but the cause is confounded**

**OBSERVED, a clean 3 × 2 on `clcloud.minimed.eu`.**

| route | `v11` | `v12` | `v13` |
|---|---|---|---|
| `…/display/message` OPTIONS | 200, `acao: *` | 200, `acao: *` | 200, `acao: *` |
| `…/discover/android/3.6` OPTIONS | **401**, `x-ca-err: 990`, **no `Access-Control-*`** | **401**, `990`, none | **401**, `990`, none |

So **"the gateway adds CORS to `clcloud.*`" is false as a rule** — the same host, the same
method, the same session, one path-family apart, differ. That much is OBSERVED and it is
what the new pins in `04-deep-surface.hurl` guard.

**What these 6 cells do NOT establish — corrected after review.** An earlier draft of this
file concluded "preflight configuration is a per-route property". **That over-claims, and the
claim is withdrawn.** Across **all 101 captured response heads in `findings-log/`**, exactly
**14** carry `access-control-allow-origin` and **every one of the 14 is a `200`**; **zero
non-2xx responses anywhere in the corpus carry it** (the 10 CORS-less `200`s are document
fetches on a different host surface — `disc-*`, `config-*`, `countries-*`). On `clcloud.*`,
therefore, **"carries a preflight" and "answers 200" are the same observation in this
corpus**.

The consequence: `discover/android/3.6` answering `401` with no CORS headers does **not**
show that the route has no preflight configured. It is equally consistent with the route
demanding a token on `OPTIONS`, given that no non-2xx response in the corpus carries CORS
headers. **These two readings are not separated by any cell on disk**, and the observation
must not be stated as the cause. It is recorded as an observation.

Note also that `verdict.py` prints the `discover` `OPTIONS` cells as `LIVE - token-gated` —
the same verdict it gives the `display/message` GETs — which is the honest reading and is
in mild tension with any "this route has no preflight" phrasing. `verdict.txt` is the
authority on the verdict; this section is the authority on its limits.

**What would settle it:** one `OPTIONS` on a `clcloud.*` route returning **`200` without**
`access-control-allow-origin`, or **`401` with** it. Neither exists on disk. That is
successor area X.

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
- **Why the two route families differ in their CORS headers.** See Finding 3 — confounded
  with status code in this corpus, and not separated by any cell on disk.
- **`v12` outside the three hosts**, and any `v14`+ behaviour, were not probed and are not
  claimed.
- The `x-ca-err: 990` reading follows `docs/09` §2: `990` distinguishes "reached the Layer7
  authorizer" from any other 401. The mechanism behind `990` itself is **not** established
  (INFERRED from the header's behaviour, n = 10 responses).

## Correction (2026-10-12, after independent review)

Five defects were raised by a fresh-context verifier that did not watch this pass being
built. All five are fixed here; the retraction history is kept rather than edited away.

| # | Defect | Disposition |
|---|---|---|
| 1 | The `discover` pin asserted only `401` + `x-ca-err: 990`, never the **absence** of `Access-Control-*`, so the structural claim could rot silently | **Fixed.** Added `access-control-allow-origin not exists` + `access-control-allow-methods not exists`. A one-directional pin is a restatement, not a guard |
| 2 | "Preflight presence is a per-route property" **over-claimed** — confounded with `status == 200` across all 101 captured heads | **Claim withdrawn.** Finding 3 rewritten as an observation with the confound stated. The rule it falsified ("the gateway adds CORS uniformly") survives |
| 3 | The 2.033 s gap was described as an "open discrepancy"; it is arithmetically impossible under the committed harness | **Re-characterised** as a provenance problem with a clock-step explanation derived from the cancelling errors. Cause still not proven; stated as far as the evidence goes |
| 4 | "15 of 16 same-host gaps" — there are **14** same-host gaps (16 counts all gaps incl. 2 cross-host) | **Fixed.** Corrected in place with the miscount named |
| 5 | The 4 hurl pin-validation requests appeared only in the PR body, not in the log, so "21 of 24" was unsourced | **Fixed.** Now recorded in the Method section with hurl's own output; a 5th request re-validated the changed `discover` cell, making it 22 of 24 |

## The one spacing anomaly — a clock artefact, established to the limit the evidence allows

`eu` → request 7 records a **2.033 s** gap where every other same-host gap is 2.6–3.6 s.
That is **below the `sleep 2.5`** the committed harness ends every `req()` with, and it is
therefore **arithmetically impossible for the committed harness to have produced both
timestamps**.

Three facts, all checkable:

1. **The committed harness is the one that ran.** `probe.sh` mtime `15:14:44`, first request
   `15:14:48`, no later write. So the harness was not edited after the run.
2. **The harness cannot emit a sub-2.5 s gap.** `ts` is captured at `probe.sh:66`, `curl`
   runs at `:69`, and `sleep 2.5` is `:138` — the last statement in `req()`, with no
   conditional path. So `gap(ts_i, ts_{i+1}) = curl + processing + 2.500 ≥ 2.500`.
3. **The anomaly cancels against its neighbour.** Gap `5→6` is `3.208 s` (**+0.582** above
   the 2.627 s median same-host gap) and gap `6→7` is `2.033 s` (**−0.594**). The pair sums
   to **5.241 s** against a two-gap nominal of **5.253 s** — a 12 ms difference.

**INFERRED**, from those three: the two timestamps are not both faithful, and the most
economical explanation is a **transient backwards step of the local clock** between the two
`date` calls, because the error appears and then cancels — no request time was actually
lost. That is the signature of an NTP correction, not of a short or skipped `sleep`.

**The alternative is not excluded.** That `run.log` was altered after the fact would
produce the same arithmetic, and the mtime evidence rules out a later edit to `probe.sh`
but says nothing about `run.log`. **The pass does not claim to know which**, only that the
harness and the log cannot both be exactly right. Either way the **measured floor stands at
2.033 s**, the repo's ≥2 s floor is met, and **21 of 24 requests is unaffected**.

## Reproduction

```bash
bash findings-log/2026-10-12-area-b-v12-routing/probe.sh   # refuses to run twice
python3 findings-log/2026-10-12-area-b-v12-routing/verdict.py \
        findings-log/2026-10-12-area-b-v12-routing/results.jsonl
```