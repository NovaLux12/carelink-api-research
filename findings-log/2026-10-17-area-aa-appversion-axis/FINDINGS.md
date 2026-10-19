# Area AA — does the `android/<app-version>` axis gate anything on `.com` and `-trials`, or only on `.eu`?

Pass of **2026-10-17**, written up 2026-10-19. Claim issue **#151**. Branch
`research/aa-appversion-axis`.

**Answer, up front.** The axis is **gating at base `v13` on both `.com` and
`-trials`, and not gating at base `v6` on `-trials`.** It is also **not a
validation gate anywhere**: a syntactically fabricated tail
(`android/absent-probe-871`) answers `200` on both hosts at every base that
serves at all. So the area's either/or — "content gate or echo" — is the wrong
pair of terms. The tail is *both* echoed into the payload and, at `v13`,
selective about which document comes back. §4 gives the per-cell evidence.

**20 of a 20 cap** — all 20 requests sent, GET only, cap not revised. One deviation
is disclosed in full
(§2). No pin is added, for the reason in §7.

---

## 1 · Request accounting

Ledger: [`results.jsonl`](./results.jsonl) — **20 rows**, one per request, `seq`
1…20 with no gaps and no duplicates. Harness: [`probe.sh`](./probe.sh), whose
`CAP=20` (`:74`) and `DELAY=2.5` (`:75`) were asserted before every send — the cap
is re-checked at `:109-110` and the delay applied at `:153`, inside the lock.

| # | host | base | app-version | role | status | B | `body_sha256` |
|---|---|---|---|---|---|---|---|
| 1 | `clcloud.minimed.com` | `v99` | `3.6` | control-absent | 403 | 42 | `f249b63cb2fcb66b…` |
| 2 | `clcloud.minimed.com` | `v11` | `3.6` | control-served | 200 | 18105 | `2103b7e850c4ad9c…` |
| 3 | `clcloud.minimed.com` | `v13` | `3.5` | data-v13 | 200 | 20256 | `192c47c062d71c15…` |
| 4 | `clcloud.minimed.com` | `v13` | `3.6` | data-v13 | 200 | 20256 | `f84886265667b1b6…` |
| 5 | `clcloud.minimed.com` | `v13` | `3.9` | data-v13 | 200 | 18105 | `015a25288ba89bb3…` |
| 6 | `clcloud.minimed.com` | `v13` | `absent-probe-871` | data-v13 | 200 | 18118 | `8786c15268d3788e…` |
| 7 | `clcloud.minimed.com` | `v6` | `3.5` | data-v6 | 403 | 42 | `f249b63cb2fcb66b…` |
| 8 | `clcloud.minimed.com` | `v6` | `3.6` | data-v6 | 403 | 42 | `f249b63cb2fcb66b…` |
| 9 | `clcloud.minimed.com` | `v6` | `3.9` | data-v6 | 403 | 42 | `f249b63cb2fcb66b…` |
| 10 | `clcloud.minimed.com` | `v6` | `absent-probe-871` | data-v6 | 403 | 42 | `f249b63cb2fcb66b…` |
| 11 | `clcloud-trials.minimed.com` | `v99` | `3.6` | control-absent | 403 | 42 | `f249b63cb2fcb66b…` |
| 12 | `clcloud-trials.minimed.com` | `v11` | `3.6` | control-served | 200 | 20345 | `94b739dda4784c7b…` |
| 13 | `clcloud-trials.minimed.com` | `v13` | `3.5` | data-v13 | 200 | 20256 | `192c47c062d71c15…` |
| 14 | `clcloud-trials.minimed.com` | `v13` | `3.6` | data-v13 | 200 | 20256 | `f84886265667b1b6…` |
| 15 | `clcloud-trials.minimed.com` | `v13` | `3.9` | data-v13 | 200 | 16369 | `66ac7fbd19a28b5a…` |
| 16 | `clcloud-trials.minimed.com` | `v13` | `absent-probe-871` | data-v13 | 200 | 16382 | `fa4711cc4801a8e9…` |
| 17 | `clcloud-trials.minimed.com` | `v6` | `3.5` | data-v6 | 200 | 10053 | `9b61847639ce66a0…` |
| 18 | `clcloud-trials.minimed.com` | `v6` | `3.6` | data-v6 | 200 | 10053 | `1aab9bb1e721254c…` |
| 19 | `clcloud-trials.minimed.com` | `v6` | `3.9` | data-v6 | 200 | 10053 | `a8903df2e934737e…` |
| 20 | `clcloud-trials.minimed.com` | `v6` | `absent-probe-871` | data-v6 | 200 | 10066 | `bad674413bc3746b…` |

