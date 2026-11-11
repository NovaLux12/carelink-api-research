# Area AV — has the portal device table (module `68462`) grown past `78960`, and what does it name the four tail codes?

**Pass date:** 2026-11-11 · **Claim issue:** #223 · **Branch:** `research/lav`
**Ledger:** `results.jsonl` (6 rows, one per HTTP request) · **Harness:** `probe.sh` (requests) ·
`extract.sh` (offline extraction, zero requests)
**Derived tables:** `build-table-summary.tsv`, `instinct-table.tsv`, `census-7896x.tsv`,
`sku-offsets.tsv`

## Verdict

**No digest moved, so the device table is the SAME artefact the 2026-10-13 pass read — and it
still stops at `78960`. The four tail codes are in none of the five bodies.**

| Question cell | Answer | Class |
|---|---|---|
| Do the five portal hosts still serve the pinned builds? | **Yes — 5 of 5 digests reproduce the pinned value byte for byte** | OBSERVED |
| Does module `68462` now carry `78963`/`78964`/`78965`/`78968`? | **No — 0 hits in 5 of 5 bodies, in any of the three code forms** | OBSERVED |
| What does the table name the codes it *does* carry? | 6 → `Instinct™ Sensor`, 3 → `Instinct™ Go`, `MMT-5420` → `Instinct™ Sensor` — **identical to the 2026-10-13 record** | OBSERVED |
| Does the portal table now agree with `model-mapping`? | **No, and the disagreement is unchanged**: `model-mapping` gives all 13 codes `name: "Instinct Sensor"`; the portal table splits 9 of them 6/3 across two product names. The split is still not reproduced by the vendor's own name document | OBSERVED (both sides) + INFERRED (the reconciliation reading, §5) |

The area's **close condition says a negative counts**, and this is the negative it named: the
portal table is still the incomplete side of the three-table comparison, exactly as area AI
recorded it (`13` codes on the patient side against `9` here, the four in the difference being
the tail). What is *new* is not the verdict but its **date and its provenance** — the earlier
statement rested on a 2026-10-13 capture, and the vendor's config demonstrably moved in between
(the patient report list grew 214 → 236). This pass shows the **JS build did not move with it**.

## 1. Controls, sent before any question cell

| # | Host | Control | Result | What it proved |
|---|---|---|---|---|
| 1 | `carelinkhp.minimed.eu` | `GET /` — the entry document | 200, `text/html; charset=UTF-8`, **5518 B**, sha256 `0f2c5f6257a6fc6af22e4b31309264df4c148e08016c196e1048bdc19a87e32d` | The host family is serving the artefact this lane's question is about, and the client build digest reproduces area G seq 2 / area V seq 9 **in full** (OBSERVED, seq 1). Had this failed, the run stopped: `probe.sh control` exits 3 on a mismatch and the asset step is a separate invocation |

The control is the entry document, not a fabricated asset path, because on this family the
catch-all **is** the entry document — an absent asset path and `GET /` return the same bytes
(area G's seq 1 ≡ 2, area V's seq 8 ≡ 9). A fabricated-asset control here would therefore test
nothing that `GET /` does not.

## 2. Every digest assertion (the load-bearing table)

Each fetch is on a **content-hashed asset name recorded by an earlier pass**, from its own host,
and each body was hashed after `curl --compressed` decompressed it. `probe.sh` prints
`PASS`/`MOVED`/`NOT-AN-ASSET` per fetch and exits 4 on anything but `PASS`
(`assert_asset`); nothing below was read before its assertion passed.

