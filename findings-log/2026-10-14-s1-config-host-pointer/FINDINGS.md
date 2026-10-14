# Lane S1 — published `config.host` pointer identity (successor to area F, successor 1)

Claim issue **#90** (`swarm lane S1: published config.host pointer identity`).
2026-10-14, run `s1-headliner`.

**Total 3 of a 3 cap.** GET only — 3 GET, 0 POST, 0 OPTIONS, no
authentication, no token exchange, no cookie. **≥3 s between hosts**
(sequential, no same host was hit twice). Three hosts:
`carelink.minimed.eu`, `carelink.minimed.com`,
`carelink-trials.minimed.com`.

Response bodies are transient by design (`AGENTS.md` §7 — no raw captures); this
pass consumed them while they were in hand and deleted them. The evidence below
is the digests and derived shape facts that survived, by design, in
`results.jsonl` (3 rows) and `derived.json`.

## Question

Is the published pointer `personal.patient.timeline.config.host` the full, unabbreviated
`https` string of each deployment's `patient-timeline` gateway, or does it name
something else?

**Closed.** Yes, on all three deployments, and the match is exact on the
gateway-id segment, not merely shape/region-consistent.

## Deliverable 1 — unabbreviated `host` member, in hand

**OBSERVED.** `personal.patient.timeline.config` is an object of exactly two
members, `featureEnabled` and `host`, on all three deployments (member-set hash
`bffc059a…` re-appears here unchanged from the 2026-10-13 pool run). `featureEnabled`
is boolean `true` everywhere. `host` is an `https` string whose measured form,
with the gateway-id segment redacted, is:

| | `.eu` | `.com` | `-trials` |
|---|---|---|---|
| host length (chars) | 79 | 76 | 76 |
| sha256 of the whole string | `f81e6648…` | `24ee5564…` | `988acbd7…` |
| masked shape | `https://<REDACTED_ID>.execute-api.eu-central-1.amazonaws.com/prod/patient-timeline` | `https://<REDACTED_ID>.execute-api.us-east-1.amazonaws.com/prod/patient-timeline` | `https://<REDACTED_ID>.execute-api.us-east-1.amazonaws.com/prod/patient-timeline` |
| region segment | `eu-central-1` | `us-east-1` | `us-east-1` |
| gateway-id segment length | 10 | 10 | 10 |
| gateway-id segment sha256 | `bfda4356…` | `30a035af…` | `f11b68e5…` |
| stage/path suffix | `/prod/patient-timeline` | `/prod/patient-timeline` | `/prod/patient-timeline` |

The 3-character length delta (79 vs 76) is exactly the difference between
`eu-central-1` (13) and `us-east-1` (10), leaving nothing unexplained. The three
whole-string digests are byte-identical to the ones recorded in
`findings-log/2026-10-13-pool-f-config-host/FINDINGS.md`, so the value has
not moved between passes.

**The match, established while the body was in hand.** The 10-character gateway-id
segment of each pointer hashes as shown above. **OBSERVED**, each of those three
digests equals the SHA-256 of the 10-character gateway id published for the same
deployment's `patient-timeline` gateway in
`findings-log/2026-10-12-published-pointers/enumeration-scrubbed.txt`
(lines 121, 187 and 245 respectively — one id per deployment). That file is the
repo's own record of the probed gateway's host. So the pointer does not merely
*have the right shape and the right region* — it carries the same 10-character
gateway id as the gateway this repo records as `patient-timeline`, on every
deployment. This upgrades the earlier "consistent-with" reading (pool-f, 2026-10-13)
to a positive match, and nothing in the measurement contradicts it.

The raw `host` value and the raw gateway id are **not published here**, by the
deliberate non-decision recorded in area F's successor 1 (publication is a
disclosure decision for a human holding `scripts/scrub-patterns.txt`). A reader
can verify the match above by hashing the ids in
`enumeration-scrubbed.txt` lines 121/187/245 and comparing to the digests in
`derived.json`. The same match is what lets region and id be compared without
republishing the id.

## Regional differences (searched, not assumed)

- **Region segment differs exactly as expected:** `eu-central-1` on `.eu` versus
  `us-east-1` on `.com` and `-trials` — the 3-character difference, accountable
  to nothing else.
- **Gateway id differs per deployment:** the three id-segment digests above are
  distinct, so the pointer names a *per-deployment* gateway, not one shared id
  with the region swapped. The earlier record already had a different id per
  deployment; this pass confirms the pointer agrees with that on all three.
- **Stage/path is constant:** `/prod/patient-timeline` on all three — the
  pointer's deployment variance is region + id only.
- **Reader-side region verification (response headers)** agrees with the
  pointer's region:
  - `.eu`: CSP `connect-src` names `clcloud.minimed.eu`, `commoncore.minimed.eu`,
    `commoncore.medtronic.eu`;
  - `.com`: same three with `.com`;
  - `-trials`: the same three with `-trials` prefixes.
  These are attributes of the *portal* surface that serves the document, not of
  the pointer, but they corroborate which deployment answered, which is the
  existing control for "am I looking at the right region's bulk document".
- Nothing else in the pointer's `host` varies: structure, scheme, `.execute-api.`,
  `.amazonaws.com`, stage and path are identical across deployments.

## What did not change

- Member set, `featureEnabled = true`, and all three digests are unchanged from
  the 2026-10-13 pool pass.
- The region/id variance recorded here is consistent with, and now verifies, the
  existing `2026-10-08` record rather than correcting it.

## Controls actually sent

1. `GET /patient/v2/configuration/public` on `.eu` — `200 application/json`,
   26992 B; confirms the public envelope is live and readable unauthenticated on
   this deployment before its `host` member is read.
2. Same on `.com` — `200 application/json`, 24479 B.
3. Same on `-trials` — `200 application/json`, 31698 B.

No certainly-absent path was added: the cap is 3, consumed entirely by reading
the pointer while the body was in hand, which is the one thing a later re-fetch
cannot recover (`AGENTS.md` §7). The three public documents are themselves the
positive controls — the member and the header set are read from the same response,
so there is no split between "control request" and "data request". The CSP /
`x-amz-cf-pop` headers above are the regional corroborators and were captured
verbatim (see `headers/`).

## What this does not settle

Area F's own question — *who calls `patient-timeline`, and can a third-party
client reach it at all* — is **not** closed by this pass. It settles the
pointer's identity sub-question, which is what issue #90 asked for. The
`messages/en` envelope question was already closed by the 2026-10-13
pool-successor pass and is not re-probed here.

## Assumptions (INFERRED)

- That `findings-log/2026-10-12-published-pointers/enumeration-scrubbed.txt`
  lines 121/187/245 name the same gateways this repo probed rather than other
  gateways with coincidentally different ids — INFERRED from the repo's own
  record naming those ids as the `patient-timeline` gateways, and from the
  agreement of region segments between that file, the 2026-10-08 probe and the
  pointer read here.
- Nothing here assumes the raw pointer value is publishable. Whether it may be
  published remains a deliberate non-decision; only its digests and masked shape
  are recorded.
