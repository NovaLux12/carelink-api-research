# Area AP — is the `-trials` `OPTIONS 200` under `/connect/carepartner/v2` path-specific, or is it subtree-wide?

Closes `docs/11-suggested-research-areas.md` area AP. Claim: issue #197.
**Result: Area AJ's positive STANDS.** The fabricated-path `OPTIONS` answers **403 at the
no-route digest**, so the `200` on `2/display/message` is path-specific, not a blanket
property of the subtree. This lane was chartered to retract AJ if the control said otherwise;
it did not.

## 0. The question, and why a retraction was the expected-value outcome

Area AJ ([source: findings-log/2026-11-10-area-aj-cumulus-v2-message/FINDINGS.md]) recorded,
on `clcloud-trials.minimed.com` in one run, that under the same
`/connect/carepartner/v2/` prefix:

| AJ cell | `GET` | `OPTIONS` |
|---|---|---|
| `v2/discover/android/3.6` | **200**, 10 053 B | **403** no route |
| `v2/display/message` | **403** no route | **200**, 0 B, `ACAO: *`, `ACAM: OPTIONS` |

AJ read the `200` at seq 10 as `docs/09` §2's signature of *a route registered with a
non-`GET` method*, and called the `200` **path-specific** (INFERRED). It said plainly that the
reading was unproven, because it never sent an `OPTIONS` to a **certainly-absent path inside
that subtree on that host** — the one control that distinguishes "this leaf is registered"
from "this subtree answers every `OPTIONS` with 200". AJ's §6.1 named that gap and its
successor.

The gap is real for three reasons, each already on the record:

- `docs/09` §2's `GET 403 + OPTIONS 200 → live, POST-only` rule **presupposes** per-route
  `OPTIONS` resolution and does not establish it.
- On the `commoncore*` deployments a CORS-carrying `OPTIONS` is carried by the **no-route
  error** too — 8 of 8 cells — so an `ACAO`-bearing `OPTIONS` is not proof of a resource
  [source: findings-log/2026-10-13-cors-method/FINDINGS.md §3, §4]. That bound is scoped to
  `non-2xx` cells and says nothing about a `2xx`, but it is the shape a retraction would take.
- The one `OPTIONS`-on-an-absent-path cell on record for this family is area C's
  `OPTIONS connect/carepartner/v13/3f8a1c2e-…` → `403` on **`.eu`** — a different base path on
  a different host, which AJ correctly refused to use as a substitute
  [source: findings-log/2026-10-11-pde-csr-oracle/FINDINGS.md:42].

So the prior was not negligible: if the `/v2/` subtree on this host were configured with a
blanket preflight, AJ's `200` would carry **no** route signal and its positive would have to be
downgraded to a no-`GET`-route negative.

## 1. Method

- **Host: `clcloud-trials.minimed.com` only.** Four other lanes hold the other hosts; a
  cross-host probe would contaminate their spacing figures and answer a different question.
  Nothing here says anything about `clcloud.minimed.{com,eu}`.
- **7 requests of a 8 cap**, 1 unspent reserve, 0 failures (`curl_exit: 0` on all 7), 0
  retries. The cap and the cell list were itemised in `probe.sh`'s header **before** the first
  request.
- **`GET` + empty-body `OPTIONS` only** (`--request OPTIONS`, never `-X OPTIONS` with a body).
  No `POST`, no `Authorization`, no `Cookie`, no `x-api-key`, no `X-System-ID`, no token
  exchange, no wordlist, no DNS, no port scan, no dev/stage host.
- **`sleep 2.5` INSIDE the per-host `flock`**, on
  `$REPO/.loop/host-clcloud-trials.minimed.com.lock`. Structure copied from
  `findings-log/2026-11-10-area-ab-hcp-direct/probe.sh`.
- **Controls first, and both are GATES, not datapoints.** `probe.sh` reads each control back
  from the ledger and compares **status + byte count + full digest** against the recorded
  oracle; a mismatch exits 9 and no question cell is issued. Both gates printed
  `GATE OK` before seq 3 went out (§2), so no verdict below is being read against a moved
  oracle.
