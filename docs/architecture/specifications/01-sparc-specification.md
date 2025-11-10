# SPARC Specification: Photo-to-3D-Model Fitting Application

## Document Control
- **Document Type**: SPARC Specification Phase
- **Version**: 1.0.0
- **Date**: 2025-11-10
- **Status**: Draft
- **Author**: System Architecture Team

---

## 1. Executive Summary

### 1.1 Project Vision
Develop a privacy-preserving web application that transforms single or multiple photographs of a person into a fitted 3D body model using the Anny parametric model. The system will automatically extract body measurements, intelligently average multi-image inputs, and generate personalized 3D visualizations while maintaining strict data privacy standards.

### 1.2 Core Value Proposition
- **Non-invasive Measurement**: Extract body metrics from photos without physical contact
- **Accessibility**: No specialized equipment required beyond a camera/smartphone
- **Personalization**: Generate accurate 3D models for individuals across all ages (infant to elder)
- **Privacy-First**: Temporary photo processing with no permanent storage of images
- **Research & Clinical Applications**: Support anthropometry research, garment fitting, health monitoring

### 1.3 Success Criteria
- **Accuracy**: ≤20mm mean per-vertex error (PVE) on standard test datasets
- **Speed**: <10 seconds total processing time per subject (single image)
- **Scalability**: Support 100+ concurrent users
- **Privacy**: Zero photo retention post-processing
- **Usability**: Single-click operation for end users

---

## 2. Functional Requirements

### 2.1 Image Upload & Management (FR-IMG)

**FR-IMG-001: Single Image Upload**
- User can upload a single full-body photograph
- Supported formats: JPEG, PNG, WebP
- Maximum file size: 10MB
- Minimum resolution: 1024x768 pixels
- Automatic EXIF data stripping on upload

**FR-IMG-002: Multiple Image Upload**
- User can upload 2-8 photographs of the same subject
- Support batch upload with drag-and-drop interface
- Visual preview of all uploaded images
- Individual image removal before processing

**FR-IMG-003: Image Validation**
- Automatic detection of human presence in image
- Warning if image quality insufficient (blur, lighting)
- Rejection of inappropriate content
- Validation of aspect ratio and composition

### 2.2 Vision Processing Pipeline (FR-VIS)

**FR-VIS-001: Pose & Landmark Detection**
- Detect 2D body keypoints using state-of-the-art pose estimation (MediaPipe/OpenPose)
- Extract facial landmarks (68+ points)
- Detect hand landmarks if visible
- Estimate camera parameters (focal length, distance)

**FR-VIS-002: Depth & Silhouette Estimation**
- Generate depth maps from single images using monocular depth estimation
- Extract precise body silhouettes via segmentation
- Handle occlusions and partial visibility
- Multi-view depth fusion for multiple images

**FR-VIS-003: Anthropometric Measurement Extraction**
- Calculate body measurements from keypoints and depth:
  - Height
  - Shoulder width
  - Chest/waist/hip circumference
  - Arm/leg lengths
  - Head circumference
- Account for camera distortion and perspective
- Provide confidence scores for each measurement

**FR-VIS-004: Multi-Image Fusion**
- Intelligent averaging of measurements from multiple views
- Weighted fusion based on confidence scores
- Outlier detection and rejection
- Uncertainty quantification for fused estimates

### 2.3 Parameter Mapping & Model Fitting (FR-FIT)

**FR-FIT-001: Vision-to-Phenotype Mapping**
- Map extracted measurements to Anny phenotype parameters:
  - `gender` (0-1: male-female)
  - `age` (-0.33-1.0: newborn-elder)
  - `height` (0-1: min-max)
  - `weight` (0-1: min-max)
  - `muscle` (0-1: min-max)
  - `proportions` (0-1: ideal-uncommon)
- Use learned regression model or analytical mapping
- Handle measurement ambiguity (e.g., gender estimation)

**FR-FIT-002: Iterative Model Optimization**
- Leverage existing `ParametersRegressor` class
- Optimize both pose and phenotype parameters
- Multi-stage fitting: age → height → all phenotypes
- Regularization to prevent overfitting to noise

**FR-FIT-003: Pose Estimation from Images**
- Convert 2D keypoints to 3D joint rotations
- Initialize pose using detected body orientation
- Refine pose through inverse kinematics
- Handle hands/feet if detected in images

