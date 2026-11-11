# Area AY (minted as AQ) — do the three "live, POST-only" verdicts survive a same-subtree absent-path `OPTIONS` control on `.com` and `.eu`?

Closes `docs/11-suggested-research-areas.md` area **AY** (the `OPTIONS` half). Claim: issue #209.
Branch `research/aq-options-per-route`. Directory stays `area-aq-options-per-route` because that
is the name this lane was chartered under; **the area letter is `AY`** — see §9.

**Result: all three verdicts STAND. `OPTIONS` resolves PER ROUTE in all three subtrees, on all
three cumulus hosts — nine fabricate-vs-real pairs, nine `403`s at the no-route digest against
nine `200`s with CORS.** No `OPTIONS` half falls, so no correction is appended to areas C, N or
Z. The per-route step `docs/09` §2 has been assuming since the rule was written is now measured
on `.com` and `.eu` as well as `-trials`, and under three bases rather than one.

## 0. The question, and what a fall would have cost

Area AP ([source: findings-log/2026-11-11-area-ap-trials-options-specificity/FINDINGS.md §4])
proved on `clcloud-trials.minimed.com` alone that `/connect/carepartner/v2/` resolves `OPTIONS`
per route: a fabricated path answered `403` at the no-route digest while `v2/display/message`
answered `200`. Three route verdicts elsewhere in this repo rest on the same step, and none of
them had ever been controlled:

| verdict | written as | cell that carries it | source |
|---|---|---|---|
| `connect/csr/v2/display/message` | live, POST-only | `OPTIONS` 200 + `ACAO: *` | [source: findings-log/2026-10-11-pde-csr-oracle/FINDINGS.md:69] |
| `connect/v2/display/message` (bare) | live, POST-only | `OPTIONS` 200 + `ACAO: *` | [source: findings-log/2026-10-12-csr-cross-host/FINDINGS.md:58] |
| `connect/carepartner/v6/display/message` | live, POST-only | `OPTIONS` 200 + `ACAO: *` | [source: findings-log/2026-10-12-area-z-origin-reflection/FINDINGS.md:116] |

If the preflight on `.com`/`.eu` were subtree-wide, each of those verdicts would lose its
`OPTIONS` half and fall back to "no `GET` route" — a materially weaker claim than the pages
make, and one that would need a dated `## Correction` in three log files.

## 1. Method

- **Three hosts, and no others**: `clcloud.minimed.com`, `clcloud.minimed.eu`,
  `clcloud-trials.minimed.com`. The clinic hosts and `carelinkhp` belong to sibling lanes.
  Nothing here says anything about those.
- **24 of a 24 cap**, zero failures, zero retries, zero `curl_exit != 0` (§7). The cell list was
  itemised in `probe.sh`'s header **before** the first request. **No revision was needed** — the
  plan was 8 cells × 3 hosts from the start, so the one recorded-revision allowance is unspent.
- **`GET` + empty-body `OPTIONS` only** (`--request OPTIONS`, never `-X OPTIONS` with a body).
  No `POST`, no `Authorization`, no `Cookie`, no `x-api-key`, no `X-System-ID`, no token
  exchange, no wordlist, no DNS, no port scan, no dev/stage host.
- **`sleep 2.5` inside the per-host `flock`** — a ≥ 2.5 s delay between requests to the same
  host, held inside the lock — on `$REPO/.loop/host-<host>.lock`, one lock file per host,
  structure copied from
  `findings-log/2026-11-11-area-ap-trials-options-specificity/probe.sh`.
- **Controls first on every host, and both are GATES.** Per host, in this order: the live
  `GET /connect/carepartner/v13/display/message` must be `401` / 36 B / `d551247201fc8fc2…`, and
  the no-route oracle `GET /connect/carepartner/v2/zz-aq2-absent-7241` must be `403` / 42 B /
  `f249b63cb2fcb66b47e86f906c98f8fd912e82dd035b4e53d7e72fc1960cfd16`. `gate()` compares
  status **and** byte count **and** full digest **and** host; a mismatch exits 9 with no question
  cell issued for that host. All six gates printed `GATE OK` (§2).
