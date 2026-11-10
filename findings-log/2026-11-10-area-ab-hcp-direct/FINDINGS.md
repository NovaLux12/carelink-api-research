# The six direct `/hcp/configuration/*` verdicts are **deployment-portable** — 6 of 6, on three deployments, with the same 48-byte gate body on all nine 401 cells

**Date:** 2026-11-10 · **Claim issue:** [#162](https://github.com/NovaLux12/carelink-api-research/issues/162) ·
**Branch:** `research/ab-hcp-direct` · **Area:** AB ·
**Hosts swept:** `carelink.medtronic.com`, `carelink.medtronic.eu`, `carelink-support.medtronic.com` ·
**Host used as the recorded baseline, not re-swept:** `carelinkhp.minimed.eu`

Legend, per `AGENTS.md` §2 — **OBSERVED** = seen in a live response · **PUBLISHED** =
in a vendor document served without a login · **INFERRED** = reasoned, not seen.

## Cap accounting

**43 of a 43 cap.** The cap is a single assignment in `probe.sh` (`CAP=43`) and its
itemisation is the cap — nothing below is slack:

| item | cells | ledger seq |
|---|---:|---|
| 6 candidates x 3 swept hosts | 18 | 9–14, 22–27, 35–40 |
| 4 controls x 3 swept hosts | 12 | 5–8, 18–21, 31–34 |
| empty-body `OPTIONS` on the 3 POST-only routes x 3 swept hosts | 9 | 15–17, 28–30, 41–43 |
| corpus-control re-assertion of the four build digests, **one per host** | 4 | 1–4 |
| **total** | **43** | |

`wc -l results.jsonl` = **43**, all 43 with `curl_exit: 0`. **No request overran, no
retry was needed, and no ledger row was deleted, reordered or edited.** No `gate-suite`
rows are absorbed into this ledger: the repository's own pinned suite is a separate
traffic class and this pass does not count it as research (the position lane l2 argued
for and this lane adopts without re-litigating).

**Disclosed, because it is vendor traffic and must not be invisible:** the repository's own
pinned suite (`regression/hurl/05-public-config.check.sh`) issues **13 vendor requests on
every gate invocation**, and this pass invoked the gate once per correction cycle — the
first run went red on a hygiene regex because no delay figure appeared in the shape the
parser reads, and each subsequent red→green cycle cost one more run. **This section
therefore gives the rate and not a total, on purpose:** a total would be wrong the moment
the next correction forces another run, which is the failure `AGENTS.md` §6 item 7
describes — a figure that moves while you edit it. The two fixed, checkable facts are
**13 requests per invocation** and **0 gate rows in `results.jsonl`**: gate traffic is
CI-mandated infrastructure, not research, and it is **not** counted against the 43.

**The cap is 43 and the sweep is three hosts, not four — the difference is the
arithmetic, stated before any sweep request went out** (`plan.md` §Which three hosts).
`carelinkhp.minimed.eu` carries the *recorded* verdicts this pass tests for portability
(`findings-log/probe-2026-10-08/recon/HCP-CONFIG-SCHEMA.md` §3 at `:112`, request table
at `:166`, `:175`, `:178`), and §10 of that file is titled **"Do not re-run"**. It is
still touched once, by the corpus control, because that control is performed **per host**
and not per build — the lesson docs/11's AB correction blockquote records. Sweeping it
would have been 24 candidate cells, and it would have answered "do they exist", which
is settled.

## Method

`GET` only, plus **9 empty-body `OPTIONS`** (no `-d`, no request body) on the three
routes recorded POST-only. No `POST`, no token, no cookie, no authentication beyond the
`X-System-ID: ProWeb` control header, no port scan, no wordlist, `--compressed` on every
request. **≥ 2.5 s** between requests to the same host (the harness sleeps 2.5 s and the measured floor is 2.595 s), slept **inside** the shared
per-host `flock` in the main clone's `.loop/`. A `000`/5xx/timeout/unexpected 4xx would
have been recorded as a **failure** and re-issued with its own row; none occurred.
Bodies are transient — the ledger carries only status, byte count, digest and a header
map, and the four 3.4 MB bundles were held in `.loop/` (gitignored), never in this
directory. Every file here is far under 1 MiB.

### Measured same-host spacing floor

Two instruments, both reported because they disagree and the disagreement is a known
defect class in this repository (OBSERVED, `spacing.py`):

| instrument | floor | gaps | under 2.5 s |
|---|---:|---:|---:|
| `t_sent` series (stamped inside the `flock`) | **2.108 s** | 39 | **4** |
| kernel body-mtime oracle (not re-derivable from a clean clone) | **2.595 s** | 39 | **0** |

39 same-host gaps: 13 per swept host (the baseline contributes one request, no gap).
**Four `t_sent` gaps read under the declared 2.5 s** — seq 10 (2.108 s), seq 29
(2.438 s), seq 36 (2.211 s), seq 42 (2.270 s) — and **all four are above the repo's
`>= 2 s` floor**. The kernel-mtime oracle, which measures when the body landed rather
than when the harness stamped the request, shows **0 of 39 under 2.5 s**. **Three rows
carry `t_done` earlier than `t_sent`** (seq 9 −501 ms, seq 35 −393 ms, seq 41 −341 ms),
which is arithmetically impossible if both stamps are faithful — the same corrupt-`t0`
class areas B, X, F and Q recorded. **No cause is asserted** and no row was smoothed:
the ledger keeps the impossible values, and the mtime oracle is the figure this pass
relies on. That oracle is **not re-derivable from a clean clone** (git does not preserve
mtimes; the bodies live outside the repository), so the sub-2.5 s count of **4 of 39**
is the reproducible statement and the floor claim rests on it being above 2 s.

## Controls, first per host — 12 of 12 reproduce

Each host was given the four standing controls **before** any candidate. All four are
lane l2's, proven live on this host family
(`findings-log/2026-10-17-hcp-config-deployments/plan.md` rows 1–15):

| control | expected | `.com` | `.eu` | `support` |
|---|---|---|---|---|
| `pow.crm.settings` + `X-System-ID: ProWeb` | 200 | **200**, 97 B | **200**, 96 B | **200**, 97 B |
| `CSU.CONTROL.CODES.SETTINGS` (UPPER) | 404, 0 B | **404**, 0 B | **404**, 0 B | **404**, 0 B |
| `cua.control.codes.settings` (lower) | 200 | **200**, 778 B | **200**, 778 B | **200**, 778 B |
| `logbook.supported.entry.types`, **no header** | 412 | **412**, 0 B | **412**, 0 B | **412**, 0 B |

**12 of 12 reproduce exactly (OBSERVED).** What that buys, stated as three separate
things rather than one: the verdict rule is **live** on each host (a known key answers
200 with the header); a `404` on each host is a **true absence** and not the 5518 B SPA
fallback, because the certainly-absent UPPER spelling 404s with 0 bytes and no
`content-type`; the namespace is **case-sensitive** on each host, because the same key
in the other case answers 200; and the **header gate is real** on each host, because a
header-less request to a `public/*` key returns 412. The `pow.crm.settings` byte counts
reproduce lane l2's and area A's record (96 B on `.eu`, 97 B on both `.com` hosts), which
is the third read of a value this repo already pins.

**Declared limit on these controls:** all four live under `public/`. The header gate has
never been measured on the **direct** subtree, and that is precisely the INFERRED
assumption AB was minted to falsify. It is settled by the candidates themselves, not by
these controls — see §The 412 assumption.

## The per-route x per-host verdict table — 18 of 18 cells

Baseline column is the **recorded** verdict from `HCP-CONFIG-SCHEMA.md` (`:112`, and the
request table at `:166`–`:178`); the three swept columns are this pass's OBSERVED cells.

| route | baseline `carelinkhp` (recorded) | `carelink.medtronic.com` | `carelink.medtronic.eu` | `carelink-support.medtronic.com` | portable? |
|---|---|---|---|---|---|
| `access/config` | 401, gated | **401**, 48 B | **401**, 48 B | **401**, 48 B | **yes** |
| `appContext` | 401, gated | **401**, 48 B | **401**, 48 B | **401**, 48 B | **yes** |
| `whitelisted` | 401, gated | **401**, 48 B | **401**, 48 B | **401**, 48 B | **yes** |
| `application` | 405, POST-only | **405**, 0 B | **405**, 0 B | **405**, 0 B | **yes** |
| `productContext` | 405, POST-only | **405**, 0 B | **405**, 0 B | **405**, 0 B | **yes** |
| `user` | 405, POST-only | **405**, 0 B | **405**, 0 B | **405**, 0 B | **yes** |

**6 of 6 portable, 18 of 18 cells agreeing with the baseline (OBSERVED).** Zero 404s,
zero 412s, zero 200s, zero 5xx, zero `000`. Every 405 carries **0 bytes and no
`content-type`**; every 401 carries **`application/json`**. Not one cell drifted between
the clinic hosts and the support host, which serve **different JavaScript builds**
(`2a7fa8e7af519c2b…` / `a054555a0f22176e…`, 4 of 4 digests re-asserted in `derive.txt`).

**The candidates are derived, not typed.** `probe.sh derive` re-extracted them offline
from the two fetched builds and **aborts the sweep** (exit 3, no request issued) unless
the extraction returns exactly the six named in the plan. It returned **6 direct
literals on each of the four captures, identical sets, 0 build-only literals**, and 15
`public/*` literals per build — the same populations `HCP-CONFIG-SCHEMA.md` §10
describes, which is the self-check that this extraction reads the recorded surface and
not a neighbouring one. `derive.txt` prints the four digests, the two route tables and
the set comparison.

## The 401 body digest, compared across hosts — one artefact, not three

The recorded body is `{"error":{"type":"InvalidToken","group":"AUTH"}}`, **48 B**
(PUBLISHED-by-record, `HCP-CONFIG-SCHEMA.md` §3). This pass's 401 responses:

- **9 of 9 cells** — 3 routes x 3 hosts — returned **48 B**,
  `application/json`, sha256 **`247825a42646079838401214de5456d83c4d5bf93ab482c06371e04dd4ea73ad`**.
- **One digest across the whole set.** The body was read on the first cell and compared
  as bytes: it is exactly the recorded `InvalidToken`/`AUTH` envelope. **No deployment
  answered 401 with a different body, and none answered 200** — the two outcomes the
  area said would be findings.
- That digest is **the same 48-byte envelope this repository already records on a
  different host family**: `findings-log/2026-10-12-area-o-reports-namespace/results.jsonl`
  seq 2/3/10/11/18/19 carry `247825a426460798…` on `carelink.minimed.{eu,com}` and
  `carelink-trials.minimed.com`. So the gate's rejection body is **one artefact shared
  across the portal and patient families**, on this pass's own measurement. That is a
  reproduction by this repo of this repo — **one source, not two** (`AGENTS.md` §2.1),
  and no strength word is used about it.

**Bound, stated because it is load-bearing:** the digest matching proves the *rejection*
is the same object. It does **not** prove the gateways behind the 401 are the same
component, and this pass asserts nothing about that. What it does establish is the
portability claim AB needed: nothing about the 401 differs between deployments except
`access-control-allow-headers`, which is `X-System-ID, Content-Type, authorization` on
both clinic hosts and `X-System-ID` alone on the support host (OBSERVED, 9 of 9) —
reproducing lane l2's hardening observation on a second route family.

## The `OPTIONS` cells — the allow-methods record this family did not have

9 cells: empty-body `OPTIONS` on `application`, `productContext`, `user` x 3 hosts.

| host | route | status | `allow` | `access-control-allow-methods` | body |
|---|---|---|---|---|---|
| all three | `application` | **200** | **`POST, OPTIONS`** | **absent** | 13 B, `text/plain;charset=UTF-8` |
| all three | `productContext` | **200** | **`POST, OPTIONS`** | **absent** | 13 B, `text/plain;charset=UTF-8` |
| all three | `user` | **200** | **`POST, OPTIONS`** | **absent** | 13 B, `text/plain;charset=UTF-8` |

- **9 of 9 OPTIONS answered 200 with `allow: POST, OPTIONS` and a 13-byte body that is
  the same method list** (one digest, `16f1efa415bfdd7a…`, on all nine). The three
  routes that answer 405 to `GET` answer 200 to `OPTIONS`, on every deployment: the
  route is **registered and method-filtered**, not unrouted (OBSERVED).
- **`allow` is present on the 405 too, with the identical value** — 9 of 9 GET-405
  cells carry `allow: POST, OPTIONS`. So on this family the `Allow` header and the
  preflight's body are one statement, and the preflight's own status agrees with it.
  **INFERRED, and it matters that it is labelled:** that `Allow` is generated by the
  server from the route's registered methods (the `server:` header is
  `Apache/2.4.62 (Red Hat Enterprise Linux) OpenSSL/3.5.5` on all 43 responses) rather
  than configured per route. The observation is the agreement; the mechanism is not
  established.