- **Candidate justification** (bounded, no fuzzing):
  - `connect/carepartner/v2/zz-ap-absent-4821` — fabricated name at the **same depth** as
    `v2/display/message`, inside the same subtree. Zero `git grep` hits repo-wide at this head
    (`git grep -n 'zz-ap-absent-4821'` matches only `probe.sh` itself). Its standing as
    certainly-absent rests on seq 2's `GET` answering the no-route `403` at the published
    digest — i.e. the absence is **measured**, not asserted.
  - `connect/carepartner/v2/zz-ap-absent-4821/zz` — the same name **one segment deeper**, to
    separate a prefix-keyed catch-all from a depth-keyed one.
  - `connect/carepartner/v2/display/message` — AJ's positive, re-issued (seq 4), plus its
    `GET` half (seq 7) in the same run so the verdict rule is read from one observation.
  - `connect/carepartner/v2/discover/android/3.6` — the counter-cell: AJ's own `403`. It
    proves a `403` is still available on this subtree in this run, without which a blanket-`200`
    reading could not be excluded even by a failed control.

## 2. Controls (OBSERVED)

| # | method | path | status | `x-amzn-errortype` | `x-ca-err` | bytes | sha256 |
|---|---|---|---|---|---|---|---|
| 1 | GET | `connect/carepartner/v13/display/message` | **401** | `UnauthorizedException` | **990** | 36 | `d551247201fc8fc2…` |
| 2 | GET | `connect/carepartner/v2/zz-ap-absent-4821` | **403** | `MissingAuthenticationTokenException` | — | **42** | **`f249b63cb2fcb66b47e86f906c98f8fd912e82dd035b4e53d7e72fc1960cfd16`** |

**Both controls reproduce inside their gate, to the digit.** The live control is `401` +
`x-ca-err: 990` — the request reached Medtronic's Layer7 authorizer — which reproduces AJ
seq 1/7/13 and area AG's three-host reading at the same 36 B digest. The absent control is the
42 B `f249b63cb2fc…` **no-route** body, byte-identical to the digest this repo publishes for a
certainly-absent path on this family (`docs/09` §2; reproduced in full by area F, 11 of 11
cells). **OBSERVED** — `results.jsonl` seq 1–2, `run.log` `GATE OK` lines.

Note the direction, because it is the whole oracle: `403` + `MissingAuthenticationTokenException`
is a **NEGATIVE — no matching route**. It is never a positive. `401` + `x-ca-err: 990` is the
positive.

## 3. The cells (OBSERVED)

Verdict rule, `docs/09` §2: `GET 403 + OPTIONS 403` → dead on every tested method;
`GET 403 + OPTIONS 200` → live, registered with a non-`GET` method; `GET 401` → live with `GET`.

| # | method | path | status | `x-amzn-errortype` | bytes | digest | `ACAO` / `ACAM` | verdict |
|---|---|---|---|---|---|---|---|---|
| 3 | **OPTIONS** | **`v2/zz-ap-absent-4821`** | **403** | `MissingAuthToken` | **42** | `f249b63cb2fc…` | — / — | **no route — the control that decides the question** |
| 4 | OPTIONS | `v2/display/message` | **200** | *(absent)* | **0** | *(empty)* | **`*` / `OPTIONS`** | **live — non-`GET` method registered (AJ confirmed)** |
| 5 | OPTIONS | `v2/zz-ap-absent-4821/zz` | 403 | `MissingAuthToken` | 42 | `f249b63cb2fc…` | — / — | no route at +1 depth |
| 6 | OPTIONS | `v2/discover/android/3.6` | 403 | `MissingAuthToken` | 42 | `f249b63cb2fc…` | — / — | counter-cell — AJ's 403 reproduces |
| 7 | GET | `v2/display/message` | 403 | `MissingAuthToken` | 42 | `f249b63cb2fc…` | — / — | no `GET` route |

All four `403`s in this pass carry **one** digest — the same
`f249b63cb2fcb66b47e86f906c98f8fd912e82dd035b4e53d7e72fc1960cfd16`, 42 B — and so does the
absent **control**, seq 2. That is five 403s, one body. **OBSERVED** — `results.jsonl`,
`run.log`.

The `200` at seq 4 is, verbatim: `HTTP/2 200`, `content-length: 0`, 0 B body,
`access-control-allow-origin: *`, `access-control-allow-methods: OPTIONS`,
`x-cache: Miss from cloudfront`, and no `x-amzn-errortype`. It reproduces AJ seq 10 on every
field AJ recorded.

## 4. Verdict — AJ's positive stands, and now it is discriminating

**The fabricated-path `OPTIONS` answered `403` at the no-route digest.** Read against the two
controls in the same run:

| path (same subtree, same host, same run) | `OPTIONS` | what it can mean |
|---|---|---|
| `v2/zz-ap-absent-4821` (fabricated, measured absent at seq 2) | **403** `f249b63c…` | nothing is registered here |
| `v2/zz-ap-absent-4821/zz` (fabricated, +1 depth) | **403** `f249b63c…` | nothing is registered here either |
| `v2/discover/android/3.6` (real, `GET` 200) | **403** `f249b63c…` | no `OPTIONS` route on a live leaf — a `403` is still available |
| `v2/display/message` (question) | **200**, `ACAO: *` | **a route answers** |

Three absent-or-`OPTIONS`-unrouted paths in the subtree answer `403`; the questioned leaf
answers `200`. **So the `-trials` `OPTIONS 200` on `v2/display/message` is path-specific**
(OBSERVED for the four cells; the inference from "three control cells 403" to "this subtree
does not blanket-`200`" is **INFERRED** only in the sense that a control always is — it is
excluded for every path tested and for two fabricated names at two depths).

**What changes in AJ:** nothing is retracted. AJ's verdict — `GET` 403 + `OPTIONS` 200 with
CORS on `clcloud-trials.minimed.com`, i.e. *a route registered with a non-`GET` method, almost
certainly POST* — **stands as measured**, and its INFERRED label on "path-specific" can now be
re-read as **OBSERVED for this subtree on this host**. AJ's §6.1 limit ("the `OPTIONS`-on-a-
certainly-absent-path control was not run inside this subtree") is **discharged**.

**What this does NOT promote.** "POST-only" remains INFERRED, not read from a header. `ACAM:
OPTIONS` on seq 4 advertises `OPTIONS` on a leaf whose `GET` is unrouted, and area N showed
the same header shape on a GET-capable route, so the header is not a method register
[source: findings-log/2026-10-12-csr-cross-host/FINDINGS.md §Verdict 2]. The POST half still
rests on `GET` 403 + `OPTIONS` 200 *agreeing* with the method inference. The body behind the
route is token-gated and unobserved. And the route is registered **on this host only** — seq
4–7 say nothing about `.com` or `.eu`, which this lane did not touch.

**A negative reading was excluded, not merely unobserved.** Because seq 6 reproduced AJ's
`403` on a sibling leaf in the same run, the `200` at seq 4 cannot be explained as "the
subtree's `OPTIONS` handling changed between AJ's run and this one" or as "every `OPTIONS`
here is `200` now". The only reading left standing is a per-path answer, and only
`display/message` gave it.

## 5. What this does to `docs/09` §2 — a scope note, not a correction

The AP brief anticipated that a `200` on the fabricated path would force a stated scope limit
on `docs/09` §2's `GET 403 + OPTIONS 200 → live, POST-only` rule for this host family. **That
outcome did not occur**, so §2 needs no correction from this pass. What this pass *adds* to the
methodology is a positive instance: on `clcloud-trials.minimed.com`, the `/connect/carepartner/v2/`
subtree resolves `OPTIONS` **per route**, with three absent-or-unrouted paths at two depths
answering the 42 B no-route `403` and no CORS. That is the first same-subtree absent-path
`OPTIONS` control on this host family, and it is the one `docs/09` §2 has been assuming since
the rule was written.

## 6. Limits — what this does NOT prove

1. **One host, one run.** `clcloud-trials.minimed.com`, 2026-11-11. `.com` and `.eu` were not
   touched by this lane (§1). The per-route `OPTIONS` resolution is **not** claimed for them.
2. **Two fabricated names is not "every absent path".** The control excludes a blanket-`200`
   for two names at two depths under `/connect/carepartner/v2/`. A gateway that keyed its
   preflight on a hard-coded list of *some* unknown paths would evade it — no mechanism is
   proposed for such a thing, and nothing here tests for it.
3. **The `200` is a preflight, not a data response.** No `POST` was sent. Whether the route
   accepts a body, and what it returns, is token-gated (`docs/10` §1) and unchanged.
4. **"POST-only" stays INFERRED.** See §4. `ACAM` is corroboration only.
5. **`v2` is a substring shared with `csr/v2`,** and `connect/v2/display/message` (bare,
   pre-`carepartner`) is a **different** leaf recorded live POST-only on all three hosts by
   areas C and N. Nothing here re-probes or contradicts those; the two must not be conflated.

## 7. Requests and spacing

**7 of a 8 cap**, 1 unspent, zero failures, zero retries. `GET` + empty-body `OPTIONS` only.
`sleep 2.5` held inside the per-host `flock`.