| seq | Host | Asset | Bytes | sha256 | Pinned value (source) | Assertion |
|---|---|---|---|---|---|---|
| 2 | `carelinkhp.minimed.eu` | `/main.fb5f8cb7eb60c4d5.js` | 3 397 615 | `2a7fa8e7af519c2b493caf62c00b46c5e75a357048444dbf7abff6136bfc02ba` | `2a7fa8e7…` / 3 397 615 B (area G seq 3; area V seq 10) | **PASS** |
| 3 | `carelink.medtronic.com` | `/main.fb5f8cb7eb60c4d5.js` | 3 397 615 | `2a7fa8e7af519c2b493caf62c00b46c5e75a357048444dbf7abff6136bfc02ba` | same (area A seq 8) | **PASS** |
| 4 | `carelink.medtronic.eu` | `/main.fb5f8cb7eb60c4d5.js` | 3 397 615 | `2a7fa8e7af519c2b493caf62c00b46c5e75a357048444dbf7abff6136bfc02ba` | same (area A seq 19) | **PASS** |
| 5 | `carelink-support.medtronic.eu` | `/main.759cddab23085086.js` | 3 410 666 | `a054555a0f22176ecb51d8f6439680a394e2be5e889494bec5004c93be28c954` | `a054555a…` / 3 410 666 B (area G seq 6; area V seq 13) | **PASS** |
| 6 | `carelink-support.medtronic.com` | `/main.759cddab23085086.js` | 3 410 666 | `a054555a0f22176ecb51d8f6439680a394e2be5e889494bec5004c93be28c954` | same (area A seq 20) | **PASS** |

All five carried `content-type: application/javascript` and were brotli-encoded in transit
(`content-encoding: br`, decompressed by `--compressed` before hashing) — the verdict rule area
G and area V committed. Two further signals reproduce the 2026-10-13 record: the ETags
(`W/"33d7ef-659fa96cd58c0"` on the three clinic hosts, `W/"340aea-659fa99b90700"` on the two
support hosts) and `last-modified: Wed, 26 Aug 2026 22:17:47 GMT` / `22:18:36 GMT` (OBSERVED,
`headers/*.h`). They are corroboration of the digests from the same source, not a second source.

**No digest moved, so the 2026-10-13 offset applies in full** and the table below is a re-read of
the same artefact, not a new one. That is the opposite of the outcome the brief primed for: the
config drift of 214 → 236 did **not** carry the JS bundle with it. **INFERRED** (assumption
stated): that the portal build and the patient public config are deployed independently, which
this pass cannot observe — the observation is that one moved and the other did not.

## 3. Module `68462` — where it is, and how it was located

`extract.sh` asserts three things before it parses anything, so a shifted or renamed module
cannot be read as the table:

1. the module table entry is the **last** `68462` occurrence in the file, and it must be the
   literal `68462:(ct,Z,r)=>` — in both builds the other two occurrences are `r(68462)` call
   sites (byte 53 583 and one mid-file), not the table;
2. the module ends at the next webpack module boundary (`}},<id>:(ct,Z,r)=>`);
3. the four section keys are exactly `PUMP`, `SENSOR`, `StandaloneCGM`, `InsulinDelivery` — a
   renamed or dropped section fails the script rather than yielding a silently shorter census.

| Build | Hosts | Module start byte | Module bytes | Named pairs | `SKU-` pairs | Instinct-named pairs |
|---|---|---|---|---|---|---|
| A (`pow`), `2a7fa8e7…` | hp, `.com`, `.eu` | 2 999 302 | 9 172 | 97 | 9 | 10 |
| B (`cua`), `a054555a…` | support `.eu`, support `.com` | 2 801 145 | 9 172 | 97 | 9 | 10 |

`extract.sh` also asserts a **fourth** control the first version of this script got wrong and
which is recorded here rather than smoothed over: `78963` and `78965` *do* have substring hits in
every body — 11 and 2 respectively — but every one sits inside the zxcvbn password dictionary of
module `14520` (`…,element,1478963,zipp…`, `…,fishy,78963214…`, `…,luckydog,789654,pistol…`), at
**identical byte offsets in all five bodies**. A bare `\b7896\d\b` count would have reported them
as hits. The census in `census-7896x.tsv` therefore separates three forms — the quoted named pair
`"SKU-NNNNN-01":{name:`, the `SKU-` string anywhere, and a bare `NNNNN-01` not preceded by
`SKU-` — and carries the raw substring count separately in a `loose_substring_hits` column with a
`substring-only(zxcvbn)` label. This is `docs/09` §5's false-hit class and `AGENTS.md` §6.2.

