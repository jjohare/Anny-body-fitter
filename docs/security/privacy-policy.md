# Privacy Policy - Anny Body Fitter

**Last Updated**: 2025-11-10
**Effective Date**: 2025-11-10

## Introduction

This Privacy Policy explains how Anny Body Fitter ("we", "our", "the Application") collects, uses, processes, and protects personal information, including photos and physical measurements.

## Information We Collect

### 1. Photos

**What**: User-submitted photographs for body shape analysis
**Purpose**: Generate 3D body models and measurements
**Storage**: Temporary only (automatically deleted after processing)
**Retention**: Maximum 30 minutes, then permanently deleted
**Encryption**: HTTPS/TLS in transit, not stored at rest

### 2. Personal Measurements

**What**: Physical measurements including:
- Height
- Weight
- Body circumferences (chest, waist, hip, etc.)
- Age or Date of Birth

**Purpose**: Generate accurate body shape models
**Storage**: Encrypted in database if user chooses to save
**Retention**: As long as user account is active, or until user requests deletion
**Encryption**: AES-256-GCM field-level encryption

### 3. Technical Information

**What**:
- IP address (for security and rate limiting)
- Browser type and version
- Operating system
- Session identifiers

**Purpose**: Security, performance monitoring, abuse prevention
**Storage**: Logs retained for 30 days
**Retention**: Automatically purged after 30 days

## How We Use Your Information

### Primary Use
1. **Body Shape Analysis**: Process photos to generate 3D body models
2. **Measurement Calculation**: Derive physical measurements from photos
3. **Model Personalization**: Customize body models based on parameters

### Secondary Use
1. **Security**: Detect and prevent abuse, fraud, and malicious use
2. **Performance**: Monitor system performance and optimize processing
3. **Compliance**: Meet legal obligations and respond to lawful requests

## Data Protection Measures

### Photo Security

```
Upload → Validation → Temporary Storage → Processing → Secure Deletion
   ↓          ↓              ↓                ↓              ↓
Size      Magic #      Encrypted RAM      Isolated      Overwrite
Check     Check        Memory Only        Process       + Delete
```

**Protections**:
- ✅ Automatic deletion after 30 minutes maximum
- ✅ No permanent photo storage
- ✅ Secure overwrite deletion (3-pass)
- ✅ Session-based isolation
- ✅ TLS 1.3 encryption in transit
- ✅ File type and size validation
- ✅ Malware scanning

### PII Encryption

**Algorithm**: AES-256-GCM (authenticated encryption)
**Key Management**: Environment-based master key with rotation support
**Fields Encrypted**:
- Date of Birth
- Height measurements
- Weight measurements
- Body circumferences
- Any identifying measurements

**What's NOT Encrypted**:
- Non-PII data (model parameters)
- Anonymized analytics
- System logs (PII redacted)

### Access Controls

1. **Authentication**: Required for all data access
2. **Authorization**: Role-based access control (RBAC)
3. **Rate Limiting**: Prevents abuse and brute force
4. **Audit Logging**: All access logged and monitored
5. **Session Management**: Secure session tokens with expiration

## Your Rights (GDPR)

### Right to Access
Request copy of all personal data we hold about you.
**How**: Contact privacy@example.com
**Timeline**: Within 30 days

### Right to Rectification
Correct inaccurate or incomplete personal data.
**How**: Update through account settings or contact us
**Timeline**: Immediate for user updates

### Right to Erasure ("Right to be Forgotten")
Request deletion of all personal data.
**How**: Account deletion or contact privacy@example.com
**Timeline**: Within 7 days
**Scope**: All data including:
- Photos (already auto-deleted)
- Measurements (permanently deleted from database)
- Logs (PII redacted)
- Backups (included in deletion)

### Right to Data Portability
Receive personal data in machine-readable format.
**How**: Download from account settings
**Format**: JSON or CSV
**Timeline**: Immediate

### Right to Object
Object to processing of personal data.
**How**: Contact privacy@example.com
**Effect**: Processing stopped immediately

### Right to Restrict Processing
Restrict how we process your data.
**How**: Contact privacy@example.com
**Options**: Temporary restriction or limitation

## Data Retention

