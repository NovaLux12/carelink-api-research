# Area G — cross-check the model tables per build (N-way reconciliation)

**Pass date:** 2026-10-13 · **Claim issue:** #32
**Branch:** `research/g-device-tables-per-build` · **Ledger:** `results.jsonl` (6 rows, one per HTTP request)
**Harness:** `probe.sh` (requests) · `extract.sh` (offline extraction, zero requests)

## Verdict

**The recorded negative: both builds' device tables are identical as data.**
The clinic `pow` build (`main.fb5f8cb7eb60c4d5.js`, 3,397,615 B) and the support
`cua` build (`main.759cddab23085086.js`, 3,410,666 B) carry the same 78-code
device table (module `68462`), the same 9 `SKU-*` rows, the same 76 display-name
pairs, the same unquoted `MMT5100`/`MMT5101` bare aliases, and the same
module-`90991` `["MMT-8600","MMT-8601"]` sensor-branch array. Whole-file census:
80 distinct `MMT-*` per build, identical sets. G's premise ("the clinic bundle's
device table" is one thing) is unchanged, and the reconciliation below stands
three-way — per the claim's close condition, **a negative closes it**.

One positive side-finding, new against `docs/05`: **`MMT-8200`/`8201`
("Guardian™ 4 system") and `MMT-8400`/`8401` ("Simplera™ system") are present in
both portal builds' device tables.** `docs/05` records them as present in the
HCP report config and absent from the patient family map; they are now also
confirmed present in both portal builds, so the only source that lacks them is
the patient map.

## Request accounting

**6 of a 12 cap.** GET only throughout — literal `GET`, no `-X`, no `-d`, no
POST, no token, no authentication, no port scan, no DNS brute force, no wordlist.
Two hosts only: `carelinkhp.minimed.eu` (clinic `pow` build) and
`carelink-support.medtronic.eu` (support `cua` build).

**Declared delay: 2.5 s, sleep inside the per-host `flock`** (sleep and curl in
one `flock ... -c` string per request, per the pool brief). Measured from
`results.jsonl` `t_done` series (millisecond resolution): **4 same-host gaps,
minimum 2.595 s, all 4 ≥ the declared 2.5 s and ≥ the repo's 2 s floor.**
`run.log` whole-second rendering agrees (every gap reads 2–3 s). No sub-declared
gap, no `docs/09` §4 timing artefact in this pass.

**Ledger note (repaired, not smoothed over):** `probe.sh`'s first version
emitted `ctype_full` with raw header bytes, and the `ETag: W/"…"` quotes broke
JSON parsing of every row. `results.jsonl` as committed is the same 6 rows with
identical fields, mechanically re-encoded; the re-encode step is now part of
`probe.sh` so a re-run produces valid JSON directly. `t_sent` equals `t_queued`
(pre-lock timestamp): the true send instant inside the lock is unobservable from
outside, so spacing is measured done-to-done, which is conservative (it includes
the sleep plus the transfer).

Asset bodies (~3.4 MB each) are deliberately **not** committed (area A
precedent): digests, byte ranges, and `extract.sh` are.

## Controls, in the order they were sent

Controls were sent **first on each host**, before that host's asset fetch.

| # | Host | Control | Result | What it proved |
|---|---|---|---|---|
| 1 | `carelinkhp.minimed.eu` | Certainly-absent asset path `GET /main.deadbeefdeadbeef.js` | 200 `text/html` 5518 B, sha `0f2c5f…` (seq 1) | SPA-fallback trap live on this host: a status-only read of an asset fetch would be worthless |
| 2 | same | Entry document root `GET /` | 200 `text/html` 5518 B, same sha `0f2c5f…` (seq 2) | Build identity anchored: seq 1≡2, and the digest reproduces area A's clinic entry digest `0f2c5f6257a6fc6a…` |
| 4 | `carelink-support.medtronic.eu` | Certainly-absent asset path (same fabricated name) | 200 `text/html` 5518 B, sha `f637c8d0…` (seq 4) | Fallback trap live here too, with the *other* build's digest |
| 5 | same | Entry document root `GET /` | 200 `text/html` 5518 B, same sha `f637c8d0…` (seq 5) | Build identity anchored: seq 4≡5, reproducing area A's support entry digest `f637c8d0cd4ec6bc…` |