The 97 named pairs decompose as 76 quoted `MMT-*`, 2 unquoted bare aliases (`MMT5100`,
`MMT5101`), 9 `SKU-*`, and 10 non-code keys (`DEFAULT` ×4, `CSS-7200`/`CSS-7201` +
`CSS7200`/`CSS7201`, `gm3_snapshot`, `gm4_snapshot`) — reproducing area G's 76 + 2 + 9 shape.

## 4. The INSTINCT rows, verbatim as data

Identical in both builds and on all five hosts (`instinct-table.tsv`; the per-build set
difference is empty in both directions).

| Key | `name` | `shortName` | Section |
|---|---|---|---|
| `MMT-5420` | `Instinct™ Sensor` | `Instinct™ Sensor` | SENSOR |
| `SKU-78893-01` | `Instinct™ Sensor` | `Instinct™ Sensor` | SENSOR |
| `SKU-78953-01` | `Instinct™ Sensor` | `Instinct™ Sensor` | SENSOR |
| `SKU-78955-01` | `Instinct™ Sensor` | `Instinct™ Sensor` | SENSOR |
| `SKU-78957-01` | `Instinct™ Sensor` | `Instinct™ Sensor` | SENSOR |
| `SKU-78959-01` | `Instinct™ Sensor` | `Instinct™ Sensor` | SENSOR |
| `SKU-78960-01` | `Instinct™ Sensor` | `Instinct™ Sensor` | SENSOR |
| `SKU-78954-01` | `Instinct™ Go` | `Instinct™ Go` | SENSOR |
| `SKU-78956-01` | `Instinct™ Go` | `Instinct™ Go` | SENSOR |
| `SKU-78958-01` | `Instinct™ Go` | `Instinct™ Go` | SENSOR |

The trademark is the literal `\u2122` escape in the source (`"Instinct\u2122 Sensor"`), not a
UTF-8 `™`; `extract.sh` decodes it for the tables and the raw slice is quoted in §3's context
lines. Byte offsets per code per host are in `sku-offsets.tsv` (e.g. `SKU-78960-01` at byte
3 005 736 in the clinic build, 2 807 579 in the support build).

Order in the source is not code order — the Sensor six and the Go three are interleaved — so the
split is read from the `name` value, never from position. **The parity is worth stating plainly:
6 Sensor + 3 Go, and the Go three are exactly `78954`, `78956`, `78958`, i.e. every second code
from `78954` to `78958`.** This reproduces area G's record exactly; it is not a new observation,
which is the point of the pass.

## 5. The `model-mapping` comparison

The vendor's own name document (`patient/configuration/system/model-mapping/{US,GB}`) was read by
area AM on 2026-11-11 and is committed there (PUBLISHED at an unauthenticated URI; that pass spent its whole
budget of 16 requests): **all 13** `INSTINCT` codes — including `78960` and the four tail codes — carry
`name: "Instinct Sensor"`, `family: "INSTINCT"`, in both markets
[source: findings-log/2026-11-11-area-am-instinct-name-hunt/FINDINGS.md; `tail-names.tsv`;
`coverage-13.tsv`].

So on the axis this area was asked about:

| Code | Portal table `name` (this pass) | `model-mapping` `name` (area AM) | Agree? |
|---|---|---|---|
| `78893`, `78953`, `78955`, `78957`, `78959`, `78960` | `Instinct™ Sensor` | `Instinct Sensor` | **same product, trademark also differs** |
| `78954`, `78956`, `78958` | `Instinct™ Go` | `Instinct Sensor` | **no** |
| `78963`, `78964`, `78965`, `78968` | *absent* | `Instinct Sensor` | **portal table has no row** |