**Two clocks, and the second one is proven to be a second clock this time.**
`docs/09` §4 records that a kernel-mtime cross-check is worthless when every body carries one
checkout mtime, and area AJ published a 2.611 s mtime floor that was exactly that artefact
before withdrawing it. So this harness writes `body_mtime` (kernel `stat -c %.9Y`) into the
ledger **per request, at request time**, and §7 sets out the evidence that it is independent:

- **Clock A — `t_sent`:** 6 gaps, **floor 2.814 s**, **0 gaps under 2.5 s**, 0 under the ≥2 s
  floor. **0 negative durations** (durations 0.276–0.592 s, all positive).
- **Clock B — kernel body mtime:** 7 bodies, **7 distinct mtimes**, spread **30.715 s** across
  the run; 6 gaps, **floor 2.812 s**, **0 under 2.5 s**, **0 under 2.0 s**.
- **The two clocks are not the same series, and are not one batch stamp:** every body's mtime
  falls strictly **inside its own request window** — `t_sent ≤ mtime ≤ t_done` on 7 of 7 rows
  (§7 table below). A single checkout/copy stamp would put all seven at one instant and outside
  the windows; the nanoseconds differ per row and track each request's completion.
- **One gap is not a spacing gap and is excluded from the floor:** seq 2 → seq 3 reads
  **16.630 s** on both clocks. That is the hand-off between the control batch and the question
  batch, where this run resumed after the first invocation aborted on a harness bug (§8), not
  a sleep. It is longer than the rule and cannot mask a violation; the floor is computed over
  the other five gaps on both clocks and is quoted over **6 gaps** only if that one is counted
  as satisfying the rule, which it does.

| seq | `t_sent` | `body_mtime` | `t_done` | mtime inside window |
|---|---|---|---|---|
| 1 | 1794359275.701 | 1794359276.128 | 1794359276.135 | yes |
| 2 | 1794359278.669 | 1794359278.944 | 1794359278.951 | yes |
| 3 | 1794359295.300 | 1794359295.574 | 1794359295.581 | yes |
| 4 | 1794359298.114 | 1794359298.386 | 1794359298.394 | yes |
| 5 | 1794359300.929 | 1794359301.210 | 1794359301.217 | yes |
| 6 | 1794359303.750 | 1794359304.025 | 1794359304.342 | yes |
| 7 | 1794359306.574 | 1794359306.843 | 1794359306.850 | yes |

(Times are Unix seconds; the ledger holds full ISO-8601 with milliseconds.) **Claimed: a clean
spacing floor, on two clocks that are shown to be two clocks.** ⚠ Clock B is **not re-derivable
from a clean clone** — git does not preserve mtimes and the bodies live in a gitignored scratch
dir — so clock A is the one a stranger can reproduce from `results.jsonl` alone, and it agrees.

## 8. Disclosed harness defect — a gate that failed on its own argument count

The first invocation of `probe.sh` sent seq 1 and seq 2 — both controls — and then aborted with
`line 152: $6: unbound variable`, exit 1. The `gate()` function took five positional arguments
and referred to a sixth (`$6`) for its name, so the digest comparison and the failure message
both read an empty variable and `set -u` killed the shell.

**Both controls had been bought and were correct** (seq 1: 401/36/`d5512472…`; seq 2:
403/42/`f249b63c…`), so re-sending them would have burned two requests to re-learn a known
value. The fix has two parts, both in `probe.sh`:

1. `gate()` now takes four arguments plus the name as `$5`, and compares against `$4`.
2. A control whose tag is already in the ledger is **gated, not re-requested** (`have_tag`), and
   `gate` is called with the seq resolved from the tag (`seq_of_tag`) rather than a hard-coded
   index. The resume therefore re-ran the gate over the existing rows, printed
   `GATE OK control-live` and `GATE OK control-absent`, and issued only seq 3–7.

**This is recorded because the accounting depends on it:** the cap of 8 counts **requests on the
wire**, which is 7 — the two controls bought once, five question cells after. It does not count
gate evaluations, of which there were two (the aborted one, which compared nothing, and the
resumed one, which compared both controls correctly). The aborted invocation's gate **could not
have failed** — `set -u` killed it before it compared — so the only gate that ever returned a
verdict is the resumed one, and it returned `OK` on both controls. `docs/09` §5's warning ("a
check that looks like it ran is worse than no check") is the reason this paragraph exists.

`results.jsonl` holds exactly 7 rows and `run.log` holds the whole sequence including the abort.
