# Area AI — the `INSTINCT` range tail: what are `SKU-78961-01` … `SKU-78968-01`?

**Pass date:** 2026-11-10 · **Claim issue:** [#181](https://github.com/NovaLux12/carelink-api-research/issues/181)
**Branch:** `research/ai-instinct-sku-tail` · **Ledger:** `results.jsonl` (12 rows, one per HTTP request)
**Harness:** `probe.sh` (requests) · `extract.py` (offline extraction, zero requests)

## Verdict

**Half the tail is present, half is absent — and the range is not a range.**

`docs/05` records the `INSTINCT` family as `SKU-78893-01 … SKU-78968-01`, which reads as a
contiguous span of 76 integers. It is not one. The patient family map's `INSTINCT` row holds
**13** `SKU-NNNNN-01` codes, and of the 76 integers between 78893 and 78968 only those 13 appear
anywhere: **4 of the 8 tail codes are present and 4 are absent**, in both patient documents, on
all three deployments:

| tail code | family map | report-naming list |
|---|---|---|
| `78961` | absent | absent |
| `78962` | absent | absent |
| `78963` | **present** | **present** |
| `78964` | **present** | **present** |
| `78965` | **present** | **present** |
| `78966` | absent | absent |
| `78967` | absent | absent |
| `78968` | **present** | **present** |

**Neither patient document gives any of these codes a display name**, so the question "what do they
map to" has a precise answer and it is *not* the one the area hoped for: they map to **family
`INSTINCT`**, and to **no product name at all**. The only source in this repository that assigns a
product name to an `INSTINCT` SKU is the portal JS device table (module `68462`), which carries
**9** codes — every one of them in the `78893`–`78960` half. So the `Instinct™ Sensor` / `Instinct™
Go` split area G found **covers none of the four tail codes**, and no source held here extends it.

**The finding that changes a `docs/` claim:** area G's row reads *"`SKU-78893-01…78960-01` (9 of the
`INSTINCT` range) … **present** (exactly these 9) | portal's 9 are within the recorded range"*. Read
against the patient document, that is **backwards in direction**: the patient map is the **larger**
table (13 codes) and the portal builds are the **smaller** (9), so the four tail codes are
*patient-map-only* codes, not portal-only ones. Area G compared the portal builds against
`docs/05` alone and never read the patient row; this pass reads the patient row and finds the
portal table is the incomplete side, again — the same shape as `MMT-8600`/`MMT-8601` (below).

## Method, and why this method

**One document fetch per host per document, then a local scan. No per-SKU probes.**

Both patient documents that carry `SKU-` strings are key-addressable at routes this repository
already records, so the whole population is reachable in **two** requests per host:

| document | route | recorded |
|---|---|---|
| the 16-family map | `/patient/configuration/system/personal.device.family.to.model.mapping` | area E seq 40 (`.com`) and 116 (`-trials`), 200, 3470 B, sha256 `ae70bde0…` |
| the report-naming dict | `/patient/configuration/system/personal.common.core.report.generation` | area E seq 29 (`.com`) and 105 (`-trials`), 200, 10937 B, sha256 `2f918b71…` |

A per-SKU GET would have to address `/patient/configuration/system/<some.key>.<SKU>`, and **no
sub-key grammar for that is recorded anywhere in this repository** — inventing one is wordlist
fuzzing dressed up as a probe, and it would have spent 8 requests re-fetching bytes these two
documents already contain. Eight probes could not have answered the question either: the answer is
a *set difference* between two tables, not eight independent yes/no facts, and 8 probes against one
host would have measured one host. So the cap was spent on **breadth across deployments** (all
three patient hosts, so a deployment split could not hide) rather than depth on a fabricated key
grammar. `extract.py` does the scan at zero requests and exits non-zero if either document will not
parse, so a parse failure cannot be reported as an absence.

Both documents are served wrapped: `{"value": "<json-encoded string>"}`. The unwrap is explicit in
`extract.py:unwrap()` and a body that does not unwrap is a hard failure.

## Request accounting

**12 of a 16 cap.** GET only throughout — literal `GET`, no `-X`, no `-d`, no POST, no OPTIONS, no
token, no cookie, no authentication, no wordlist. Three hosts, all in this lane's set:
`carelink.minimed.com`, `carelink.minimed.eu`, `carelink-trials.minimed.com`. Per host: 2 controls +
2 documents = 4; ×3 = 12. **4 requests unspent** — the tail is not a per-SKU question, so there was
nothing left to buy.

