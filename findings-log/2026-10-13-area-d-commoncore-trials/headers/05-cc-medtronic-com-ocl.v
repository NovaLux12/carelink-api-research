* Host commoncore.medtronic.com:443 was resolved.
* IPv6: (none)
* IPv4: 54.230.201.102, 54.230.201.93, 54.230.201.26, 54.230.201.45
*   Trying 54.230.201.102:443...
* ALPN: curl offers h2,http/1.1
} [5 bytes data]
* TLSv1.3 (OUT), TLS handshake, Client hello (1):
} [1568 bytes data]
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
*   subject: C=US; ST=Minnesota; L=Minneapolis; O="Medtronic, Inc."; CN=commoncore.medtronic.com
*   start date: Sep 17 00:00:00 2026 GMT
*   expire date: Apr  3 23:59:59 2027 GMT
*   issuer: C=US; O=DigiCert Inc; CN=DigiCert Global G2 TLS RSA SHA256 2020 CA1
*   Certificate level 0: Public key type RSA (2048/112 Bits/secBits), signed using sha256WithRSAEncryption
*   Certificate level 1: Public key type RSA (2048/112 Bits/secBits), signed using sha256WithRSAEncryption
*   Certificate level 2: Public key type RSA (2048/112 Bits/secBits), signed using sha256WithRSAEncryption
*   subjectAltName: "commoncore.medtronic.com" matches cert's "commoncore.medtronic.com"
* OpenSSL verify result: 0
* SSL certificate verified via OpenSSL.
* Established connection to commoncore.medtronic.com (54.230.201.102 port 443) from 192.168.8.133 port 38920 
* using HTTP/2
* [HTTP/2] [1] OPENED stream for https://commoncore.medtronic.com/reports-broker/v1/ocl
* [HTTP/2] [1] [:method: GET]
* [HTTP/2] [1] [:scheme: https]
* [HTTP/2] [1] [:authority: commoncore.medtronic.com]
* [HTTP/2] [1] [:path: /reports-broker/v1/ocl]
* [HTTP/2] [1] [user-agent: carelink-bridge-research/1.0]
* [HTTP/2] [1] [accept: */*]
* [HTTP/2] [1] [accept-encoding: deflate, gzip, br, zstd]
} [5 bytes data]
> GET /reports-broker/v1/ocl HTTP/2
> Host: commoncore.medtronic.com
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
< x-amz-cf-pop: LHR61-P3
< date: Tue, 13 Oct 2026 15:21:39 GMT
< access-control-allow-methods: *
< x-amzn-requestid: 2c75b4ba-17e0-484e-8668-3a81e7839ab2
< access-control-allow-origin: *
< content-encoding: deflate
< access-control-allow-headers: *
< x-amzn-errortype: MissingAuthenticationTokenException
< x-amz-apigw-id: FMDknH3SoAMEmuA=
< via: 1.1 93c05674a873410f17afbb33f0b6fa7c.cloudfront.net (CloudFront), 1.1 1def70c22be61dda839a9d3977f9f5bc.cloudfront.net (CloudFront)
< x-cache: Error from cloudfront
< x-amz-cf-pop: LHR82-P3
< x-amz-cf-id: 1WpbA8b7uUzF9z5tXMcrBHt9LKy8pXGg7LDEfxPlLPa98IfjYTAiBw==
< 
{ [50 bytes data]
* Connection #0 to host commoncore.medtronic.com:443 left intact
