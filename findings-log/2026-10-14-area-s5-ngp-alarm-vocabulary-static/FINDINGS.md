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

Module `68095` defines a component-local constant (verbatim source from the chunk):

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

Recovered from that component's `init()` method (verbatim, simplified only by
whitespace):

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
  corpus returned **0 hits** for `connect.ble.` (and 0 for `connect.ble.002` and kin),
  and only `connect.ble.` as a runtime template string appears at all. The message
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
  3. confirmed no `connect.ble.` definition exists in the 215-file chunk corpus
     (`grep -R`, 0 hits).
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
quoted control flow on line 85, the PR body, and `docs/05` line 291) says two:
`"00-1"` and `"121"` (the early-return set `["00-1","121"]`). The committed TSV
contains neither `00-1` nor `121`, so the correct count is **two**. The original
phrasing was over-stated by one; it is retained above and corrected here rather
than deleted. The "three" did not affect any count, code, or pin.
