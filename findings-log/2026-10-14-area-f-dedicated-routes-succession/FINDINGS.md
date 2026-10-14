# Area F succession — dedicated-route envelopes on `.com` and `-trials`

Issue #102 (pool lane). Cap 14. Area letter: F addendum, dated 2026-10-14.
Parent record: `findings-log/2026-10-13-area-f-dedicated-routes/FINDINGS.md`
(controls-first re-derivation of the same routes on the same two hosts).

## Result

All three dedicated routes answer `200 application/json` on both
`carelink.minimed.com` and `carelink-trials.minimed.com`. The envelopes are
host- and language-independent in shape (see below). Four controls (two per
host) return `404` with an empty body and no `content-type`. No new regression
pin moved; no value the bridge pins is changed.

## Requests used

**14 of a 14 cap**, GET only. Delay `≥2.5 s` sleep **inside** the per-host
`flock` (`.loop/host-<host>.lock`), plus the global `.loop/carelink.lock` for
the whole run. Cap restated to 14 by the issue plan; 0 unused.

Hosts: `carelink.minimed.com`, `carelink-trials.minimed.com`. `carelink.minimed.eu`
was deliberately not re-probed (its verdicts are committed in the cited parent
logs).

## Method

`curl -s --compressed --max-time 30`, `User-Agent: carelink-bridge-research/1.0`.
Controls first on each host, before any route probe. Response bodies are
transient (`mktemp` dir, removed at the end); only status, `content-type`,
`content-length`, sha256, body shape, `x-cache`, `acao`, body mtime and
timestamps enter `results.jsonl`. Headers are committed under `headers/`.
`probe.sh` is committed in this directory and is the record of what was sent.

## Oracle verdict

On `carelink.minimed.*` the status line is a usable discriminator for this
plane: both controls 404 with `0` bytes, no `content-type`, `x-cache: Error
from cloudfront`; every real dedicated route returns 200 with
`content-type: application/json`. This reproduces the area-O / carelinkhp
oracle already recorded for `carelink.*` and matches the parent pass.

## Controls (sent first, both hosts)

| seq | host | tag | path | code | bytes | content-type |
|---|---|---|---|---|---|---|
| 1 | com | 001-control-version | `/patient/configuration/version` | 404 | 0 | (none) |
| 2 | com | 002-control-root | `/patient/configuration/` | 404 | 0 | (none) |
| 8 | trials | 001-control-version | `/patient/configuration/version` | 404 | 0 | (none) |
| 9 | trials | 002-control-root | `/patient/configuration/` | 404 | 0 | (none) |

Empty body sha256 on all four: `e3b0c44298fc…b855` (0 bytes). These four
rows are the only `404`s this pass produced.

## Dedicated routes (OBSERVED)

| seq | host | tag | path | code | bytes | content-type | body sha256 | envelope shape |
|---|---|---|---|---|---|---|---|---|
| 3 | com | 003-dedicated-defaultCountry | `/patient/configuration/defaultCountry` | 200 | 20 | application/json | `a8c04033…de763` | `{"value": <2-char string>}` |
| 4 | com | 004-dedicated-recaptcha-key | `/patient/configuration/recaptcha/key` | 200 | 58 | application/json | `2018cee4…feddb` | `{"value": <40-char string>}` |
| 5 | com | 005-dedicated-messages-en | `/patient/configuration/messages/en` | 200 | 22 | application/json | `04868b50…227` | `{"messages": []}` (0) |
| 6 | com | 006-dedicated-messages-fr | `/patient/configuration/messages/fr` | 200 | 22 | application/json | `04868b50…227` | `{"messages": []}` (0) |
| 7 | com | 007-dedicated-messages-de | `/patient/configuration/messages/de` | 200 | 22 | application/json | `04868b50…227` | `{"messages": []}` (0) |
| 10 | trials | 003-dedicated-defaultCountry | `/patient/configuration/defaultCountry` | 200 | 20 | application/json | `a8c04033…de763` | `{"value": <2-char string>}` |
| 11 | trials | 004-dedicated-recaptcha-key | `/patient/configuration/recaptcha/key` | 200 | 58 | application/json | `a3e59c56…e681` | `{"value": <40-char string>}` |
| 12 | trials | 005-dedicated-messages-en | `/patient/configuration/messages/en` | 200 | 22 | application/json | `04868b50…227` | `{"messages": []}` (0) |
| 13 | trials | 006-dedicated-messages-fr | `/patient/configuration/messages/fr` | 200 | 22 | application/json | `04868b50…227` | `{"messages": []}` (0) |
| 14 | trials | 007-dedicated-messages-de | `/patient/configuration/messages/de` | 200 | 22 | application/json | `04868b50…227` | `{"messages": []}` (0) |