**Declared delay: `sleep 2.5`, inside the per-host `flock`** (one `flock 9` per request, the sleep
and the curl both inside it). **Measured same-host spacing floor 2.591 s by the kernel body-mtime
oracle** — 9 gaps across the three hosts, **0 under 2.5 s** (`2.870, 2.815, 2.664` / `2.591, 2.602,
2.593` / `2.661, 2.666, 2.687`), every one **≥ 2.5 s** — the declared delay held on all 9 gaps.

⚠ **The `t_sent`/`t_done` series disagrees with itself and is disclosed, not smoothed.** The
`t_sent` series reads a 2.469 s floor with one gap under 2.5 s, and the `t_done` series reads
**1.899 s** and **2.046 s**, with one request's `t_queued` (seq 6, `23:55:56.104Z`) falling
**before** the previous request's `t_done` (seq 5, `23:55:56.767Z`) — a negative duration. This is
the known corrupt-`t0` class `docs/09` §4 records and this is the **fourth** pass to hit it; **no
cause is asserted**. The kernel body-mtime oracle, which does not depend on the harness clock, is
the measurement above, and it says every gap held.

## Controls, in the order they were sent

Two controls **per host, first**, before either document. All 6 passed.

| # | Host | Control | Result | What it proved |
|---|---|---|---|---|
| 1 | `.com` | certainly-absent dotted key `zzz.not.a.real.key.zzz` | **404**, 0 B, `text/vnd.a` | a 404 on this namespace is a genuine absence, not a catch-all — so the 200s below are documents, not shells |
| 2 | `.com` | known-live `logbook.supported.entry.types` | **200**, 281 B, sha256 `7f0a5bb4…` | the route family is live on this host; reproduces area E seq 2 exactly |
| 5,6 | `.eu` | the same two | 404 / 200 281 B `7f0a5bb4…` | as above, on the third deployment this lane owns |
| 9,10 | `-trials` | the same two | 404 / 200 281 B `7f0a5bb4…` | as above |

The 404s are **0 bytes** with `content-type: text/vnd.a` and the 200s are **281 bytes** — the
control pair discriminates, so neither is a fallback. The live control's digest `7f0a5bb46ea59a78…`
reproduces `findings-log/2026-10-13-area-e-perkey-deployments/results.jsonl:2` (`.com`) and `:78`
(`-trials`) **in full**.

## The two documents, per host

**Both documents are byte-identical on all three deployments** — one digest per document, three
hosts, and the `.eu` host is included for the first time on these two routes.

| document | `.com` | `.eu` | `-trials` | reproduces |
|---|---|---|---|---|
| family map (seq 3, 7, 11) | 3470 B `ae70bde0342e44e3…` | same | same | area E seq 40/116 **in full** |
| report dict (seq 4, 8, 12) | 9470 B `ef92e9f39a1709b4…` | same | same | **no** — see the drift note |

### The family map — reproduces, and its `INSTINCT` row is unchanged since 2026-10-13

3470 B and sha256 `ae70bde0342e44e38c3d53b8afb71c262f124f12bd501246465de152280d8b9f` on all three
hosts **is** area E's recorded value, so this is a re-derivation of one artefact served three times,
not three sources (§2.1 — no strength word used). The `INSTINCT` row committed here
(`family-map-verbatim.txt:11`) is **byte-identical** to the row area H first committed at
`findings-log/2026-10-13-area-h-report-naming/family-map-verbatim.txt:11` — verified by `diff`, exit 0.

Row contents, measured: **30 strings** = 13 `SKU-NNNNN-01` + the same 13 as bare `NNNNN-01` + 4
placeholders (`SKU-N/A`, `NA`, `N/A`, `SKU-`). The 16 family names are exactly the recorded 16.

The 13 adopted integers: `78893 · 78953 · 78954 · 78955 · 78956 · 78957 · 78958 · 78959 · 78960 ·
78963 · 78964 · 78965 · 78968`.

### The report-naming list — content reproduces, body size does not

`reportFileNamingSupportedPumpModels` holds **236** entries. Compared against the list committed at
`findings-log/2026-11-03-report-list-drift/list-verbatim-2026-11-03.txt`, the **set is equal and the
order is equal** (both `True`, measured in code). Its 13 `SKU-` entries are **the same 13** as the
family map's, so the two patient tables agree on this axis completely — the only two sources here
that agree, and they are two keys of one document, so that is one source (§2.1).