Every row above is `results.jsonl:<seq>`; every status, byte count and digest in
it is the harness's own record, not a re-read. `run.log` carries the same values
per request, and `headers/<NN>-*.h` / `.b` are the captured heads and bodies.
`gh-run-err.log` is **empty** and is kept as evidence that the pre-send gate
check ran and wrote nothing.

### Controls, as actually sent

Both controls were sent **first on each host**, before any data cell
(`probe.sh:153` runs the gate check, then the sleep, inside the lock):

- **certainly-absent** `v99` at `android/3.6` — `403` at the corpus 42 B
  no-route digest `f249b63cb2fc…` on **both** hosts (`results.jsonl:1`,
  `:11`). The oracle is sound on both hosts.
- **served** `v11` at `android/3.6` — `200` on both hosts
  (`results.jsonl:2`, `:12`).

`AGENTS.md` §8 notes the `clcloud.*` `403` line is uniform and useless and that
`x-amzn-errortype` is the signal. All six `403` cells carry
`x-amzn-errortype: MissingAuthenticationTokenException` and **all six are the
same digest** — one envelope, not six distinct answers (§6).

### Spacing

[`spacing.py`](./spacing.py) → [`spacing.txt`](./spacing.txt), re-run for this
write-up. **Counting rule:** one gap per consecutive same-host pair in request
order, so 10 bodies give 9 gaps per host. **Two clocks** are reported — the
`t_sent` field in the ledger, and the capture file mtime — because one clock alone
cannot catch a mis-stamped date series. They are two *measurements*, not two
sources: both come from this one run, so under `AGENTS.md` §2.1 the count is **1**
and neither is described as corroborating the other.

| host | gaps | `t_sent` min | `t_sent` max | gaps < 2.5 s | gaps < 2.0 s |
|---|---|---|---|---|---|
| `clcloud.minimed.com` | 9 | **3.304 s** | 8.992 s | **0** | **0** |
| `clcloud-trials.minimed.com` | 9 | **3.425 s** | 9.051 s | **0** | **0** |

**Measured floor: 3.304 s**, against a stated 2.5 s and a repo floor of 2 s
(`AGENTS.md` §8). The mtime series gives 3.312 s / 3.442 s minima
with the same zero counts.

Two things are reported rather than smoothed. First, the series **disagree** on
2 of 9 gaps (`.com`) and 4 of 9 (`-trials`) by more than 0.5 s; that is a
reordering around the one slow request in each host's second cell (`.com` seq 2
took 5.77 s of wire time), not a spacing failure — the span check bounds it
(mtime span 36.906 s vs `t_sent` span 37.022 s, 0.12 s apart) and **every gap
clears the floor on both clocks**. Second, `spacing.py`'s self-conviction check
reports **0 of 20** rows with `t_done < t_sent`, so the series is not
self-refuting and its gaps are evidence.

---

## 2 · Host deviation from claim #151 — disclosure

**Claim #151 named `carelink.minimed.com` and `carelink-trials.minimed.com`.
This pass sent `clcloud.minimed.com` and `clcloud-trials.minimed.com`.** The
claim's literal host list was wrong for this route family.

**Why the claim was wrong.** The route under test is
`/connect/carepartner/<base>/discover/android/<tail>`, and that path is
published on the **cumulus** hosts, not on the `carelink.*` app/API hosts. The
bridge reads it from `baseUrlCumulus`, which
[`docs/03` §1](../../docs/03-discovery-and-versions.md) records as
`…clcloud-trials.minimed.com/connect/carepartner/v13`, and the same section lists
the three hosts the discovery document is read from as
`clcloud.{minimed.eu, minimed.com, clcloud-trials.minimed.com}`. A `carelink.*`
host is a different plane: it is
where `baseUrlCareLink` points, not where discovery lives.