Full digests are in `results.jsonl`; abbreviations above are for readability.

## Findings (all OBSERVED unless labelled)

1. **All three dedicated routes are live on both hosts.** This extends the parent
   pass's three-path sweep with two further language cells and reproduces every
   earlier digest exactly.
2. **Envelope member sets are stable.**
   - `defaultCountry` → `{value}` with a 2-character string value.
   - `recaptcha/key` → `{value}` with a 40-character string value (a reCAPTCHA
     site-key shaped string; **the value is deliberately not published**).
   - `messages/{lang}` → `{messages}` with an empty array of length 0.
3. **`defaultCountry` and `messages/*` are byte-identical across hosts** — one
   digest each on `.com` and `-trials`.
4. **`recaptcha/key` differs by host** (two distinct digests), consistent with
   the per-host reCAPTCHA keys already recorded in `scripts/scrub-patterns.txt`.
   No key value is published here.
5. **The `messages` envelope is language-independent in this sample.** `en`,
   `fr` and `de` all return the same 22-byte digest and an empty array on both
   hosts. No language-dependent content was observed; whether *any* language
   carries a translated string is not established by this sample.
6. **Controls.** Both `/patient/configuration/version` and the namespace root 404
   with an empty body and no `content-type` on both hosts. **No**
   `application/vnd.nervana` or `text/vnd.a` case was produced by this pass;
   the three-valued 404 content-type set stands exactly as area E recorded it
   (`application/vnd.nervana` on `-trials` for one plausible-but-absent name).
7. **No regression pin moved.** The routes and their envelopes were already
   described; this pass only corroborates them on the two remaining hosts and
   adds three new language cells. Assertion counts unchanged.

## Envelope behaviour — what a consumer can rely on

- Treat each route as a two-field-or-one envelope: `{"value": string}` for the
  two config-escape routes and `{"messages": array}` for the messages namespace.
- An empty `messages` array is a valid, routable response, not a 404. Do not
  infer "no messages configured" from absence of the route.
- `recaptcha/key` is host-specific: do not cache a key from one deployment and
  replay it on another.
- A 404 from `/patient/configuration/version` or the root is a genuine absence on
  this plane and carries no `content-type`; but the control's shape does not
  generalise to every plausible name on every host (area E, 2026-10-13).

## Spacing evidence

Measured from the per-request `t_sent` series (millisecond resolution) in
`results.jsonl`:

- `carelink.minimed.com`: 6 gaps, min 2.675 s, none below the declared 2.5 s,
  none below the repo floor of 2.0 s.
- `carelink-trials.minimed.com`: 6 gaps, min **2.187 s** (seq 10 → seq 11),
  four above 2.5 s and two at/above 2.0 s. The same interval's queued gap
  (seq 10 queued 15:59:32.565 → seq 11 queued 15:59:35.397) measures 2.832 s,
  and seq 10 also recorded a backwards clock step (`t_done` 15:59:35.346 before
  `t_sent` 15:59:35.716). No cause is asserted for either, per `docs/09` §4;
  all intervals remain at or above the repo's 2.0 s floor.

## What this pass does not settle

- Whether any language yields a non-empty `messages` array. The three tested
  (`en`, `fr`, `de`) were all empty; the endpoint accepts arbitrary path
  segments and returns 200 + empty rather than 404, so coverage of the vendor's
  supported languages is not claimed.
- The 404 content-type set on additional plausible names (the issue's
  "deployment-dependent" half). This pass used its full 14-request budget on the
  two controls plus five routes × two hosts. That half remains as area E
  recorded it.
- No new successor area is minted beyond the issue's own proposal (see below);
  no letter is free.

## Successor (per issue #102, restated here)

- **A pinned cell-digest artefact in any future per-key sweep**, 0 requests.
  Closes when the per-cell digest is committed with both columns re-hashable.
  Assumptions (INFERRED): none beyond the quoted addendum claims.

## Evidence class key

OBSERVED = seen in a live response this pass (response head in `headers/`).
OBSERVED-for-EU items are cited from the parent pass's log.
