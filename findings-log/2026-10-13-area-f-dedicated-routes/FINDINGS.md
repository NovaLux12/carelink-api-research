# Area F — dedicated config-escape routes (`.com` and `-trials`), re-derivation

Issue #77. Area letter F, dated 2026-10-13. Successor pass to the dedicated-route half of area F
([findings-log/2026-10-13-area-f-timeline-config/FINDINGS.md] "Deliverable 3"). EU is not
re-requested; its verdicts are cited from that log.

**Verdict:** all three dedicated routes answer `200 application/json` on both
`carelink.minimed.com` and `carelink-trials.minimed.com`, at the byte digests recorded by
the earlier pass. The two controls (`version`, namespace root) `404` with `0` bytes on both
hosts. Measurement reproduces the earlier record exactly, including the per-host digest split
on `recaptcha/key`. No regression pin moved by this pass; the routes were already described
in `docs/04-configuration.md` from the earlier record, and their bodies are region-specific
values with no durable public claim at stake.

## Requests used

`10 of a 14 cap`, GET only. Delay `≥2.5 s` (declared `2.5 s`) between same-host requests,
sleep inside the per-host `flock` (`.loop/host-<host>.lock`). Cap declared 14; 4 left unused.
No POST; no token exchange; no authentication.

Hosts probed: `carelink.minimed.com`, `carelink-trials.minimed.com`. `carelink.minimed.eu`
was deliberately not re-probed (its verdicts are committed in the cited log).

## Method

`curl -s --compressed --max-time 30`, method `GET`, `User-Agent: carelink-bridge-research/1.0`.
Per-host flock (`flock` on `.loop/host-<host>.lock`) with `sleep 2.5` inside the lock, as in
the prior pass. Controls first per host, before any of the three route probes. Response
*bodies are transient* (mktemp dir, removed at the end); only status, `content-type`,
`content-length`, sha256, `x-cache`, body mtime and timestamps enter `results.jsonl`. Headers
are committed under `headers/`.

## Oracle verdict

The status line on `carelink.minimed.*` is usable as a discriminator on this plane: both
controls 404 (LHR cloudfront, `x-cache: Error from cloudfront`, `content-length: 0`, no
`content-type`), and every real dedicated route returns 200 with `content-type:
application/json`. This matches the area-O / carelinkhp oracle behaviour recorded for
`carelink.*`.

## Controls (per host, sent first)

| # | host | tag | path | code | bytes | ctype |
|---|---|---|---|---|---|---|
| 1 | com | 001-control-version | `/patient/configuration/version` | 404 | 0 | (none) |
| 2 | com | 002-control-root | `/patient/configuration/` (root) | 404 | 0 | (none) |
| 3 | trials | 001-control-version | `/patient/configuration/version` | 404 | 0 | (none) |
| 4 | trials | 002-control-root | `/patient/configuration/` (root) | 404 | 0 | (none) |

Both controls establish the same shape they were recorded with in the earlier pass:
404, 0 bytes, no `content-type`. The 404s are a real absence on this host family, not a
fallback page.

## Dedicated routes (OBSERVED)

| # | host | tag | path | code | bytes | ctype | body sha256 | matches 2026-10-13-area-f record |
|---|---|---|---|---|---|---|---|---|
| 5 | com | 003-dedicated-defaultCountry | `/patient/configuration/defaultCountry` | 200 | 20 | application/json | `a8c04033…de763` | yes |
| 6 | com | 004-dedicated-recaptcha-key | `/patient/configuration/recaptcha/key` | 200 | 58 | application/json | `2018cee4…feddb` | yes |
| 7 | com | 005-dedicated-messages-en | `/patient/configuration/messages/en` | 200 | 22 | application/json | `04868b50…227` | yes |

<|end|> # | host | tag | path | code | bytes | ctype | body sha256 | matches 2026-10-13-area-f record |
|---|---|---|---|---|---|---|---|---|
| 8 | trials | 003-dedicated-defaultCountry | `/patient/configuration/defaultCountry` | 200 | 20 | application/json | `a8c04033…de763` | yes |
| 9 | trials | 004-dedicated-recaptcha-key | `/patient/configuration/recaptcha/key` | 200 | 58 | application/json | `a3e59c56…e681` | yes |
| 10 | trials | 005-dedicated-messages-en | `/patient/configuration/messages/en` | 200 | 22 | application/json | `04868b50…227` | yes |

Full shas are in `results.jsonl`; abbreviations here are for readability only.

**Findings, all OBSERVED unless labelled otherwise:**

1. **All three dedicated routes are live on both `.com` and `-trials`.** A third read
   path exists on every deployment, not on EU only. (INFERRED would have been "EU-only";
   the earlier area-E prediction is refuted on both remaining hosts.)
2. **`defaultCountry` and `messages/en` are byte-identical across the two hosts**
   (same body sha256 on com and trials: `a8c04033…` and `04868b50…` respectively).
3. **`recaptcha/key` differs by host** (different body sha256: `2018cee4…` vs `a3e59c56…`),
   consistent with the region-specific reCAPTCHA keys already recorded in
   `scripts/scrub-patterns.txt`. No key *value* is published here; the route returns
   `{"value":"..."}` with a 58-byte body on each host.
4. **The 404 content-type on the controls is absent** (`content-length: 0`, no
   `content-type` header) on both hosts — the same 404 shape the earlier pass found for these
   two paths. No `application/vnd.nervana` case was produced by these probes; that remains a
   per-name shape recorded by area E on trials only.
5. `messages/en` returns `22` bytes on both hosts (`04868b50…`), i.e. the same envelope as
   the earlier `messages/en` 22-byte record; whether the array is empty is a shape
   question owned by the successor to area F and is not settled from size alone. The 16
   vs 22 byte difference against the 2026-10-08 record is a formatting difference, per the
   `pool-f-config-host` addendum.

## What this pass does not add

- No new regression pin. The earlier pass already records the routes and the numbered
  shape; this pass re-derives them under controls first, on the two remaining hosts, without
  changing any asserted value. Nothing in `regression/hurl/` was added or modified, so the
  assertion counts are unchanged by this pass.
- No edit to `docs/04-configuration.md`'s existing statement of the dedicated-route paths;
  it was already accurate at the time of this pass and this record only corroborates it.

## Successors

Area F remains open on its own terms (caller / reachability of `patient-timeline` and
related). This pass discharges nothing new against those two questions and names no new
successor; the two existing successors in `docs/11` stand unchanged:

1. Does the published `config.host` pointer name the gateway this repo probed? (`docs/11` §F
   successor 1; 3 requests, values not published here.)
2. What is in `/patient/configuration/messages/{lang}` now? (shape only; 3 requests.)

Both were addressed by the `pool-f-config-host` addendum recorded in `docs/11` and remain
INFERRED on the point of client reachability.

## Evidence class key

OBSERVED = seen in a live response this pass (response head available in `headers/`).
OBSERVED-for-EU items are cited from the earlier pass's log.