- **One fabricated name serves all three subtrees**: `zz-aq2-absent-7241`. It sits at the same
  depth as each subtree's `display/message` leaf (two segments below the base). It had **zero hits
  in the committed tree before this pass wrote anything** (`git grep -c 'zz-aq2-absent-7241'
  origin/main -- .` → 0); at this head it appears only in this lane's own artefacts and in the
  `docs/11` row describing them.
- **The deciding cell** is one empty-body `OPTIONS` to that name inside the subtree, paired in
  the same run with the same `OPTIONS` to the real leaf. `403` at the no-route digest ⇒ per-route.
  `200` with CORS ⇒ subtree-wide, and that verdict's `OPTIONS` half does not stand.

## 2. Controls (OBSERVED)

| # | host | method | path | status | `x-amzn-errortype` | `x-ca-err` | bytes | sha256 |
|---|---|---|---|---|---|---|---|---|
| 1 | `.com` | GET | `carepartner/v13/display/message` | **401** | `UnauthorizedException` | **990** | 36 | `d551247201fc8fc2…` |
| 2 | `.com` | GET | `carepartner/v2/zz-aq2-absent-7241` | **403** | `MissingAuthenticationTokenException` | — | **42** | **`f249b63cb2fc…`** |
| 9 | `.eu` | GET | `carepartner/v13/display/message` | **401** | `UnauthorizedException` | **990** | 36 | `d551247201fc8fc2…` |
| 10 | `.eu` | GET | `carepartner/v2/zz-aq2-absent-7241` | **403** | `MissingAuthenticationTokenException` | — | **42** | **`f249b63cb2fc…`** |
| 17 | `-trials` | GET | `carepartner/v13/display/message` | **401** | `UnauthorizedException` | **990** | 36 | `d551247201fc8fc2…` |
| 18 | `-trials` | GET | `carepartner/v2/zz-aq2-absent-7241` | **403** | `MissingAuthenticationTokenException` | — | **42** | **`f249b63cb2fc…`** |

**Both controls reproduce inside their gate, on all three hosts, to the digit.** `401` +
`x-ca-err: 990` is the request reaching Medtronic's Layer7 authorizer; `403` +
`MissingAuthenticationTokenException` at 42 B is the gateway's unmatched-route answer. Note the
direction, because it is the whole oracle: **`403` is a NEGATIVE — no matching route — and never
a positive.** **OBSERVED** — `results.jsonl` seq 1, 2, 9, 10, 17, 18; `run.log` `GATE OK` lines.

## 3. The nine fabricate-vs-real pairs (OBSERVED)

Verdict rule, `docs/09` §2: `GET 403 + OPTIONS 403` → dead on every tested method;
`GET 403 + OPTIONS 200` → live, registered with a non-`GET` method; `GET 401` → live with `GET`.

| base | host | fabricated `OPTIONS` | status | bytes | digest | `ACAO` | real leaf `OPTIONS` | status | `ACAO` / `ACAM` | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| `csr/v2` | `.com` | seq 3 | **403** | 42 | `f249b63c…` | — | seq 4 | **200** | `*` / `OPTIONS,POST` | **PER-ROUTE** |
| `csr/v2` | `.eu` | seq 11 | **403** | 42 | `f249b63c…` | — | seq 12 | **200** | `*` / `OPTIONS,POST` | **PER-ROUTE** |
| `csr/v2` | `-trials` | seq 19 | **403** | 42 | `f249b63c…` | — | seq 20 | **200** | `*` / `OPTIONS,POST` | **PER-ROUTE** |
| bare `v2` | `.com` | seq 5 | **403** | 42 | `f249b63c…` | — | seq 6 | **200** | `*` / `POST,OPTIONS` | **PER-ROUTE** |
| bare `v2` | `.eu` | seq 13 | **403** | 42 | `f249b63c…` | — | seq 14 | **200** | `*` / `POST,OPTIONS` | **PER-ROUTE** |
| bare `v2` | `-trials` | seq 21 | **403** | 42 | `f249b63c…` | — | seq 22 | **200** | `*` / `POST,OPTIONS` | **PER-ROUTE** |
| `v6` | `.com` | seq 7 | **403** | 42 | `f249b63c…` | — | seq 8 | **200** | `*` / `OPTIONS` | **PER-ROUTE** |
| `v6` | `.eu` | seq 15 | **403** | 42 | `f249b63c…` | — | seq 16 | **200** | `*` / `OPTIONS` | **PER-ROUTE** |
| `v6` | `-trials` | seq 23 | **403** | 42 | `f249b63c…` | — | seq 24 | **200** | `*` / `OPTIONS` | **PER-ROUTE** |