- **`access-control-allow-origin` and `access-control-allow-methods` are absent on 43 of
  43** responses, including all 9 OPTIONS 200s. **`access-control-allow-headers` is present
  on 43 of 43**, and its value splits **per host, not per method**: `carelink.medtronic.com`
  and `carelink.medtronic.eu` (and the `carelinkhp.minimed.eu` corpus-control row) carry
  `X-System-ID, Content-Type, authorization` on **all 29** of their rows; the support host
  `carelink-support.medtronic.com` carries the short `X-System-ID` on **all 14** of its rows —
  on every status and both methods alike. ⚠ **This bullet has now been wrong twice, and both
  errors are recorded rather than smoothed over.** The first draft said "No
  `Access-Control-Allow-*` preflight header appears on this family at all … Only
  `access-control-allow-headers` appears, on the 401s" — refuted by its own ledger (43 of 43,
  all statuses). The first *fix* then attributed the split to the OPTIONS 200s versus the rest,
  which the ledger also refutes: it is a **host** split, and a verifier caught the second error
  after the first was "fixed". The lesson is worth more than the sentence: **a correction
  written from a summary of the data inherits the summary's shape, so re-derive the
  breakdown from the ledger, not from the previous paragraph.** **This is the opposite of the
  cumulus family**, where an `OPTIONS` 200 carries the full CORS set and `docs/09` §2 warns
  that `ACAM` is not a method register. Here there is no `ACAM` to misread: the signal is
  `Allow`, in the body and the header. That does not make `Allow` a method register in general
  — it makes it one **on this family, for these three routes**, which is all this pass claims.
