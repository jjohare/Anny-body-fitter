# Threat Model - Anny Body Fitter

**Version**: 1.0
**Date**: 2025-11-10
**Classification**: Internal Security Documentation

## Executive Summary

This document outlines potential security threats to the Anny Body Fitter application and corresponding mitigation strategies. The application processes sensitive personal data (photos and physical measurements), requiring robust security controls.

**Risk Level**: HIGH (handles PII and photos)
**Compliance Requirements**: GDPR, CCPA, HIPAA (if medical use)

## System Architecture

```
User Device
    ↓ (HTTPS)
Load Balancer
    ↓
Application Server
    ├── Photo Processing Module
    ├── Body Model Generator
    ├── Measurement Calculator
    └── API Gateway
    ↓
Database (Encrypted)
Temporary Storage (Auto-Delete)
```

## Assets

### Critical Assets
1. **User Photos**: Highly sensitive, potential privacy breach
2. **Personal Measurements**: PII requiring encryption
3. **User Accounts**: Authentication credentials
4. **Encryption Keys**: Master keys for data encryption
5. **Application Code**: Intellectual property, potential vulnerabilities

### Asset Classification
- **Confidential**: Photos, measurements, DOB
- **Restricted**: User credentials, session tokens
- **Internal**: Application logs, analytics
- **Public**: Documentation, marketing materials

## Threat Actors

### 1. External Attackers
**Motivation**: Financial gain, identity theft, blackmail
**Capabilities**: Moderate to advanced technical skills
**Likelihood**: MEDIUM
**Impact**: HIGH

### 2. Malicious Users
**Motivation**: Abuse service, extract data, DoS
**Capabilities**: Basic to moderate technical skills
**Likelihood**: HIGH
**Impact**: MEDIUM

### 3. Insider Threats
**Motivation**: Financial gain, revenge, curiosity
**Capabilities**: High (legitimate access)
**Likelihood**: LOW
**Impact**: HIGH

### 4. Automated Bots
**Motivation**: Scraping, spam, resource exhaustion
**Capabilities**: Automated scripts
**Likelihood**: HIGH
**Impact**: MEDIUM

### 5. Nation-State Actors
**Motivation**: Surveillance, espionage
**Capabilities**: Very high technical skills
**Likelihood**: VERY LOW
**Impact**: CRITICAL

## Threat Scenarios

### T1: Malicious Photo Upload

**Description**: Attacker uploads malware disguised as image file
**Attack Vector**: File upload endpoint
**Likelihood**: HIGH
**Impact**: CRITICAL (code execution, data breach)

**Attack Chain**:
1. Craft malicious file with image extension
2. Bypass file type validation
3. Exploit image processing vulnerability
4. Execute arbitrary code on server
5. Exfiltrate data or install backdoor

**Mitigations**:
- ✅ Magic number validation (file signature checking)
- ✅ File size limits (10MB maximum)
- ✅ Image content validation with PIL
- ✅ Sandboxed processing environment
- ✅ Malware signature scanning
- ✅ Disable script execution in upload directory
- ⚠️ TODO: Integrate antivirus scanning API

**Residual Risk**: LOW

---

### T2: Photo Data Exfiltration

**Description**: Attacker gains access to stored photos
**Attack Vector**: Database breach, backup theft, insider access
**Likelihood**: MEDIUM
**Impact**: CRITICAL (privacy breach, GDPR violation)

**Attack Chain**:
1. Exploit application vulnerability (SQL injection)
2. Gain database access
3. Extract photo files or file paths
4. Download and distribute photos

**Mitigations**:
- ✅ No permanent photo storage (30-minute TTL)
- ✅ Automatic secure deletion (overwrite + delete)
- ✅ Session-based file isolation
- ✅ No photos in database (paths only)
- ✅ Encrypted file system (optional)
- ✅ Access logging and monitoring
- ⚠️ TODO: Implement database encryption at rest

**Residual Risk**: VERY LOW (photos not permanently stored)

---

### T3: PII Data Breach

**Description**: Unauthorized access to encrypted personal measurements
**Attack Vector**: Database compromise, encryption key theft
**Likelihood**: MEDIUM
**Impact**: HIGH (GDPR violation, identity theft)

**Attack Chain**:
1. Exploit SQL injection or application vulnerability
2. Extract encrypted data from database
3. Attempt to steal encryption keys
4. Decrypt sensitive fields
5. Exfiltrate PII data

**Mitigations**:
- ✅ Field-level encryption (AES-256-GCM)
- ✅ Separate key storage (environment variables)
- ✅ Parameterized queries (SQL injection prevention)
- ✅ Input validation and sanitization
- ✅ Access control and authentication
- ✅ Key rotation capability
- ⚠️ TODO: Implement Hardware Security Module (HSM) for keys
- ⚠️ TODO: Add database activity monitoring

**Residual Risk**: LOW

---

