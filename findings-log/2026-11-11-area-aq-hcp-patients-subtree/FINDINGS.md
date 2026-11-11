# Area AQ — the `hcp/patients/` subtree is route-live, and its 405 is **per-route**, not a subtree constant

**Claim:** [NovaLux12/carelink-api-research#199](https://github.com/NovaLux12/carelink-api-research/issues/199) ·
**Date:** 2026-11-11 · **Area:** AQ · **Branch:** `research/aq-hcp-patients-subtree`
**Hosts swept:** all four HCP portal hosts — `carelinkhp.minimed.eu`, `carelink.medtronic.com`,
`carelink.medtronic.eu`, `carelink-support.medtronic.com`

Legend (`AGENTS.md` §2) — **OBSERVED** = seen in a live response · **PUBLISHED** = in a vendor
document served without a login · **INFERRED** = reasoned, not seen.

---

## The answer in one paragraph

**`hcp/patients/` is a live, method-filtered subtree, and it does NOT behave like
`/hcp/configuration/`.** An absent child directly under `hcp/patients/` answers a real **`404`,
0 bytes, no `Content-Type`** on all four hosts — the same shape as `/hcp/<absent>` — so the
`/hcp/configuration/` `405 + Allow` that area AG found to be a subtree constant is **not** a
property of a handler mounted over `/hcp/`: it stops at that one subtree. Because the absent
child 404s, a `405` inside `hcp/patients/` **does** discriminate a registered route from an
absent path on this subtree, and 17 of the 23 candidates returned exactly that, all with the
identical `Allow: POST, OPTIONS`. Two further candidates answered **`412`** — the
`X-System-ID` header gate — and four answered `404`. **The claim's 12-name list was 11 names
short:** the builds name **22** probeable literals in this subtree, and two of the twelve the
claim asserted (`sendInviteToPersonal`, `getInviteToPersonalTemplate`) are **not routed**.

---

## 1. Request accounting — 36 of a 36 cap

| | n |
|---|---:|
| **Cap, declared before the first request** | **36** |
| Requests sent | **36** |
| `curl_exit` ≠ 0 | **0** |
| Rows in `results.jsonl` | **36** |
| Hosts contacted | **4** — the whole declared host set, no others |

The cap is a single assignment in `probe.sh` (`CAP=36`) and its itemisation *is* the cap:
corpus control **1** + (2 controls × 4 hosts) **8** + (absent-child boundary cell × 4 hosts)
**4** + 23 candidates on the derivation host **23** = **36**. `verify.py` re-derives that sum
from `derive.txt` and `candidates.txt` and prints `1 + 8 + 4 + 23 = 36 (cap is 36)`.

**ONE RECORDED CAP REVISION: 24 → 36**, taken **after request 1** (the corpus control, which
is what makes the derivation possible) and **before any candidate**. The claim's cap of 24
assumed 12 routes. The derivation returned **22** probeable literals plus the claim's
one name no build carries, i.e. **23** candidates — so 12 + 23 = 35 did not fit in 24, and
the derived set was allowed to set the price. Under claim #199's own instruction the derived
set wins; a cap that pays for twelve names when the build names twenty-two would have
answered the wrong question precisely.

**Method:** `GET` only. No `POST`, no `OPTIONS`, no token, no cookie, and **no patient id —
not even a fabricated one**. The only header sent is `X-System-ID: ProWeb` on the four
positive controls; every candidate and every boundary cell went header-less, which is what
makes the `412` column (§5) interpretable. `--compressed` on every request. `--max-time 120`. **≥ 2.5 s
between requests to the same host**, slept *inside* the per-host `flock`
(`$REPO/.loop/host-<host>.lock`), the structure copied from area AB's `probe.sh` down to the
single `CAP=` assignment and the `cap_guard` that reads it.
No wordlist: the candidate list is written to `candidates.txt` by `derive.py` before the sweep
and the sweep re-reads that file rather than a list typed into it.

## 2. Delay accounting — two clocks, one of them the repo's known-bad one

The harness is in the recorded **corrupt-`t0` class** (`docs/09` §4). Both clocks are
published and no cause is asserted (`python3 verify.py` re-derives both; zero requests).

```
clock A — t_sent (re-derivable from results.jsonl)
  gaps 31   min 1.841 s   median 2.632 s   max 76.001 s
  under 2.5 s : seq 8->9 (1.841 s), seq 29->30 (2.229 s)
  under 2.0 s : seq 8->9 (1.841 s)
  impossible negative DURATIONS (t_done < t_sent): seq 1 -0.508 s, seq 8 -0.695 s, seq 29 -0.307 s

clock B — kernel body mtimes (NOT re-derivable from a clean clone)
  bodies stat-able 36 of 36   gaps 31
  min 2.594 s   median 2.630 s   max 76.628 s
  under 2.5 s : none          FLOOR ON THIS CLOCK: 2.594 s
```

**The two clocks conflict on exactly the rows the harness clock convicts, and nowhere else.**
The single sub-2.0 s gap is `seq 8→9`, and `seq 8` is one of the three rows whose own
`t_done` precedes its `t_sent` — arithmetically impossible, so at least one stamp on it is
corrupt. Under the counting rule `docs/09` §4 already sets, a short gap measured off a
provably corrupt series is an artefact of that corruption and is **not** evidence of
underspacing: the kernel mtime counter reads **0 of 31 gaps under 2.5 s, floor 2.594 s**
(OBSERVED). **No delay rule is claimed breached, and no clean `t_sent` floor is claimed
either** — clock A's floor is published as measured at 1.841 s.

The 76 s max is the batch gap: request 1 (`bundles`) finished, then `derive.py` ran offline
before `sweep` began. It is a between-batches pause, not a within-host spacing defect.

## 3. Controls first, per host — 8 of 8 reproduce

Sent **before** any boundary cell or candidate on that host, because a status is not an oracle
until it is shown to discriminate.

| control | expected | `carelinkhp` | `.com` | `.eu` | `support` |
|---|---|---|---|---|---|
| `/hcp/configuration/public/pow.crm.settings` + `X-System-ID: ProWeb` | 200 | **200**, 96 B | **200**, 97 B | **200**, 96 B | **200**, 97 B |
| `/hcp/zz-aq-absent-9157` (no header) | 404, 0 B | **404**, 0 B | **404**, 0 B | **404**, 0 B | **404**, 0 B |

**8 of 8 reproduce exactly (OBSERVED).** The 96/97-byte split reproduces area A's and lane
l2's record (`a977733a53ee0d5f…` on `carelinkhp` and `.eu`, `370e3bba0d28c540…` on `.com` and
`support`), so the four hosts are serving the documents this repository pins. The absent cell
at `/hcp/` answers a real `404` with **no `Content-Type` header** on all four, confirming
again that the 5518 B SPA fallback stops at `/hcp/` (area AK) and that a `404` below that
prefix is a true absence rather than a fallback page.

