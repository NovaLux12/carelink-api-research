# Area W — is the per-key projection a complete enumeration path?

**77 of a 84 cap** (claim issue #31). Cap violated: no. **GET only** throughout —
no POST, no `-X`, no `-d`, no token, no authentication. Every request sent with
`curl --compressed` (unconditional gzip on this host). Single host:
`carelink.minimed.eu` (EU deployment). Delay: **2.5 s sleep inside the per-host
`flock`** before every request; measured spacing floor from kernel body-file
mtimes **2.574 s minimum, 0 of 76 gaps under 2.5 s, 0 under the ≥2 s floor**.
The harness `date` series disagrees (minimum consecutive `t_sent` gap **1.7 s**,
3 gaps under 2.0 s) and records **3 negative request durations** (seq 19, 31,
74) — the known corrupt-`t0` class in `docs/09` §4, recorded not smoothed over,
no cause asserted. mtime span 198.7 s vs harness `t_sent` span 198.8 s,
confirming the mtime series is the run's own.

Request accounting: 2 controls + 1 bulk-document fetch + 69 per-key GETs +
4 captcha-subkey GETs + 1 re-issue = **77**. `wc -l results.jsonl` = 77.

## 0. Deviation from the claim, stated first

The claim derives the 69-name candidate list from
`findings-log/2026-10-12-published-pointers/docs/config-eu.json` **"verified 69"**.
**That file does not exist** — on this branch or on `origin/main`. Raw captures
are never committed (AGENTS.md §7), and no committed file carries the full
69-name list (`docs/04` says so explicitly: "Not all 69 key names are
recoverable from the sources"). So the candidate list was derived **live**
instead: one GET of the bulk public config (seq 3, the same URL the pinned
`05-public-config` suite already fetches — no new target), 69 top-level keys
asserted in-harness (`assert len(keys)==69`), sorted, probed in order. Cost: 1
request of the cap's 9-request slack. The full name list is committed here as
`keys.txt` — the first artefact on disk to carry all 69 names.

## 1. Controls, first on the host, and what each proved

| seq | request | result | proves |
|---|---|---|---|
| 1 | `GET /patient/configuration/system/zzz.not.a.real.key.zzz` | **404**, `content-type: text/vnd.a`, 0 B | 404 on this namespace is genuine absence, not a catch-all |
| 2 | `GET /patient/configuration/system/logbook.supported.entry.types` | **200** `application/json`, 281 B, `{"value": "..."}` envelope | the projection is live; anchors the value comparison |

Both reproduce the 2026-10-08 control shapes exactly (281 B for the live key).

## 2. The sweep

Bulk document (seq 3): 200, 26,992 B, **69 top-level keys**, of which **5 null**:
`country.reports`, `outages.nextupdateat`, `personal.inpen.redirect.url`,
`personal.retina.endpoint.config`, `system.logbook.entry.validation.config` —
exactly the five the claim predicted.

Per-key verdicts for all 69 (seq 4–72; full table in `verdicts.tsv`):

- **61 VALUED-match** — 200 `application/json`, envelope unwrapped (with the
  string-boolean second parse) deep-equals the bulk subtree.
- **5 NULL-404** — the five null-valued keys, all 404 with 0-byte bodies.
- **2 DEDICATED-ROUTE-404** — `captcha` and `default.country`: non-null in bulk,
  404 per-key, served at `/patient/configuration/recaptcha/key` and
  `/patient/configuration/defaultCountry` respectively (routes recorded
  2026-10-08, not re-probed here).
- **1 VALUED-QUIRK** — `personal.common.core.reporting.enabled.countries`
  (seq 30, §4).

Captcha subkeys in flat-name form (seq 73–76): `captcha.enabled`, `captcha.key`,
`captcha.type`, `captcha.testKey` → **all 404**. There is no flat-name subkey
grammar; `captcha` answers only through the dedicated recaptcha route. (The
grammar choice was INFERRED in the claim; the negative resolves it.)

## 3. The close condition, met by the negative

**No per-key name outside the bulk document was found.** The only probed names
absent from the bulk doc — the certainly-absent control and the four captcha
subkeys — all 404. The two key sets are identical on EU: 69 bulk names in, 69
per-key verdicts out, zero extras. **The per-key form is a projection of the
bulk document, not an enumeration path to anything further** — the "69-request
enumeration path" framing in `docs/04` is retired, not extended.

Country × bulk vocabulary (offline, zero requests): the 35 area-D country-key
names and the 69 bulk names have a **0-name intersection** — disjoint
vocabularies (camelCase vs dotted/lowercase), answering area W's addendum
question. Name-shape comparison only; no semantic mapping is asserted.

## 4. The stray-bracket quirk (OBSERVED, reproduced)

`GET /patient/configuration/system/personal.common.core.reporting.enabled.countries`
returns 200 / 251 B, but the envelope's value string is the 29-country array
**plus one extra trailing `]`** — `'["AT", …, "AE"]]'` — which is not valid
JSON (`json.loads` fails: Extra data) and not equal to the bulk subtree.
Stripping one trailing `]` yields the 29-element list **equal to the bulk
value**. Re-issued once (seq 77): **byte-identical body, same sha256
`b8806788…`** — vendor-side serialization shape, not a one-off corruption. A
consumer that unwraps-then-parses every per-key value hits this on exactly one
key; a consumer that string-compares envelopes never notices. The sibling
`personal.inpen.supported.countries` (object-valued) parses cleanly — the quirk
rides with the bare-array shape.

## 5. 404-shape discriminator (OBSERVED)

The certainly-absent control's 404 carries `content-type: text/vnd.a`. **All 12
other 404s in this pass** (5 null keys, `captcha`, `default.country`, 4 captcha
subkeys) carry **no `content-type` header at all**. Do not promote this to an
oracle — n=1 control shape — but a reader discriminating "never existed" from
"null-or-aliased" has one more header to check. `docs/04`'s "do not
discriminate on that odd content-type" stands.

## 6. Every negative, in one place

- `captcha` + 4 flat-name subkeys: no per-key form (§2).
- `default.country`: no per-key form (dedicated route, unre-probed).
- 5 null-valued keys: 404, as predicted, none re-probed beyond its single GET.
- 35 country keys vs 69 bulk keys: disjoint, no overlap to resolve.
- Reporting-countries quirk: the one key that does not round-trip (§4).

## Evidence table

| Claim | Class | Source |
|---|---|---|
| 69 keys, 5 named nulls in live bulk doc | OBSERVED | `results.jsonl` seq 3; `keys.txt` |
| 61 per-key values equal bulk subtrees | OBSERVED | `results.jsonl` seq 4–72; `verdicts.tsv` |
| 5 null keys 404; captcha/default.country 404; 4 subkeys 404 | OBSERVED | `results.jsonl` seq 1, 4, 7, 12, 21, 42, 58, 71, 73–76; `headers/` |
| reporting-countries stray `]`, reproduced same-sha | OBSERVED | `results.jsonl` seq 30, 77 |
| 404 content-type split (control vs real keys) | OBSERVED | `headers/001-control-absent.h` vs the 12 other 404 heads |
| country/bulk vocabularies disjoint | OBSERVED (offline) | `keys.txt` × `../2026-10-12-area-d-country-sweep/matrix.tsv` |
| no per-key name outside the bulk doc | INFERRED from 76 negative cells | this file §3 (assumes the 69+4+1 list exhausts the plausible namespace) |
| spacing floor 2.574 s; date-series artefacts | OBSERVED | `run.log`; body mtimes in transient `$TMPD` (not committed) |

Response bodies are transient (`mktemp` dir, not committed) per the run brief;
digests, sizes and content-types are in `results.jsonl`. No credential, session
value, or internal hostname appears in this pass. `probe.sh` is the harness as
sent. Seq 77 (re-issue) was sent separately, by a one-shot invocation of the same shape — `flock` on the same per-host lock, `sleep 2.5` inside, one `curl --compressed` GET of the same URL — with its timestamps recorded into `results.jsonl`/`run.log`/`headers/` to the same schema.
