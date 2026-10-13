# Area H — `reportFileNamingSupportedPumpModels`, entry by entry (2026-10-13)

## §0 Two self-corrections, stated first

**Correction 1 — the claim's corpus premise was right; a mid-course
"correction" of it was wrong.** During the read phase the committed path
`findings-log/2026-10-12-published-pointers/docs/config-eu.json` was found not
to exist and no `.md` file names `personal.common.core.report.generation`, so
the list was provisionally re-located to the HCP family
(`pow.common.core.report.generation`, committed matrix at
`findings-log/probe-2026-10-08/recon/HCP-CONFIG-SCHEMA.md:164`). That
re-location was wrong: the live patient document (seq 5, `results.jsonl:5`)
carries a top-level key `personal.common.core.report.generation` whose value
holds `reportFileNamingSupportedPumpModels` with exactly 214 entries, verified
in code. The grep miss happened because the key appears in live JSON, never in
prose. Both keys exist — they are different documents on different host
families — and the 214-entry list the claim named is the patient's.

**Correction 2 — three of five requests were wasted on Correction 1.**
Seqs 1, 2 and 4 went to `carelinkhp.minimed.eu` chasing the wrong document,
and all three additionally carried a broken header (§1). They are recorded as
sent, count against the cap, and prove only the header gate — not absence, not
liveness. The area still closes because seq 5 returned both halves of the
corpus (list + family map) in one document, as the claim said it would.

## §1 Accounting — 5 of a 6 cap

**5 of a 6 cap. Method GET throughout** — no POST, no OPTIONS, no `-d`, no
token exchange, no authentication. Delay: `sleep 2.5` inside each per-host
`flock` (lock files in the main clone's `.loop/`, hostnames as lock names),
`curl --compressed` on every request. Harness committed as `probe.sh`;
per-request ledger in `results.jsonl` (one row per request, seq 1–5);
response heads in `headers/`; completion timestamps in `run.log`.

**Harness defect (mine, disclosed).** `probe.sh` passed extra curl args
through unquoted `$*`, so `-H "X-System-ID: ProWeb"` split into
`-H "X-System-ID:"` plus a stray pseudo-URL `ProWeb`. Curl therefore ran two
transfers per hp request — one failing (http code `000`) and one reaching the
vendor with an **empty** `X-System-ID` value (http `412`) — and the two `-w`
codes concatenated into the `000412` recorded in `run.log`. The vendor's
actual response on all three hp requests was **HTTP 412, `content-length: 0`,
no `Content-Type`** (`results.jsonl:1,2,4`; `headers/hp-*.h`). The patient
requests (seqs 3, 5) take no extra args and are unaffected.

**Timing instrumentation gap (mine, disclosed).** The harness recorded only
completion timestamps at 1-second resolution; `t_queued`/`t_sent` were not
separately instrumented, so `results.jsonl` carries `t_done` only. Same-host
completion gaps from `run.log`: hp 2 s then 6 s (seqs 1→2→4), patient 7 s
(seq 3→5). The 2 s hp reading is **below the declared 2.5 s sleep at this
resolution and cannot be resolved further** — completions at 08:28:36 and
08:28:38 are consistent with both a held sleep and a short gap, and no cause
is asserted either way (the same provenance problem `docs/09` §4 records for
three prior passes). The floor over the run is therefore stated as **≥2 s
measured, 2.5 s intended** — the repo's 2 s floor holds on every gap; the
declared 2.5 s is unproven on one.

## §2 Controls — what each proved

| Seq | Control | Result | Proves |
|---|---|---|---|
| 1 | certainly-absent hp path `…/public/zzz.this.does.not.exist.zzz` (same path the 2026-10-08 matrix used) | 412, empty, **not** 404 | **Nothing about absence** — the empty header voids it. It corroborates one thing: the `X-System-ID` gate is enforced (412 on empty value), consistent with the committed matrix's header-rejected rows (OBSERVED same-day, INFERRED match to the matrix's cause) |
| 2 | known-live hp key `cua.control.codes.settings` (778 B in the matrix) | 412, empty | Same: header gate enforced, liveness unproven |
| 3 | certainly-absent patient per-key path `/patient/configuration/system/zzz.not.a.real.key.zzz` (claim control 1) | **404**, `content-type: text/vnd.a`, 0 B (`results.jsonl:3`) | **Absence reads on the patient per-key form.** A missing key 404s with an empty body — so a 200 carrying a body is a true presence |

