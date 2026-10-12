GET https://carelink-login-trials.minimed.com/.well-known/jwks.json
HTTP 200
[Asserts]
jsonpath "$.keys" count == 2
jsonpath "$.keys[0].kty" == "RSA"
jsonpath "$.keys[0].alg" == "RS256"
jsonpath "$.keys[0].kid" == "kCezLNMQV0tlc3hZinEly"
jsonpath "$.keys[1].kid" == "pNzjt7ruOaWE4rlDCBPoP"
