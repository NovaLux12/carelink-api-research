*   Trying 13.33.153.120:443...
* ALPN: curl offers h2,http/1.1
} [5 bytes data]
* TLSv1.3 (OUT), TLS handshake, Client hello (1):
} [1573 bytes data]
* SSL Trust Anchors:
*   OpenSSL default paths (fallback)
* Host commoncore-trials.minimed.com:443 was resolved.
* IPv6: (none)
* IPv4: 13.33.153.120, 13.33.153.57, 13.33.153.59, 13.33.153.46
{ [5 bytes data]
* TLSv1.3 (IN), TLS handshake, Server hello (2):
{ [1210 bytes data]
* TLSv1.3 (IN), TLS change cipher, Change cipher spec (1):
{ [1 bytes data]
* TLSv1.3 (IN), TLS handshake, Encrypted Extensions (8):
{ [19 bytes data]
* TLSv1.3 (IN), TLS handshake, Certificate (11):
{ [3020 bytes data]
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
*   subject: C=US; ST=Minnesota; L=Minneapolis; O="Medtronic, Inc."; CN=commoncore-trials.minimed.com
*   start date: Jul  9 00:00:00 2026 GMT
*   expire date: Jan 23 23:59:59 2027 GMT
*   issuer: C=US; O=DigiCert Inc; CN=DigiCert Global G2 TLS RSA SHA256 2020 CA1
*   Certificate level 0: Public key type RSA (2048/112 Bits/secBits), signed using sha256WithRSAEncryption
*   Certificate level 1: Public key type RSA (2048/112 Bits/secBits), signed using sha256WithRSAEncryption
*   Certificate level 2: Public key type RSA (2048/112 Bits/secBits), signed using sha256WithRSAEncryption
*   subjectAltName: "commoncore-trials.minimed.com" matches cert's "commoncore-trials.minimed.com"
* OpenSSL verify result: 0
* SSL certificate verified via OpenSSL.
* Established connection to commoncore-trials.minimed.com (13.33.153.120 port 443) from 192.168.8.133 port 36718 
* using HTTP/2
* [HTTP/2] [1] OPENED stream for https://commoncore-trials.minimed.com/reports-broker/v1/ocl
* [HTTP/2] [1] [:method: GET]
* [HTTP/2] [1] [:scheme: https]
* [HTTP/2] [1] [:authority: commoncore-trials.minimed.com]
* [HTTP/2] [1] [:path: /reports-broker/v1/ocl]
* [HTTP/2] [1] [user-agent: carelink-bridge-research/1.0]
* [HTTP/2] [1] [accept: */*]
* [HTTP/2] [1] [accept-encoding: deflate, gzip, br, zstd]
} [5 bytes data]
> GET /reports-broker/v1/ocl HTTP/2
> Host: commoncore-trials.minimed.com
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
< date: Tue, 13 Oct 2026 15:21:31 GMT
< access-control-allow-methods: *
< x-amzn-requestid: d71b5887-a678-4483-ad1c-0956924a5d5d
< access-control-allow-origin: *
< content-encoding: deflate
< access-control-allow-headers: *
< x-amzn-errortype: MissingAuthenticationTokenException
< x-amz-apigw-id: FMDjUGe8oAMED_Q=
< via: 1.1 a655fb0e17f8cdf2bbca8c04e0feb440.cloudfront.net (CloudFront), 1.1 be993ff6709a842c113f017007d31760.cloudfront.net (CloudFront)
< x-cache: Error from cloudfront
< x-amz-cf-pop: LHR3-P4
< x-amz-cf-id: 3apofFS_P1uV6dZjazRnwqhOJAY7Fmw8xv3XO5GzAQWL429xjHbxzg==
< 
{ [50 bytes data]
* Connection #0 to host commoncore-trials.minimed.com:443 left intact
