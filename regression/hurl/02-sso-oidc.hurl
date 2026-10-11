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