### T4: Man-in-the-Middle (MitM) Attack

**Description**: Attacker intercepts photo upload in transit
**Attack Vector**: Network interception, certificate compromise
**Likelihood**: LOW (with HTTPS)
**Impact**: CRITICAL (photo interception)

**Attack Chain**:
1. Position on network path
2. Intercept HTTPS connection
3. Perform SSL stripping or certificate substitution
4. Capture photos in plaintext
5. Forward to destination to avoid detection

**Mitigations**:
- ✅ TLS 1.3 mandatory
- ✅ HSTS (HTTP Strict Transport Security)
- ✅ Certificate pinning (mobile apps)
- ✅ Strong cipher suites only
- ✅ Regular certificate rotation
- ⚠️ TODO: Implement Certificate Transparency monitoring

**Residual Risk**: VERY LOW

---

### T5: Injection Attacks (SQL, XSS, Command)

**Description**: Attacker injects malicious code via input fields
**Attack Vector**: User input forms, API parameters
**Likelihood**: HIGH
**Impact**: HIGH (data breach, account takeover)

**Attack Types**:
- SQL Injection: Extract or modify database data
- XSS (Cross-Site Scripting): Steal session tokens
- Command Injection: Execute system commands
- LDAP Injection: Bypass authentication

**Mitigations**:
- ✅ Input validation for all fields
- ✅ Parameterized queries (SQL injection prevention)
- ✅ HTML escaping (XSS prevention)
- ✅ Content Security Policy (CSP)
- ✅ Output encoding
- ✅ Whitelist validation
- ⚠️ TODO: Implement Web Application Firewall (WAF)

**Residual Risk**: LOW

---

### T6: Denial of Service (DoS)

**Description**: Attacker overwhelms system with requests
**Attack Vector**: API endpoints, photo upload
**Likelihood**: MEDIUM
**Impact**: MEDIUM (service unavailability)

**Attack Types**:
- Volume-based: Massive traffic flood
- Protocol-based: SYN flood, ping flood
- Application-layer: Slow uploads, complex requests
- Decompression bomb: Malicious image files

**Mitigations**:
- ✅ Rate limiting per IP/session
- ✅ File size limits
- ✅ Request timeout limits
- ✅ Image decompression bomb protection (PIL)
- ✅ Load balancing
- ⚠️ TODO: Implement DDoS protection service
- ⚠️ TODO: Add CAPTCHA for suspicious activity

**Residual Risk**: MEDIUM

---

### T7: Authentication Bypass

**Description**: Attacker gains unauthorized access to accounts
**Attack Vector**: Weak passwords, session hijacking, credential stuffing
**Likelihood**: MEDIUM
**Impact**: HIGH (account takeover, data access)

**Attack Chain**:
1. Obtain credentials (phishing, breach, brute force)
2. Attempt login with stolen credentials
3. Bypass MFA (if weak implementation)
4. Access user data and photos

**Mitigations**:
- ⚠️ TODO: Implement authentication system
- ⚠️ TODO: Require strong passwords (min 12 chars)
- ⚠️ TODO: Multi-factor authentication (MFA)
- ⚠️ TODO: Account lockout after failed attempts
- ⚠️ TODO: Session timeout and rotation
- ⚠️ TODO: Password breach checking
- ⚠️ TODO: OAuth2/OpenID Connect support

**Residual Risk**: MEDIUM (not yet implemented)

---

### T8: Privilege Escalation

**Description**: User gains admin access or accesses other users' data
**Attack Vector**: Authorization flaws, API vulnerabilities
**Likelihood**: LOW
**Impact**: CRITICAL (full system compromise)

**Attack Chain**:
1. Identify authorization weakness
2. Manipulate user ID or session parameters
3. Access admin functions or other users' data
4. Modify system configuration or steal data

**Mitigations**:
- ⚠️ TODO: Implement RBAC (Role-Based Access Control)
- ⚠️ TODO: Validate user permissions on every request
- ⚠️ TODO: Separate admin and user interfaces
- ⚠️ TODO: Audit all privileged operations
- ⚠️ TODO: Principle of least privilege

**Residual Risk**: MEDIUM (not yet implemented)

---

### T9: Data Retention Violation

**Description**: Photos or PII retained longer than stated policy
**Attack Vector**: Backup systems, failed deletion, logs
**Likelihood**: MEDIUM
**Impact**: HIGH (GDPR violation, trust breach)

**Scenarios**:
- Photos not deleted after 30 minutes
- PII in backup systems after account deletion
- Personal data in log files
- Cached data not cleared

**Mitigations**:
- ✅ Automatic photo deletion (30-minute TTL)
- ✅ Secure overwrite deletion
- ✅ Background cleanup task
- ⚠️ TODO: Backup data anonymization
- ⚠️ TODO: Log sanitization (PII redaction)
- ⚠️ TODO: Data retention monitoring
- ⚠️ TODO: Compliance audit trail