**Does it answer the area as posed?** **Yes, for the question the area asks,
and no for the literal wording.** The area's question is whether the app-version
axis gates anything on `.com` and `-trials` — and `.com`/`-trials` are the
*deployment* designations, carried by `clcloud.minimed.com` and
`clcloud-trials.minimed.com`. The axis on the `carelink.*` hosts was not swept,
so this pass **does not** speak to it, and no sentence in this log should be
read as doing so. Recorded as a correction to the claim's host list, not as a
narrowing that preserves the claim's wording.

---

## 3 · Cross-check against the prior closed row — no contradiction

Area C's closed row records that "the bare `connect/carepartner/` prefixes [are]
dead on both [methods]"
([`docs/11` Closed table, row C](../../docs/11-suggested-research-areas.md);
source `findings-log/2026-10-11-pde-csr-oracle/FINDINGS.md:72-77`). That row's
own cells are the **prefix parents** — `connect/carepartner/`,
`connect/carepartner/v13`, `connect/carepartner/v13/discover` — each `403` on
`GET` and `OPTIONS`, and the log describes them as "prefix parents of
known-live leaves" (`FINDINGS.md:30-31`).

These cells are `/connect/carepartner/v{11,13}/discover/android/<tail>` — a
fully-routed leaf four segments below that prefix. **Distinct claims, not a
contradiction.** The precedent for the distinction is already written down for
the neighbouring namespace at `docs/00-summary-the-map.md:93` ("the bare
`/connect/pde/v3` prefix itself was never requested, so 'the namespace is
unroutable' is a statement about the two recorded paths"). Noted in one line,
as required, and not written around.

---

## 4 · Echo or gate — the actual result

The area framed this as *gate or echo*. Both are true at once, and the
discriminator is in the bodies, not the status line.

**Instrument.** [`structure.py`](./structure.py) → [`structure.txt`](./structure.txt).
Zero requests; it reads only the captured bodies under `headers/`. Method:
replace the requested tail with a fixed marker wherever it occurs, re-serialise,
and sha256 the result. A pure echo cannot survive that. **Counting rule:** one
canonical group per distinct tail-erased digest; a group of size **1** proves
nothing about constancy, and only groups of size ≥2 are cited as evidence of the
tail *not* varying the rest of the body.

### 4.1 The echo — OBSERVED, all 14 documents

Every one of the 14 `200` bodies begins `{"config":"android,<requested tail>",`
and the tail occurs **exactly once** in the body bytes in every case
(`structure.txt`, "Q1"). The fabricated tail `absent-probe-871` was echoed
verbatim and answered `200` at three cells — `results.jsonl:6`, `:16`, `:20`.
**There is no allow-list on this segment:** not `400`, not `404`, not `403`.

### 4.2 The gate — OBSERVED at base `v13`, on both hosts

After the echo is erased, base `v13` yields **three** distinct documents per
host, and the tail selects between them:

| tail | `clcloud.minimed.com` | `clcloud-trials.minimed.com` |
|---|---|---|
| `3.5` | `a803d42bcd09` · advCumulus **v11** · carelink v2 · CP 3 · ctry 109 | `a803d42bcd09` · advCumulus **v11** · carelink v2 · CP 3 · ctry 109 |
| `3.6` | `7ad212402d7f` · advCumulus **v13** · carelink v2 · CP 3 · ctry 109 | `7ad212402d7f` · advCumulus **v13** · carelink v2 · CP 3 · ctry 109 |
| `3.9` | `7ac09335c7e4` · advCumulus **v2** · carelink v1 · CP 2 · ctry 99 | `9962b3db79b1` · advCumulus **v2** · carelink v1 · CP 2 · ctry 76 |
| `absent-probe-871` | `7ac09335c7e4` — **same group as `3.9`, n=2** | `9962b3db79b1` — **same group as `3.9`, n=2** |

The selection is substantive, not cosmetic. Going `3.6` → `3.9` changes the
advertised `baseUrlCumulus` base (`v13` → `v2`), the `baseUrlCareLink` API
version (`v2` → `v1`), the `CP[]` length (3 → 2, i.e. the CLINICAL entry
disappears), the country count (109 → 99 / 76), and the SSO config file family
(`oauth20_sso_carepartner_*_v6.json` → `sso_cp_us_v6.json` /
`eu_sso_cp_eu_v6.json`). **This is a gate.**

The `3.5` and `3.6` documents are **byte-identical across the two hosts** —
the same canonical digests, and the same raw digests at `results.jsonl:3`/`:13`
(`192c47c062d71c15…`) and `:4`/`:14` (`f84886265667b1b6…`). The `3.9`-class
document is **not**: it carries the EU SSO entry and 99 countries on `.com`
against a US-only 76 on `-trials`.

### 4.3 Not gating — base `v6` on `-trials`

At `clcloud-trials.minimed.com` base `v6`, all four tails collapse to **one**
canonical digest `3b9d84b2525c`, **n=4** (`results.jsonl:17`, `:18`, `:19`,
`:20`). The tail is echoed and **nothing else about the request varies the
body**. This is the strongest single result in the pass: a four-cell group where
a fabricated tail is indistinguishable from three numeric ones.

That cell is also a **re-derivation, not a new claim** — `results.jsonl:18`
(`1aab9bb1e721254c…`, 10053 B) is the same digest and byte count the
2026-10-17 three-host matrix pass recorded for trials `v6` at `android/3.6`
(`findings-log/2026-10-17-discover-3host-matrix/FINDINGS.md:113,:143`). Per
`AGENTS.md` §2.1 that is **one source** — this repository — observed twice, not
two independent sources, so no strength word is used for it.

### 4.4 No verdict — base `v11`, and base `v6` on `.com`

Base `v11` was sent at **one** tail only, as the served control. One cell cannot
distinguish "selects" from "does not select"; `structure.py` emits `NO VERDICT`
there rather than a number. Likewise base `v6` on `clcloud.minimed.com`, where
there is no document for the tail to select (§5).

---

## 5 · The `v6` host split **reads as** a base-axis effect, not an app-version effect

**The reading is INFERRED; the refutations it rests on are OBSERVED.** The class
is carried into `docs/03` §3b.4 and `docs/11` wherever the claim is asserted, so
no page states it as fact.

`clcloud.minimed.com` answers `403 MissingAuthenticationTokenException` on **all
four** `v6` cells (`results.jsonl:7-10`) at the corpus no-route digest
`f249b63cb2fc…`; `clcloud-trials.minimed.com` answers `200` on all four
(`:17-20`). The area flagged this as possibly a route-family difference rather
than an app-version effect, and **the rows rule that one reading out** (the
refutation is OBSERVED, the reading it supports is INFERRED):

**The `403` is not explained by the tail.** The served control on the *same
host*, at the *same tail* `3.6`, returned `200` (`results.jsonl:2`,
`base v11`) — that cell is OBSERVED. Reading the discriminator as the
**base segment** rather than the tail — all four tails behave
identically under `v6`, and the one cell that varies only the base flips the
answer. That is what makes it a base-axis fact (**INFERRED**).

**What the rows cannot separate.** Whether `v6` is unrouted on `.com` because of
the *version segment* or because of the `v6/discover/android/*` *route family*
is **not established here** — no `v6/display/message` cell and no
`v6/discover` prefix cell was sent on that host. This is consistent with, and
does not contradict, the prior matrix pass, which recorded `v6` as `no-route` on
both patient hosts at the base-axis level
(`findings-log/2026-10-17-discover-3host-matrix/FINDINGS.md:113`); it neither
adds to nor overturns that. **No choice is made between the two readings.**

---

## 6 · What the rows do not establish

- **Lookup table or threshold rule.** Only four tails were sent — `3.5`, `3.6`,
  `3.9`, one fabricated — and they are adjacent. A boundary anywhere in
  `(3.5, 3.6]` or `(3.6, 3.9]` is exactly as consistent with the data as a
  per-value table. **Cannot be separated.** This is the load-bearing unknown and
  it is what successor **AE** is for.
- **Why the fabricated tail lands on the `3.9`-class document.** Consistent with
  "unrecognised tails fall back to the legacy/default document"; equally
  consistent with "any tail outside the current-generation pattern falls
  through". Two informative observations would not settle it — at `v6` the
  fabricated tail tells us nothing, because every tail there gives the same
  document (§4.3).
- **The `3.9`-class document's host difference.** Why `.com` carries an EU SSO
  entry and 99 countries where `-trials` carries US only and 76 is **not
  established**; no row varies the country axis.
- **`x-cum-signature`.** All 14 `200` cells carry a 344-char signature and every
  one differs per cell. This pass did **not** vary the axis that would settle
  whether it is a function of `(document, host)` as `docs/03` §1 now holds, and
  **makes no claim about it.** Two of the `v13` documents each arrive byte-identical
  on both hosts — `results.jsonl:3`/`:13` (`192c47c062d71c15…`, the `3.5` cell) and
  `:4`/`:14` (`f84886265667b1b6…`, the `3.6` cell) — which is the shape `docs/03` §1
  already records. Restated, not re-derived.

---

## 7 · No pin added — measure, do not pin

**No assertion is added to `regression/hurl/` by this pass**, as the area
directed. The candidate is the trials `v6` block — a **four-cell canonical group
(tail-erased digest `3b9d84b2525c…`, n=4) across four different tails**. State the
right identifier: the four bodies have four *different* raw digests
(`9b61847639ce…` / `1aab9bb1e721…` / `a8903df2e934…` / `bad674413bc37…`, byte counts
10053/10053/10053/10066); only after the echoed tail is erased do they collapse to
one. `1aab9bb1e721…` is the **`3.6` cell's raw digest alone** and is the value the
matrix pass recorded. It is the cleanest negative in the corpus and the most
tempting thing to freeze.

It is not worth the budget. `AGENTS.md` §11 gives the weekly drift sweep a budget
of **~80 requests per sweep**; pinning the `v6` block costs **4 requests per sweep** on
every push forever, and the same sweep would still be needed to notice the one
change that would actually matter — the *departure* of the `3.6`-class document
at `v13`. The prior matrix pass declined the same pin for the same reason
(`findings-log/2026-10-17-discover-3host-matrix/FINDINGS.md:235`). **Measure.**

---

## 8 · Independence

One lane, one run, one ledger, one author. Under `AGENTS.md` §2.1 the count is
**1** for every claim here, including the cross-host byte-identity at `3.5`/`3.6`
— a single run reporting on two hosts is one source observed twice. The words
*independently*, *corroborated*, *confirms* and *double-sourced* carry no claim in
this log or in the prose derived from it; where agreement between measurements is
worth reporting it is named as coherence (*consistent with*, *does not contradict*)
rather than multiplicity.

## 9 · Evidence table

| # | Claim | Class | Source |
|---|---|---|---|
| 1 | 20 requests sent, 20 ledger rows, cap not revised | OBSERVED | `results.jsonl:1-20`; `probe.sh:74` |
| 2 | Same-host spacing floor 3.304 s, 0 gaps under 2.5 s | OBSERVED | `spacing.txt` §measured floor |
| 3 | Both hosts: `v99` control `403` at `f249b63cb2fc…`, `v11` control `200` | OBSERVED | `results.jsonl:1`, `:11`, `:2`, `:12` |
| 4 | Claim #151's host list was wrong for this route family | INFERRED | judgement; the supporting publication is `docs/03` §1 |
| 5 | Area C's bare-prefix row is a distinct claim, not a contradiction | INFERRED | judgement; the supporting cells are `findings-log/2026-10-11-pde-csr-oracle/FINDINGS.md:30-31`, `:72-77` |
| 6 | All 14 `200` bodies echo the requested tail exactly once | OBSERVED | `structure.txt` §Q1 |
| 7 | A fabricated tail answers `200` — no allow-list | OBSERVED | `results.jsonl:6`, `:16`, `:20` |
| 8 | At `v13` the tail selects 3 documents per host | OBSERVED | `structure.txt` §Q2 |
| 9 | At trials `v6` the tail selects nothing (n=4) | OBSERVED | `structure.txt` §Q2; `results.jsonl:17-20` |
| 10 | The `v6` `403` on `.com` is a base-axis effect | INFERRED | the refutations are OBSERVED (`results.jsonl:2` vs `:7-10`); the reading that the base segment is the discriminator is one step further |
| 11 | trials `v6` digest is a re-derivation of the matrix pass | OBSERVED | `findings-log/2026-10-17-discover-3host-matrix/FINDINGS.md:113`, `:143` |
| 12 | Lookup-vs-threshold is not separable from four tails | INFERRED | §6; assumption stated there |
| 13 | Base `v11` and `.com`-`v6` carry no verdict | INFERRED | `structure.txt`; one cell / no cell |
| 14 | Every claim above rests on 1 source | INFERRED | an audit conclusion about source identity, not something seen in a response — same species as rows 4 and 5 |
