* Host commoncore-trials.medtronic.com:443 was resolved.
* IPv6: (none)
* IPv4: 3.166.65.64, 3.166.65.5, 3.166.65.18, 3.166.65.129
*   Trying 3.166.65.64:443...
* ALPN: curl offers h2,http/1.1
} [5 bytes data]
* TLSv1.3 (OUT), TLS handshake, Client hello (1):
} [1575 bytes data]
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
{ [3027 bytes data]
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
*   subject: C=US; ST=Minnesota; L=Minneapolis; O="Medtronic, Inc."; CN=commoncore-trials.medtronic.com
*   start date: Jul  9 00:00:00 2026 GMT
*   expire date: Jan 23 23:59:59 2027 GMT
*   issuer: C=US; O=DigiCert Inc; CN=DigiCert Global G2 TLS RSA SHA256 2020 CA1
*   Certificate level 0: Public key type RSA (2048/112 Bits/secBits), signed using sha256WithRSAEncryption
*   Certificate level 1: Public key type RSA (2048/112 Bits/secBits), signed using sha256WithRSAEncryption
*   Certificate level 2: Public key type RSA (2048/112 Bits/secBits), signed using sha256WithRSAEncryption
*   subjectAltName: "commoncore-trials.medtronic.com" matches cert's "commoncore-trials.medtronic.com"
* OpenSSL verify result: 0
* SSL certificate verified via OpenSSL.
* Established connection to commoncore-trials.medtronic.com (3.166.65.64 port 443) from 192.168.8.133 port 34466 
* using HTTP/2
* [HTTP/2] [1] OPENED stream for https://commoncore-trials.medtronic.com/reports-broker/v1/ocl-probe-absent
* [HTTP/2] [1] [:method: GET]
* [HTTP/2] [1] [:scheme: https]
* [HTTP/2] [1] [:authority: commoncore-trials.medtronic.com]
* [HTTP/2] [1] [:path: /reports-broker/v1/ocl-probe-absent]
* [HTTP/2] [1] [user-agent: carelink-bridge-research/1.0]
* [HTTP/2] [1] [accept: */*]
* [HTTP/2] [1] [accept-encoding: deflate, gzip, br, zstd]
} [5 bytes data]
> GET /reports-broker/v1/ocl-probe-absent HTTP/2
> Host: commoncore-trials.medtronic.com
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
< x-amz-cf-pop: LHR86-P3
< date: Tue, 13 Oct 2026 15:21:47 GMT
< access-control-allow-methods: *
< x-amzn-requestid: 55753088-ca39-441d-b5c5-87fdb515e825
< access-control-allow-origin: *
< content-encoding: deflate
< access-control-allow-headers: *
< x-amzn-errortype: MissingAuthenticationTokenException
< x-amz-apigw-id: FMDl5FBKoAMEbAQ=
< via: 1.1 ef666dcc5bd113c8a03a61d7dfc173c4.cloudfront.net (CloudFront), 1.1 2d3636034ab1a12d1ff5b7c6de114156.cloudfront.net (CloudFront)
< x-cache: Error from cloudfront
< x-amz-cf-pop: LHR3-P2
< x-amz-cf-id: eHNfhn4dqGQ2vGujbUJwGe1aX6sufnMltTlffPUT4TAmqm0qpEkaFw==
< 
{ [50 bytes data]
* Connection #0 to host commoncore-trials.medtronic.com:443 left intact