No valid same-day control exists for the hp namespace; the hp oracle rests on
the committed 2026-10-08 matrix (absent→404, live→200+JSON at
`HCP-CONFIG-SCHEMA.md:164`), labelled a prior observation, not re-derived
here. No candidate was read from that namespace.

## §3 Corpus — one response holds both halves (OBSERVED, seq 5)

`GET https://carelink.minimed.eu/patient/v2/configuration/public` → **200,
`application/json`, 6359 B compressed / 26992 B raw**
(`results.jsonl:5`; body digest `d68b6b5…f1cb2d`, decompressed). Verified in
code against the decompressed body:

- **69 top-level keys** — the document shape area T recorded is unchanged.
- `personal.common.core.report.generation` is a dict with
  `reportFileNamingSupportedPumpModels`: a list of **214 strings, all `str`**
  — the count `docs/05:115` states, now re-derived rather than repeated.
  Verbatim in `list-verbatim.txt` (index + entry per line).
- `personal.device.family.to.model.mapping`: a dict of **16 families** —
  `BLE700 BLE720 BLE740 BLE770 BLE780 CC840 CC880 EAGLE GM GST INSTINCT NMX7
  NMX8 SIMPLERA SIMPLERACC SIMPLERACCOLID`. Full value rows verbatim in
  `family-map-verbatim.txt` (this is the first commit of the complete value
  set; prose sources previously quoted 8 of 16 rows).

`content-length: 6359` reproduces the 2026-10-11 reading `docs/00:333`
records byte-for-byte at the compressed level.

## §4 Classification — every entry, in code (PUBLISHED)

Rule (applied to the stripped entry): placeholder ∈ {`N/A`,`NA`,`SKU-N/A`,
`SKU-`} · bare number `^[0-9]+$` · wire code `^(MMT-?|SKU-)` or unprefixed
`^\d{5}-\d{2}$` (the INSTINCT alias shape) · display name = the rest.
Result over all 214 rows: **wire code 129 · display name 71 · bare number 10
· placeholder 4**.

Anomalies, each enumerated:

- **Duplicates (2):** `MMT-9015` ×2 and `Precision Xtra® / Xceed™` ×2
  (Counter over the 214 rows; `MMT-9015` is EAGLE's in the family map, so the
  wire-code dupe doubles a real entry).
- **Whitespace anomaly (1):** `MMT-5100J      ` (trailing spaces) — and it
  matches the family map's own padded `SIMPLERA` entry **exactly**, so the
  padding is vendor-side, not corruption.
- **Placeholders (4):** `SKU-N/A`, `N/A`, `NA`, `SKU-` — all four are
  **themselves INSTINCT family values** (`family-map-verbatim.txt:10`), so
  they match (§5), not dangle.
- **Bare numbers (10):** `515 522 523 551 554 715 722 723 751 754` — each sits
  beside its `MMT-` form (`MMT-515` + `515`, …), the pairing the claim named.
  None matches any family value, exactly or normalized.
- **Display-name mixing (71):** three sub-shapes — (a) 34 lowercase slugs
  (`bayer*`, `lifescan*`, `roche*`, `therasense*`, plus `gm3_snapshot`,
  `gm4_snapshot`, `DEMMT-105ELNA`); (b) 35 meter names with `®`/`™`
  (`Accu-Chek®…`, `CONTOUR®…`, `OneTouch®…`, …); (c) `CSS-7200`/`CSS-7201` +
  unhyphenated `CSS7200`/`CSS7201` (the alias split `docs/05:148` records for
  `MMT5100`/`MMT5101`, here in a second prefix). None matches any family
  value.

