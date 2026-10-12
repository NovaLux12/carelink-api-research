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