**FR-FIT-004: Quality Assessment**
- Calculate fitting error metrics (PVE, joint error)
- Detect fitting failures (convergence issues)
- Provide user feedback on fitting quality
- Suggest additional photos if quality insufficient

### 2.4 Subject Metadata Management (FR-META)

**FR-META-001: Subject Profile Creation**
- Store subject metadata in database:
  - Name (optional, anonymization option)
  - Date of birth
  - Gender (self-reported, optional)
  - Unique subject ID (UUID)
  - Timestamp of capture

**FR-META-002: Performance Metrics Storage**
- Store fitting quality metrics:
  - Per-vertex error (PVE)
  - Anthropometric measurement accuracy
  - Processing time
  - Number of images used
- Link metrics to subject profile

**FR-META-003: Model Parameters Storage**
- Persist fitted Anny parameters:
  - Phenotype parameters (JSON)
  - Pose parameters (tensor storage)
  - Local changes (if applicable)
- Enable model reconstruction without re-processing

**FR-META-004: Session Management**
- Track user sessions
- Allow session resumption
- Expire sessions after inactivity (30 minutes)
- Clear temporary data on logout

### 2.5 Visualization & Export (FR-VIZ)

**FR-VIZ-001: Interactive 3D Viewer**
- Real-time 3D model rendering in browser
- Orbit/pan/zoom camera controls
- Lighting and material controls
- Overlay original photos for comparison

**FR-VIZ-002: Measurement Display**
- Overlay anthropometric measurements on 3D model
- Show measurement comparison (photo vs. model)
- Display confidence intervals
- Export measurements to CSV/JSON

**FR-VIZ-003: Model Export**
- Export 3D mesh in standard formats:
  - OBJ with texture coordinates
  - GLTF/GLB for web
  - FBX for animation software
- Export fitted parameters as JSON
- Generate shareable viewer link (24-hour expiry)

**FR-VIZ-004: Comparison View**
- Side-by-side comparison of multiple subjects
- Overlay multiple models for difference visualization
- Measurement comparison tables
- Longitudinal tracking (same subject over time)

### 2.6 Privacy & Security (FR-SEC)

**FR-SEC-001: Temporary Photo Storage**
- Store uploaded photos in memory/temp storage only
- Automatic deletion after processing (max 5 minutes)
- No cloud storage of photos
- Secure deletion (overwrite data)

**FR-SEC-002: Anonymization Options**
- Face blurring option before processing
- Remove identifiable metadata (EXIF)
- Anonymize subject names in database
- Generate pseudonymous IDs

**FR-SEC-003: Access Control**
- User authentication (OAuth 2.0)
- Role-based access (user, researcher, admin)
- Subject data isolation (users only see own data)
- Audit logging of data access

**FR-SEC-004: Data Retention Policy**
- Photos: 0 retention (immediate deletion)
- Metadata: User-defined retention (default 90 days)
- 3D models: Optional long-term storage
- Compliance with GDPR/HIPAA

---

## 3. Non-Functional Requirements

### 3.1 Performance (NFR-PERF)

**NFR-PERF-001: Processing Speed**
- Single image processing: <10 seconds
- Multiple images (4 photos): <30 seconds
- 3D visualization load time: <2 seconds
- API response time: <500ms (95th percentile)

**NFR-PERF-002: Scalability**
- Support 100 concurrent users
- Handle 1000 subjects per day
- Auto-scaling based on load (cloud deployment)
- Database query optimization (<100ms)

**NFR-PERF-003: Resource Efficiency**
- GPU memory usage: <4GB per processing job
- CPU usage: <80% during peak load
- Storage: <50MB per subject (excluding photos)
- Network bandwidth: <100KB/s per user

### 3.2 Reliability (NFR-REL)

**NFR-REL-001: Availability**
- System uptime: 99.5% (excluding maintenance)
- Graceful degradation under load
- Automatic retry for transient failures
- Health monitoring and alerting

**NFR-REL-002: Error Handling**
- Graceful handling of malformed images
- Fallback to default parameters on fitting failure
- Clear error messages to users
- Automatic crash recovery

**NFR-REL-003: Data Integrity**
- Database transactions with ACID guarantees
- Backup of subject metadata (daily)
- Version control for model parameters
- Checksum validation for exports

### 3.3 Usability (NFR-USE)