**Verdict rule (as committed in #32):** asset identity by sha256 of the
decompressed body + `Content-Type: application/javascript` + size — never
status, never length alone. Both assets pass it:

| Asset | Host | Size | sha256 (decompressed) | Content-Type |
|---|---|---|---|---|
| `main.fb5f8cb7eb60c4d5.js` (seq 3) | `carelinkhp.minimed.eu` | 3,397,615 B | `2a7fa8e7af519c2b…` | `application/javascript` |
| `main.759cddab23085086.js` (seq 6) | `carelink-support.medtronic.eu` | 3,410,666 B | `a054555a0f22176e…` | `application/javascript` |

All four digests and both sizes reproduce area A's ledger values exactly
(OBSERVED, `results.jsonl` seq 1–6; area A values in
`findings-log/2026-10-12-area-a-clinic-portal-region/FINDINGS.md` §1–§2).
No stop condition fired: both fallbacks returned the expected per-build 5518 B
page, no host was in a parked-wildcard space, and no response carried a
credential, session value, internal hostname, or patient identifier.

## Offline extraction (zero requests)

`extract.sh` re-derives everything below from re-fetched bodies. Method, per
`docs/09` §5: exhaustive grep with byte offsets and case-sensitivity controls —
a hit proves the token exists, not what it means, so every token below carries
its offsets and its context reading.

### Case-sensitivity controls (identical in both builds)

| Token | hp-main hits @ bytes | sup-main hits @ bytes | Reading |
|---|---|---|---|
| `medicalDeviceFamily` | 0 | 0 | absent from both portal builds (reproduces `docs/05`) |
| `deviceFamily` | 2 @ 1243187, 2874214 | 2 @ 1243187, 3256997 | `deviceFamilyMapping` selector + localStorage patient-filter object — neither is a wire field (reproduces `docs/05` correction context) |
| `sourceMappingURL` | 1 @ 1791807 | 1 @ 1792143 | `worker-loader` string literal (`//# sourceMappingURL="+F+"`), not a directive. hp offset **1791807 reproduces the exact byte offset `docs/09` §5 records** — same file, same finding |
| `GUARDIAN` (case-sensitive) | 0 | 0 | rest are display names and zxcvbn noise (reproduces `docs/05`) |
| `SIMPLERA` (case-sensitive) | 2 @ 55191, 3008062 | 2 @ 55191, 2809905 | only the enum key `SIMPLERA_SYSTEM` (reproduces `docs/05`) |
| `"BLE"` (quoted) | 0 | 0 | case-insensitive hits are `TABLE`, `ENABLED`, … (reproduces `docs/05`) |
| `NGP` (uppercase) | 0 | 0 | lowercase `ngp` hits (6 each, same bytes 214434… in both) are zxcvbn password-list noise |

### The per-build device tables (module 68462)

78 `MMT-*` codes + 9 `SKU-*` codes per build, **identical sets**:

```
MMT-105NNBLNA MMT-1510 MMT-1511 MMT-1512 MMT-1710 MMT-1711 MMT-1712 MMT-1714
MMT-1715 MMT-1740 MMT-1741 MMT-1742 MMT-1780 MMT-1781 MMT-1782 MMT-1800
MMT-1801 MMT-1805 MMT-1809 MMT-1810 MMT-1811 MMT-1812 MMT-1817 MMT-1818
MMT-1880 MMT-1881 MMT-1882 MMT-1883 MMT-1884 MMT-1884XCU MMT-1885 MMT-1885XCE
MMT-1886 MMT-1886XCE MMT-1886XCF MMT-1900 MMT-1902 MMT-1904 MMT-1906 MMT-1907
MMT-1908 MMT-5100 MMT-5101 MMT-5120 MMT-515 MMT-522 MMT-523 MMT-5420 MMT-551
MMT-554 MMT-6500 MMT-6501 MMT-715 MMT-722 MMT-723 MMT-751 MMT-754 MMT-7731
MMT-7763 MMT-7811 MMT-7821 MMT-7841 MMT-7910 MMT-7911 MMT-8062 MMT-8063
MMT-8082 MMT-8083 MMT-8084 MMT-8085 MMT-8162 MMT-8163 MMT-8200 MMT-8201
MMT-8400 MMT-8401 MMT5100 MMT5101

SKU-78893-01 SKU-78953-01 SKU-78954-01 SKU-78955-01 SKU-78956-01 SKU-78957-01
SKU-78958-01 SKU-78959-01 SKU-78960-01
```

Display names compared as data (76 quoted `"MMT…":{name,shortName}` pairs +
2 unquoted `MMT5100`/`MMT5101` bare aliases + 9 `SKU-*` pairs): **all
identical between builds**, including `MMT-8200`/`8201` → "Guardian™ 4 system",
`MMT-8400`/`8401` → "Simplera™ system", `MMT-105NNBLNA` → "InPen"
(InsulinDelivery section), and the `INSTINCT` split (`78893/78953/78955/78957/
78959/78960` → "Instinct™ Sensor"; `78954/78956/78958` → "Instinct™ Go").
The 90 KB table segments differ at the byte level (minified variable
renaming — e.g. `fs=` vs `ms=` at the `deviceFamilyMapping` selector — and
shifted offsets), so byte-identity was never the claim; code-set and
name-pair identity is, and both hold.

Whole-file census: **80 distinct `MMT-*` per build, identical sets.** The 2
codes outside the table window are `MMT-8600`/`MMT-8601`, each occurring once
per build in module `90991` as `const S=["MMT-8600","MMT-8601"]` (hp @
3230062, sup @ 3031986) — reproducing the `docs/05` sensor-branch reading, now
confirmed in **both** builds.

### Reconciliation per build (against committed sources only, offline)

Patient-map side: `personal.device.family.to.model.mapping` rows as recorded
in `findings-log/probe-2026-10-08/PUBLIC-CONFIG-FINDINGS.md` (8 families with
verbatim rows; the remaining 8 families' model lists are not committed
anywhere — the suite pins the map hash `8ce419a22fd3`, not the rows — so only
the recorded rows are compared, and the limit is stated rather than exceeded).
HCP side: the 214-entry count and the named deltas in
`findings-log/probe-2026-10-08/recon/HCP-CONFIG-SCHEMA.md` §9 (the full
214-entry list is not on disk). **Every row below holds for both builds**
(the two builds' code sets are identical, so there is no per-build split to
report — which is itself the negative result):

| Model code(s) | Patient map (recorded rows) | HCP 214 list (recorded) | Both portal builds | Reading |
|---|---|---|---|---|
| `MMT-8600`/`8601` | present (`SIMPLERACC`) | present | present (module 90991, not the table) | three sources agree on presence; portal keeps them out of the table — reproduces `docs/05` |
| `MMT-8200`/`8201`, `MMT-8400`/`8401` | **absent** | present | **present** (table, with display names) | **new:** the only source lacking them is the patient map; the "third partial table" is the patient map, not the portal |
| `MMT-8021`/`8022`/`8023` (`CC840`) | present | unrecorded | **absent** (whole-file) | patient-map-only among compared sources |
| `MMT-1909` (`NMX7`: 1906–1908 present) | present (row reads 1906-1909) | unrecorded | **absent** | portal carries 3 of the row's 4 |
| `MMT-8602` (`SIMPLERACCOLID`) | present | unrecorded | **absent** | patient-map-only |
| `MMT-9015`/`9017`/`9115`/`9117` (`EAGLE`) | present | unrecorded | **absent** (all 4) | no EAGLE token anywhere in either build |
| `MMT-8162XCF`/`8172XCF`/`8163XCF`/`8173XCF`/`8173XCC` (`CC880` variants) | present | unrecorded | **absent** (all 5; no `XCF`/`XCC` string in either build) | portal carries only the 6 base Flex codes |
| `MMT-1886XCY` (`BLE780` variant per recorded row) | present (row names XCU/XCE/XCF/XCY) | unrecorded | **absent** (XCU/XCE/XCF present) | portal carries 4 of the row's 5 suffix forms |
| `MMT-5100JC1`/`JD4`/`5101P`/`M` etc. (`SIMPLERACC` suffixes) | present | unrecorded | **absent** (base `MMT-5100`/`5101` + bare aliases present) | portal carries the base codes only |
| `MMT-8062`/`8063`/`8082`–`8085` (`CC880` base six) | present | unrecorded | **present** (8062 ×3 occurrences each, as `docs/05` notes) | agreement |
| `MMT-8162`/`8163` (`NMX8`) | present | unrecorded | **present** | agreement |
| `MMT-1884`/`1885`/`1886` + XCU/XCE/XCF (`BLE780` base) | present | unrecorded | **present** | agreement |
| `SKU-78893-01…78960-01` (9 of the `INSTINCT` range) | range recorded as `…78968-01` | unrecorded | **present** (exactly these 9) | portal's 9 are within the recorded range; `78961`–`78968` not checked (range tail unrecorded) |

**Limits, stated:** the HCP 214-entry list is compared only through its
recorded count and named deltas — a code marked "unrecorded" above is not
claimed absent from it. The patient map is compared only through its 8
recorded family rows. No single source is authoritative — `docs/05`'s standing
position, unchanged by this pass.

## What was searched and found empty (negatives)

- **No per-build split.** The premise's hoped-for difference does not exist:
  identical code sets (78+9), identical name pairs (76+2+9), identical 90991
  array, identical whole-file census (80), identical answers on all 23
  patient-map spot checks. A negative that closes the area.
- **`MMT-8602`, all of `EAGLE`, all of `CC840`, `MMT-1909`:** 0 hits in either
  build (whole-file, case-exact).
- **No `XCF`/`XCC` suffixed code** in either build (0 hits for the pattern
  `MMT-8[0-9]{3}X[A-Z]+`).
- **`medicalDeviceFamily`, `GUARDIAN`, `"BLE"`, uppercase `NGP`:** 0 hits in
  either build — the `docs/05` negatives reproduce exactly.
- **No source-map directive** in either build: the single `sourceMappingURL`
  hit per build is the `worker-loader` string literal (`docs/09` §5 class).

## Reproducing

```bash
TMPBODIES=$(mktemp -d)
bash findings-log/2026-10-13-area-g-device-tables/probe.sh   # 6 requests, cap 12
# bodies land in $TMPBODIES (printed at end); then, zero requests:
TMPBODIES=$TMPBODIES bash findings-log/2026-10-13-area-g-device-tables/extract.sh
```

`results.jsonl` rows carry `t_queued`/`t_sent`/`t_done` (UTC ISO-8601, ms
resolution); `headers/` holds one `<tag>.h` per request; `run.log` carries the
start line, one line per request, and the end line.

## Evidence table

| Claim | Class | Source |
|---|---|---|
| 6 requests of a 12 cap, GET only, controls first per host | OBSERVED | `results.jsonl` seq 1–6; `run.log` |
| Same-host spacing floor 2.595 s, 4/4 gaps ≥ 2.5 s | OBSERVED | `results.jsonl` `t_done` series |
| Fallback trap live on both hosts (fabricated asset → per-build 5518 B page) | OBSERVED | `results.jsonl` seq 1, 4 |
| Build identity per host (absent≡root; hp `0f2c5f…`, sup `f637c8d0…`) | OBSERVED | `results.jsonl` seq 1≡2, 4≡5 |
| Clinic asset 3,397,615 B `2a7fa8e7…` + `application/javascript` | OBSERVED | `results.jsonl` seq 3; `headers/hp-main.h` |
| Support asset 3,410,666 B `a054555a…` + `application/javascript` | OBSERVED | `results.jsonl` seq 6; `headers/sup-main.h` |
| All four digests + both sizes reproduce area A | OBSERVED | `results.jsonl`; `findings-log/2026-10-12-area-a-clinic-portal-region/FINDINGS.md` §1–§2 |
| Device tables identical as data (78+9 codes, 76+2+9 name pairs) | OBSERVED | `results.jsonl` seq 3, 6 (bodies, uncommitted); `extract.sh` output |
| Whole-file census 80 MMT-* per build, identical sets | OBSERVED | `extract.sh` output |
| `MMT-8600`/`8601` in module 90991 in both builds, not in either table | OBSERVED | `extract.sh` output (S-array bytes 3230062 / 3031986) |
| `MMT-8200`/`8201`/`8400`/`8401` in both builds' tables with display names | OBSERVED | `extract.sh` output |
| 23 patient-map spot checks identical across builds (incl. 9 absences) | OBSERVED (builds) + PUBLISHED (map rows) | `extract.sh` output; `findings-log/probe-2026-10-08/PUBLIC-CONFIG-FINDINGS.md` |
| HCP-list comparison limited to recorded count + deltas | INFERRED limit | assumption: the full 214-entry list is not on disk; absent-from-record ≠ absent-from-list |
| Region is not a variable; product role is (inherited, not re-probed) | INFERRED from area A | assumption: area A's host↔build mapping still holds; this pass re-anchored both digests |