**Residual Risk**: MEDIUM

---

### T10: Supply Chain Attack

**Description**: Malicious code in dependencies or build tools
**Attack Vector**: Compromised npm packages, Docker images
**Likelihood**: LOW
**Impact**: CRITICAL (backdoor, data theft)

**Attack Chain**:
1. Attacker compromises popular package
2. Malicious code injected into dependency
3. Application builds with compromised package
4. Backdoor deployed to production
5. Data exfiltration or system compromise

**Mitigations**:
- ⚠️ TODO: Dependency vulnerability scanning
- ⚠️ TODO: Software composition analysis (SCA)
- ⚠️ TODO: Package signature verification
- ⚠️ TODO: Private package registry
- ⚠️ TODO: Automated security updates
- ⚠️ TODO: Container image scanning

**Residual Risk**: MEDIUM

---

## Risk Matrix

| Threat | Likelihood | Impact | Current Risk | Residual Risk |
|--------|-----------|--------|--------------|---------------|
| T1: Malicious Upload | HIGH | CRITICAL | HIGH | LOW |
| T2: Photo Exfiltration | MEDIUM | CRITICAL | MEDIUM | VERY LOW |
| T3: PII Breach | MEDIUM | HIGH | MEDIUM | LOW |
| T4: MitM Attack | LOW | CRITICAL | LOW | VERY LOW |
| T5: Injection Attacks | HIGH | HIGH | HIGH | LOW |
| T6: DoS | MEDIUM | MEDIUM | MEDIUM | MEDIUM |
| T7: Auth Bypass | MEDIUM | HIGH | HIGH | MEDIUM |
| T8: Privilege Escalation | LOW | CRITICAL | MEDIUM | MEDIUM |
| T9: Retention Violation | MEDIUM | HIGH | MEDIUM | MEDIUM |
| T10: Supply Chain | LOW | CRITICAL | MEDIUM | MEDIUM |

**Risk Levels**:
- VERY LOW: Acceptable
- LOW: Monitor
- MEDIUM: Remediate in next release
- HIGH: Remediate urgently
- CRITICAL: Immediate action required

## Security Controls Summary

### Implemented ✅
1. Photo auto-deletion (30-minute TTL)
2. Secure file deletion (overwrite)
3. Field-level encryption (AES-256-GCM)
4. Input validation and sanitization
5. File upload validation (magic numbers)
6. Size limits and malware detection
7. Session-based file isolation

### In Progress ⚠️
1. Database encryption at rest
2. API authentication and authorization
3. Rate limiting
4. Audit logging

### Planned 📋
1. WAF (Web Application Firewall)
2. DDoS protection
3. HSM for key management
4. MFA (Multi-Factor Authentication)
5. Dependency scanning
6. Container security

## Monitoring and Detection

### Security Events to Monitor
- Failed authentication attempts (threshold: 5/hour)
- Large file uploads (>5MB)
- Unusual API request patterns
- Database access anomalies
- Photo deletion failures
- Encryption errors

### Alerting Thresholds
- **Critical**: Immediate notification (SMS + email)
- **High**: Notification within 15 minutes
- **Medium**: Daily digest
- **Low**: Weekly report

### Incident Response

**Phase 1: Detection** (0-1 hour)
- Automated alerts trigger
- Security team notified
- Initial triage

**Phase 2: Containment** (1-4 hours)
- Isolate affected systems
- Block attacker access
- Preserve evidence

**Phase 3: Investigation** (4-24 hours)
- Analyze logs and forensics
- Determine scope and impact
- Identify root cause

**Phase 4: Recovery** (24-72 hours)
- Restore services
- Apply patches
- Verify security

**Phase 5: Lessons Learned** (1 week)
- Post-incident review
- Update threat model
- Improve controls

## Compliance Mapping

### GDPR Requirements
| Requirement | Control | Status |
|-------------|---------|--------|
| Data minimization | No permanent photo storage | ✅ Implemented |
| Encryption | AES-256 field encryption | ✅ Implemented |
| Right to erasure | Secure deletion mechanism | ✅ Implemented |
| Breach notification | 72-hour notification process | ⚠️ Planned |
| DPO | Data Protection Officer assigned | ⚠️ Required |

### CCPA Requirements
| Requirement | Control | Status |
|-------------|---------|--------|
| Right to know | Data export functionality | ⚠️ Planned |
| Right to delete | Account deletion + data purge | ⚠️ Planned |
| Do not sell | No data sales (N/A) | ✅ N/A |

## Penetration Testing

**Frequency**: Annually + after major changes
**Scope**: All application components
**Methods**:
- Automated vulnerability scanning
- Manual penetration testing
- Social engineering testing
- Red team exercises

**Last Test**: Not yet conducted
**Next Test**: Before production launch

---

**Approved By**: Security Team
**Next Review**: 2025-12-10 (or after significant changes)