**NFR-USE-001: User Interface**
- Mobile-responsive design (Bootstrap/Tailwind)
- Accessibility compliance (WCAG 2.1 AA)
- Multi-language support (English, French, Spanish)
- Intuitive workflow (<5 clicks to result)

**NFR-USE-002: Documentation**
- User guide with photo-taking tips
- API documentation (OpenAPI spec)
- Developer setup guide
- Video tutorials

**NFR-USE-003: Feedback & Guidance**
- Real-time processing progress indicator
- Quality feedback (photo composition tips)
- Error explanations with corrective actions
- Tooltips for technical terms

### 3.4 Security (NFR-SEC)

**NFR-SEC-001: Authentication & Authorization**
- Secure password storage (bcrypt)
- Multi-factor authentication (optional)
- Session timeout (30 minutes inactivity)
- API key management for researchers

**NFR-SEC-002: Data Encryption**
- HTTPS/TLS 1.3 for all communications
- Encryption at rest for database (AES-256)
- Encrypted backups
- Secure key management (AWS KMS, HashiCorp Vault)

**NFR-SEC-003: Compliance**
- GDPR compliance (data deletion, consent)
- HIPAA compliance (optional, for clinical use)
- Regular security audits
- Penetration testing (annual)

### 3.5 Maintainability (NFR-MAINT)

**NFR-MAINT-001: Code Quality**
- Test coverage: >80%
- Type annotations (Python, TypeScript)
- Linting and formatting (Black, ESLint)
- Code review process

**NFR-MAINT-002: Modularity**
- Microservices architecture (optional)
- Clear separation of concerns
- Dependency injection
- API versioning

**NFR-MAINT-003: Monitoring & Logging**
- Structured logging (JSON)
- Distributed tracing (OpenTelemetry)
- Metrics collection (Prometheus)
- Centralized log aggregation (ELK)

---

## 4. System Context

### 4.1 User Personas

**Persona 1: Clinical Researcher**
- Needs: Batch processing, measurement accuracy, data export
- Technical skill: Medium
- Usage frequency: Daily
- Key feature: Multi-subject comparison

**Persona 2: Fashion Designer**
- Needs: Quick fitting, 3D export for CAD
- Technical skill: Low-medium
- Usage frequency: Weekly
- Key feature: Garment overlay capability

**Persona 3: Individual User**
- Needs: Personal 3D avatar, privacy
- Technical skill: Low
- Usage frequency: Once
- Key feature: Easy photo upload

**Persona 4: Fitness Trainer**
- Needs: Longitudinal tracking, measurement changes
- Technical skill: Low
- Usage frequency: Monthly per client
- Key feature: Progress visualization

### 4.2 External Interfaces

**INT-001: User Web Interface**
- Modern SPA (React/Vue.js)
- REST API backend
- WebSocket for real-time updates
- WebGL/Three.js for 3D rendering

**INT-002: REST API**
- OpenAPI 3.0 specification
- JSON request/response
- JWT authentication
- Rate limiting (100 req/hour/user)

**INT-003: Database Interface**
- PostgreSQL (primary data)
- Redis (caching, sessions)
- S3-compatible object storage (exports)

**INT-004: Vision AI Services**
- MediaPipe API (pose estimation)
- Optional: Custom depth estimation model
- Face detection API (privacy filtering)

### 4.3 Constraints & Assumptions

**Constraints:**
- Must use existing Anny model (no re-training base model)
- GPU required for processing (NVIDIA with CUDA support)
- Browser must support WebGL 2.0
- Maximum image size: 10MB (CDN limit)

**Assumptions:**
- Users have basic smartphone/camera
- Subjects wear form-fitting clothing for accurate measurement
- Lighting is adequate (no extreme shadows)
- Full-body photos include entire person (head to feet)
- Internet connection: >1 Mbps upload

---

## 5. Data Requirements

### 5.1 Data Entities

**Entity: Subject**
```
- subject_id (UUID, PK)
- user_id (FK to User)
- name (String, nullable, encrypted)
- date_of_birth (Date, nullable)
- gender (Enum: male/female/other/unspecified, nullable)
- created_at (Timestamp)
- updated_at (Timestamp)
- anonymized (Boolean)
```

**Entity: FittedModel**
```
- model_id (UUID, PK)
- subject_id (FK to Subject)
- phenotype_parameters (JSONB)
- pose_parameters (Binary)
- local_changes (JSONB, nullable)
- fitting_error (Float)
- processing_time (Float)
- num_images_used (Integer)
- created_at (Timestamp)
```

