# Medtronic CareLink — SSO config + OpenID Connect surface
#
# Downstream consumer: https://github.com/NovaLux12/carelink-bridge — the bridge runs this suite before a release
# (`npm run drift:check` on the bridge side). A failure here reaches their
# release checklist; see https://github.com/NovaLux12/carelink-bridge/blob/main/docs/vendor-api/README.md
#
# These are public, unauthenticated. They back the login flow in
# https://github.com/NovaLux12/carelink-bridge/blob/main/src/login.ts.
# If any of these fail, login breaks before any patient data is touched.
#
# Verified live 2026-10-08. JWKS URI is /.well-known/jwks.json (NOT /jwks.json).

# EU Auth0 SSO config — hosts the client_id the bridge authenticates with
GET https://carelink.minimed.eu/configs/v1/carepartner_auth0_ous_sso_config_v1.json
HTTP 200
[Captures]
eu_host: jsonpath "$.server.hostname"
[Asserts]
jsonpath "$.server.hostname" == "carelink-login.minimed.eu"
jsonpath "$.client.client_secret" == ""
jsonpath "$.client.audience" == "carepartner.patient.ous"
jsonpath "$.client.scope" contains "offline_access"
jsonpath "$.client.redirect_uri" == "com.medtronic.carepartner:/sso"
jsonpath "$.system_endpoints.authorization_endpoint_path" == "/authorize"
jsonpath "$.system_endpoints.token_endpoint_path" == "/oauth/token"
jsonpath "$.system_endpoints.token_revocation_endpoint_path" == "/oauth/revoke"

# US Auth0 SSO config
GET https://carelink.minimed.com/configs/v1/carepartner_auth0_us_sso_config_v1.json
HTTP 200
[Asserts]
jsonpath "$.server.hostname" == "carelink-login.minimed.com"
jsonpath "$.client.audience" == "carepartner.patient.us"
jsonpath "$.system_endpoints.authorization_endpoint_path" == "/authorize"

# OIDC discovery — the bridge reads issuer + endpoints from here indirectly
GET https://carelink-login.minimed.eu/.well-known/openid-configuration
HTTP 200
[Asserts]
jsonpath "$.issuer" == "https://carelink-login.minimed.eu/"
jsonpath "$.grant_types_supported" contains "authorization_code"
jsonpath "$.grant_types_supported" contains "refresh_token"
jsonpath "$.code_challenge_methods_supported" contains "S256"
jsonpath "$.token_endpoint_auth_methods_supported" contains "none"
jsonpath "$.jwks_uri" == "https://carelink-login.minimed.eu/.well-known/jwks.json"
jsonpath "$.authorization_endpoint" == "https://carelink-login.minimed.eu/authorize"
jsonpath "$.token_endpoint" == "https://carelink-login.minimed.eu/oauth/token"

GET https://carelink-login.minimed.eu/.well-known/jwks.json
HTTP 200
[Asserts]
jsonpath "$.keys" count >= 1
jsonpath "$.keys[0].kty" == "RSA"
jsonpath "$.keys[0].alg" == "RS256"

GET https://carelink-login.minimed.com/.well-known/openid-configuration
HTTP 200
[Asserts]
jsonpath "$.issuer" == "https://carelink-login.minimed.com/"
jsonpath "$.code_challenge_methods_supported" contains "S256"

