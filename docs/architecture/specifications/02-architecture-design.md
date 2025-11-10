# System Architecture Design: Photo-to-3D-Model Fitting Application

## Document Control
- **Document Type**: SPARC Architecture Phase
- **Version**: 1.0.0
- **Date**: 2025-11-10
- **Status**: Draft
- **Author**: System Architecture Team

---

## 1. Architecture Overview

### 1.1 Architecture Style
**Chosen Style**: **Layered Architecture with Microservices Modularity**

**Rationale**:
- **Layered**: Clear separation of concerns (Presentation, Business Logic, Data Access)
- **Modular**: Vision processing, model fitting, and API services can scale independently
- **Pragmatic**: Avoid over-engineering for v1.0 while enabling future microservices migration

**Alternative Considered**: Full microservices architecture (rejected due to operational complexity for initial deployment)

### 1.2 High-Level Architecture (C4 Context Diagram)

```
┌─────────────────────────────────────────────────────────────────────┐
│                          System Context                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────┐                                      ┌──────────┐    │
│  │   User   │──────── HTTPS/WebSocket ────────────▶│  Web App │    │
│  │ (Browser)│◀───────── 3D Model/UI ───────────────│ (Frontend)│   │
│  └──────────┘                                      └─────┬────┘    │
│                                                           │         │
│                                                           │         │
│                                                           ▼         │
│                                                    ┌──────────────┐ │
│                                                    │   API Server │ │
│                                                    │   (FastAPI)  │ │
│                                                    └──────┬───────┘ │
│                                                           │         │
│                     ┌─────────────────────────────────────┼────┐    │
│                     │                                     │    │    │
│                     ▼                                     ▼    ▼    │
│              ┌──────────────┐                     ┌───────────────┐│
│              │ Vision       │                     │ Model Fitting ││
│              │ Processing   │                     │ Service       ││
│              │ Service      │                     │ (Anny)        ││
│              └──────┬───────┘                     └───────┬───────┘│
│                     │                                     │        │
│                     │                                     │        │
│                     └─────────────┬───────────────────────┘        │
│                                   │                                │
│                                   ▼                                │
│                            ┌─────────────┐                         │
│                            │  Database   │                         │
│                            │ (PostgreSQL)│                         │
│                            └─────────────┘                         │
│                                                                     │
│  External:                                                          │
│  ┌────────────┐         ┌─────────────┐        ┌──────────────┐   │
│  │ MediaPipe  │         │   Redis     │        │ Object Store │   │
│  │   API      │         │  (Cache)    │        │   (S3/Minio) │   │
│  └────────────┘         └─────────────┘        └──────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.3 Technology Stack Decision Matrix

| Component | Technology | Alternatives Considered | Decision Rationale |
|-----------|-----------|------------------------|-------------------|
| **Backend API** | FastAPI | Flask, Django | Async support, auto OpenAPI docs, high performance |
| **Frontend** | React + Three.js | Vue.js, Angular | Strong ecosystem, WebGL integration, component reusability |
| **Database** | PostgreSQL | MySQL, MongoDB | JSONB support for parameters, ACID compliance, robust |
| **Cache** | Redis | Memcached | Pub/sub for WebSocket, session storage, rich data types |
| **Vision AI** | MediaPipe | OpenPose, AlphaPose | Free, cross-platform, GPU optimized, maintained by Google |
| **3D Rendering** | Three.js | Babylon.js, PlayCanvas | Mature, extensive community, glTF support |
| **Containerization** | Docker | Podman | Industry standard, extensive tooling, image registry support |
| **Web Server** | Nginx | Apache, Caddy | High performance, reverse proxy, static file serving |

---

## 2. Container Architecture (C4 Container Diagram)

### 2.1 System Containers

```
┌───────────────────────────────────────────────────────────────────────┐
│                        Container Diagram                              │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐     │
│  │              Frontend Container (React SPA)                 │     │
│  │  - React components                                         │     │
│  │  - Three.js 3D viewer                                       │     │
│  │  - Axios HTTP client                                        │     │
│  │  - WebSocket client                                         │     │
│  │  Deployment: Nginx static files + CDN                       │     │
│  └────────────────────────┬────────────────────────────────────┘     │
│                           │ REST/WebSocket                            │
│                           ▼                                           │
│  ┌─────────────────────────────────────────────────────────────┐     │
│  │            API Gateway Container (Nginx)                    │     │
│  │  - Reverse proxy                                            │     │
│  │  - SSL/TLS termination                                      │     │
│  │  - Rate limiting                                            │     │
│  │  - Load balancing                                           │     │
│  └────────────────────────┬────────────────────────────────────┘     │
│                           │                                           │
│                           ▼                                           │
│  ┌─────────────────────────────────────────────────────────────┐     │
│  │         Backend API Container (FastAPI + Uvicorn)           │     │
│  │  - REST endpoints (/api/v1/*)                               │     │
│  │  - WebSocket server (progress updates)                      │     │
│  │  - Authentication middleware (JWT)                          │     │
│  │  - Request validation (Pydantic)                            │     │
│  │  - Business logic orchestration                             │     │
│  │  Deployment: Uvicorn workers (4x processes)                 │     │
│  └────┬──────────────────────┬────────────────┬─────────────────┘    │
│       │                      │                │                      │
│       ▼                      ▼                ▼                      │
│  ┌──────────────┐   ┌────────────────┐  ┌─────────────────┐        │
│  │   Vision     │   │  Model Fitting │  │  Visualization  │        │
│  │  Processing  │   │    Service     │  │    Service      │        │
│  │  Container   │   │   Container    │  │   Container     │        │
│  │              │   │                │  │                 │        │
│  │ - MediaPipe  │   │ - Anny model   │  │ - Mesh export   │        │
│  │ - Pose est.  │   │ - Regressor    │  │ - glTF gen.     │        │
│  │ - Depth est. │   │ - PyTorch      │  │ - Measurement   │        │
│  │ - Segment.   │   │ - Anthropometry│  │   calculation   │        │
│  │              │   │                │  │                 │        │
│  │ GPU: Optional│   │ GPU: Required  │  │ GPU: No         │        │
│  └──────┬───────┘   └────────┬───────┘  └─────────┬───────┘        │
│         │                    │                     │                │
│         └────────────────────┼─────────────────────┘                │
│                              │                                      │
│                              ▼                                      │
│         ┌────────────────────────────────────────────────┐          │
│         │   Data Layer Containers                       │          │
│         │                                                │          │
│         │  ┌──────────────┐      ┌───────────────┐      │          │
│         │  │ PostgreSQL   │      │     Redis     │      │          │
│         │  │  Container   │      │   Container   │      │          │
│         │  │              │      │               │      │          │
│         │  │ - Subjects   │      │ - Sessions    │      │          │
│         │  │ - Models     │      │ - Cache       │      │          │
│         │  │ - Measurements│     │ - WebSocket   │      │          │
│         │  │ - Users      │      │   pub/sub     │      │          │
│         │  └──────────────┘      └───────────────┘      │          │
│         │                                                │          │
│         │  ┌──────────────┐                              │          │
│         │  │ Object Store │                              │          │
│         │  │ (MinIO/S3)   │                              │          │
│         │  │              │                              │          │
│         │  │ - Model      │                              │          │
│         │  │   exports    │                              │          │
│         │  │ - Temp files │                              │          │
│         │  └──────────────┘                              │          │
│         └────────────────────────────────────────────────┘          │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### 2.2 Container Specifications

**Frontend Container (React SPA)**
- **Base Image**: `node:20-alpine`
- **Build**: Multi-stage (build → serve with nginx)
- **Port**: 80 (internal), 443 (external via gateway)
- **Resources**: 512MB RAM, 0.5 CPU

**API Gateway Container (Nginx)**
- **Base Image**: `nginx:1.25-alpine`
- **Configuration**: Custom nginx.conf (reverse proxy, SSL, rate limiting)
- **Port**: 80, 443
- **Resources**: 256MB RAM, 0.25 CPU

**Backend API Container (FastAPI)**
- **Base Image**: `python:3.11-slim`
- **Workers**: 4x Uvicorn processes
- **Port**: 8000 (internal)
- **Resources**: 2GB RAM, 2 CPU
- **Environment Variables**: `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`

**Vision Processing Container**
- **Base Image**: `python:3.11-slim` + MediaPipe
- **GPU**: NVIDIA GPU (optional, CPU fallback)
- **Port**: 8001 (internal gRPC/HTTP)
- **Resources**: 4GB RAM, 2 CPU, 4GB GPU memory

**Model Fitting Container**
- **Base Image**: `pytorch/pytorch:2.0-cuda11.8-cudnn8-runtime`
- **GPU**: NVIDIA GPU (required)
- **Port**: 8002 (internal gRPC/HTTP)
- **Resources**: 8GB RAM, 4 CPU, 8GB GPU memory

**Visualization Container**
- **Base Image**: `python:3.11-slim`
- **Libraries**: PyTorch3D, trimesh
- **Port**: 8003 (internal)
- **Resources**: 2GB RAM, 1 CPU

**PostgreSQL Container**
- **Base Image**: `postgres:16-alpine`
- **Port**: 5432 (internal)
- **Volumes**: `/var/lib/postgresql/data` (persistent)
- **Resources**: 4GB RAM, 2 CPU

**Redis Container**
- **Base Image**: `redis:7-alpine`
- **Port**: 6379 (internal)
- **Resources**: 1GB RAM, 0.5 CPU

**Object Storage Container (MinIO)**
- **Base Image**: `minio/minio:latest`
- **Port**: 9000 (API), 9001 (console)
- **Volumes**: `/data` (persistent)
- **Resources**: 2GB RAM, 1 CPU

---

## 3. Component Architecture (C4 Component Diagram)

### 3.1 Backend API Components

```
┌───────────────────────────────────────────────────────────────────┐
│                  Backend API Components                           │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │                    API Layer                             │    │
│  │                                                          │    │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐        │    │
│  │  │   Auth     │  │  Subject   │  │   Model    │        │    │
│  │  │ Controller │  │ Controller │  │ Controller │        │    │
│  │  │            │  │            │  │            │        │    │
│  │  │ POST /auth │  │ POST /     │  │ POST /fit  │        │    │
│  │  │ GET /user  │  │ GET /:id   │  │ GET /:id   │        │    │
│  │  └──────┬─────┘  └──────┬─────┘  └──────┬─────┘        │    │
│  │         │                │                │             │    │
│  └─────────┼────────────────┼────────────────┼─────────────┘    │
│            │                │                │                  │
│            ▼                ▼                ▼                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                  Business Logic Layer                    │   │
│  │                                                          │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐        │   │
│  │  │   Auth     │  │  Subject   │  │   Fitting  │        │   │
│  │  │  Service   │  │  Service   │  │  Service   │        │   │
│  │  │            │  │            │  │            │        │   │
│  │  │ - Login    │  │ - Create   │  │ - Process  │        │   │
│  │  │ - Register │  │ - Update   │  │ - Optimize │        │   │
│  │  │ - Validate │  │ - Delete   │  │ - Export   │        │   │
│  │  └──────┬─────┘  └──────┬─────┘  └──────┬─────┘        │   │
│  │         │                │                │             │   │
│  │         │                ▼                │             │   │
│  │         │       ┌────────────────┐        │             │   │
│  │         │       │   Orchestrator │        │             │   │
│  │         │       │                │        │             │   │
│  │         │       │ - Vision call  │        │             │   │
│  │         │       │ - Fitting call │        │             │   │
│  │         │       │ - Progress pub │        │             │   │
│  │         │       └────────┬───────┘        │             │   │
│  └─────────┼────────────────┼────────────────┼─────────────┘   │
│            │                │                │                  │
│            ▼                ▼                ▼                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                  Data Access Layer                       │   │
│  │                                                          │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐        │   │
│  │  │    User    │  │  Subject   │  │   Model    │        │   │
│  │  │ Repository │  │ Repository │  │ Repository │        │   │
│  │  │            │  │            │  │            │        │   │
│  │  │ - CRUD ops │  │ - CRUD ops │  │ - CRUD ops │        │   │
│  │  │ - Queries  │  │ - Queries  │  │ - Queries  │        │   │
│  │  └──────┬─────┘  └──────┬─────┘  └──────┬─────┘        │   │
│  │         │                │                │             │   │
│  └─────────┼────────────────┼────────────────┼─────────────┘   │
│            │                │                │                  │
│            └────────────────┴────────────────┘                  │
│                             │                                   │
│                             ▼                                   │
│                    ┌─────────────────┐                          │
│                    │   PostgreSQL    │                          │
│                    │    Database     │                          │
│                    └─────────────────┘                          │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 3.2 Vision Processing Components

```
┌───────────────────────────────────────────────────────────────────┐
│              Vision Processing Service Components                 │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐      │
│  │               Image Input Handler                      │      │
│  │                                                        │      │
│  │  - Validate format (JPEG/PNG/WebP)                    │      │
│  │  - Resize to max 2048px                               │      │
│  │  - Strip EXIF metadata                                │      │
│  │  - Normalize color space                              │      │
│  └─────────────────────┬──────────────────────────────────┘      │
│                        │                                         │
│                        ▼                                         │
│  ┌────────────────────────────────────────────────────────┐      │
│  │          Pose & Landmark Detector                      │      │
│  │                                                        │      │
│  │  ┌──────────────┐    ┌──────────────┐                 │      │
│  │  │  MediaPipe   │    │  Keypoint    │                 │      │
│  │  │  Holistic    │───▶│  Extractor   │                 │      │
│  │  │              │    │              │                 │      │
│  │  │ - Body pose  │    │ - 33 body    │                 │      │
│  │  │ - Face mesh  │    │ - 68 face    │                 │      │
│  │  │ - Hands      │    │ - 21 hand    │                 │      │
│  │  └──────────────┘    └──────────────┘                 │      │
│  └─────────────────────┬──────────────────────────────────┘      │
│                        │                                         │
│                        ▼                                         │
│  ┌────────────────────────────────────────────────────────┐      │
│  │          Depth & Silhouette Estimator                  │      │
│  │                                                        │      │
│  │  ┌──────────────┐    ┌──────────────┐                 │      │
│  │  │  Monocular   │    │   Segment    │                 │      │
│  │  │   Depth      │    │   Anything   │                 │      │
│  │  │  (MiDaS)     │    │   Model      │                 │      │
│  │  │              │    │              │                 │      │
│  │  │ - Depth map  │    │ - Body mask  │                 │      │
│  │  │ - Z buffer   │    │ - Silhouette │                 │      │
│  │  └──────────────┘    └──────────────┘                 │      │
│  └─────────────────────┬──────────────────────────────────┘      │
│                        │                                         │
│                        ▼                                         │
│  ┌────────────────────────────────────────────────────────┐      │
│  │        Anthropometric Measurement Extractor            │      │
│  │                                                        │      │
│  │  - Calculate height from keypoints                    │      │
│  │  - Estimate circumferences from depth+silhouette      │      │
│  │  - Compute limb lengths                               │      │
│  │  - Account for camera perspective                     │      │
│  │  - Assign confidence scores                           │      │
│  └─────────────────────┬──────────────────────────────────┘      │
│                        │                                         │
│                        ▼                                         │
│  ┌────────────────────────────────────────────────────────┐      │
│  │            Multi-Image Fusion (Optional)               │      │
│  │                                                        │      │
│  │  - Weighted average by confidence                     │      │
│  │  - Outlier rejection (RANSAC)                         │      │
│  │  - Uncertainty quantification                         │      │
│  └─────────────────────┬──────────────────────────────────┘      │
│                        │                                         │
│                        ▼                                         │
│                   [Output: Measurements Dict]                    │
│                   {                                              │
│                     "height": (value, confidence),               │
│                     "waist_circ": (value, confidence),           │
│                     ...                                          │
│                   }                                              │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 3.3 Model Fitting Components

```
┌───────────────────────────────────────────────────────────────────┐
│             Model Fitting Service Components                      │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐      │
│  │         Measurement-to-Phenotype Mapper                │      │
│  │                                                        │      │
│  │  - Map height → height parameter                      │      │
│  │  - Map weight indicators → weight parameter           │      │
│  │  - Estimate age from proportions (if no DOB)          │      │
│  │  - Estimate gender from measurements (optional)       │      │
│  │  - Initialize phenotype dict                          │      │
│  └─────────────────────┬──────────────────────────────────┘      │
│                        │                                         │
│                        ▼                                         │
│  ┌────────────────────────────────────────────────────────┐      │
│  │              Anny Model Loader                         │      │
│  │                                                        │      │
│  │  - Load pre-trained Anny model                        │      │
│  │  - Initialize ParametersRegressor                     │      │
│  │  - Configure optimization settings                    │      │
│  │  - Move to GPU (if available)                         │      │
│  └─────────────────────┬──────────────────────────────────┘      │
│                        │                                         │
│                        ▼                                         │
│  ┌────────────────────────────────────────────────────────┐      │
│  │           Iterative Parameter Optimizer                │      │
│  │                                                        │      │
│  │  ┌──────────────────────────────────────────┐         │      │
│  │  │  Stage 1: Age Anchor Search              │         │      │
│  │  │  - Try age = [0.0, 0.33, 0.67, 1.0]      │         │      │
│  │  │  - Optimize height only                  │         │      │
│  │  │  - Select best age by PVE                │         │      │
│  │  └──────────────────┬───────────────────────┘         │      │
│  │                     │                                  │      │
│  │                     ▼                                  │      │
│  │  ┌──────────────────────────────────────────┐         │      │
│  │  │  Stage 2: Full Phenotype Optimization    │         │      │
│  │  │  - Fix age from Stage 1                  │         │      │
│  │  │  - Optimize all phenotypes               │         │      │
│  │  │  - Jacobian-based updates                │         │      │
│  │  │  - Regularization (prevent overfitting)  │         │      │
│  │  └──────────────────┬───────────────────────┘         │      │
│  │                     │                                  │      │
│  │                     ▼                                  │      │
│  │  ┌──────────────────────────────────────────┐         │      │
│  │  │  Stage 3: Pose Refinement                │         │      │
│  │  │  - Jointwise registration                │         │      │
│  │  │  - Root joint alignment                  │         │      │
│  │  │  - Face joint identity lock              │         │      │
│  │  └──────────────────────────────────────────┘         │      │
│  └─────────────────────┬──────────────────────────────────┘      │
│                        │                                         │
│                        ▼                                         │
│  ┌────────────────────────────────────────────────────────┐      │
│  │            Quality Assessment                          │      │
│  │                                                        │      │
│  │  - Calculate PVE (per-vertex error)                   │      │
│  │  - Compute anthropometric error                       │      │
│  │  - Flag if error > threshold                          │      │
│  │  - Suggest additional photos if needed                │      │
│  └─────────────────────┬──────────────────────────────────┘      │
│                        │                                         │
│                        ▼                                         │
│                   [Output: Fitted Model]                         │
│                   {                                              │
│                     "phenotype_params": {...},                   │
│                     "pose_params": Tensor,                       │
│                     "pve": 15.2mm,                               │
│                     "vertices": Tensor                           │
│                   }                                              │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 4. Data Architecture

### 4.1 Database Schema (PostgreSQL)

```sql
-- Users table
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user' CHECK (role IN ('user', 'researcher', 'admin')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    INDEX idx_email (email)
);

-- Subjects table
CREATE TABLE subjects (
    subject_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    name VARCHAR(255), -- Nullable for anonymization
    date_of_birth DATE,
    gender VARCHAR(50) CHECK (gender IN ('male', 'female', 'other', 'unspecified')),
    anonymized BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
);

-- Fitted models table
CREATE TABLE fitted_models (
    model_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_id UUID NOT NULL REFERENCES subjects(subject_id) ON DELETE CASCADE,
    phenotype_parameters JSONB NOT NULL, -- {"gender": 0.5, "age": 0.3, ...}
    pose_parameters BYTEA, -- Binary tensor storage
    local_changes JSONB, -- {"macro_detail_01": 0.1, ...}
    fitting_error FLOAT, -- PVE in mm
    processing_time FLOAT, -- Seconds
    num_images_used INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_subject_id (subject_id),
    INDEX idx_created_at (created_at)
);

-- Measurements table
CREATE TABLE measurements (
    measurement_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID NOT NULL REFERENCES fitted_models(model_id) ON DELETE CASCADE,
    measurement_type VARCHAR(100) NOT NULL, -- 'height', 'waist_circumference', etc.
    value FLOAT NOT NULL,
    unit VARCHAR(50) NOT NULL, -- 'meters', 'kilograms', etc.
    confidence FLOAT, -- 0.0-1.0
    extracted_from VARCHAR(50) CHECK (extracted_from IN ('image', 'model')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_model_id (model_id),
    INDEX idx_measurement_type (measurement_type)
);

-- Sessions table (for active processing sessions)
CREATE TABLE sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    subject_id UUID REFERENCES subjects(subject_id) ON DELETE SET NULL,
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'expired', 'completed')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_expires_at (expires_at)
);

-- Audit log table
CREATE TABLE audit_log (
    log_id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
    action VARCHAR(255) NOT NULL, -- 'subject_create', 'model_fit', 'data_export', etc.
    resource_type VARCHAR(100), -- 'subject', 'model', etc.
    resource_id UUID,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT,
    INDEX idx_user_id (user_id),
    INDEX idx_timestamp (timestamp),
    INDEX idx_action (action)
);
```

### 4.2 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      Data Flow Diagram                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌────────┐                                                     │
│  │ User   │                                                     │
│  │ Upload │                                                     │
│  │ Photo  │                                                     │
│  └────┬───┘                                                     │
│       │                                                         │
│       ▼                                                         │
│  ┌────────────────┐                                             │
│  │ 1. HTTPS POST  │──────────────────┐                         │
│  │ /api/v1/fit    │                  │                         │
│  │ Content-Type:  │                  │                         │
│  │ multipart/form │                  ▼                         │
│  └────────────────┘         ┌─────────────────┐                │
│                             │  API Gateway    │                │
│                             │  (Nginx)        │                │
│                             └────────┬────────┘                │
│                                      │                         │
│                                      ▼                         │
│                             ┌─────────────────┐                │
│                             │ 2. FastAPI      │                │
│                             │ Request Handler │                │
│                             └────────┬────────┘                │
│                                      │                         │
│                 ┌────────────────────┼───────────────────┐     │
│                 │                    │                   │     │
│                 ▼                    ▼                   ▼     │
│       ┌──────────────┐     ┌──────────────┐    ┌──────────────┐│
│       │ 3a. Store in │     │ 3b. Validate │    │ 3c. Create   ││
│       │ RAM disk     │     │ Auth (JWT)   │    │ Session      ││
│       │ (tmpfs)      │     │              │    │ (Redis)      ││
│       └──────┬───────┘     └──────────────┘    └──────────────┘│
│              │                                                  │
│              ▼                                                  │
│       ┌──────────────────┐                                     │
│       │ 4. Call Vision   │                                     │
│       │ Processing       │                                     │
│       │ Service (gRPC)   │                                     │
│       └──────┬───────────┘                                     │
│              │                                                  │
│              ▼                                                  │
│       ┌──────────────────────┐                                 │
│       │ 5. Vision Pipeline   │                                 │
│       │ - Pose detection     │                                 │
│       │ - Depth estimation   │                                 │
│       │ - Measurements       │                                 │
│       └──────┬───────────────┘                                 │
│              │                                                  │
│              ▼                                                  │
│       ┌──────────────────────┐                                 │
│       │ 6. Return            │                                 │
│       │ Measurements JSON    │                                 │
│       └──────┬───────────────┘                                 │
│              │                                                  │
│              ▼                                                  │
│       ┌──────────────────────┐                                 │
│       │ 7. Call Model        │                                 │
│       │ Fitting Service      │                                 │
│       │ (gRPC)               │                                 │
│       └──────┬───────────────┘                                 │
│              │                                                  │
│              ▼                                                  │
│       ┌──────────────────────┐                                 │
│       │ 8. Anny Fitting      │                                 │
│       │ - Phenotype mapping  │                                 │
│       │ - Iterative optimize │                                 │
│       │ - Pose refinement    │                                 │
│       └──────┬───────────────┘                                 │
│              │                                                  │
│              ▼                                                  │
│       ┌──────────────────────┐                                 │
│       │ 9. Return Fitted     │                                 │
│       │ Model (vertices,     │                                 │
│       │ params, error)       │                                 │
│       └──────┬───────────────┘                                 │
│              │                                                  │
│              ▼                                                  │
│       ┌──────────────────────┐                                 │
│       │ 10. Store to DB      │                                 │
│       │ - Subject metadata   │                                 │
│       │ - Fitted params      │                                 │
│       │ - Measurements       │                                 │
│       └──────┬───────────────┘                                 │
│              │                                                  │
│              ▼                                                  │
│       ┌──────────────────────┐                                 │
│       │ 11. DELETE Photo     │                                 │
│       │ from RAM disk        │                                 │
│       │ (secure wipe)        │                                 │
│       └──────┬───────────────┘                                 │
│              │                                                  │
│              ▼                                                  │
│       ┌──────────────────────┐                                 │
│       │ 12. WebSocket Notify │                                 │
│       │ "Processing complete"│                                 │
│       └──────┬───────────────┘                                 │
│              │                                                  │
│              ▼                                                  │
│       ┌──────────────────────┐                                 │
│       │ 13. Return Model ID  │                                 │
│       │ to Frontend          │                                 │
│       └──────┬───────────────┘                                 │
│              │                                                  │
│              ▼                                                  │
│  ┌──────────────────┐                                          │
│  │ 14. Frontend     │                                          │
│  │ GET /api/v1/     │                                          │
│  │ models/:id       │                                          │
│  └────┬─────────────┘                                          │
│       │                                                         │
│       ▼                                                         │
│  ┌──────────────────┐                                          │
│  │ 15. Reconstruct  │                                          │
│  │ 3D mesh from     │                                          │
│  │ stored params    │                                          │
│  └────┬─────────────┘                                          │
│       │                                                         │
│       ▼                                                         │
│  ┌──────────────────┐                                          │
│  │ 16. Render in    │                                          │
│  │ Three.js viewer  │                                          │
│  └──────────────────┘                                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Deployment Architecture

### 5.1 Docker Compose Development

```yaml
# docker-compose.yml (Development)
version: '3.8'

services:
  nginx:
    image: nginx:1.25-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - backend

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    volumes:
      - ./frontend/src:/app/src
    environment:
      - NODE_ENV=development

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/anny_fitter
      - REDIS_URL=redis://redis:6379/0
      - JWT_SECRET=${JWT_SECRET}
    depends_on:
      - postgres
      - redis
    volumes:
      - ./backend:/app

  vision-service:
    build:
      context: ./services/vision
      dockerfile: Dockerfile
    ports:
      - "8001:8001"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  fitting-service:
    build:
      context: ./services/fitting
      dockerfile: Dockerfile
    ports:
      - "8002:8002"
    volumes:
      - ./models:/models
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: anny_fitter
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    volumes:
      - minio_data:/data
    ports:
      - "9000:9000"
      - "9001:9001"

volumes:
  postgres_data:
  minio_data:
```

### 5.2 Production Deployment (Kubernetes Overview)

**Deployment Strategy**: Blue-Green deployment with Kubernetes

**Key Components**:
- **Ingress Controller**: NGINX Ingress with TLS (Let's Encrypt)
- **API Deployment**: 3 replicas (auto-scaling 2-10)
- **Vision Service**: 2 replicas with GPU node affinity
- **Fitting Service**: 2 replicas with GPU node affinity
- **Database**: PostgreSQL StatefulSet with persistent volume
- **Cache**: Redis Deployment with persistent volume
- **Monitoring**: Prometheus + Grafana
- **Logging**: ELK Stack (Elasticsearch, Logstash, Kibana)

**Resource Allocation** (per node):
- **Frontend**: 512MB RAM, 0.5 CPU
- **Backend**: 2GB RAM, 2 CPU
- **Vision**: 4GB RAM, 2 CPU, 4GB GPU
- **Fitting**: 8GB RAM, 4 CPU, 8GB GPU
- **Database**: 8GB RAM, 4 CPU
- **Redis**: 2GB RAM, 1 CPU

---

## 6. Security Architecture

### 6.1 Authentication Flow

```
┌────────────────────────────────────────────────────────────┐
│                 Authentication Flow                        │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  1. User Login Request                                     │
│     POST /api/v1/auth/login                                │
│     { "email": "user@example.com", "password": "***" }     │
│                │                                           │
│                ▼                                           │
│  2. Backend validates credentials                          │
│     - Hash password with bcrypt                            │
│     - Compare with database                                │
│                │                                           │
│                ▼                                           │
│  3. Generate JWT token                                     │
│     - Payload: { user_id, role, exp }                      │
│     - Sign with SECRET_KEY (HS256)                         │
│     - Expiry: 24 hours                                     │
│                │                                           │
│                ▼                                           │
│  4. Return JWT + Refresh Token                             │
│     {                                                      │
│       "access_token": "eyJhbGciOi...",                     │
│       "refresh_token": "uuid",                             │
│       "expires_in": 86400                                  │
│     }                                                      │
│                │                                           │
│                ▼                                           │
│  5. Client stores in localStorage                          │
│     - Access token in memory (security best practice)     │
│     - Refresh token in httpOnly cookie                    │
│                │                                           │
│                ▼                                           │
│  6. Subsequent requests include JWT                        │
│     Authorization: Bearer eyJhbGciOi...                    │
│                │                                           │
│                ▼                                           │
│  7. Backend validates JWT                                  │
│     - Verify signature                                     │
│     - Check expiry                                         │
│     - Extract user_id and role                             │
│                │                                           │
│                ▼                                           │
│  8. Proceed with request                                   │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### 6.2 Data Privacy Measures

**Photo Handling**:
1. Upload to RAM disk (`/dev/shm` or tmpfs)
2. Process in memory (no disk writes)
3. Secure deletion (overwrite with zeros)
4. No logging of photo content

**Encryption**:
- **In Transit**: TLS 1.3 (all HTTPS traffic)
- **At Rest**: AES-256 for database (PostgreSQL encryption)
- **Secrets**: HashiCorp Vault or AWS Secrets Manager

**Access Control**:
- **RBAC**: User, Researcher, Admin roles
- **Row-Level Security**: Users only access own subjects
- **API Rate Limiting**: 100 requests/hour per user

**Compliance**:
- **GDPR**: Right to deletion, data portability, consent management
- **HIPAA** (optional): PHI encryption, audit logging, access controls

---

## 7. Monitoring & Observability

### 7.1 Metrics Collection

**Application Metrics** (Prometheus):
- Request rate (requests/second)
- Response latency (p50, p95, p99)
- Error rate (4xx, 5xx)
- Processing time (vision, fitting)
- GPU utilization (%)
- Database connection pool usage

**Business Metrics**:
- Subjects processed per day
- Average fitting error (PVE)
- Multi-image usage rate
- Export format distribution

**Dashboards** (Grafana):
- System health overview
- API performance
- GPU resource utilization
- User activity heatmap

### 7.2 Logging Strategy

**Structured Logging** (JSON format):
```json
{
  "timestamp": "2025-11-10T14:30:00Z",
  "level": "INFO",
  "service": "backend-api",
  "trace_id": "abc123",
  "user_id": "uuid",
  "action": "model_fitting",
  "duration_ms": 8500,
  "error": null
}
```

**Log Aggregation**: ELK Stack (Elasticsearch, Logstash, Kibana)

**Distributed Tracing**: OpenTelemetry (trace requests across services)

---

## 8. Scalability Strategy

### 8.1 Horizontal Scaling

**Stateless Services** (easy to scale):
- Backend API: Add more replicas (Kubernetes HPA)
- Frontend: CDN distribution (CloudFlare, Akamai)

**Stateful Services** (scaling strategies):
- PostgreSQL: Read replicas for queries, write to primary
- Redis: Redis Cluster (sharding)

### 8.2 Vertical Scaling

**GPU Services**:
- Vision: Scale to larger GPU instances (V100 → A100)
- Fitting: Multi-GPU parallelization (future enhancement)

### 8.3 Caching Strategy

**Redis Caching**:
- Session data (30-minute TTL)
- Frequently accessed subjects (1-hour TTL)
- API rate limit counters

**CDN Caching**:
- Frontend static assets (1-year TTL)
- Exported 3D models (24-hour TTL)

---

## 9. Error Handling & Recovery

### 9.1 Error Categories

| Error Type | HTTP Code | Recovery Strategy |
|------------|-----------|------------------|
| Invalid photo format | 400 | Return user-friendly message |
| Pose detection failure | 422 | Suggest better photo, provide example |
| Fitting convergence failure | 500 | Return default model, flag for review |
| GPU out of memory | 503 | Retry with CPU fallback |
| Database timeout | 503 | Retry with exponential backoff |

### 9.2 Circuit Breaker Pattern

**Vision Service Circuit Breaker**:
- **Threshold**: 5 failures in 60 seconds
- **Action**: Open circuit, return cached default
- **Recovery**: Half-open after 30 seconds, test single request

---

## 10. Future Architecture Enhancements

**Phase 2 Enhancements**:
1. **Microservices Migration**: Split into independent services with API gateway (Kong, AWS API Gateway)
2. **Event-Driven Architecture**: Use message queue (RabbitMQ, Kafka) for async processing
3. **Multi-Tenancy**: Separate database schemas per organization
4. **Global CDN**: Distribute frontend and assets worldwide (CloudFront, Fastly)

**Phase 3 Enhancements**:
1. **Real-Time Video Processing**: WebRTC for live camera feed
2. **Edge Computing**: Run vision processing on device (ONNX models)
3. **Federated Learning**: Train models across users without data centralization
4. **Blockchain**: Immutable audit trail for research compliance

---

## Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-11-10 | Architecture Team | Initial architecture design |