**Entity: Measurement**
```
- measurement_id (UUID, PK)
- model_id (FK to FittedModel)
- measurement_type (Enum: height, waist, chest, etc.)
- value (Float)
- unit (Enum: meters, kilograms, etc.)
- confidence (Float)
- extracted_from (Enum: image, model)
```

**Entity: User**
```
- user_id (UUID, PK)
- email (String, unique)
- password_hash (String)
- role (Enum: user, researcher, admin)
- created_at (Timestamp)
- last_login (Timestamp)
```

**Entity: Session**
```
- session_id (UUID, PK)
- user_id (FK to User)
- subject_id (FK to Subject, nullable)
- status (Enum: active, expired, completed)
- created_at (Timestamp)
- expires_at (Timestamp)
```

### 5.2 Data Flows

**Flow 1: Photo Upload → Model Fitting**
1. User uploads photo(s) → Temporary storage (memory/RAM disk)
2. Vision pipeline extracts measurements → In-memory processing
3. Parameter regressor fits Anny model → GPU computation
4. Store fitted parameters → Database
5. Delete photos → Secure wipe
6. Return 3D model → Client (WebGL)

**Flow 2: Retrieve Subject History**
1. User requests subject list → API
2. Database query → Subject + FittedModel join
3. Return metadata (no photos) → Client
4. User selects subject → Load parameters
5. Reconstruct 3D model → Anny forward pass
6. Render → WebGL viewer

---

## 6. Quality Attributes

### 6.1 Accuracy Targets

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Height error | <2cm | Ground truth comparison |
| Circumference error | <3cm | Ground truth comparison |
| PVE (mean) | <20mm | Mesh-to-mesh distance |
| Gender classification | >95% | Self-reported labels |
| Age estimation (±5 years) | >80% | DOB comparison |

### 6.2 Privacy Guarantees

- **Photo retention**: 0 seconds post-processing
- **Face anonymization**: 100% if enabled
- **EXIF stripping**: 100% on upload
- **Access logging**: 100% coverage
- **Encryption**: 100% of sensitive data

### 6.3 User Experience

- **Time to first result**: <15 seconds
- **Mobile usability**: 100% feature parity
- **Accessibility**: WCAG 2.1 AA compliance
- **Error rate**: <1% (photos rejected)

---

## 7. Risks & Mitigation

### 7.1 Technical Risks

**Risk 1: Poor Image Quality**
- **Impact**: High (fitting failures)
- **Probability**: Medium
- **Mitigation**: Pre-upload quality checks, user guidance, fallback defaults

**Risk 2: GPU Availability**
- **Impact**: Critical (system unusable without GPU)
- **Probability**: Low
- **Mitigation**: Cloud GPU instances (auto-scaling), CPU fallback (slow mode)

**Risk 3: Model Fitting Convergence**
- **Impact**: Medium (inaccurate results)
- **Probability**: Medium
- **Mitigation**: Multi-stage fitting, age anchor search, conservative regularization

### 7.2 Privacy Risks

**Risk 4: Photo Leakage**
- **Impact**: Critical (legal, reputation)
- **Probability**: Low
- **Mitigation**: Memory-only storage, secure deletion, no logging of photos, audit trails

**Risk 5: Re-identification from 3D Model**
- **Impact**: High (privacy breach)
- **Probability**: Low
- **Mitigation**: Face anonymization option, consent workflow, encrypted storage

### 7.3 Operational Risks

**Risk 6: Scaling Bottlenecks**
- **Impact**: High (poor UX)
- **Probability**: Medium
- **Mitigation**: Load testing, auto-scaling, queueing system, CDN for static assets

**Risk 7: Database Failures**
- **Impact**: High (data loss)
- **Probability**: Low
- **Mitigation**: Daily backups, database replication, transaction logging

---

## 8. Dependencies & Integrations

### 8.1 Core Dependencies

**Python Ecosystem:**
- PyTorch (≥2.0): Anny model inference
- NumPy/SciPy: Numerical computation
- OpenCV: Image preprocessing
- MediaPipe: Pose/face landmark detection
- Pillow: Image I/O

**Backend:**
- FastAPI (or Flask): REST API
- SQLAlchemy: ORM
- Alembic: Database migrations
- Redis: Caching, session storage
- Celery (optional): Async task queue