The fabricated name is **`zz-aq-absent-9157`**. `git grep -c 'zz-aq-absent-9157' -- .` at this
head returns **0** — a name no tracked file carries.

## 4. The derivation — the derived set won, 22 against 12

`derive.py` runs **zero requests** and reads two sources, because this build names its routes
in two places: the eager bundle fetched as request 1 (`main.fb5f8cb7eb60c4d5.js`, **3 397 615 B**,
sha256 `2a7fa8e7af519c2b…`, reproducing the digest area K recorded and areas AB/AK re-asserted),
and the committed lazy-chunk route delta
(`findings-log/2026-10-14-area-k-clinic-controlflow/route-delta.json`, `chunk_only`).

| population | n | what it is |
|---|---:|---|
| eager-bundle literals, no placeholder | **21** | named outright, safe to request |
| chunk-only literal | **1** | `hcp/patients/checkPhoneNumber`, from the committed route delta |
| **probeable, derived** | **22** | |
| needs-id (`((patientId))`) | **15** | **recorded, NOT probed** — probing one means inventing a patient id |
| claim-only (in the claim, in no build) | **1** | `hcp/patients`, the bare collection |
| **candidates issued** | **23** | 21 + 1 + 1 |

**The derived set disagrees with the claimed set, and the derived set wins** (claim #199).
Eleven derived names are absent from the claim's list — `addPatient`, `care-partner/search`,
`clearPatientsFlags`, `flagPatient`, `getAllClinicArchivedPatients`,
`getAllClinicUnarchivedPatients`, `getInviteToPersonalSubjectPlaceholder`,
`otc-linking/code/email/send`, `unFlagPatient`, `unarchivePatient`,
`updatePatientsMealProfilesAndDailyHabits` — and one claimed name, the bare collection, appears
in neither build. `derive.txt` prints both sets and the symmetric difference; `probe.sh` refuses
to sweep if the extraction returns nothing (exit 2) or if the build digest has moved (exit 4).

**Why the derivation is not the claim's list plus padding:** every derived name comes from a
string literal in a shipped bundle or from a hash-pinned committed route delta. Nothing was
guessed, and no candidate was formed by inflecting a known name.

**Method, derived offline and reported as a limit rather than a claim.** I attempted to read
each route's HTTP verb from the build by resolving the literal to its module-level alias and
finding `.get(`/`.post(` on it. **That extraction does not survive this bundle's minification**:
the aliases (`Hr`, `ht`, `ws`, `Bt`, …) are single- and double-letter names that collide with
unrelated identifiers in other scopes — `ht` alone has 323 occurrences, `Hr` 57 — so an
alias-keyed search returns call sites belonging to Angular internals, not to the service. The
attempt is committed as `callsite-methods.json` **so the failure is on the record**, and it is
labelled unusable. **The method column below therefore comes from the live `Allow` header, not
from static code reading**, and the two call-site verbs the repository does record statically
are cited where they exist (§5).

## 5. The per-route verdict table — 23 of 23 cells

All candidates on `carelinkhp.minimed.eu`, header-less. `Allow` is quoted verbatim.

| # | route literal | status | bytes | `Allow` | verdict |
|---:|---|---:|---:|---|---|
| 14 | `addPatient` | **405** | 0 | `POST, OPTIONS` | **routed**, POST-only |
| 15 | `archivePatient` | **405** | 0 | `POST, OPTIONS` | **routed**, POST-only |
| 16 | `care-partner/search` | **412** | 0 | — | **routed, header-gated** |
| 17 | `checkPhoneNumber` | **405** | 0 | `POST, OPTIONS` | **routed**, POST-only |
| 18 | `clearPatientsFlags` | **405** | 0 | `POST, OPTIONS` | **routed**, POST-only |
| 19 | `flagPatient` | **405** | 0 | `POST, OPTIONS` | **routed**, POST-only |
| 20 | `getAllClinicArchivedPatients` | **405** | 0 | `POST, OPTIONS` | **routed**, POST-only |
| 21 | `getAllClinicUnarchivedPatients` | **405** | 0 | `POST, OPTIONS` | **routed**, POST-only |
| 22 | `getInviteToPersonalSubjectPlaceholder` | **404** | 0 | — | **not routed** |
| 23 | `getInviteToPersonalTemplate` | **404** | 0 | — | **not routed** |
| 24 | `getPatient` | **405** | 0 | `POST, OPTIONS` | **routed**, POST-only |
| 25 | `getPatientsMealProfilesAndDailyHabits` | **405** | 0 | `POST, OPTIONS` | **routed**, POST-only |
| 26 | `linkPatient` | **405** | 0 | `POST, OPTIONS` | **routed**, POST-only |
| 27 | `otc-linking/allowed` | **412** | 0 | — | **routed, header-gated** |
| 28 | `otc-linking/code/email/send` | **405** | 0 | `POST, OPTIONS` | **routed**, POST-only |
| 29 | `otc-linking/code/sms/send` | **405** | 0 | `POST, OPTIONS` | **routed**, POST-only |
| 30 | `sendInviteToPersonal` | **404** | 0 | — | **not routed** |
| 31 | `unFlagPatient` | **405** | 0 | `POST, OPTIONS` | **routed**, POST-only |
| 32 | `unarchivePatient` | **405** | 0 | `POST, OPTIONS` | **routed**, POST-only |
| 33 | `unlinkPatient` | **405** | 0 | `POST, OPTIONS` | **routed**, POST-only |
| 34 | `updatePatient` | **405** | 0 | `POST, OPTIONS` | **routed**, POST-only |
| 35 | `updatePatientsMealProfilesAndDailyHabits` | **405** | 0 | `POST, OPTIONS` | **routed**, POST-only |
| 36 | `hcp/patients` (bare collection) | **404** | 0 | — | **no GET-visible handler** |

**Histogram: 17 × `405`, 2 × `412`, 4 × `404`.** Every `405` carries **0 bytes, no
`Content-Type` and the identical `Allow: POST, OPTIONS`** — one value, 17 of 17. `ACAM` and
`ACAO` are **absent on 36 of 36** responses, and `Server: Apache/2.4.62 (Red Hat Enterprise
Linux) OpenSSL/3.5.5` is on 36 of 36, consistent with areas AB and AG.

### The claim's own twelve, each against its cell

| claimed route | this pass | note |
|---|---|---|
| bare `hcp/patients` | **404** | the only claimed name no build carries |
| `archivePatient` | **405** | routed, POST-only |
| `checkPhoneNumber` | **405** | routed, POST-only; the committed call-site verb is `POST` (`route-delta.json` `chunk_only`, and `s4-full/pairs.tsv`), which agrees |
| `getInviteToPersonalTemplate` | **404** | **the claim's assertion is not routed** |
| `getPatient` | **405** | routed, POST-only |
| `getPatientsMealProfilesAndDailyHabits` | **405** | routed, POST-only |
| `linkPatient` | **405** | routed, POST-only |
| `otc-linking/allowed` | **412** | routed, behind the `X-System-ID` gate |
| `otc-linking/code/sms/send` | **405** | routed, POST-only |
| `sendInviteToPersonal` | **404** | **the claim's assertion is not routed** |
| `unlinkPatient` | **405** | routed, POST-only |
| `updatePatient` | **405** | routed, POST-only |

**8 of the claim's 12 are routed POST-only, 1 is routed header-gated, and 3 are not routed at
all** — one of which is the bare collection and two of which are real string literals in the
shipped bundle that no handler answers. **A literal in a bundle is a call site, not a route**;
that is the plainest lesson in this table and the reason the claim's phrasing ("call sites read
out of shipped code, never route-probed") was the right one to test.

## 6. The subtree has **no** 405 constant — the deliverable the claim asked for

The question was whether `hcp/patients/` behaves like `/hcp/configuration/` (where an absent
child answers `405 + Allow`, so a `405` proves nothing — area AG) or like `/hcp/` (a real
`404`). Four cells, one per host, same fabricated token one level deeper:

| host | `/hcp/patients/zz-aq-absent-9157` | bytes | `Content-Type` | `Allow` |
|---|---|---:|---|---|
| `carelinkhp.minimed.eu` | **404** | 0 | (none) | — |
| `carelink.medtronic.com` | **404** | 0 | (none) | — |
| `carelink.medtronic.eu` | **404** | 0 | (none) | — |
| `carelink-support.medtronic.com` | **404** | 0 | (none) | — |

**4 of 4 hosts: a real `404`, byte-identical in shape to the `/hcp/<absent>` control
(OBSERVED).** So `hcp/patients/` is **transparent to absence** and the `405` inside it is not
a mount-level constant. The `405` region on this family is therefore **narrower** than
`/hcp/`: `/hcp/configuration/` answers `405` to anything under it; `hcp/patients/` answers
`404` to anything it does not route and `405` only to routes it does.

**This is also the second data point area AL's successor `AR` asked for**, and it lands on the
negative side: `AR`'s close condition explicitly says *"if the third subtree answers 404 instead
of 405, the constant is scoped to `/hcp/configuration/` after all"* — `hcp/patients/` is that
subtree, it answers `404`, and the constant is therefore scoped to one subtree. `AR` remains
open for a **third** subtree; this pass does not close it.

**Two independent lines of evidence inside the same sweep, not one cell:**
1. The absence control at depth 1 returned `404` — a wildcard child handler would have to
   answer `405` here to produce the `/hcp/configuration/` behaviour, and it does not.
2. **Three single-segment candidates returned `404` alongside fifteen that returned `405`.**
   Fifteen `405`s and three `404`s at the *same depth under the same parent* cannot both come
   from a handler that answers every child; they can only come from per-route registration.
   `verify.py` prints this as `statuses at depth 1: {'405': 15, '404': 3}`.

## 7. The two `412` cells are a second gate, and it is **per-route**

`care-partner/search` and `otc-linking/allowed` answered **`412`, 0 bytes, no `Content-Type`**,
while every other candidate in the same sweep answered `405`. The absence control — sent with
**the same header-less request shape** — answered `404`. So on this subtree:

- **`412` is falsifiable against a `404` measured on the same host in the same run**: a
  header-less GET to a path that does not exist gives `404`, and a header-less GET to these
  two gives `412`. **`412` therefore discriminates presence here** — it is not a blanket
  response for the subtree, and it is not the absence shape.
- **The `X-System-ID` gate is per-route on `hcp/patients/`, not subtree-wide.** 17 routes
  answered `405` with no header at all, so the gate does not cover them; only these two
  demanded it. That is a different shape from `/hcp/configuration/public/*`, where the gate
  was measured across the whole sub-namespace (area AB's four controls).
- **What is NOT established:** what these two answer *with* the header present. `412` means the
  edge rejected the request for a missing header, not that a route handler ran. Whether `200`,
  `401` or `404` follows `ProWeb` here is **unmeasured** — successor **AS**.

**INFERRED, and it is an inference:** that `412` on these two is the same gate mechanism as the
`412` area AB recorded under `public/*`. The observation is that both are `412`, 0 bytes and
header-less-triggered; the mechanism is not established, and the `ACAH` value differs per host
(§8), so the gate could be configured differently.

## 8. Headers, and the one host that differs

`access-control-allow-methods` and `access-control-allow-origin` are **absent on 36 of 36**
responses. `access-control-allow-headers` is present on all 36 and splits **per host, not per
status or method** — exactly as area AB recorded on `/hcp/configuration/`:

| host | `access-control-allow-headers` |
|---|---|
| `carelinkhp.minimed.eu`, `carelink.medtronic.com`, `carelink.medtronic.eu` | `X-System-ID, Content-Type, authorization` |
| `carelink-support.medtronic.com` | `X-System-ID` |

`verify.py` prints this as two sets over 36 rows. It reproduces area AB's split on a second
route family, in a different subtree, and it is a **reproduction by this repository of this
repository** — one source, so no strength word applies (`AGENTS.md` §2.1).

## 9. What this does not establish

- **Nothing behind any gate.** No token, no cookie, no patient id. `412` and `405` are
  statements about the edge and the method filter; not one byte of a patient record was read.
- **Not the 15 `((patientId))` literals.** They are recorded in `derive.txt` as needs-id and
  were **not probed**. Whether the `{patientId}` subtree carries the same `405`/`412`/`404`
  shapes as its parent is **unmeasured**, and it cannot be measured without a real patient id
  (successor **AT** carries the half that does not need one).
- **Not the method each route accepts.** `Allow: POST, OPTIONS` is what the deployment
  *advertises*; no `POST` was sent, and `Allow` is not a method register in general — area AG
  showed it is a constant that a non-existent path can reproduce *on `/hcp/configuration/`*.
  What this pass shows is that here it does **not** reproduce on an absent path, so on this
  subtree it is evidence — of what the deployment advertises, and no more.
- **Not portability.** Every candidate was sent to **one** host. Only the boundary cell and the
  controls were measured on all four. A per-deployment difference in the route table is not
  excluded; area AB is the prior art for that question on the sibling subtree.
- **Not a disclosure.** Every cell is an unauthenticated `GET` on a public host. No `POST`, no
  token, no patient id, and no fabricated id.
- **Not the verb column from static code.** §4 records the attempt and why it failed.

## 10. Successors

- **AS** (minted in `docs/11`) — what do the two header-gated routes answer *with*
  `X-System-ID`?
- **AT** (minted in `docs/11`) — does the bare collection have a handler that a `GET` cannot
  see?

**Both were minted as `AS` and `AT`, not `AR`/`AS`, because of a letter collision found at merge
time.** While this pass ran, two sibling lanes merged to `main` and took `AR` (area AL's
successor, "does the `/hcp/configuration/` 405 constant extend to a **third** subtree") and
`AQ` (area AP's successor, on `csr`/`v2` absent-path `OPTIONS` controls). Letters are never
reused here, so this pass's successors moved down to the next free pair. `AR` is **not** this
area's successor and this pass did not touch it.
- The `{patientId}` subtree is recorded as a **blocked** row: it needs a real patient id,
  which only a clinician session supplies.

## 11. Evidence index

| file | what it holds |
|---|---|
| `probe.sh` | the 36-cell sweep; cap as one assignment; `cap_guard`; per-host `flock` with the sleep inside |
| `derive.py` | zero-request route extraction; writes `derive.txt` and `candidates.txt` |
| `derive.txt` | the two route populations, the symmetric difference, the build digest |
| `candidates.txt` | the 23 literals the sweep actually issued, written before it ran |
| `callsite-methods.json` | the **failed** static verb extraction, committed so the failure is on the record |
| `results.jsonl` | 36 rows, one per request, status / bytes / digest / header map only |
| `verify.py` | re-derives every figure above from the ledger; zero requests |
| `verify.txt` | its output at this head |
| `run.log` | per-request line, UTC stamps, cap-stop guard |

No response body is committed; no bundle; no credential, internal hostname or machine path
appears in any file. `results.jsonl` is 36 rows of metadata.