Every fabricated sibling returns **one** body — the 42 B no-route `403` at
`f249b63cb2fcb66b…`, byte-identical to its host's control — with **no** `ACAO`, **no** `ACAM`,
**no** `Allow` and **no** `x-amzn-errortype` other than `MissingAuthenticationTokenException`
(OBSERVED, `results.jsonl` seq 3, 5, 7, 11, 13, 15, 19, 21, 23). Every real leaf returns
`HTTP/2 200`, `content-length: 0`, `access-control-allow-origin: *`, `x-cache: Miss from
cloudfront`, and no `x-amzn-errortype` (OBSERVED, seq 4, 6, 8, 12, 14, 16, 20, 22, 24).

The `ACAM` values reproduce the recorded per-route ordering exactly: `OPTIONS,POST` for
`csr/v2`, `POST,OPTIONS` for bare `v2`, bare `OPTIONS` for `v6` — the same three orderings
area N recorded as stable across all three hosts. **OBSERVED**, and it is corroboration only
(see §4.3).

## 4. Verdict — all three stand, and the control now travels with them

**The fabricated path in each subtree answered `403` at the no-route digest while the real leaf
in the same subtree answered `200` with CORS, on all three hosts.** Nine pairs, nine consistent
answers. Read against the same-run controls:

| subtree | fabricated sibling | what a `403` there means | real leaf | reading |
|---|---|---|---|---|
| `csr/v2` | `403` `f249b63c…` | no route matched that path for `OPTIONS` | `200` + `ACAO *` | a route answers only at `display/message` |
| bare `v2` | `403` `f249b63c…` | same | `200` + `ACAO *` | same |
| `v6` | `403` `f249b63c…` | same | `200` + `ACAO *` | same |

An absent path in a subtree cannot answer `403` and a blanket-preflight subtree cannot answer
`200` for the same request shape on the adjacent leaf; that the two differ **within one subtree
in one run** is what makes the `200` a route signal rather than a subtree property (INFERRED —
this is the inference from nine control cells to three subtree properties, excluded for every
path tested and for the one fabricated name at the leaf depth in each subtree).

### 4.1 What changes in areas C, N and Z: nothing is retracted

`findings-log/2026-10-11-pde-csr-oracle/FINDINGS.md:69`,
`findings-log/2026-10-12-csr-cross-host/FINDINGS.md:58` and
`findings-log/2026-10-12-area-z-origin-reflection/FINDINGS.md:116` all keep their verdicts as
measured. What changes is the status of the **step** they rest on: on these three hosts the
`OPTIONS` half is no longer an assumption, it is a measured per-route resolution. **No
`## Correction` is appended to any of the three**, because the condition that would require one
— a fabricated sibling answering `200` — did not occur.

### 4.2 What this does NOT promote

1. **"POST-only" stays INFERRED.** `ACAM: OPTIONS,POST` advertises methods on a leaf whose `GET`
   is unrouted, and area N showed the same header shape on a GET-capable route, so the list is
   not a method register [source: findings-log/2026-10-12-csr-cross-host/FINDINGS.md §Verdict 2].
   No `POST` was sent. The body behind each route is token-gated and unobserved.
