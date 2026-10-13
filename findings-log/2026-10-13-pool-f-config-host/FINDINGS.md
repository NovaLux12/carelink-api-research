# Successor A of area F — published `config.host` pointer and `messages/en` shape

Claim issue **#55** (area F). 2026-10-13, successor run `pool-f-config-host`.

**Total 6 of a 6 cap.** GET only — 6 GET, 0 POST, 0 OPTIONS, no
authentication, no token exchange, no cookie. **≥2.5 s between requests to the
same host** (a `sleep 2.5` ran *inside* a per-host `flock` in the parent clone's
`.loop/`, so the delay is enforced by the lock rather than by intent alone;
three other workers were running concurrently on the same machine). Three hosts:
`carelink.minimed.eu`, `carelink.minimed.com`, `carelink-trials.minimed.com`.

Each host received exactly **one** request to each of the two routes below, so
there are no same-host consecutive pairs in this pass (0 same-host gaps to
measure; the floor is stated at the mechanism level rather than as a measured
value). The cross-host gaps in `run.log` are 2.54–2.79 s. Ledger: `results.jsonl`,
6 rows, one per request.

Response bodies are transient by design (`AGENTS.md` §7 — no raw captures); this
pass consumed them while they were in hand and deleted them. The evidence below
is the digests and derived shape facts that survived, by design.

---

## Deliverable 1 — does the published `config.host` pointer name the gateway this repo probed?

**OBSERVED.** `personal.patient.timeline.config` is an object of exactly two
members, `featureEnabled` and `host`, on all three deployments (`member set`
hashed per cell, `results.jsonl`):

| | `.eu` | `.com` | `-trials` |
|---|---|---|---|
| member set | `featureEnabled, host` | `featureEnabled, host` | `featureEnabled, host` |
| `featureEnabled` | boolean `true` | boolean `true` | boolean `true` |
| `host` type | string | string | string |
| `host` length (chars) | **79** | **76** | **76** |
| `host` raw digest (`sha256` of the string, no quotes) | `f81e6648…` | `24ee5564…` | `988acbd7…` |
| `host` canonical-string digest (with quotes) | `4795c0df…` | `fbc3c350…` | `f51cfeeb…` |

The three raw digests are **identical** to those recorded for the same member in
area F (`2026-10-13-area-f-timeline-config`); the value has not changed between
passes. The object-level digest is distinct per deployment because of the `host`
member (`a96b7d57…` / `f9daee21…` / `09233608…`), which is expected.

**Shape classification (derived in-process, the bytes are not committed).** On
every deployment the `host` string:
- starts with `https://`,
- contains `.execute-api.`,
- contains an API-Gateway id of exactly **10** characters,
- contains the region string matching the recorded AWS shape (`eu-central-1` on
  `.eu`, `us-east-1` on `.com` and `-trials`),
- ends with `/prod/patient-timeline`.

It is therefore an AWS API Gateway host shaped exactly like the service this repo
records as the `patient-timeline` gateway in `probe-2026-10-08/CROSS-REGION-CONFIG-FINDINGS.md`,
differing only in the region segment.

**The discrepancy is accounted for.** EU is 3 characters longer than the other
two deployments (`79` vs `76`); the recorded region strings differ by the same 3
(`eu-central-1` is 13 characters, `us-east-1` is 10). That is the three
characters, on its own, with nothing left over. So the pointer is *consistent with*
naming the same gateway family this repo probed: the only region-level difference
in the recorded shape is 3 characters and the measured difference is 3 characters.

This does **not** prove the id segment is identical to the probed gateway's id —
that comparison would require publishing the id, which this repo deliberately
does not do (`AGENTS.md` §7 and the scrub list). It is INFERRED-strongly from
shape plus length arithmetic: the pointer carries the same *family* of host as
the probed gateway and no unexplained extra characters. **A negative on this
question would have been "the pointer does not name the gateway"; that is not
what was observed.** The answer is *consistent-with-yes* on the evidence
available without publishing the value, and nothing in the measurement contradicts
it.

**The `system.gc.gz.transition.flags` envelope member is unrelated.** It is a
top-level key (69-key document, `results.jsonl` seq 1–3) and on these reads it
was a six-member object of feature flags (`sendPeriodicToCumulus`,
`sendDiagnosticLogsToCumulus`, `sendSMSFromCumulus`,
`pullSMSHistoryFromCumulus`, `pullGMInfoFromCumulus`, `displayMessage` — six
members); it carries no `host` and no `TimelineConfig` and is recorded here
only because it appears beside the key under test in the same envelope. No claim
about those flags is made beyond their presence.

---

## Deliverable 2 — what is in `/patient/configuration/messages/{lang}` now?

**OBSERVED.** All three deployments answer `200 application/json` with a
body of 22 bytes whose `sha256` is `04868b50…` on all three (byte-identical by
digest, `results.jsonl` seq 4–6):

| | `.eu` | `.com` | `-trials` |
|---|---|---|---|
| status | `200` | `200` | `200` |
| content-type | `application/json` | `application/json` | `application/json` |
| body bytes | 22 | 22 | 22 |
| body digest | `04868b50…` | `04868b50…` | `04868b50…` |
| envelope members | `messages` | `messages` | `messages` |
| `messages` array length | **0** | **0** | **0** |

So: the envelope still has exactly one member, `messages`, and the array is empty
on every deployment. The 22 bytes are the pretty-printed empty array form
(`{"messages" : [ ]}`); the 2026-10-08 record of 16 bytes was a differently
formatted rendering of the same empty array, so the earlier transport note about
byte counts is resolved in favour of "same empty content, different formatting".

No translated string content exists to report — the array has length 0, so there
is no member list beyond the single envelope key and no entry shape to
characterise. The negative case ("the array is still empty and the 6 bytes are
elsewhere in the envelope") is what was observed and is worth recording
precisely.

---

## What did not change

- No new top-level key, no renamed key, no new `host` pointer value: the
  `personal.patient.timeline.config` digests match the 2026-10-13 record.
- The three deployments remain distinct on `host` (three raw digests) and identical
  on `featureEnabled` (`b5bea41b…`).
- `messages/en` remains empty everywhere.
- `host` value **not published here** and its content is not claimed beyond the
  derived shape facts above; whether an un-abbreviated publication is appropriate
  remains a deliberate non-decision for a human with `scripts/scrub-patterns.txt`
  in front of them.

## What this does not settle

Area F's own question — *who calls `patient-timeline`, and can a third-party
client reach it at all* — is **not** closed by this pass. It settles two
sub-questions (the pointer's shape/region is consistent-with-yes, and the
`messages/en` envelope is still empty), in line with the pool-successor scope. F
stays open; this file is the evidence addendum the successor asked for.

## Controls actually sent (in order)

1. `GET /patient/v2/configuration/public` on `.eu` — positive control on the
   public envelope itself; 200 + `application/json` + 26992 B. Proved the envelope
   is live and readable unauthenticated on this deployment.
2. Same, `.com` — 200 + `application/json` + 24479 B.
3. Same, `-trials` — 200 + `application/json` + 31698 B.
4. `GET /patient/configuration/messages/en` on `.eu` — 200 + `application/json`
   + 22 B; empty array.
5. Same, `.com` — 200 + `application/json` + 22 B; empty array.
6. Same, `-trials` — 200 + `application/json` + 22 B; empty array.

Six requests, three hosts, GET only, no token. No other host touched. No vendor
request for any other patient-public path was made by this pass.