## §5 Matching — each wire-code entry vs the family map (PUBLISHED vs PUBLISHED)

Exact match of the stripped entry against the 16-family value set
(`family-map-verbatim.txt`), then normalized
(uppercase + strip non-alphanumerics, the `docs/05:231` rule):

- **Wire codes: 82 matched / 47 unmatched, exact.** Normalization changes
  **nothing** — the unmatched set is identical under both rules, so no entry
  is a mere hyphenation/padding variant of a family value.
- Matched by family: INSTINCT 26 · SIMPLERACC 14 · BLE780 9 · CC880 6 ·
  EAGLE 5 (incl. both `MMT-9015` rows) · BLE770 4 · BLE720 4 · BLE700 3 ·
  NMX7 3 · BLE740 2 · NMX8 2 · SIMPLERA 2 · GST 1 · SIMPLERACCOLID 1.
  GM matches nothing (its sole value `GM` is not in the list).
- **Placeholders: 4/4 matched** (all INSTINCT). **Bare numbers: 0/10.
  Display names: 0/71.** Overall: **86 rows matched, 128 unmatched.**
- The 47 unmatched wire codes group by numeric prefix (verbatim sets, no
  hardware asserted): `105*` ×12 (`MMT-105EL…`/`NN…`/`SP…` — 8–10-char
  suffixes, the longest codes in the list) · `151*` ×3 · `171*` ×5 ·
  `178*` ×3 · legacy `5xx`/`7xx` pairs ×20 (`MMT-515`+`515` … `MMT-754`+`754`)
  · `MMT-5101` · `MMT-5420` · `MMT-6500/6501` · `77xx/78xx/79xx` ×6
  (`7731 7763 7821 7841 7910 7911`) · **`MMT-8200/8201/8400/8401`** — present
  in this patient list *and* (per `HCP-CONFIG-SCHEMA.md:457-461`) the HCP
  report doc, absent from the family map. `docs/05:113`'s "present in the HCP
  report config, absent here" is therefore half-stale: the four codes are in
  **both** report lists and in **neither** family table — correction attached
  in `docs/05`, original row left readable.

INFERRED (assumption stated): the unmatched prefixes read as older hardware
generations the family map no longer carries — the map's oldest rows are
`BLE7xx`/`SIMPLERA`, while the list reaches back to `5xx`/`7xx` and sideways
to pen-shaped `105*` codes. No response observed here demonstrates what any
of these codes is; the grouping is structural (shared prefix + MMT-form/bare
pairing), not an identification.

## §6 Negatives recorded

- The HCP namespace contributed nothing usable (seqs 1, 2, 4 voided by §1's
  defect); no third POST, no retry — a re-run would exceed the 6 cap.
- No entry required normalization to match: exact == normalized throughout.
- No display name and no bare number appears in any family; GM matches
  nothing in the list.
- `personal.common.core.report.generation` holds exactly the two sibling
  keys `dualReportEnabled`/`deviceModelShouldBeInclude` plus the list — no
  further naming vocabulary on this document.

## §7 Close

Close condition met: 214 entries extracted and classified entry-by-entry,
each wire-code entry matched against the family map (82 matched by family,
47 unmatched by prefix group named), anomalies enumerated (2 dupes,
1 whitespace, 4 placeholders, 10 bare numbers, 71 display names in 3
sub-shapes). The negative the claim allowed (exact family-map agreement) did
**not** occur — the residue is 128 rows — and that disagreement is the
finding: the report list is a superset vocabulary reaching past the family
map, not a view of it. Successor: `docs/10` §1 new row (per-build mapping of
these 214 once area G lands).