2. **Per-route is not per-route-everywhere.** This is measured under three bases on three
   cumulus hosts. It says nothing about `commoncore*`, the clinic hosts, `carelinkhp`, or any
   base not listed in §3.
3. **`ACAM` ordering is corroboration, not proof.** Three distinct orderings reproducing three
   prior observations is agreement with one source family (`csr/v2`, bare `v2` and `v6` were all
   recorded by the same pass family), not an independent confirmation.

## 5. What this does to `docs/09` §2 — a positive instance, not a correction

`docs/09` §2's `GET 403 + OPTIONS 200 → live, POST-only` rule presupposes per-route `OPTIONS`
resolution and previously established it only by analogy. This pass adds the positive instance
for `.com` and `.eu` and for bare `v2` and `v6` as well as `carepartner/v2`, so §2's assumption
now has direct OBSERVED support on all three cumulus hosts. §2 needs no correction from this
pass; the row it needs is a scope *strengthening*, and the `AY` row in `docs/11` carries it.

## 6. Limits — what this does NOT prove

1. **One run, three hosts, 2026-11-11.** A gateway reconfiguration after this date re-opens the
   question; nothing here is pinned into `regression/hurl/` (see §6.4).
2. **One fabricated name per subtree.** A preflight keyed on a hard-coded list of *some* unknown
   paths would evade it. No mechanism is proposed for such a thing, and nothing here tests for it.
3. **Depth.** The fabricated name sits at the leaf depth. A catch-all keyed one segment higher or
   lower would not be excluded. Area AP tested two depths on `-trials` and got `403` at both;
   this pass tested one depth per subtree.
4. **Not pinned.** These nine pairs are not in the regression suite, so this control is evidence
   as of its run date, not a standing assertion. A successor area could pin three of the nine.

## 7. Requests, spacing, and the two clocks

**24 of a 24 cap**, zero unspent, zero failures, zero retries, `curl_exit: 0` on all 24 rows,
`GET` + empty-body `OPTIONS` only, `sleep 2.5` held inside the per-host `flock`.

**Two clocks, one of them with a declared defect.**

- **Clock A — `t_sent`:** 21 gaps, of which **15 are clean** and **6 touch a corrupt row**
  (§7.1). Over the 15 clean gaps the **floor is 2.589 s, 0 under 2.5 s**. The 2 sub-2.5 s gaps in
  the whole set (`4→5` at 1.936 s, `11→12` at 1.974 s) both start on a corrupt row; across those
  same pairs the kernel-mtime gap is **2.660 s and 2.612 s**, both over the rule.
- **Clock B — kernel body mtime** (`stat -c %.9Y` on the response body, captured per request at
  request time): **24 bodies, 24 distinct mtimes**, spread **62.850 s**; 21 gaps, **floor
  2.589 s, 0 under 2.5 s**. This is the clock the spacing claim actually rests on, and it is
  proven to be a second clock rather than one batch stamp: the mtimes differ per row in the
  nanoseconds and each falls after its own `t_queued` (§7.1).
- ⚠ **Clock B is not re-derivable from a clean clone** — git does not preserve mtimes, and the
  bodies live in a gitignored scratch dir. Clock A is the one a stranger can reproduce from
  `results.jsonl` alone, and over its clean subset it agrees.

### 7.1 Disclosed harness defect — four rows carry a corrupt `t_sent`

Sequences **4, 8, 11 and 16** have `t_done < t_sent` (durations −0.600, −0.139, −0.561,
−0.793 s). On all four, `t_sent` reads **later** than the response body's own kernel mtime,
which is impossible in program order: no ordering of `t_sent`, `t_done` and `body_mtime`
satisfies it. So it is not "one bad field" — the `date`-derived fields on those rows are
mutually inconsistent and **all four must be treated as unreliable**, not just `t_done`.