# Clinical / trials tenant — the fifth carelink-login.* issuer, and the one the
# four-way comparison never covered. Added 2026-10-12 (area I, #23); until then
# docs/02 recorded its JWKS kids as "Unknown — not in any source".
# Source: findings-log/2026-10-12-area-i-auth0-tenant-behaviour/FINDINGS.md §2, §3.
#
# Policy parity is NOT asserted here. It is a property of all five documents
# compared together (one digest after the hostname is substituted out), which no
# single-request pin can express. What is pinned is that this tenant does not
# diverge on the fields a client branches on.
#
# A KEY ROTATION HERE IS EXPECTED DRIFT, NOT A DEFECT — re-record the kids from
# the live jwks.json and update docs/02 §1 rather than treating a red suite as
# an outage.
GET https://carelink-login-trials.minimed.com/.well-known/openid-configuration
HTTP 200
[Asserts]
jsonpath "$.issuer" == "https://carelink-login-trials.minimed.com/"
jsonpath "$.authorization_endpoint" == "https://carelink-login-trials.minimed.com/authorize"
jsonpath "$.token_endpoint" == "https://carelink-login-trials.minimed.com/oauth/token"
jsonpath "$.jwks_uri" == "https://carelink-login-trials.minimed.com/.well-known/jwks.json"
jsonpath "$.registration_endpoint" == "https://carelink-login-trials.minimed.com/oidc/register"
jsonpath "$.grant_types_supported" contains "authorization_code"
jsonpath "$.grant_types_supported" contains "refresh_token"
jsonpath "$.code_challenge_methods_supported" contains "S256"
jsonpath "$.code_challenge_methods_supported" contains "plain"
jsonpath "$.token_endpoint_auth_methods_supported" contains "none"
header "Access-Control-Allow-Origin" == "*"
header "Access-Control-Allow-Credentials" == "false"

GET https://carelink-login-trials.minimed.com/.well-known/jwks.json
HTTP 200
[Asserts]
jsonpath "$.keys" count == 2
jsonpath "$.keys[0].kty" == "RSA"
jsonpath "$.keys[0].alg" == "RS256"
jsonpath "$.keys[0].kid" == "kCezLNMQV0tlc3hZinEly"
jsonpath "$.keys[1].kid" == "pNzjt7ruOaWE4rlDCBPoP"

# Advertised Auth0 sibling endpoints by OPTIONS (area J, 2026-10-13, #34).
# Source: findings-log/2026-10-13-area-j-advertised-endpoints/FINDINGS.md §2.
# All three paths are POST-only by specification, so a GET-only probe reads
# every one of them as dead (area I's retracted error); the preflight below
# is what proves routing without invoking the route. EU patient-tenant cells
# pinned as canaries; the full 3-paths-x-5-tenants matrix is in the log.
#
# If any of these goes red, the vendor moved the advertised surface: re-run
# the area-J probe before "fixing" the pin. In particular a 204 on
# /bc-authorize means CIBA was enabled, not that the pin is stale.

# /mfa/challenge answers the preflight on all five tenants (204 + CORS).
# The allow-methods value is pinned EXACT (not contains): it is a broad
# six-method list, unlike /oidc/register's bare POST, and a reordering or
# narrowing is a change this header makes that contains cannot see.
OPTIONS https://carelink-login.minimed.eu/mfa/challenge
Origin: https://example.invalid
Access-Control-Request-Method: POST
Access-Control-Request-Headers: content-type
HTTP 204
[Asserts]
header "access-control-allow-origin" == "*"
header "access-control-allow-methods" == "GET, PUT, POST, DELETE, PATCH, OPTIONS"

# /bc-authorize is advertised but unrouted on all five tenants: the preflight
# gets the front door's unrouted signature, byte-identical to a
# one-character-different control on the same host.
OPTIONS https://carelink-login.minimed.eu/bc-authorize
Origin: https://example.invalid
Access-Control-Request-Method: POST
Access-Control-Request-Headers: content-type
HTTP 404
[Asserts]
header "x-auth0-not-found" == "1"
header "content-type" == "text/plain; charset=utf-8"

# /oauth/global-token-revocation/connection/Auth0 is unrouted for this
# connection name on all five tenants (same unrouted signature). The
# {connectionName} template means another name could route; this pin covers
# only the Auth0 name already recorded in docs/02 and 04-deep-surface.hurl.
OPTIONS https://carelink-login.minimed.eu/oauth/global-token-revocation/connection/Auth0
Origin: https://example.invalid
Access-Control-Request-Method: POST
Access-Control-Request-Headers: content-type
HTTP 404
[Asserts]
header "x-auth0-not-found" == "1"
header "content-type" == "text/plain; charset=utf-8"