**They do not agree, and the disagreement has two independent halves.** (a) *Coverage*: the
table omits four codes the name document carries. (b) *Vocabulary*: where both speak, the table
splits into two product names and the name document does not — its only Sensor/Go distinction
lives in `features.patientListPremium`/`patientDashboard`, i.e. i18n copy, not a per-SKU field
[source: findings-log/2026-11-11-area-am-instinct-name-hunt/FINDINGS.md]. **INFERRED**: that the
two artefacts serve different purposes — the table is a display map keyed by SKU, the document a
family/enumeration map — which would explain a per-SKU name in one and a constant name in the
other. This pass did not read the calling code for either, so the mechanism is a hypothesis, not
an observation, and **which physical SKU is `Instinct™ Go` remains unrecovered by both**.

## 6. Zero-request side-finding — the resolver that reads the table keys by 8-char prefix

The table is consumed by module `1287` (`1287:(ct,Z,r)=>`, byte 53 446 in both bodies, 3 411 B),
which imports it as `var e=r(68462)`. Three functions in that module address the table, and the
address is **not** a plain key lookup:

```js
const R=(null==(z=H.SENSOR)?void 0:z[U])||(null==(x=H.SENSOR)?void 0:x[U.slice(0,8)])
       ||(null==(ie=H.StandaloneCGM)?void 0:ie[U])||(null==(ve=H.StandaloneCGM)?void 0:ve[U.slice(0,8)]);
```

That is `P(I,H,V)` at byte 55 700 of the bundle (OBSERVED, quoted verbatim). A code is looked up
**whole**, then **truncated to its first 8 characters**, in `SENSOR`, then the same two ways in
`StandaloneCGM`. `PUMP` is never consulted by this function at all. Simulated against the
extracted table of both builds (`extract.sh`, zero requests):

| Code passed in | Resolves via | `name` |
|---|---|---|
| `SKU-78960-01` | `SENSOR["SKU-78960-01"]` (whole key) | `Instinct™ Sensor` |
| `SKU-78953-01` … `SKU-78958-01` | whole key | Sensor / Go as in §4 |
| `SKU-78963-01`, `SKU-78964-01`, `SKU-78965-01`, `SKU-78968-01` | **none** — prefix `SKU-7896` is not a key | *null* |
| `MMT-5100JC1`, `MMT-5100CLX`, … | `SENSOR["MMT-5100"]` (8-char prefix) | `Synergy Sensor` |
| `MMT-1884XCU`, `MMT-1886XCF` | **none** — they are `PUMP` keys and `PUMP` is not read here | *null* |
| `MMT-105NNBLNA` | **none** — `PUMP`-side / `InsulinDelivery`, not read here | *null* |

Three consequences, each OBSERVED from the code plus the table and **INFERRED** only where marked:

1. **The 8-char fallback is what makes the long `MMT-` variants nameable, and it only works
   because the base code is a key.** `MMT-5100JC1` resolves because `MMT-5100` is in `SENSOR`.
   `MMT-1884XCU` does **not** resolve here even though it *is* a table key — it sits in `PUMP`,
   which this function does not read (OBSERVED for the code path and the key location; **INFERRED**
   that no other caller names it, since only three call sites of this export set appear in the
   bundle).
2. **`SKU-7895` is an ambiguous 8-char prefix.** Seven `SENSOR` keys share it —
   `78953/78954/78955/78956/78957/78958/78959` — and they span **both** names, three `Go` and four
   `Sensor`. The `||` chain takes the whole-key match first, so no ambiguity arises for a real
   13-character code; it would arise only for a code truncated to `SKU-7895`, which the table does
   not contain. That is a **latent** hazard in the resolver, not an observed defect, and it is
   recorded as such.