**Frontend:**
- React (or Vue.js): UI framework
- Three.js: 3D rendering
- Axios: HTTP client
- TailwindCSS: Styling

**Infrastructure:**
- PostgreSQL: Primary database
- Nginx: Reverse proxy
- Docker: Containerization
- Kubernetes (optional): Orchestration

### 8.2 External Services

**Optional Integrations:**
- **Cloud Storage**: AWS S3, Google Cloud Storage (for exports)
- **Authentication**: Auth0, OAuth providers (Google, GitHub)
- **Monitoring**: Sentry (error tracking), Datadog (metrics)
- **Email**: SendGrid (user notifications)

---

## 9. Future Enhancements (Out of Scope v1.0)

**Phase 2 Features:**
- Real-time video processing (live fitting)
- Garment overlay and virtual try-on
- Multi-subject scene processing
- Advanced texture mapping from photos
- Motion capture from video

**Phase 3 Features:**
- Mobile app (iOS/Android)
- AR visualization (smartphone overlay)
- Social sharing (anonymized models)
- Marketplace integration (custom avatars for games)
- AI-powered pose suggestion

---

## 10. Acceptance Criteria

### 10.1 Functional Acceptance

- [ ] User can upload 1-8 photos via web interface
- [ ] System extracts measurements within 10 seconds
- [ ] Fitted 3D model matches subject with <20mm PVE
- [ ] Subject metadata is stored and retrievable
- [ ] Photos are deleted immediately post-processing
- [ ] 3D model renders in browser (<2 seconds)
- [ ] User can export model as OBJ/GLTF
- [ ] Measurements are exported as CSV/JSON

### 10.2 Non-Functional Acceptance

- [ ] System handles 100 concurrent users
- [ ] API response time <500ms (95th percentile)
- [ ] Test coverage >80%
- [ ] WCAG 2.1 AA accessibility compliance
- [ ] HTTPS/TLS encryption for all endpoints
- [ ] Database backups run daily
- [ ] Security audit passed (zero critical vulnerabilities)

### 10.3 Usability Acceptance

- [ ] User completes photo-to-3D workflow in <5 clicks
- [ ] Mobile interface tested on iOS/Android
- [ ] User documentation published
- [ ] Developer API docs published (OpenAPI)
- [ ] Error messages are clear and actionable

---

## Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-11-10 | Architecture Team | Initial SPARC specification |

---

## Appendices

### Appendix A: Anny Phenotype Parameters

| Parameter | Range | Description |
|-----------|-------|-------------|
| `gender` | [0, 1] | 0=male, 1=female |
| `age` | [-0.33, 1.0] | -0.33=newborn, 0=baby, 0.33=child, 0.67=young, 1.0=old |
| `height` | [0, 1] | 0=minimum height, 1=maximum height |
| `weight` | [0, 1] | 0=minimum weight, 1=maximum weight |
| `muscle` | [0, 1] | 0=minimum muscle, 1=maximum muscle |
| `proportions` | [0, 1] | 0=ideal proportions, 1=uncommon proportions |
| `cupsize` | [0, 1] | 0=minimum, 1=maximum (if applicable) |
| `firmness` | [0, 1] | 0=minimum, 1=maximum (if applicable) |

### Appendix B: Key Anthropometric Measurements

- **Height**: Maximum Z-axis extent
- **Waist Circumference**: Perimeter at waist vertices
- **Chest Circumference**: Perimeter at chest level
- **Hip Circumference**: Perimeter at hip level
- **Shoulder Width**: Distance between shoulder joints
- **Arm Length**: Shoulder to wrist distance
- **Leg Length**: Hip to ankle distance
- **Body Mass Index (BMI)**: Derived from volume and height

### Appendix C: Glossary

- **PVE (Per-Vertex Error)**: Mean Euclidean distance between predicted and ground-truth vertex positions
- **Phenotype Parameters**: High-level shape descriptors controlling Anny model (gender, age, etc.)
- **Blendshapes**: Mesh deformations encoding shape variations
- **Pose Parameters**: Joint rotations and translations defining body posture
- **Anthropometry**: Science of human body measurement
- **GDPR**: General Data Protection Regulation (EU privacy law)
- **HIPAA**: Health Insurance Portability and Accountability Act (US healthcare privacy)
