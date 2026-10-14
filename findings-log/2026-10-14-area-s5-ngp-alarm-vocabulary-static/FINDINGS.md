# Research lane S5 — NGP alarm vocabulary static recovery

**Pass date:** 2026-10-14
**Claim issue:** #94 (CLAIM: swarm lane S5: NGP alarm vocabulary static recovery)
**Successor context:** area P (issue #80) settled the NGP `lastAlarm.code` wire form as
**numeric** (zero-padded to three digits in the UI) and recorded the excluded set
`{"00-1","121"}` plus a *BLE-code name map* without publishing it
[source: findings-log/2026-10-13-area-p-static-schema/FINDINGS.md §5.2].

**Verdict:** **Partial positive.** One client-side NGP alarm-code artefact is recovered
verbatim from the reproducible patient lazy-chunk corpus: a **137-input → 62-canonical
code canonicalisation map** embedded in the connect monitor component, plus its
application rules (pump-model gating, two excluded codes, fallback to canonical
`062`). It is a real, usable recovery of the aliasing the client applies before
looking the code up in its i18n table. It is not, however, the human-readable
vocabulary or an unauthenticated server surface: no `connect.ble.*` message key was
found in any of the 215 chunk files in the same corpus, and no `alarmCode` identifier
exists on any vendor surface probed by the project. The token-blocked rows in
`docs/10-open-questions.md` (#38, #39, #84) are tightened but not closed by this pass.

**Inter-request delay:** n/a — 0 vendor requests; the AGENTS.md §8 floor of ≥2s between requests to the same host is vacuously satisfied.

**Tooling:** GNU grep 3.12 (literal, quoted-payload mode), Python 3.14.8,
Node 24.21.0 (only to parse an unquoted-key JavaScript object literal locally),
`sha256sum` 0.10.0. Read-only static pass over chunk files already on disk — **0 vendor
requests**, no GET/OPTIONS/POST/DNS to any host, no authentication, no token handling.

## 1. Corpus used (digest oracle from prior passes)

| Artefact | Size (B) | sha256 (as recorded) | Role |
|---|---|---|---|
| patient bundle (main) | 3,417,255 | `0fb4fbd483b5f5d21320ffc595e1befad999eac170d1e7d484fd1c9b09c8ebaa` | config-key registry; source of the device-family enum [source: findings-log/2026-10-13-area-p-static-schema/FINDINGS.md §1] |
| patient lazy chunk map | 211 chunks (map at `findings-log/2026-10-13-area-k-patient-chunks/runtime-map.txt`) | re-derived from the runtime, not a single digest | indexes which chunk carries the connect UI [source: findings-log/2026-10-13-area-k-patient-chunks/FINDINGS.md] |
| **patient lazy chunk carrying the map** | 101,594 | `eee8093c0cc1829a7ca4ae4a34dbc23c7494d8b6576b21945398c6cd0f9c7bc9` (measured on the on-disk file used in this pass) | connect monitor / notification component, module `68095` |

**Why this chunk and not a fresh fetch:** area P's controls named module `68095` at
byte range 76,305–87,700 of this chunk as the site of the `lastAlarm.code` numeric
handling; this pass re-reads the *same* component and finds the sibling constant `e`
at bytes 84,468–85,984. No network was used, no new host or candidate list was
introduced, per AGENTS.md §8 and §11.

## 2. What was recovered — the NGP alarm code canonicalisation map

Module `68095` defines a component-local constant (value-exact transcription from
the chunk; numeric keys are quoted here that the source leaves unquoted):

```js
const e = {
  "002": "002", "003": "002", "004": "002", "006": "006", "007": "007",
  "008": "007", "011": "011", "012": "012", "013": "002", "014": "002",
  "015": "002", "016": "002", "017": "002", "018": "002", "019": "002",
  "020": "002", "022": "002", "023": "002", "024": "024", "025": "025",
  "026": "002", "027": "002", "028": "002", "029": "029", "030": "002",
  "031": "002", "033": "002", "034": "002", "035": "024", "037": "037",
  "038": "037", "039": "037", "040": "024", "041": "037", "042": "037",
  "043": "037", "044": "002", "045": "002", "046": "002", "047": "024",
  "048": "024", "049": "002", "050": "024", "051": "051", "052": "052",
  "053": "002", "054": "002", "055": "024", "057": "057", "058": "058",
  "060": "002", "061": "061", "062": "062", "063": "002", "064": "002",
  "065": "002", "066": "066", "067": "002", "068": "002", "069": "069",
  "070": "062", "071": "062", "072": "062", "073": "011", "074": "002",
  "075": "002", "076": "002", "077": "077", "079": "002", "080": "002",
  "081": "002", "082": "002", "084": "084", "100": "100", "103": "103",
  "104": "104", "105": "105", "106": "105", "107": "107", "108": "062",
  "109": "109", "110": "110", "113": "113", "114": "062", "117": "117",
  "130": "130", "131": "024", "140": "140", "775": "775", "776": "776",
  "777": "777", "778": "777", "779": "779", "780": "780", "781": "780",
  "784": "784", "786": "062", "787": "062", "788": "062", "789": "777",
  "794": "794", "795": "795", "796": "796", "797": "797", "798": "797",
  "799": "062", "801": "801", "802": "802", "803": "803", "805": "805",
  "806": "062", "807": "807", "808": "807", "809": "809", "810": "810",
  "811": "810", "812": "812", "814": "814", "815": "815", "816": "816",
  "817": "817", "819": "819", "820": "819", "821": "821", "822": "822",
  "823": "823", "824": "823", "825": "062", "827": "827", "828": "062",
  "829": "829", "830": "829", "831": "829", "832": "832", "833": "833",
  "869": "869", "870": "870"
};
```

Recovered from that component's `init()` method (value-exact; the §2 prose bullets
below flatten one documented branch — see Correction item 2):

- `this.isNGP = "NGP" === K.deviceFamily;`
- `H = K.sLastAlarmCode;` (already the UI's zero-padded string for NGP, otherwise
  `${O.code}`)
- excluded, early return (no alarm name shown):
  `if (["00-1","121"].includes(H)) return;`
- lookup: `const ee = e[H];`
- if `ee` exists:
  - if the pump model `pe` is one of `MMT-1809`, `MMT-1810`, `MMT-1818` and
    `H` is one of
    `803,806,807,808,809,810,811,812,814,815,819,820,821,822,823,824,825,827,828,829,830,831,832,833`,
    the display code is forced to `"062"` (i.e. `H = "062"`) and the name key
    becomes `connect.ble.062`;
  - otherwise, if `ee === "062"` the name key is `null`;
  - otherwise the name key is `` `connect.ble.${ee}` ``.
- if `ee` is absent: `ye = true; H = "062";` name key `connect.ble.062`.
- trailing guard that nulls the name key:
  `0 == +H` or `H in {070,071,072,108,114,786,787,788,799,806,825,828}` or
  (`!nameKey && !ye`).

**Counts (verified, counting rule: entries in the object literal, keys are the JS
string properties).** 137 input codes collapse to 62 distinct canonical codes; 75
inputs are aliases (`k != v`) and 62 are identity mappings. Full table:
`alarm-code-map.tsv` (same directory, 137 rows).

Evidence class: **OBSERVED** — string literals and control flow read directly from a
reproducible (on-disk) patient lazy chunk whose containing bundle's digest is
pinned in prior passes. The *wire value carries these code strings*
interpretation stays **INFERRED** only in the usual client-representativeness sense
already carried by area P; the alias map itself is code the client actually runs.

## 3. What was *not* recovered

- **Human-readable alarm meanings.** The client resolves the (possibly canonicalised)
  code through `this.translateService.instant(`connect.ble.${code}`)` / the
  `connect.ble.<code>` i18n key. A literal search of all 215 chunk files in the same
  corpus found **no definition** of that key and **no concrete `connect.ble.<digit>`
  form** (`connect.ble.[0-9]` → 0). The bare literal `connect.ble.` does occur — **4
  times, in exactly one chunk**, the one this pass names — and every occurrence is a
  runtime template of the form `connect.ble.${...}`. An earlier version of this
  section reported the literal as "0 hits", which was false; see Correction item 3.
  The message
  bundles that define those keys are not in the reproducible corpus, so the
  code→meaning table remains token-gated on a real device report or an i18n asset
  delivery. The numbers themselves (002…870) plus the two excluded (`00-1`, `121`)
  and the dead-end set above are now pinned.
- **Server-side or configured vocabulary.** `alarmCode` still occurs **0 times** across
  patient + clinic + support portals + 211 chunks; the 28-key
  `hcp/configuration/public/...` family and the per-key form still return 404
  unauthenticated. Nothing here changes that negative
  [source: findings-log/2026-10-13-area-p-static-schema-recovery/FINDINGS.md §3-4;
   source: docs/10-open-questions.md].
- **`alarmCode` wire spelling and an official/authoritative vocabulary.** Still
  only the client-side numeric/alias view; no vendor document names the keys.

## 4. Request accounting and controls

- Vendor health-surface requests: **0 of a 0 cap** (0 GET, 0 OPTIONS, 0 POST, 0 DNS, 0 probe to any
  host, including Common Crawl). No credentials, cookies, or headers were sent.
- Controls performed (local, read-only):
  1. re-read `init()` control flow before and after the constant (offsets
     84,468–85,984) to confirm `e` is the same object the lookup `` const ee = e[H] ``
     consumes.
  2. counted object properties with Node (`Object.keys`, 137) and cross-checked against
     a hand count of distinct CSV tokens in the same string.
  3. confirmed no `connect.ble.` **definition** and no concrete `connect.ble.<digit>`
     key exists in the 215-file chunk corpus: the bare literal occurs 4x in exactly
     one file, all four runtime templates (`grep -ral 'connect\\.ble\\.'` → 1 file;
     `grep -rao 'connect\\.ble\\.[0-9]'` → 0).
  4. confirmed the chunk file used is byte-for-byte the one area P referenced at
     the same byte range (size 101,594; runtime-map name `k-6746-c6795ff7e9ff468d-js.b`).

## 5. Consequence for the open questions

| `docs/10` row | Before | After this pass |
|---|---|---|
| #38 — NGP alarm-code vocabulary (#84) | firm negative on surfaces; value unknown | unchanged on *server*; client now gives a **canonical code set + alias table** (137 → 62) and two excluded codes, but no code→meaning |
| #39 — numeric vs string wire form | settled numeric by area P | unchanged; this pass adds alias/normalisation rules on top |
| #77 — validation config field set | negative | unchanged |

This pass is a real half-step, not a closure, and does not mint a new area letter:
the remaining work is the same as area P's close note named — a real device report or
an authenticated `POST hcp/configuration/application` for the meaning side.

## 6. Scrub and citation notes

- No credential, session value, or internal hostname appears in this log; only the
  established scrub-safe hostname spellings. No raw archive capture is committed:
  the chunk file was read locally and is not part of this repository.
- Citations above resolve to `findings-log/2026-10-13-area-p-static-schema/FINDINGS.md`
  and `findings-log/2026-10-13-area-k-patient-chunks/FINDINGS.md`, both present.

## Correction (2026-10-14)

The pass's §1 sentence said "three excluded codes" where every other surface (the
quoted control flow at lines 86-87 (the bullet and its quoted code), the PR body,
and `docs/05` line 292) says two:
`"00-1"` and `"121"` (the early-return set `["00-1","121"]`). The committed TSV
contains neither `00-1` nor `121`, so the correct count is **two**.