3. **Adding the four tail codes as `SENSOR` keys would make them nameable with no code change** —
   `SKU-7896` is not currently a key, so the prefix path cannot fire for them either. This is what
   "the table is the incomplete side" means *mechanically*: the resolution machinery is already
   generic; only the data rows are missing. (**INFERRED** — it assumes the client sends the
   13-character `SKU-` form, which area AI's family-map row shows is the form the patient config
   publishes, but which no captured request in this repo demonstrates.)

## 7. What was searched, and found empty (the population named in each sentence)

- **The four tail codes are absent from the five decompressed bodies named in
  `build-table-summary.tsv`** (3 distinct digests, 2 builds, 5 hosts): `SKU-78963-01`,
  `SKU-78964-01`, `SKU-78965-01`, `SKU-78968-01` each have **0** quoted-pair hits, **0**
  `SKU-` string hits and **0** bare `NNNNN-01` hits (OBSERVED, `census-7896x.tsv`, all five rows
  per code). `78961`, `78962`, `78966` and `78967` are absent in all three forms as well — a
  **fourth** vendor artefact skipping them after the family map, the name document and area AI's
  two patient documents.
- **`78963` and `78965` occur only as password-list substrings** in the five bodies: 11 and 2
  hits, all inside module `14520`'s zxcvbn dictionary, at identical byte offsets in every body.
  They are not codes in this bundle, and a count that included them would have been wrong.
- **No section was added to module `68462`.** The four keys are `PUMP`, `SENSOR`,
  `StandaloneCGM`, `InsulinDelivery` in both builds and all five bodies; the named-pair count is
  97 on every one, the same as area G's 78 + 9 + 2 + 8 shape.
- **No per-host split.** Three hosts serve build A byte-identically and two serve build B
  byte-identically, so there is no deployment-level difference to report on this axis — a
  negative that matches area G's identical-code-set result.

## 8. Request accounting

**6 of a 14 cap.** GET only throughout — literal `GET`, no `-X`, no `-d`, no POST, no OPTIONS, no
token, no cookie, no authentication, no port scan, no DNS brute force, no wordlist. One control
plus five asset fetches.

**Declared delay ≥ 2.5 s between requests to the same host, sleep inside a per-host
`flock`.** Measured same-host spacing is in the table below. Only one host received two requests
(`carelinkhp.minimed.eu`, seq 1 → 2); the other four received one each and so contribute no gap
to a same-host statistic. Grouped by host and sorted by seq **before** measuring:

| Host | Reqs | Same-host gaps (s, from `t_sent`) |
|---|---|---|
| `carelinkhp.minimed.eu` | 2 | **4.820** |
| `carelink.medtronic.com` | 1 | — |
| `carelink.medtronic.eu` | 1 | — |
| `carelink-support.medtronic.eu` | 1 | — |
| `carelink-support.medtronic.com` | 1 | — |

**Floor 4.820 s, 1 gap, 0 under 2.5 s, 0 under the repo's 2 s floor.**

**The second clock is PROVEN LIVE, not assumed.** Kernel body mtimes are 6 of 6 distinct, strictly
ascending in seq order, and every one is later than its own `t_sent` (deltas 0.089–0.955 s). Per
`docs/09` §4 a clock is only claimable when it discriminates; this one does. The mtime floor over
the same single interval is **4.975 s**. No negative or impossible duration appears in either
series.

## 9. Method notes and limits

- **Bodies (~3.4 MB each) are deliberately not committed** — area A, G and V precedent. Digests,
  sizes, byte offsets and every derived row are. The bodies live in the gitignored scratch tree
  and are re-creatable with `probe.sh`.
- **A script defect was found and fixed during this pass, and the fix is the record:** the first
  `extract.sh` counted `7896\d` with `(?<![0-9])NNNNN(?![0-9])` and reported `SKU-78960-01` as a
  "bare form" hit and 11 zxcvbn integers as code hits. The committed version separates the three
  forms and labels the raw substring count. The wrong numbers never left the scratch dir; they are
  described here so the next reader of `census-7896x.tsv` knows why the columns are shaped that
  way.