⚠ **The body is not the 2026-10-13 body.** Area E recorded 10937 B, sha256 `2f918b71cb2889d2…`. This
pass reads **9470 B, sha256 `ef92e9f39a1709b49e921c3f1681481e6a79c0450b944123641c589c7a26b41a`** on all
three hosts. The inner value is pretty-printed at 2-space indent (8 302 B of it, 440 newlines). **The
cause is not established and none is offered** — the one array this pass compares is identical to
the 2026-11-03 capture, so a serialisation change and a content change are not separable from the
bytes kept here. `drift-report-gen.txt` records the document's five top-level keys
(`dualReportEnabled` true, `deviceModelShouldBeInclude` true, the 236-entry list,
`reportGenerationRules` 9, `separateDevices` 29), which is the same key set area H's §6 correction
recorded, so the **structure is unchanged even though the byte size is not**.

## What the tail actually is

**`78961`, `78962`, `78966`, `78967` do not appear in either patient document, on any deployment.**
A whole-document scan for the `SKU-\d{5}-\d{2}` and `\d{5}-\d{2}` shapes returns 26 tokens per
document and **not one of them is one of these four** (`sku-occurrences.tsv`). This is not a
"range tail unrecorded" residue — the row is enumerated, the enumeration skips them, and the skips
are inside the span as well as in the tail (`78894`–`78952` are skipped too, 59 integers). So
`docs/05`'s `SKU-78893-01 … SKU-78968-01` is **a range only in the arithmetic sense**: 13 of its 76
integers are codes, and the endpoints are the first and last of those 13.

**`78963`, `78964`, `78965`, `78968` are present in both patient documents and carry no name.**
There is no display-name field in either document for any family, for any SKU — the documents map
family → code list, they do not name products. The naming source is the portal device table, and it
stops at `78960`.

### Side-finding, zero extra requests: the portal table names an `INSTINCT` code in no family

`MMT-5420` is the portal's **`"Instinct™ Sensor"`** (`findings-log/probe-2026-10-08/recon/JS-API-SURFACE.md:493`)
and it is the **only** `INSTINCT`-named non-`SKU` code. Measured here: it is **absent from all 16
family rows** of the patient map (0 hits across 16 values) and **present in the report list at
index 102**. So the portal's `INSTINCT` naming covers 10 codes (`MMT-5420` + 9 `SKU-`), of which
**one is in no family table at all** and **nine are a strict subset** of the patient map's thirteen.
The naming table is not derived from the family map in either direction — which is the same
conclusion area G reached for `MMT-8600`/`MMT-8601` by a different route, and it is the reason a
client cannot infer a product name from a family row.

## What was searched and found empty (negatives)

- **No name for any tail code, in any source held here.** The two patient documents carry no display
  name for any `SKU-` string, and the portal table covers `78893`–`78960` only. `Instinct™ Sensor` /
  `Instinct™ Go` **cannot be extended past `78960` from this repository's sources** — that is the
  answer to "what do they map to", and a name for `78963`/`78964`/`78965`/`78968` would be a guess.
- **No deployment split.** One digest per document across three hosts. The `.eu` deployment is
  identical to `.com` and `-trials` on both routes, which is the first measurement of its kind for
  these two keys.
- **No disagreement between the two patient tables** on the `SKU-` axis: the same 13 codes, in
  matching form, both SKU-prefixed and bare.

## Limits, stated

- **The portal device table was not re-fetched.** The "9 codes" figure and every product name in
  this log are **cited from area G's record**, not measured here — those assets are 3.4 MB each and
  outside this area's question. Area G's own limits apply unchanged.
- **A family-row membership is not a product identity.** `78963` being in the `INSTINCT` row says
  the vendor files it under `INSTINCT`; it does not say which of the two `INSTINCT` products it is.
  No source here separates them for the tail.
- **The body-size change on the report document is unexplained** and is recorded as a fact only.
- **Neither document exposes a name-to-code direction**, so this pass cannot say whether
  `Instinct™ Go` is the `78954/78956/78958` subset *by product* or by packaging.

## Reproducing

```bash
bash findings-log/2026-11-10-area-ai-instinct-sku-tail/probe.sh   # 12 requests, cap 16
AI_SCRATCH=<printed path> python3 findings-log/2026-11-10-area-ai-instinct-sku-tail/extract.py
```

