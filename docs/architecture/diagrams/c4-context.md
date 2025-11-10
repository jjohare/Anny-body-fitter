# C4 Model: Context Diagram

## System Context - Photo-to-3D-Model Fitting Application

```mermaid
C4Context
    title System Context Diagram - Photo-to-3D Model Fitting

    Person(user, "End User", "Person wanting 3D body model")
    Person(researcher, "Researcher", "Uses system for anthropometry studies")
    Person(designer, "Fashion Designer", "Creates custom garments")

    System(anny_fitter, "Anny Body Fitter", "Converts photos to 3D body models using Anny parametric model")

    System_Ext(mediapipe, "Google MediaPipe", "Pose and landmark detection API")
    System_Ext(email, "Email Service", "SendGrid/AWS SES for notifications")
    System_Ext(auth, "OAuth Provider", "Google/GitHub authentication")
    System_Ext(storage, "Cloud Storage", "AWS S3/GCS for exports")

    Rel(user, anny_fitter, "Uploads photos, views 3D model", "HTTPS")
    Rel(researcher, anny_fitter, "Batch processes subjects, exports data", "HTTPS/API")
    Rel(designer, anny_fitter, "Exports 3D models for CAD", "HTTPS")

    Rel(anny_fitter, mediapipe, "Detects pose/landmarks", "HTTPS/gRPC")
    Rel(anny_fitter, email, "Sends processing notifications", "SMTP/API")
    Rel(anny_fitter, auth, "Authenticates users", "OAuth 2.0")
    Rel(anny_fitter, storage, "Stores exported models", "S3 API")
```

## Key Relationships

### Users → System
- **End User**: Casual user wanting personal 3D avatar
- **Researcher**: Batch processing for anthropometry studies
- **Fashion Designer**: Export models for garment fitting

### System → External Services
- **MediaPipe**: Real-time pose estimation (33 body + 68 face + 21 hand landmarks)
- **Email Service**: Async notification when processing completes
- **OAuth Provider**: Social login (Google, GitHub)
- **Cloud Storage**: Long-term storage of exported models (OBJ, GLTF)

## Trust Boundaries

1. **Public Internet** → **API Gateway** (HTTPS, rate limiting)
2. **API Gateway** → **Backend Services** (internal network, mTLS)
3. **Backend** → **Database** (encrypted connection, row-level security)
4. **Backend** → **External APIs** (API keys, secrets management)

## Data Flows (High-Level)

```
User Photo → Upload (HTTPS) → RAM-Only Storage → Vision Processing →
Measurements → Model Fitting → 3D Model → Database (params only) →
Photo Deleted → 3D Viewer (WebGL)
```

**Critical Privacy Flow**: Photos never leave RAM, deleted <5 minutes

## System Boundaries

**Inside System**:
- Web frontend (React + Three.js)
- API server (FastAPI)
- Vision processing service
- Model fitting service (Anny)
- Database (PostgreSQL)
- Cache (Redis)

**Outside System**:
- User devices (browsers, mobile)
- External AI APIs (MediaPipe)
- Cloud infrastructure (if deployed on AWS/GCP)
- Authentication providers

## Deployment Context

### Development
- Local Docker Compose
- SQLite for rapid testing
- Mock external services

### Production
- Kubernetes cluster
- Managed PostgreSQL (RDS/Cloud SQL)
- Managed Redis (ElastiCache/Memorystore)
- CDN for frontend assets

## Revision History
| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-11-10 | Initial C4 context diagram |