**How this was corrected, stated exactly:** the original wording was corrected
**in place** on this unmerged branch (`306ca01` → `32fc642`) — the contested
phrase is quoted here in this section so the change remains auditable, but
nothing above preserves it in place, because it was never published: the file
does not exist on `main` (`git cat-file -e origin/main:…` fails), so no published
record was altered or lost. This is why an in-place edit is permissible here and
would not be on a published claim. The "three" did not affect any count, code, or
pin.

**Three further verifier findings, accepted and recorded (2026-10-14).**

1. **"verbatim source" was an overstatement.** 64 of the 137 keys are unquoted
   numeric literals in the source (`100:`, `103:`) and are rendered quoted in the
   TSV here. No value differs; the fidelity claim is corrected to "value-exact,
   quoting normalised".
2. **"simplified only by whitespace" understates the transformation.** The §2 prose
   bullets (not `alarm-code-map.tsv`, which is a two-column input→canonical table
   containing no `null` and no `connect` string) flatten a branch: for input `062`
   on a gated pump the source emits `connect.ble.062`, while those bullets record
   the flattened `null`. Comparison basis: the §2 prose rendering against the source
   object over all **137** inputs, gated and ungated — **136 of 137 identical**,
   the one divergence being input `062` on a gated pump.

   **Why the other twelve `062` mappers still agree — corrected.** Thirteen inputs
   map to `062`; the other twelve are elements of the trailing guard list
   `["070","071","072","108","114","786","787","788","799","806","825","828"]`.
   An earlier version of this item said all twelve are "nulled by the trailing
   guard regardless". That is **false for three of them** — `806`, `825` and `828`
   are also members of the 24-code list, so on a gated pump that list branch first
   rewrites `H = "062"`; the guard then tests the **rewritten** `H`, which matches
   neither `0 == +H` nor any member of the guard list, so the name key survives as
   `connect.ble.062`. Those three agree with the prose for that different reason,
   not because the guard nulls them (source: chunk bytes 87,590-88,290).

   **The 112/137 figure, with both sides named.** It compares the source's **final
   emitted name key** against the table's **canonical code treated as a name key**
   (`null` when the canonical is `062`). That divergence set is
   `LIST24 ∪ {062}` = 25 inputs, hence 112 of 137. It is not the same measurement
   as the 136/137 above and must not be quoted as if it were.