- **Read narrowly, per `docs/09` §2:** these cells do **not** establish that `POST` is
  the only writer method, and no `POST` was sent. They establish what the deployment
  *advertises*, which is what AGENTS.md §8 asks an `OPTIONS` probe to do and what
  nothing on `docs/07` recorded for this family.

## The two INFERRED assumptions AB carried — one settled, one not

AB listed two assumptions it wanted falsified. Both are addressed; only one is closed.

1. **"The edge rejects a header-less request to the direct subtree the way it rejects
   one under `public/`."** **Not settled, and this pass deliberately did not spend a
   request on it.** Every direct candidate was sent *with* `X-System-ID: ProWeb`, so no
   direct cell is header-less; and no direct cell answered **412**, which means the gate
   did not reject any headered direct request. The 412 behaviour was measured only under
   `public/` (4 of 4 controls, all three hosts). Spending 3 of the 43 on a header-less
   direct cell would have meant dropping 3 candidate cells, and the portability claim
   needs all 18. **The honest statement is the weaker one: on this pass's cells the
   direct subtree behaves identically to `public/` when the header is present; whether it
   returns 412 when the header is absent is unmeasured.** Recorded as the successor
   half of area AB's closing note rather than claimed.
2. **"`405` on the recorded host reflects the route rather than a method filter that
   differs per deployment."** **Settled, and it does.** All three deployments return 405
   with an identical `Allow: POST, OPTIONS`, and each answers `OPTIONS` 200 with the same
   13-byte body. A per-deployment method filter that happened to agree on three hosts
   would be indistinguishable from this — so what is observed is *agreement*, and the
   reading "the filter is the route's" is INFERRED from that agreement plus the identical
   `server` header. It is the reading the area asked for; it is not a claim about
   configuration.

