# Public security posture (read-only defensive review, observed 2026-07-21)

Target: the local working tree at `~/.openclaw/workspace/projects/carelink-bridge` (the NovaLux12 community fork of domien-f/carelink-bridge), a TypeScript/Node 20+ bridge that authenticates against consumer Medtronic CareLink Personal (diabetes — 7xxG / 780G / Guardian 4 / Simplera, NOT cardiac MyCareLink) and uploads to Nightscout. Every evidence link was directly fetched; nothing was asserted that wasn't read.

## 11 evidence-linked risks

- R1 (High) — plaintext `logindata.json` with full CareLink OAuth tokens. Documented in both upstream README and fork. Verified in `src/login.ts` (`writeFileSync` with no mode/encryption). SECURITY.md characterizes these as full account access.
- R2 (High) — `.env` carries both CareLink password and Nightscout `API_SECRET`. Documented in both READMEs and `.env.example`, loaded by `src/config.ts`.
- R3 (High) — dual-system credential exposure in one Node process (CareLink tokens + Nightscout writer secret).
- R4 (Medium) — undocumented app-emulating access to consumer endpoints with no public developer program; ToS reserves termination for "abusive, illegal, disruptive" use.
- R5 (Medium) — 219 transitive deps including `puppeteer-core`, mitigated by the fork's Dependabot + minimalism policy.
- R6 (Medium) — release integrity. Fork has Dependabot/CODEOWNERS/CI/enforce_admins but no signed tags or SLSA provenance. CHANGELOG records the v0.1.1-v0.1.3 version-drift incident (#17).
- R7 (Medium, methodology) — fork-vs-upstream hardening delta. Upstream has no SECURITY.md, no Dependabot, no CODEOWNERS, no CI; still ships `https-proxy-agent`, `socks-proxy-agent`, `https.txt`; `vitest ^2.0.0`; `engines.node >=18.0.0`; version `2.0.0`. All directly verified.
- R8 (Methodology pitfall) — the recent Medtronic CVE-2025-12994/995/996/977 cluster targets cardiac CareLink Network only (Medtronic's own bulletin explicitly states it does NOT affect diabetes CareLink Personal), and CISA ICSMA-25-205-01 is MyCareLink Patient Monitor; both have zero applicability to this bridge's surface. Do not cite as CareLink Personal vulnerability.
- R9 (Medium) — verbose-mode body logging of CGM values. `src/nightscout/upload.ts` logs the full POST body to stdout when `CARELINK_QUIET=false`. The systemd unit sends stdout/stderr to journald.
- R10 (Low) — missing canonical Medtronic privacy URLs in SECURITY.md.
- R11 (Low) — CareLink email-OTP/2FA not handled by Strategy 1 automated login.

## 7 cross-cutting guardrails

- Legal posture citation: EU ToS 2024-04-24, Medtronic bulletin 2025-12-04.
- Product disambiguation: consumer diabetes vs cardiac.
- Fork-vs-upstream delta documentation (R7).
- Token lifecycle hygiene: file mode 0600 + keychain + per-file systemd grant (R1).
- Process isolation (ROADMAP v0.6.0+ split) (R3).
- Advisory triage: any future CareLink Personal-side advisory is a breaking-change event (R8).
- Additional systemd hardening: `MemoryDenyWriteExecute=true`, etc.

## Evidence (per-risk)

- R1 / R2 / R3: fork SECURITY.md, fork README, fork `.env.example`, `src/login.ts`, `src/config.ts`, `src/main.ts`, `src/nightscout/upload.ts`.
- R1 / R2 / R4: upstream README, upstream package.json (ships `https-proxy-agent ^7.0.0`, `socks-proxy-agent ^8.0.0`, `vitest ^2.0.0`, `engines.node >=18.0.0`, version `2.0.0`).
- R5: fork Dependabot graph (219 transitive + direct deps in npm + GitHub Actions ecosystems).
- R6: fork GitHub Security tab + CHANGELOG.md.
- R7: upstream `SECURITY.md` (HTTP 404), upstream GitHub Security tab ("No security policy detected").
- R8: Medtronic CareLink Network bulletin (verified body, 2025-12-04 / updated 2026-01-26), NVD entry for CVE-2025-12996 (CVSS 4.1 MEDIUM, CWE-532), Medtronic Product Security bulletin index, CISA ICSMA-25-205-01.
- R9: `src/nightscout/upload.ts` + systemd unit.
- R10: SECURITY.md lacks current Medtronic privacy URLs.
- R11: `src/login.ts` + CareLink Personal consumer FAQ.

## Conclusion

The bridge is a TypeScript / Node 20+ consumer-medical-data bridge. It authenticates against Medtronic CareLink Personal (consumer diabetes product) using a username/password + 3-strategy OAuth2 flow against Auth0 and writes access/refresh tokens to a plaintext gitignored logindata.json. It fetches pump/CGM data and uploads to Nightscout as SGVs and device-status entries via SHA-1-hashed `API_SECRET`.

The local working tree (NovaLux12/carelink-bridge fork) materially hardened the upstream (domien-f/carelink-bridge): dropped `https-proxy-agent` + `socks-proxy-agent` + `https.txt` + `USE_PROXY`; added SECURITY.md with a private-advisory intake; added Dependabot (weekly, no auto-merge); added CI on Node 20/22 with `enforce_admins` branch protection; added CODEOWNERS; dropped Node 18; bumped vitest 2→4; added an `npm run doctor` pre-flight check; added a `deploy/` directory with a hardened user-level systemd unit. The fork retains the disclaimers: not FDA-approved, not affiliated with Medtronic, may violate Medtronic ToS.

The two recent Medtronic CareLink-adjacent advisories (CVE-2025-12994/995/996/977, published 2025-12-04) target the cardiac CareLink Network and are explicitly excluded from the diabetes CareLink Personal surface per Medtronic's own bulletin — they are not applicable to this bridge.

## Correction (2026-10-11)

The target path quoted above, `~/.openclaw/workspace/projects/carelink-bridge`, is
**stale** — the working tree moved to `projects/novas-github/carelink-bridge`, so the
`novas-github/` segment is missing from the path as written. The body text is left
verbatim; this note is the correction, per the append-only rule in `AGENTS.md` §3.

The target repo is **NovaLux12/carelink-bridge**
(<https://github.com/NovaLux12/carelink-bridge>), the NovaLux12 community fork of
[domien-f/carelink-bridge](https://github.com/domien-f/carelink-bridge). No finding,
risk rating, or evidence link in this document changes — only the path and the
attribution link.