3. **The corpus figure carries two different denominators, and the rule was not
   recorded.** `211` is the lazy-chunk count re-derived from `runtime-map.txt`;
   `215` is the file count of the on-disk corpus `k-chunk-bodies/`, which holds
   **212** `*-js.b` chunk files (**212 distinct digests**) plus three non-chunk
   files: `k-main.b` (3,417,255 B), `k-runtime.b` (8,268 B) and `k-negative-twin.b`
   (196 B). The 211 map entries account for 211 of those 212 chunk files — the
   emitted `common` chunk is one of them (`runtime-map.txt` line 82, inside the
   derived block of 211), fetched under its emitted name
   `k-fu-_common-206e355a4a593fbd-js.b`. The **212th** chunk file is
   `k-2076-206e355a4a593fbd-js.b` (196 B), byte-identical to `k-negative-twin.b`
   (shared digest `80c3fe2a…`, a 404 page) — the id-form twin of the `common`
   chunk. So **215 = 211 map entries + {id-form twin, `k-main.b`, `k-runtime.b`,
   `k-negative-twin.b`}**. An earlier version of this item named "the emitted
   `common` chunk" as an extra, which double-counted it and would have left a
   re-deriver one file short. The **negative** is stated over the
   215-file superset, but its warrant is the concrete-key count, not a literal
   count: `connect.ble.<digit>` → 0 and no definition exists, while the bare
   literal `connect.ble.` appears 4x in the one chunk this pass names. An earlier
   version of this item endorsed a "0 hits" reading of that literal, which was
   false; the restatement above replaces it.
