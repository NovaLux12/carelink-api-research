# Investigation session index (2026-07-21)

Session: public, no-holds-barred investigation of the Medtronic CareLink consumer surface and how it relates to the local TypeScript bridge at `~/.openclaw/workspace/projects/carelink-bridge` (NovaLux12 community fork of domien-f/carelink-bridge). All public sources; no accounts, credentials, mutations, brute force, vulnerability testing, or patient data accessed.

## Files in this folder (all evidence-linked, observation date 2026-07-21)

1. `00-repo-state.md` — current state of the local working tree.
2. `01-endpoint-matrix.md` — public CareLink endpoint matrix (14 unauthenticated GETs).
3. `02-ecosystem-parity.md` — open-source parity vs upstream + the active Python client.
4. `03-data-model-and-gaps.md` — P0/P1/P2/P3 data-model and Nightscout-mapping gap memo.
5. `04-operational-history.md` — chronological incident / change timeline 2024-2026.
6. `05-official-docs-matrix.md` — 780G + CareLink Personal public-docs fact table.
7. `06-official-surface.md` — public CareLink Personal surface, apps, auth, privacy, terms.
8. `07-passive-infrastructure.md` — DNS / CT / PKI / privacy-statement sub-processor map.
9. `08-web-asset-surface.md` — CareLink SPA web-asset surface.
10. `09-mobile-artifacts.md` — CareLink Connect mobile store metadata and version history.
11. `10-risk-and-governance.md` — security / privacy / governance risk memo.
12. `11-public-security-posture.md` — public security posture (defensive review) of this repo.
13. `README.md` — this file.

## Top recommendations distilled from the full set

- Safety, ship before real pump: P0.1 mmol/L unit passthrough (P0 safety), P0.2 lastAlarm plumbing with stop-using-pump WARN only (no auto Nightscout alarm relay), 0600 atomic logindata.json write, journald medical-payload redaction.
- After real pump arrives (Nov 2026): P1.1 markers/treatments, P1.2 therapyAlgorithmState, P1.3 limits[] schedule, P3 trend map NONE→Flat, P2.1 reservoirLevelPercent, then P2.2 multi-patient, P2.3 additional endpoints.
- Architectural: derive `baseUrlCareLink` and `baseUrlCumulus` from discovery instead of hardcoding `/patient/*`; implement status-aware capped exponential backoff with jitter and honour `Retry-After`; remove or honour `CARELINK_MAX_RETRY_DURATION=512`; classify permanent auth failures separately from transport/5xx so refresh exceptions do not always delete the token file.
- Auth0 maintenance: pin `android/3.6`; add a "no Auth0SSOConfiguration" named error so on-call recognises the cut-over; assume `client_secret` is optional post-Auth0; add tests for same-account token invalidation, 3h access token refresh, and discovery version pinning.
- Legal/operations: cite Medtronic's own bulletin excluding CareLink Personal from CVE-2025-12994-12997. Keep the bridge strictly personal, non-commercial, single-account. Document that the bridge is not affiliated with or endorsed by Medtronic and may violate Medtronic ToS.
- Infra: bridge depends on a single AWS CloudFront provider across all seven CareLink consumer hosts; `status.minimed.com` is the operational ground truth; add a maintenance-window probe. `carelink-connect.minimed.eu` is retired — do not use.
- Mobile: store semantic version 3.8.1 ≠ discovery selector `android/3.6`. Public discovery proves 3.6/3.7 are the Auth0-compatible tracks. Treat 3.6 as a pinned dependency.

## Correction (2026-10-11)

The local path quoted in the intro above, `~/.openclaw/workspace/projects/carelink-bridge`,
is **stale** — the working tree moved to `projects/novas-github/carelink-bridge`, so the
`novas-github/` segment is missing from the path as written. The body text is left
verbatim; this note is the correction, per the append-only rule in `AGENTS.md` §3.

The sibling repo is **NovaLux12/carelink-bridge**
(<https://github.com/NovaLux12/carelink-bridge>), a community fork of
[domien-f/carelink-bridge](https://github.com/domien-f/carelink-bridge).
