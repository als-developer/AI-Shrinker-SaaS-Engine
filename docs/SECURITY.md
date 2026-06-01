# Security Architecture

## Overview
Sovereign Grid implements defense-in-depth security with multiple layers.

## Encryption
- Data at rest: AES-256
- Data in transit: TLS 1.3
- API keys: SHA-256 hashed storage

## Authentication
- JWT tokens for sessions
- API keys for programmatic access
- 2FA support for user accounts

## Compliance
- GDPR compliant
- HIPAA ready
- PCI-DSS Level 1

## Security Controls
| Control | Implementation |
|---------|----------------|
| Input validation | Regex patterns + whitelist |
| Rate limiting | Sliding window in Redis |
| SQL injection | Parameterized queries |
| XSS protection | Output encoding |
| CSRF | Tokens + SameSite cookies |

## Auditing
- All API calls logged
- Security events monitored
- Weekly vulnerability scans
