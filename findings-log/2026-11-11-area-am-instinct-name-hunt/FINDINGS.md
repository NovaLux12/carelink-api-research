# Area AM — do `SKU-78963/78964/78965/78968-01` carry a product name anywhere the vendor serves publicly?

**Pass date:** 2026-11-11 · **Claim issue:** [#195](https://github.com/NovaLux12/carelink-api-research/issues/195)
**Branch:** `research/am-instinct-name-hunt` · **Ledger:** `results.jsonl` (16 rows, one per HTTP request)
**Harness:** `probe.sh` (requests) · `extract.py` (offline extraction, zero requests)
**Plan, written before the first request:** [`PLAN.md`](PLAN.md)

## Verdict

**All four codes carry a name, it is vendor-published, unauthenticated, and it is not
`Instinct™ Go`.** A key-addressable route this repository had only ever *inventoried* answers
200 with a full name table on all three patient deployments.

| code | name (`name` / `shortName`) | `family` | US `patientListPremium` | EU (GB/DE) `patientListPremium` |
|---|---|---|---|---|
| `SKU-78963-01` | **`Instinct Sensor`** | `INSTINCT` | `Instinct` | `Instinct Go` |
| `SKU-78964-01` | **`Instinct Sensor`** | `INSTINCT` | `Instinct` | `Instinct Go` |
| `SKU-78965-01` | **`Instinct Sensor`** | `INSTINCT` | `Instinct` | `Instinct Go` |
| `SKU-78968-01` | **`Instinct Sensor`** | `INSTINCT` | `Instinct` | `Instinct Go` |

**OBSERVED**, not inferred: `GET /patient/configuration/system/model-mapping/US` → 200,
39 157 B, `application/json`, on `carelink.minimed.com` **and** `carelink.minimed.eu`
(one digest, `f0efac1d…`); `…/GB` and `…/DE` → 200, 40 105 B, `7f73c467…`. Every one of the
four appears **twice** in each document — once as `SKU-<n>-01` and once bare `<n>-01` — and
both forms carry the same name. Evidence: `results.jsonl` seq 13–16; `tail-names.tsv`;
`coverage-13.tsv`; `instinct-model-mapping.tsv`.

**The answer to the question as posed is yes, and it changes a `docs/05` claim that said no.**
`docs/05`'s 2026-11-10 correction (area AI) ends *"A name for the four present tail codes would be
a guess and none is offered."* That sentence was true of the corpora area AI held; it is **false
against the vendor's live surface**, and `docs/05` now carries a dated correction blockquote
rather than a silent rewrite of it.

**What the name is not.** The four codes are `Instinct Sensor` in *both* markets. The
`Instinct Go` string **never appears as a `name`** in either document (`instinct-model-mapping.tsv`
— 0 rows). It appears only in `features.patientListPremium` / `patientListNonPremium` /
`patientDashboard` on the EU copy, and **`Instinct Go` is `0` occurrences in the US body**
(`grep -c` returns 0; first EU occurrence at byte 11 948). So `Instinct Go` is a **EU-package
feature-string**, not a product name attached to a SKU — and the `Instinct™ Sensor` /
`Instinct™ Go` split area G read out of the portal device table **is not reproduced by this
document**: all 13 family-map codes, named or not, carry `name: "Instinct Sensor"` and are
separable only in `features`. `MMT-5420` is the one exception and keeps `Instinct™ Sensor`
(with the trademark) in both markets.

## Method, and why this method

**Two document fetches per host then a local scan — not a per-SKU probe.** Every corpus in this
pass is either a whole document or a whole bundle, so one request buys the entire population and
the scan costs nothing. A per-SKU GET cannot answer the question: no sub-key grammar for
`/patient/configuration/system/<key>.<SKU>` is recorded anywhere in this repository, and
inventing one is wordlist fuzzing (`findings-log/2026-11-10-area-ai-instinct-sku-tail/FINDINGS.md`
§Method). Requests 1–6 bought the oracle; 7–12 bought the only bundle in this lane's reach; 13–16
bought the documents the question actually needed.

### Where the route came from — and why it counts as derived, not guessed

The route is **not** new intelligence about the vendor's naming. It is written in the patient
bundle this pass fetched at seq 7, at **byte 3374392**:

```js
getDeviceModelMapping(V){return this.http.get(`patient/configuration/system/model-mapping/${V}`)}
```

called at byte **2165828** as `D.getDeviceModelMapping(y.code)` where `y` is the country store
(`setAndEmitCountryByCode(Ve.country)`, byte 2166531). Its only two prior mentions in this
repository are **call-site inventory rows, never a verdict**:
`findings-log/2026-10-14-area-s4-lazy-chunk-control-flow/pairs.tsv:63` and
`findings-log/2026-10-14-area-k-clinic-controlflow/differential.json:319`. So the request list
was **read out of the artefact**, not imagined — `AGENTS.md` §8's "derived from an observed
naming convention, with the reasoning recorded".

Country codes `US`/`GB`/`DE` come from `findings-log/2026-10-12-area-d-country-sweep/candidates.txt`,
which derived 118 codes offline from published config documents with provenance per code.

### Request accounting — **16 of a 16 cap**

GET only throughout: literal `GET`, no `-X`, no `-d`, no POST, no OPTIONS, no token, no cookie, no
authentication, no wordlist, no DNS. Three hosts, all in this lane's set:
`carelink.minimed.com`, `carelink.minimed.eu`, `carelink-trials.minimed.com`.
**6 controls + 6 assets + 4 documents = 16. Nothing left unspent.**

**Declared delay `sleep 2.5` inside the per-host `flock`** — one `flock 9` per request, the sleep
and the curl both inside it. **Measured same-host spacing floor 2.609 s by the kernel body-mtime
oracle**, 13 gaps across the three hosts (4 + 6 + 3), **0 under 2.5 s**
(`.com` 2.682/15.968/2.814/98.809 · `.eu` 2.617/16.317/2.618/96.038/2.609/2.620 ·
`-trials` 2.833/16.665/2.843). Every gap is ≥ 2.5 s.

⚠ **The `t_sent` series disagrees with itself and that is disclosed, not smoothed.** It reads a
**1.751 s** gap (seq 3→4, `carelink.minimed.eu`) — under the declared 2.5 s and under the repo's
2 s floor — and **two negative durations** (seq 3: `t_done` 01:13:34.158Z before `t_sent`
01:13:34.968Z; seq 8: `t_done` 01:13:50.326Z before `t_sent` 01:13:50.551Z). This is the known
corrupt-`t0` class `docs/09` §4 records; **no cause is asserted**. The body-mtime oracle does not
depend on the harness clock, and it reads 2.617 s for that same seq 3→4 pair. That oracle is
**not re-derivable from a clean clone** (git does not preserve mtimes) and is recorded as observed
in this run only.

## Controls, in send order — 6 of 6 PASS

Two controls **per host, first**, before any asset or document on that host.

| # | Host | Control | Result | What it proved |
|---|---|---|---|---|
| 1 | `.com` | certainly-absent `zzz.not.a.real.key.zzz` | **404**, 0 B, `text/vnd.a` | a 404 in this namespace is a real absence, not a catch-all — so the 200s below are documents |
| 2 | `.com` | known-live `logbook.supported.entry.types` | **200**, 281 B, `7f0a5bb4…` | the route family is live; reproduces area E seq 2 and area AI seq 2 |
| 3,4 | `.eu` | the same two | 404 / 200 281 B `7f0a5bb4…` | as above |
| 5,6 | `-trials` | the same two | 404 / 200 281 B `7f0a5bb4…` | as above |

`probe.sh` **stops the run** (`exit 3`) if either control disagrees — the check is an explicit
branch on status, byte count and the `text/vnd.a` content type, not an absent-output test.

**No separate control was bought for the `model-mapping` batch**, and that is deliberate: those
four paths sit in the *same namespace* as control 1, which returned 404 / 0 B / `text/vnd.a` on
all three hosts. The 404 rule therefore already reads on them. On a 200 the body must parse and
carry `name`/`family` per model or `extract.py` exits 2 — so a wrong document cannot be read as
a name.

## The assets — what the bundles did and did not contain

| seq | host | path | result |
|---|---|---|---|
| 7, 9, 11 | `.com`, `.eu`, `-trials` | `/main.6595daf83bd6d4b1.js` | **200**, 3 417 255 B, `0fb4fbd4…` on all three — reproduces area V seq 3/7 in full |
| 8, 10, 12 | `.com`, `.eu`, `-trials` | `/main.fb5f8cb7eb60c4d5.js` | **404**, 196 B, `text/html; charset=iso-8859-1`, `80c3fe2a…` on all three |

**The patient bundle contains no `7896x` token at all** — `7896\d` is **0 hits** in 3 417 255
bytes, and `SKU-`, `78893`, `78953` are likewise 0. The only `Instinct` strings in it are three
occurrences inside an **event-type table** (`{type:"INSTINCT",label:"Instinct Event",
description:"Generic Instinct app event"}`, byte 3322809) — no model code, no name. So the eager
bundle is not a name source, and the names came from the *route it names*, not from its bytes.

**The clinic build does not answer on a patient host** (404, 196 B, one digest on all three), so
the portal device table stayed out of reach — as the lane brief required. This is recorded as a
measured negative rather than assumed: one request per host, 3 of 16.

## The four documents

| seq | host | path | status | bytes | sha256 |
|---|---|---|---|---|---|
| 13 | `.com` | `…/model-mapping/US` | **200** | 39 157 | `f0efac1d2a97d092a75dfe86d43e6b92cfdc38490f0f32bbb2a68755a4a6c434` |
| 14 | `.eu` | `…/model-mapping/US` | **200** | 39 157 | `f0efac1d…` **same** |
| 15 | `.eu` | `…/model-mapping/GB` | **200** | 40 105 | `7f73c467c70ec571657c6d5b0b71d70a92330ddc5eba817ad2940345f1edf22c` |
| 16 | `.eu` | `…/model-mapping/DE` | **200** | 40 105 | `7f73c467…` **same** |

**Structure (OBSERVED, asserted by `extract.py` before any comparison):** five top-level
categories — `StandaloneCGM` 19, `InsulinDelivery` 14, `METER` 29, `SENSOR` 59, `PUMP` 73 — each a
code → object map carrying `name`, `shortName` and optionally `family`, `features`, `minValue`,
`maxValue`. Four `DEFAULT` sentinels carry no `name`; **no other entry lacks one**, and the script
aborts if any does.

**`US` is one document across two deployments; `GB` and `DE` are one document across two
countries.** That is two documents, not four observations — so the `US` vs EU difference below is
**one source**, and no strength word applies (§2.1).

### What differs between the two documents

**`US` vs `GB`: 53 of 194 entries differ**, and **30 of the 53 are the `INSTINCT` `SENSOR`
entries** — every one of them for the same two reasons:

1. a `maxValue: 500` field present in the EU copy and absent in the US copy, and
2. the four `features` strings: US `Instinct` / `Instinct sensor (MiniMed Go™ app)` vs
   EU `Instinct Go` / `Instinct Go sensor (MiniMed Go™ app)`.

`name` and `shortName` are **identical in both** — `Instinct Sensor`. The remaining 23 diffs are
outside this question (`MMT-8600`/`8601`/`8602` `withSensor` arrays, the 14 `InsulinDelivery`
`patientDashboard` **i18n keys** (`minimedgo.inpen.name.US` — a translation key, not a name), 6
`PUMP` entries, 3 `StandaloneCGM`).

**Deltas against `docs/05`, all OBSERVED in these documents:**

- `MMT-5420` → `Instinct™ Sensor`, `family: INSTINCT` — **present here**, `name` not a `features`
  string. Consistent with the portal table and with report-list index 102; it is still in **no**
  family row, which this pass does not re-derive.
- `MMT-8600`/`MMT-8601` → `MiniMed™ Go` (US) with a **two-entry `withSensor` array**
  (`SIMPLERA` 50–400, `INSTINCT` 40–400); `MMT-8602` → `MiniMed Go Clinical`, same two families.
  So the document itself states that a **`MiniMed Go` pump pairs with an `INSTINCT` sensor** —
  a relation no source in this repository recorded before, and one this pass does **not** need to
  interpret.
- `MMT-8400`/`MMT-8401`, `MMT-8200`/`MMT-8201` present with names — consistent with area G.

## What was searched and found empty (negatives)

- **No `Instinct Go` as a product name.** `name`/`shortName` for all 13 family-map codes is
  `Instinct Sensor` in **both** documents; `Instinct Go` appears only in `features` and only in
  the EU copy. `MMT-5420` is `Instinct™ Sensor`.
- **`78961`, `78962`, `78966`, `78967` are absent from this document too** — both key forms, both
  markets. That reproduces area AI's finding on a **third** vendor source, and it is the strongest
  form of it now available: three independent documents (family map, report list, model mapping)
  each enumerate the range and each skip these four. This row is *corroboration of an existing
  claim*, not a new finding, and is recorded as such.
- **No `7896x` string in the patient eager bundle** (0 hits in 3 417 255 B).
- **The clinic build does not answer on a patient host** (404, 196 B, one digest, 3 of 3).

## Limits, stated

- **The two portal builds were not read.** They live on the HCP/portal host family, which belongs
  to another lane in this pass; seq 8/10/12 only establish that the clinic *asset name* 404s on a
  patient host. So this pass cannot say whether the **portal device table grew** since 2026-10-13
  — the question the brief raised. Its 236-entry report-list drift is recorded elsewhere
  (`findings-log/2026-11-03-report-list-drift/`); **no claim here depends on it**.
- **The HCP `pow.common.core.report.generation.` copy was not fetched** (another lane's hosts).
  Three bodies are **already committed** from 2026-10-17 and were scanned offline at zero
  requests: `findings-log/2026-10-17-hcp-config-deployments/headers/k0{24,36,48}-*report.generation.b`.
  All three hold **214** entries — the pre-drift count — and all three carry the **same 13**
  `SKU-` codes, in both forms, with **no name field of any kind** (the list is a bare string
  array). So the HCP copy is a **negative** for naming and needs no follow-up on this axis; the
  cross-host question it *could* answer is whether the drift to 236 is on the HCP side too, which
  is not this area.
- **The 211 patient lazy chunks were not swept.** 211 GETs is 13× this cap. The route, the
  emitted-name defect (`2076`→`common`) and the list are all committed
  (`findings-log/2026-10-13-area-k-patient-chunks/chunks-swept.txt`), so this is a **budget**
  blocker, not a method one. Named as successor AM.1.
- **The `US` document is one artefact on two deployments**, so "identical across `.com` and `.eu`"
  is one source served twice — no independence claim is made from it (§2.1).
- **Only three country codes were read** (`US`, `GB`, `DE`) of 118 derived. The four codes are
  named in all three; **no claim is made about the other 115**, and a country whose copy lacks
  them would not be visible here.
- **Why `Instinct Go` sits in `features` for the EU and not the US is not established**, and no
  cause is offered. The document shows a product-name field that is constant and a packaging/
  feature field that is not; whether that is a market rollout, a regulatory label, or a display
  preference is not readable from these bytes.
- **A family-row membership is still not a product identity** (inherited from area AI): the four
  being `Instinct Sensor` says which **name** the vendor displays, not which physical SKU ships in
  which box.

## Reproducing

```bash
bash findings-log/2026-11-11-area-am-instinct-name-hunt/probe.sh controls   # 6 requests
bash findings-log/2026-11-11-area-am-instinct-name-hunt/probe.sh assets     # 6 requests
bash findings-log/2026-11-11-area-am-instinct-name-hunt/probe.sh modelmap   # 4 requests
AM_SCRATCH=<printed path> python3 findings-log/2026-11-11-area-am-instinct-name-hunt/extract.py
```

Bodies land in the main clone's gitignored `.loop/am-scratch/` and are **not committed**: a 39 KB
vendor name table would enter `findings-log/` as a capture, which `AGENTS.md` §7 forbids in spirit
and which area A/G/H precedent avoids. What is committed is what `extract.py` derives:
`instinct-model-mapping.tsv` (124 INSTINCT rows across the four bodies),
`tail-names.tsv` (the four codes, both key forms, both markets),
`coverage-13.tsv` (all 13 family-map codes against the document, per market).

**`extract.py` reads each body twice** — once with `json.loads` and once with an
`object_pairs_hook` that records any repeated key — and exits 2 if the two readings disagree or if
any dict carried a duplicate. That guard was written because the first draft of this pass
*believed* it had found duplicate keys; it had not, and the assertion is what proved it. A silent
last-value-wins collapse is `AGENTS.md` §6 item 3 wearing different clothes, so the check stays.

## Evidence table

| Claim | Class | Source |
|---|---|---|
| 16 of a 16 cap, GET only, controls first per host, 3 hosts | OBSERVED | `results.jsonl` seq 1–16; `run.log` |
| Absent control 404 / 0 B / `text/vnd.a` on all 3 hosts; live control 200 / 281 B / `7f0a5bb4…` on all 3 | OBSERVED | `results.jsonl` seq 1–6 |
| Spacing floor 2.609 s by body-mtime, 13 gaps, 0 under 2.5 s | OBSERVED | kernel mtime over `.loop/am-scratch/*.b`; disclosed against the `t_sent` series (§Accounting) |
| `t_sent` reads one 1.751 s gap and two negative durations; no cause asserted | OBSERVED | `results.jsonl` seq 3, 8 |
| Patient bundle 3 417 255 B `0fb4fbd4…` on all 3 hosts; reproduces area V seq 3/7 | OBSERVED | `results.jsonl` seq 7, 9, 11 |
| Clinic asset name 404 / 196 B / `80c3fe2a…` on all 3 patient hosts | OBSERVED | `results.jsonl` seq 8, 10, 12 |
| `7896\d`, `SKU-`, `78893`, `78953` are 0 hits in the patient bundle | OBSERVED | local scan of seq 7 body, 3 417 255 B |
| The route `patient/configuration/system/model-mapping/{V}` is in the patient bundle at byte 3374392, called at 2165828 with the country code | OBSERVED | seq 7 body (uncommitted); offsets quoted above |
| `model-mapping/US` → 200, 39 157 B `f0efac1d…` on `.com` **and** `.eu`; `GB`/`DE` → 200, 40 105 B `7f73c467…` | OBSERVED | `results.jsonl` seq 13–16 |
| Document structure: 5 categories (19/14/29/59/73), every entry carries `name` except 4 `DEFAULT`s | OBSERVED | `extract.py` shape assertion, exit 0 |
| **`SKU-78963/78964/78965/78968-01` carry `name: "Instinct Sensor"`, `family: INSTINCT`, in both key forms in both markets** | **OBSERVED** | `tail-names.tsv`; `coverage-13.tsv`; `instinct-model-mapping.tsv`; seq 13 and 15 |
| `Instinct Go` is 0 occurrences in the US body and appears only in `features` in the EU body | OBSERVED | local scan; `instinct-model-mapping.tsv` |
| All 13 family-map codes are named `Instinct Sensor` and separated only by `features` | OBSERVED | `coverage-13.tsv` |
| `MMT-5420` → `Instinct™ Sensor`, `family: INSTINCT`, both markets | OBSERVED | `instinct-model-mapping.tsv` |
| `MMT-8600`/`8601` → `MiniMed™ Go` with a `withSensor` array naming both `SIMPLERA` and `INSTINCT` | OBSERVED | seq 13 body; quoted in §Deltas |
| `78961`/`78962`/`78966`/`78967` absent from this document, both forms, both markets | OBSERVED (scan) + INFERRED limit | `coverage-13.tsv` covers the 13 present codes; absence measured over the full body. Assumption: 3 country codes of 118 read, so this is not a claim about the other 115 |
| The HCP `pow.common.core.report.generation` copy holds 214 entries and no name field | **PUBLISHED (cited, read from committed bodies, zero requests)** | `findings-log/2026-10-17-hcp-config-deployments/headers/k0{24,36,48}-*report.generation.b` |
| The two portal builds were not read; the clinic device table may or may not have grown | INFERRED limit | assumption: the portal host family is another lane's; seq 8/10/12 only test the asset name on a patient host |
| `US` across two deployments is one artefact, so US-vs-EU is one source | INFERRED (§2.1) | identical digest `f0efac1d…` on seq 13 and 14 |

## Correction (2026-11-11) — "12 gaps" was 13, and the parenthetical proved it

A verifier caught this and was right. The spacing paragraph said **"12 gaps across the three
hosts"** and then listed, in the same sentence, `.com` **4** · `.eu` **6** · `-trials` **3** =
**13**. The evidence table carried the same wrong figure. Nothing else in the paragraph moved:
the floor (2.609 s), the "0 under 2.5 s" reading and the disclosed `t_sent` anomalies are all
unchanged, because a missing gap cannot lower a minimum.

Recomputed from `results.jsonl`, grouping by host and sorting on `seq` (16 rows → 5/7/4 per host):

```
carelink.minimed.com        5 rows -> 4 gaps
carelink.minimed.eu         7 rows -> 6 gaps
carelink-trials.minimed.com 4 rows -> 3 gaps
                                  TOTAL 13
```

The check that would have caught it is arithmetic that must hold regardless of any filter:
**`sum(rows_per_host - 1)`**. 16 rows over 3 hosts cannot produce 12 same-host gaps, and the
lane's own list already said 13. A count that disagrees with the evidence printed beside it is
the cheapest kind of defect to find and the easiest to miss, because both halves look
authoritative.