| Data Type | Retention Period | Reason |
|-----------|------------------|--------|
| Photos | 30 minutes max | Processing only, no storage |
| Measurements (saved) | Until account deletion | User-requested storage |
| Measurements (unsaved) | Session only | Not persisted |
| Logs (with PII) | 0 days | PII immediately redacted |
| Logs (anonymized) | 30 days | Security and performance |
| Session data | 24 hours | Active sessions only |
| Deleted account data | 0 days | Immediate permanent deletion |

## Children's Privacy

**Age Requirement**: This application can process data for all ages, including children.

**Parental Consent**: For users under 16 (or local age of consent):
- Parental/guardian consent required
- Consent must be verifiable
- Parents can request data deletion at any time

**Special Protections**:
- Enhanced privacy protections for minors
- Limited data collection
- No marketing or profiling

## International Data Transfers

**Primary Jurisdiction**: European Union (GDPR compliant)
**Transfers**: Data may be processed in:
- EU/EEA countries
- Countries with adequacy decisions
- US companies under EU-US Data Privacy Framework

**Safeguards**:
- Standard Contractual Clauses (SCCs)
- Binding Corporate Rules (BCRs)
- Encryption in transit and at rest

## Cookies and Tracking

**Essential Cookies**: Session management (strictly necessary)
**Analytics Cookies**: Performance monitoring (optional, with consent)
**Marketing Cookies**: None - we don't use marketing cookies

**Your Control**:
- Reject non-essential cookies
- Cookie banner on first visit
- Change preferences anytime

## Data Breach Notification

**Commitment**: We will notify you within 72 hours of discovering a data breach that affects your personal data.

**Notification Includes**:
- Nature of the breach
- Data affected
- Potential consequences
- Mitigation measures taken
- Contact information for questions

**Our Response**:
1. Immediate containment
2. Investigation and assessment
3. Notification to affected users
4. Report to supervisory authority (if required)
5. Remediation and prevention measures

## Third-Party Services

**We Do NOT Share Photos With Third Parties**

**Limited Third-Party Services**:
- Cloud hosting (encrypted storage)
- Payment processing (if applicable)
- Analytics (anonymized only)

**Safeguards**:
- Data Processing Agreements with all vendors
- GDPR-compliant processors only
- Regular security audits

## Security Measures

### Technical Measures
- ✅ TLS 1.3 encryption
- ✅ AES-256 data encryption
- ✅ Secure password hashing (Argon2)
- ✅ Regular security updates
- ✅ Intrusion detection
- ✅ Malware scanning
- ✅ Security monitoring 24/7

### Organizational Measures
- ✅ Security training for all staff
- ✅ Access control policies
- ✅ Incident response plan
- ✅ Regular security audits
- ✅ Data Protection Officer (DPO)
- ✅ Privacy by design principles

## Changes to This Policy

**Notification**: We will notify you of material changes via:
- Email (if you have an account)
- Prominent notice in the application
- Updated "Last Modified" date

**Your Options**:
- Continue using the service (acceptance)
- Request data deletion and discontinue use

## Contact Information

**Data Protection Officer**: privacy@example.com
**General Inquiries**: support@example.com
**Security Issues**: security@example.com

**Mail**:
Anny Body Fitter - Privacy Department
[Address]
[City, Country]

**Supervisory Authority** (EU):
[Your national data protection authority]

## Legal Basis for Processing (GDPR)

1. **Consent**: For photo processing and optional data storage
2. **Contract**: To provide the body modeling service
3. **Legal Obligation**: To comply with laws (e.g., age verification)
4. **Legitimate Interest**: Security, fraud prevention, service improvement

## California Privacy Rights (CCPA)

California residents have additional rights:
- Right to know what personal information is collected
- Right to deletion
- Right to opt-out of sale (we don't sell data)
- Right to non-discrimination

## Transparency Report

We publish annual transparency reports including:
- Number of user data requests
- Government/law enforcement requests
- Data breaches (if any)
- Security improvements

## Accountability

**Data Protection Impact Assessment**: Conducted annually
**Compliance Audits**: Third-party audits every 12 months
**Staff Training**: Quarterly privacy and security training
**Documentation**: All processing activities documented

---

**Summary**: We take your privacy seriously. Photos are never stored permanently, personal measurements are encrypted, and you have full control over your data. We comply with GDPR, CCPA, and other privacy regulations.

For questions or to exercise your rights, contact: **privacy@example.com**