- **No `docs/` value needed correcting.** `docs/05` already states the portal split stops at
  `78960` and that `model-mapping` gives the four a name without the split — both re-observed
  here and unchanged. This pass adds a **date** to that statement, not a correction, and the
  `docs/05` note added alongside cites this log.
- **Not claimed:** that the table will still stop at `78960` at any later build (a digest change
  would end the claim — this pass's own method is the check for it); any mechanism for why the
  bundle did not move with the config (INFERRED only, §2); or a product identity for
  `Instinct™ Go` (§5).

## 10. Reproducing

```bash
bash findings-log/2026-11-11-area-av-portal-device-table/probe.sh control   # 1 request
bash findings-log/2026-11-11-area-av-portal-device-table/probe.sh assets    # 5 requests, each asserted
# zero requests from here; bodies default to <main>/.loop/av-scratch
bash findings-log/2026-11-11-area-av-portal-device-table/extract.sh
```

## Evidence table

| Claim | Class | Source |
|---|---|---|
| 6 of a 14 cap, GET only, control sent first | OBSERVED | `results.jsonl` seq 1–6; `run.log` |
| All five asset digests reproduce their pinned values exactly | OBSERVED | `results.jsonl` seq 2–6; `headers/*.h`; `probe.sh assert_asset` PASS lines |
| The entry-document digest reproduces area G seq 2 / area V seq 9 | OBSERVED | `results.jsonl` seq 1 |
| Module `68462` sits at byte 2 999 302 (build A) / 2 801 145 (build B), 9 172 B, four sections | OBSERVED | `build-table-summary.tsv`; `extract.sh` assertions |
| The table names 6 codes `Instinct™ Sensor` and 3 `Instinct™ Go`, plus `MMT-5420` as Sensor | OBSERVED | `instinct-table.tsv`; `sku-offsets.tsv` |
| The four tail codes are absent from all five bodies in all three code forms | OBSERVED | `census-7896x.tsv` (5 rows per code) |
| `78963`/`78965` substring hits are zxcvbn password-list integers, identical offsets in all five bodies | OBSERVED | `census-7896x.tsv` `loose_substring_hits` / `where`; module `14520` context quoted in §3 |
| `model-mapping` gives all 13 codes `name: "Instinct Sensor"` in US and GB | PUBLISHED | findings-log/2026-11-11-area-am-instinct-name-hunt/`tail-names.tsv`, `coverage-13.tsv` |
| Same-host spacing floor 4.820 s from `t_sent`; mtime floor 4.975 s; second clock proven live (6/6 distinct, ascending, all after `t_sent`) | OBSERVED | `results.jsonl` `t_sent` / `body_mtime_epoch` |
| The build and the patient public config deploy independently | INFERRED | one moved (214 → 236, area 2026-11-03 drift log) and the other did not (this pass); the deployment relation itself is not observed |
| The two artefacts serve different purposes (display map vs enumeration map) | INFERRED | shape of each document only; the name-document caller was not read |
| Module `1287` resolves a code by whole key, then by its first 8 characters, in `SENSOR` then `StandaloneCGM` — never `PUMP` | OBSERVED | byte 55 700 of both bodies, quoted verbatim in §6; `extract.sh` re-derives both tables the simulation runs against |
| `MMT-5100JC1` resolves to `Synergy Sensor` via the `MMT-5100` prefix; `MMT-1884XCU` resolves to null because it is a `PUMP` key | OBSERVED | §6 simulation over `instinct-table.tsv` / the extracted tables |
| No other caller names the `PUMP`-only variants | INFERRED | three call sites of module `1287`'s export set exist in each bundle, and none reads `PUMP`; absence of a fourth is not provable from one file |
