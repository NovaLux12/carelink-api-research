# Passive infrastructure map (observed 2026-07-21)

Methods: Google DNS-over-HTTPS (DoH) for A/AAAA/NS; crt.sh for certificate-transparency (CT) history; AWS published IP-ranges JSON; passive read of Medtronic/MiniMed hosted privacy and status pages. No port scans, no subdomain brute force, no authenticated calls.

## DNS footprint

| Host | A record (CloudFront) | AAAA range | Parent NS |
|---|---|---|---|
| carelink.minimed.com | d2dg11a8rjk1ec.cloudfront.net (3.174.141.47/87/99/122) | 2600:9000:28fd::/48 | ns2-ns5.medtronic.com |
| carelink.minimed.eu | d2wjia8tvetzw1.cloudfront.net (18.244.164.55/56/59/78) | 2600:9000:2552::/48 | ns2-ns5.medtronic.com |
| clcloud.minimed.com | d3vfunz44txmhq.cloudfront.net (52.84.118.16/26/33/120) | 2600:9000:203c::/48 | ns2-ns5.medtronic.com |
| clcloud.minimed.eu | d3ak89jujtmuns.cloudfront.net (18.165.201.9/100/112/126) | 2600:9000:23d3::/48 | ns2-ns5.medtronic.com |
| carelink-login.minimed.com | d3hjfmwxasyjhb.cloudfront.net (13.226.144.6/55/68/86) | 2600:9000:2076::/48 | ns2-ns5.medtronic.com |
| carelink-login.minimed.eu | d222is88nt984z.cloudfront.net (54.230.201.19/57/73/121) | 2600:9000:2008::/48 | ns2-ns5.medtronic.com |
| carelink-content.medtronic.com | d2unnks29ck8ft.cloudfront.net (54.230.201.60/61/99/128) | 2600:9000:2008::/48 | ns2-ns5.medtronic.com |

carelink-connect.minimed.eu: NXDOMAIN with stale SOA serial 2015011639 — RETIRED. Some 2024-2025 third-party traffic-capture write-ups still mention it.

## PKI (DigiCert only)

| Host | Latest cert validity | Issuer intermediate |
|---|---|---|
| carelink.minimed.com | 2026-04-08 → 2026-10-23 | DigiCert Global G2 TLS RSA SHA256 2020 CA1 |
| carelink.minimed.eu | 2026-04-08 → 2026-10-23 | DigiCert Global G2 TLS RSA SHA256 2020 CA1 |
| clcloud.minimed.com | 2026-04-08 → 2026-10-23 | DigiCert Global G2 TLS RSA SHA256 2020 CA1 |
| clcloud.minimed.eu | 2026-04-08 → 2026-10-23 | DigiCert Global G2 TLS RSA SHA256 2020 CA1 |
| carelink-login.minimed.com | 2025-08-27 → 2026-09-16 | DigiCert Global G2 TLS RSA SHA256 2020 CA1 |
| carelink-login.minimed.eu | 2025-08-27 → 2026-09-16 | DigiCert Global G2 TLS RSA SHA256 2020 CA1 |
| carelink-content.medtronic.com | 2026-06-05 → 2026-12-20 | DigiCert Global G2 TLS RSA SHA256 2020 CA1 |

Renewal cadence: carelink-* + clcloud-* renew every ~6 months in April / October; carelink-login-* annual in August/September; carelink-content.medtronic.com annual in June. No cert currently overlaps its expiry window with the observation date.

## Privacy-statement sub-processors (EMEA)

EEA CareLink Personal data is hosted in the EEA on AWS infrastructure. Nutrino Ltd (Tel Aviv, Israel) operates CareLink Personal on behalf of Medtronic MiniMed Inc. EU Standard Contractual Clauses + EU-US Data Privacy Framework certification cover cross-border transfers. Source: https://carelink.minimed.eu/media/en/gb/privacy_statement.pdf

## Operational anchors

- status.minimed.com is the live system status page advertised by Medtronic.
- Medtronic Diabetes "CareLink Personal Connectivity" page is the public landing for post-outage user instructions.

## Operational implications for the bridge

1. Single-CDN blast radius — AWS CloudFront outage in any meaningful region affects every CareLink consumer endpoint.
2. APEX zone authority under Medtronic control, not AWS. DNS changes go through Medtronic's name servers, not CloudFront's. A misconfigured change could CNAME the host away or drop it.
3. PKI is single-CA — DigiCert outage or revocation event impacts all seven certs simultaneously. Renewal cadence is healthy; no near-term certificate-expiry risk.
4. status.minimed.com is the operational ground truth — poll this before any exponential-backoff retry loop.
5. Authentication and data paths are split into separate CloudFront distributions — auth failure does not automatically mean upload failure and vice versa. Treat as independently retryable.
6. carelink-connect.minimed.eu is RETIRED — do not use.
7. Region routing is by hostname, not by client geography. clcloud.minimed.com is the US endpoint; clcloud.minimed.eu is the EMEA endpoint. Choose the correct host up front; CloudFront will NOT redirect.
8. TTL on CNAME records is 1800s (apex) / 3386s (clcloud.minimed.eu). Short enough for failover, but a resolver cache can pin a stale IP for up to ~56 minutes during an AWS region incident. Plan retries to refresh DNS after ~30 min.
9. Two-factor verification is mandatory at account creation (email verification code + reCAPTCHA) per the official CareLink FAQ. The bridge cannot bypass this for unattended account creation; it must drive a real email inbox.
10. EMEA Privacy Statement mandates EEA-resident storage + AWS as IT/hosting sub-processor + Nutrino (Israel) processor.
11. Brand split between medtronic.com and minimed.com/.eu — carelink-content.medtronic.com is the only target on the corporate apex and serves a different function (static-asset CDN).
12. CareLink Privacy Policy on the .eu host states no third-party data sales and 24-month inactivity deactivation. Bridges that hold credentials or tokens for long periods need to re-auth or risk silent account lockout.

## Confidence summary

- High: seven target DNS resolutions; CT histories; parent-zone NS records; AWS CloudFront attribution; current cert SANs/expiries; advertised hosts (carelink.minimed.com, carelink.minimed.eu, status.minimed.com).
- Medium: functional split between carelink (UI), clcloud (data), carelink-login (SSO), carelink-content (static CDN); EMEA hosting residency claim.
- Low: that carelink-connect.minimed.eu is fully retired; precise internal CloudFront origin hostnames for each distribution.