**The harness was repaired after the recorded run, and the repair sent zero requests.** Two defects
of mine, both in `probe.sh`, both disclosed rather than quietly fixed: a `cp "$out.b" "$SCRATCH/$tag.b"`
copied each body onto itself (harmless — the file was already there — but it emitted a "same file"
warning on all six document fetches, visible in the console; the copy is gone, the bodies were always
in the right place), and `family-map-verbatim.txt` was briefly written with the 16 rows **three times**
(one copy per host). The committed file is the correct 16 rows, and `extract.py` now **asserts** the
three host copies agree before collapsing to one row per family — a host disagreement aborts with exit
2 instead of being silently averaged away. Neither defect touched a request, a status code, a digest or
any claim above; the ledger as committed is the ledger as sent.

Bodies land in the main clone's gitignored `.loop/ai-scratch/` and are **not committed** — area A/G/H
precedent. What is committed is what `extract.py` derives from them: `family-map-verbatim.txt` (all
16 rows, verbatim, one row per family — the three hosts' copies are asserted identical before the
collapse, so a host disagreement aborts rather than being silently dropped),
`sku-occurrences.tsv` (every `SKU-`/bare token with its per-host occurrence count — all 3, i.e. no
host is missing a token another has), `tail-diff.txt` (the 8 tail codes against both documents, code
by code, plus all 76 span integers), `drift-report-gen.txt`.

## Evidence table

| Claim | Class | Source |
|---|---|---|
| 12 of a 16 cap, GET only, controls first per host, 3 hosts | OBSERVED | `results.jsonl` seq 1–12; `run.log` |
| Absent control 404 / 0 B / `text/vnd.a` on all 3 hosts | OBSERVED | `results.jsonl` seq 1, 5, 9 |
| Live control 200 / 281 B / `7f0a5bb4…` on all 3, reproducing area E seq 2 & 78 | OBSERVED | `results.jsonl` seq 2, 6, 10 |
| Family map 3470 B `ae70bde0…` on all 3, reproducing area E seq 40 & 116 in full | OBSERVED | `results.jsonl` seq 3, 7, 11 |
| Family map `INSTINCT` row byte-identical to the 2026-10-13 committed row | OBSERVED | `family-map-verbatim.txt:11`; `diff` vs `findings-log/2026-10-13-area-h-report-naming/family-map-verbatim.txt:11` |
| `INSTINCT` row = 30 strings: 13 SKU + 13 bare + 4 placeholders; 13 integer codes enumerated | OBSERVED | `family-map-verbatim.txt:11`; `sku-occurrences.tsv` |
| `78963`, `78964`, `78965`, `78968` present in both patient documents | OBSERVED | `tail-diff.txt`; `sku-occurrences.tsv` |
| `78961`, `78962`, `78966`, `78967` absent from both patient documents on all 3 hosts | OBSERVED (scan) + INFERRED limit | `tail-diff.txt`; assumption: the whole document was read, so in-document absence is measured — but absence from these two documents is not absence from every Medtronic surface |
| 13 of the 76 integers in `78893…78968` are codes; 63 integers are skipped | OBSERVED | `tail-diff.txt` |
| Report list 236 entries, set **and** order equal to the 2026-11-03 committed list | OBSERVED | `extract.py` output; `findings-log/2026-11-03-report-list-drift/list-verbatim-2026-11-03.txt` |
| Report list's 13 `SKU-` entries are the same 13 as the family map's | OBSERVED | `sku-occurrences.tsv` |
| Report document body 9470 B `ef92e9f3…`, not the recorded 10937 B `2f918b71…`; five top-level keys unchanged | OBSERVED (both bodies) / not explained | `results.jsonl` seq 4, 8, 12; `drift-report-gen.txt`; area E seq 29, 105 |
| Neither patient document names any `SKU-` string | OBSERVED | `sku-occurrences.tsv` — 26 tokens per document, all inside code lists, no adjacent name field |
| The portal device table names 10 `INSTINCT` codes (`MMT-5420` + 9 `SKU-`), all ≤ `78960` | **PUBLISHED (cited, not measured here)** | `findings-log/2026-10-13-area-g-device-tables/FINDINGS.md:114-123`; `findings-log/probe-2026-10-08/recon/JS-API-SURFACE.md:493-496` |
| `MMT-5420` is in no family row and at report-list index 102 | OBSERVED | `extract.py` output over seq 3 and seq 4 |
| Area G's "9 of the range … exactly these 9" under-counts the patient side | OBSERVED + INFERRED | **OBSERVED**: 13 codes in the patient row. **INFERRED**: that area G's 9 is the complete portal set — its own record says so, and the assets were not re-fetched |
| Measured same-host floor 2.591 s (9 gaps, 0 under 2.5 s) | OBSERVED | kernel body-mtime oracle over `.loop/ai-scratch/*.b`; disclosed against the `t_sent`/`t_done` series in §Accounting |
