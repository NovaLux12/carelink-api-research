* Host commoncore.medtronic.eu:443 was resolved.
* IPv6: (none)
* IPv4: 3.166.49.62, 3.166.49.88, 3.166.49.27, 3.166.49.57
*   Trying 3.166.49.62:443...
* ALPN: curl offers h2,http/1.1
} [5 bytes data]
* TLSv1.3 (OUT), TLS handshake, Client hello (1):
} [1567 bytes data]
* SSL Trust Anchors:
*   OpenSSL default paths (fallback)
{ [5 bytes data]
* TLSv1.3 (IN), TLS handshake, Server hello (2):
{ [1210 bytes data]
* TLSv1.3 (IN), TLS change cipher, Change cipher spec (1):
{ [1 bytes data]
* TLSv1.3 (IN), TLS handshake, Encrypted Extensions (8):
{ [19 bytes data]
* TLSv1.3 (IN), TLS handshake, Certificate (11):
{ [3023 bytes data]
* TLSv1.3 (IN), TLS handshake, CERT verify (15):
{ [264 bytes data]
* TLSv1.3 (IN), TLS handshake, Finished (20):
{ [36 bytes data]
* TLSv1.3 (OUT), TLS change cipher, Change cipher spec (1):
} [1 bytes data]
* TLSv1.3 (OUT), TLS handshake, Finished (20):
} [36 bytes data]
* SSL connection using TLSv1.3 / TLS_AES_128_GCM_SHA256 / X25519MLKEM768 / RSASSA-PSS
* ALPN: server accepted h2
* Server certificate:
*   subject: C=US; ST=Minnesota; L=Minneapolis; O="Medtronic, Inc."; CN=commoncore.medtronic.eu
*   start date: Sep 17 00:00:00 2026 GMT
*   expire date: Apr  3 23:59:59 2027 GMT
*   issuer: C=US; O=DigiCert Inc; CN=DigiCert Global G2 TLS RSA SHA256 2020 CA1
*   Certificate level 0: Public key type RSA (2048/112 Bits/secBits), signed using sha256WithRSAEncryption
*   Certificate level 1: Public key type RSA (2048/112 Bits/secBits), signed using sha256WithRSAEncryption
*   Certificate level 2: Public key type RSA (2048/112 Bits/secBits), signed using sha256WithRSAEncryption
*   subjectAltName: "commoncore.medtronic.eu" matches cert's "commoncore.medtronic.eu"
* OpenSSL verify result: 0
* SSL certificate verified via OpenSSL.
* Established connection to commoncore.medtronic.eu (3.166.49.62 port 443) from 192.168.8.133 port 51860 
* using HTTP/2
* [HTTP/2] [1] OPENED stream for https://commoncore.medtronic.eu/reports-broker/v1/ocl
* [HTTP/2] [1] [:method: GET]
* [HTTP/2] [1] [:scheme: https]
* [HTTP/2] [1] [:authority: commoncore.medtronic.eu]
* [HTTP/2] [1] [:path: /reports-broker/v1/ocl]
* [HTTP/2] [1] [user-agent: carelink-bridge-research/1.0]
* [HTTP/2] [1] [accept: */*]
* [HTTP/2] [1] [accept-encoding: deflate, gzip, br, zstd]
} [5 bytes data]
> GET /reports-broker/v1/ocl HTTP/2
> Host: commoncore.medtronic.eu
> User-Agent: carelink-bridge-research/1.0
> Accept: */*
> Accept-Encoding: deflate, gzip, br, zstd
> 
* Request completely sent off
} [5 bytes data]
* TLSv1.3 (IN), TLS handshake, Newsession Ticket (4):
{ [157 bytes data]
< HTTP/2 403 
< content-type: application/json
< content-length: 50
< x-amz-cf-pop: LHR82-P3
< date: Tue, 13 Oct 2026 15:21:44 GMT
< access-control-allow-methods: *
< x-amzn-requestid: 87106a15-afb9-4264-ada0-991a74908759
< access-control-allow-origin: *
< content-encoding: deflate
< access-control-allow-headers: *
< x-amzn-errortype: MissingAuthenticationTokenException
< x-amz-apigw-id: FMDleGllliAERpA=
< via: 1.1 38d2b97ac5fa9ac665b489b38ed0df34.cloudfront.net (CloudFront), 1.1 8416dbe5351bb3aac6683bc3f66e8f70.cloudfront.net (CloudFront)
< x-cache: Error from cloudfront
< x-amz-cf-pop: LHR3-P1
< x-amz-cf-id: QSr51juoeK3ZSJH65V8kinyFiJjOgA9S8a8JoK84Vg5P1zT-ttB5NQ==
< 
{ [50 bytes data]
* Connection #0 to host commoncore.medtronic.eu:443 left intact