- **Cause: NOT ESTABLISHED and not asserted.** It is the class `docs/09` §4 already records as a
  known corrupt-`t0` failure in this harness shape.
- **Cost: 6 of 21 clock-A gaps** (each of the four rows is the start of one gap and the end of
  another, with seq 4 and 16 sharing neighbours). The published clock-A floor is quoted over the
  **15 clean gaps** for that reason, and the 2 sub-2.5 s gaps are attributed to the defect with
  the clock-B gap across the same pairs given beside them.
- **Effect on the verdicts: none.** Every verdict in §3 is derived from HTTP status, body bytes,
  digest and headers — no timing field anywhere. The defect is quarantined in this section.
- `verify.py` re-derives all of the above at zero requests and **fails** if the corrupt set is
  not exactly {4, 8, 11, 16} or if any published figure moves.

## 8. Reproducing this at zero requests

```
python3 findings-log/2026-11-11-area-aq-options-per-route/verify.py
```

Re-derives the row count, both controls on all three hosts, the 3 × 3 matrix, the per-subtree
verdict, the corrupt-row set, the 21-gap count against `sum(rows_per_host − 1)`, the clean-gap
floor and both clocks. Exits 0 only when every one holds. It issues no requests.

## 9. The letter — `AQ` was already taken, and this is the disclosure

This lane was chartered as **area AQ** and built its directory under that name. Reading
`origin/main` at build time showed **`AQ` in use twice**:

| holder | claim | merged | where |
|---|---|---|---|
| the `hcp/patients/` subtree pass | **#199**, 01:05:47 | **PR #203, 01:38:33** | closed row `| AQ —` |
| **this pass** | #209 | **not merged** | open heading `### AQ.` as built |

**The `hcp/patients/` pass claimed the letter first and merged it**, so under merge order it keeps
`AQ` and this area is recorded as **`AY`**. Area AR's and AS's cross-references to "area **AQ**"
were written about the `hcp/patients/` pass, which is what they still mean.

`docs/11` now has **no letter used twice** (`^### [A-Z]{1,2}.` headings and `| XX —` rows,
compared as sets), and the count sentence reads **9 open plus 43 closed** as printed by
`python3 scripts/research-checks.py` at this head — quoted, not computed. The letter `AZ` is
minted for the successor; `AY` is retired by this close.

## Correction (2026-11-11) — §9's citation conflated two commits; the yield itself was right

A verifier found this and it is narrower than it first looked.

§9 said the `hcp/patients/` area took `AQ` at **`a206944` (01:18 UTC, "PR #200/#203")** and closed
it with the `| AQ —` row. Both halves of that citation are wrong in the same way — they merge two
commits into one:

| what actually happened | commit | time (UTC) |
|---|---|---|
| `hcp/patients/` mints `AQ` **in prose**, as AR's successor name | `a206944` | 01:18:23 |
| this pass's `### AQ.` **heading** enters `main` | `5a24fd1` | 01:23:30 |
| the `| AQ —` **closed row** for `hcp/patients` enters `main` | `cae2127` | 01:38:32 |

`a206944` contains **no AQ row at all** — that commit closed area AL. The row the sentence names
arrived twenty minutes later in a different PR.

**The yield decision stands, and on the correct grounds.** The `hcp/patients/` area claimed the
letter in issue **#199 at 01:05:47**, eighteen minutes before this pass's heading landed, and it
**merged at 01:38:33** while this pass has never merged. Under merge order — the rule this
repository states — `hcp/patients` keeps `AQ` and this area is `AY`. The citation was wrong; the
conclusion was not.

⚠ **A correction to an earlier correction.** My first attempt at this section went further: I read
`git log -S '### AQ.'` as settling "who was first" by when the *string* appeared (01:23:30) and
re-lettered this area back to `AQ`. That was wrong. `git log -S` measures when a string entered a
file, not who holds a claim — and the claim was taken at 01:05:47 and honoured by a merge at
01:38:33. Reverted. **Appearance in a file is not registration; a claim plus a merge is.**