## Verdict

**The six direct `/hcp/configuration/*` verdicts are deployment-portable.** 18 of 18
cells across three deployments reproduce the single-deployment reading recorded on
`carelinkhp.minimed.eu` on 2026-10-08: three routes token-gated at 401 with one identical
48-byte `InvalidToken`/`AUTH` body, three routes POST-only at 405 with 0 bytes and an
`Allow: POST, OPTIONS`. The two hosts serving the *same* build and the one host serving a
*different* build agree cell for cell, so build identity is not what carries the
verdict. **A negative is the result here and it closes AB**: there is no deployment
split to report, and the first sentence of `docs/07`'s portability section can be
extended from the 15 `public/*` keys to all 21 `hcp/configuration` route literals.

**What this pass does *not* claim:** content behind any 401 (excluded by design — no
token); that `POST` works on the three 405 routes (no POST was sent); the 412 shape on
the direct subtree (unmeasured, see above); and any mechanism for why the deployments
agree.

## `docs/07` — not changed, and why

`docs/07` is the page that describes this family, and the test for editing it is whether
this pass **moves** a sentence it carries. It does not. The three statements in
`docs/07` about the direct subtree are: the shadow portal's
`/hcp/configuration/{application,user,countries/getAllCountries}` → **405**
(a `carelink.medtronic.eu`, no-header reading) and its `pow.crm.settings` 200/96 B; and
the settled note that `application/octet-stream` covers 11 of the 13 answering `public/*`
keys, whose own text records that whether that is per-host "is NOT determined" because
`carelinkhp`'s surface was not re-probed. This pass **confirms** the 405s on `.eu` with
the header present (3 of 3) and adds nothing that contradicts either statement; the
`application/octet-stream` question is a `public/*` cell and this pass did not touch
`public/*` verdicts. **No edit to `docs/07`, recorded here rather than made silently**
(`AGENTS.md` §3: `docs/` supersedes; it does not accumulate a second description of the
same surface).

## Under 1 MiB, and no captures

`results.jsonl` (43 rows, status/bytes/digest/header map only), `run.log`, `derive.txt`,
`plan.md`, `probe.sh`, `spacing.py`, this file. No response body is committed; no
bundle; no credential, internal hostname or machine path appears in any of them.
