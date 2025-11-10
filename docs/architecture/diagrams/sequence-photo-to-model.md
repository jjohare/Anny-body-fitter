# Sequence Diagram: Photo Upload to 3D Model

## End-to-End Processing Flow

```mermaid
sequenceDiagram
    actor User
    participant Frontend as React Frontend
    participant Gateway as Nginx Gateway
    participant API as FastAPI Backend
    participant RAM as RAM Disk (/dev/shm)
    participant Vision as Vision Service
    participant Fitting as Fitting Service
    participant DB as PostgreSQL
    participant Redis as Redis Cache
    participant WS as WebSocket

    User->>Frontend: Upload photo(s)
    Frontend->>Gateway: POST /api/v1/subjects/fit<br/>(multipart/form-data)
    Gateway->>API: Forward request (HTTPS)

    API->>API: Validate JWT token
    API->>Redis: Create session (30 min TTL)
    Redis-->>API: session_id

    API->>RAM: Write photo to tmpfs
    Note over RAM: /dev/shm/<uuid>.jpg<br/>(RAM-only, no disk)

    API->>WS: Publish "upload_complete"
    WS-->>Frontend: WebSocket update (10% progress)

    API->>Vision: gRPC call: ProcessImage(photo_path)
    activate Vision

    Vision->>Vision: Strip EXIF metadata
    Vision->>Vision: MediaPipe pose detection
    Vision->>Vision: Depth estimation (MiDaS)
    Vision->>Vision: Silhouette segmentation
    Vision->>Vision: Extract measurements<br/>(height, waist, shoulders)

    Vision-->>API: Return measurements JSON<br/>+ confidence scores
    deactivate Vision

    API->>WS: Publish "vision_complete"
    WS-->>Frontend: WebSocket update (40% progress)

    API->>API: Analytical phenotype mapping<br/>(measurements → initial params)

    API->>Fitting: gRPC call: FitModel(measurements, initial_phenotypes)
    activate Fitting

    Fitting->>Fitting: Load Anny model (GPU)
    Fitting->>Fitting: Reconstruct approximate mesh<br/>(depth + keypoints)
    Fitting->>Fitting: Age anchor search<br/>(try 4 age values)
    Fitting->>Fitting: Optimize phenotypes<br/>(Jacobian-based)
    Fitting->>Fitting: Refine pose<br/>(jointwise registration)
    Fitting->>Fitting: Calculate PVE error

    Fitting-->>API: Return fitted model<br/>(phenotypes, pose, vertices, PVE)
    deactivate Fitting

    API->>WS: Publish "fitting_complete"
    WS-->>Frontend: WebSocket update (80% progress)

    API->>DB: INSERT INTO subjects<br/>(name, DOB, gender)
    DB-->>API: subject_id

    API->>DB: INSERT INTO fitted_models<br/>(phenotypes, pose, PVE)
    DB-->>API: model_id

    API->>DB: INSERT INTO measurements<br/>(height, waist, etc.)

    API->>RAM: Secure delete photo<br/>(overwrite + remove)
    Note over RAM: Photo gone forever<br/>(no recovery possible)

    API->>Redis: Delete session

    API->>WS: Publish "processing_complete"
    WS-->>Frontend: WebSocket update (100% progress)

    API-->>Gateway: Return JSON response<br/>{model_id, subject_id, PVE}
    Gateway-->>Frontend: Forward response
    Frontend-->>User: Display success message

    User->>Frontend: Click "View 3D Model"
    Frontend->>Gateway: GET /api/v1/models/{model_id}
    Gateway->>API: Forward request

    API->>DB: SELECT phenotypes, pose FROM fitted_models
    DB-->>API: Return parameters (JSONB)

    API->>API: Reconstruct mesh<br/>(Anny forward pass)

    API-->>Frontend: Return mesh vertices + faces (JSON)
    Frontend->>Frontend: Render in Three.js viewer
    Frontend-->>User: Display interactive 3D model
```

## Key Timing Constraints

| Step | Expected Duration | Timeout |
|------|------------------|---------|
| Photo upload | <2s | 30s |
| Vision processing | 3-5s | 15s |
| Model fitting | 5-8s | 30s |
| Database writes | <500ms | 5s |
| Photo deletion | <100ms | 1s |
| **Total** | **8-15s** | **60s** |

## Error Handling Scenarios

### Scenario 1: Vision Processing Failure
```mermaid
sequenceDiagram
    API->>Vision: ProcessImage(photo_path)
    Vision-->>API: Error: "No human detected"
    API->>WS: Publish "error" event
    API->>RAM: Delete photo
    API-->>Frontend: 422 Unprocessable Entity<br/>{"error": "No person detected in photo"}
```

### Scenario 2: Fitting Convergence Failure
```mermaid
sequenceDiagram
    API->>Fitting: FitModel(measurements)
    Fitting->>Fitting: Optimization diverges
    Fitting-->>API: Partial result (high PVE)
    API->>DB: Store with flag: fitting_quality="poor"
    API-->>Frontend: 200 OK (with warning)<br/>{"model_id": "...", "warning": "Low quality fit, consider uploading clearer photo"}
```

## WebSocket Event Types

| Event | Payload | Description |
|-------|---------|-------------|
| `upload_complete` | `{progress: 0.1}` | Photo uploaded to RAM |
| `vision_processing` | `{progress: 0.2, stage: "pose_detection"}` | Vision pipeline stage |
| `vision_complete` | `{progress: 0.4, measurements: {...}}` | Measurements extracted |
| `fitting_started` | `{progress: 0.5}` | Optimization started |
| `fitting_complete` | `{progress: 0.8, pve: 15.2}` | Fitting finished |
| `processing_complete` | `{progress: 1.0, model_id: "..."}` | Ready to view |
| `error` | `{error: "...", code: 422}` | Processing failed |

## Concurrency & Parallelization

### Parallel Vision Processing (Multiple Images)
```mermaid
sequenceDiagram
    par Process Image 1
        API->>Vision: ProcessImage(img1)
        Vision-->>API: measurements1
    and Process Image 2
        API->>Vision: ProcessImage(img2)
        Vision-->>API: measurements2
    and Process Image 3
        API->>Vision: ProcessImage(img3)
        Vision-->>API: measurements3
    end

    API->>API: Fuse measurements<br/>(weighted average by confidence)
    API->>Fitting: FitModel(fused_measurements)
```

## Security Checkpoints

1. **Authentication**: JWT validation before processing
2. **Authorization**: User can only access own subjects
3. **Input Validation**: File type, size, content checks
4. **Rate Limiting**: Max 10 uploads per hour per user
5. **EXIF Stripping**: Remove metadata immediately
6. **Secure Deletion**: Overwrite photo data before removal
7. **Audit Logging**: Log all access to subject data

## Revision History
| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-11-10 | Initial sequence diagram |
