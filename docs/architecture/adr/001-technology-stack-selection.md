# ADR 001: Technology Stack Selection

## Status
**ACCEPTED**

## Context
We need to select a technology stack for the photo-to-3D-model fitting application that balances:
- Development speed and team expertise
- Performance requirements (GPU processing, real-time 3D rendering)
- Ecosystem maturity and community support
- Cost-effectiveness
- Future scalability

## Decision

### Backend: FastAPI (Python)
**Selected**: FastAPI with Uvicorn
**Alternatives Considered**: Flask, Django, Node.js (Express)

**Rationale**:
- Native integration with PyTorch (Anny model is PyTorch-based)
- Async/await support for concurrent requests
- Automatic OpenAPI documentation generation
- Type hints with Pydantic for request validation
- High performance (comparable to Node.js with Starlette)
- Strong Python ML ecosystem

**Trade-offs**:
- (+) Best integration with PyTorch/NumPy/SciPy
- (+) Async support for WebSocket and concurrent processing
- (-) GIL limitations (mitigated by multi-process workers)

### Frontend: React + Three.js
**Selected**: React 18 with Three.js (r158+)
**Alternatives Considered**: Vue.js, Angular, Svelte

**Rationale**:
- Largest component ecosystem for UI
- Three.js is de facto standard for WebGL rendering
- React Fiber reconciliation works well with 3D scene updates
- Strong TypeScript support
- Excellent mobile browser compatibility

**Trade-offs**:
- (+) Mature 3D rendering ecosystem
- (+) Large community and resources
- (-) Slightly larger bundle size than alternatives

### Database: PostgreSQL
**Selected**: PostgreSQL 16
**Alternatives Considered**: MySQL, MongoDB, SQLite

**Rationale**:
- JSONB support for flexible phenotype parameter storage
- Strong ACID guarantees for metadata
- Excellent performance with proper indexing
- Built-in full-text search
- Open-source with commercial support options

**Trade-offs**:
- (+) JSONB eliminates need for separate NoSQL database
- (+) Robust transaction support
- (-) Requires proper tuning for high-concurrency writes

### Cache: Redis
**Selected**: Redis 7
**Alternatives Considered**: Memcached, Hazelcast

**Rationale**:
- Pub/sub for WebSocket communication
- Session storage with TTL
- Rate limiting counters
- Rich data structures (hashes, sets)
- Persistence options for critical cache data

**Trade-offs**:
- (+) Single solution for cache, sessions, and messaging
- (+) High performance in-memory operations
- (-) Memory-intensive (mitigated by eviction policies)

### Vision AI: MediaPipe
**Selected**: MediaPipe Holistic
**Alternatives Considered**: OpenPose, AlphaPose, MMPose

**Rationale**:
- Free and open-source
- Optimized for both CPU and GPU
- Cross-platform (web, mobile, desktop)
- Well-maintained by Google
- Integrated pose, face, and hand detection

**Trade-offs**:
- (+) Production-ready and actively maintained
- (+) Excellent performance on mobile/edge devices
- (-) Less customizable than research frameworks

### Containerization: Docker
**Selected**: Docker with Docker Compose (dev), Kubernetes (prod)
**Alternatives Considered**: Podman, bare metal

**Rationale**:
- Industry standard with extensive tooling
- Reproducible environments across dev/prod
- GPU passthrough support (NVIDIA Container Toolkit)
- Multi-stage builds for optimized images
- Kubernetes compatibility for orchestration

**Trade-offs**:
- (+) Simplifies deployment and scaling
- (+) Isolates dependencies
- (-) Slight performance overhead (negligible)

### Object Storage: MinIO (S3-compatible)
**Selected**: MinIO for self-hosted, AWS S3 for cloud
**Alternatives Considered**: File system, Ceph

**Rationale**:
- S3-compatible API (easy cloud migration)
- Self-hostable for privacy-sensitive deployments
- Built-in versioning and lifecycle policies
- High performance for large file uploads

**Trade-offs**:
- (+) Flexible deployment (on-prem or cloud)
- (+) Familiar S3 API
- (-) Requires separate service management

## Consequences

### Positive
1. **Unified Python Ecosystem**: Backend, vision, and fitting services share dependencies
2. **Modern Async Architecture**: FastAPI + Redis enable real-time progress updates
3. **Strong Typing**: Pydantic (backend) + TypeScript (frontend) catch errors early
4. **GPU Optimization**: PyTorch and MediaPipe leverage CUDA efficiently
5. **Open-Source Foundation**: No vendor lock-in, community-driven improvements

### Negative
1. **Multiple Languages**: Python (backend) + JavaScript (frontend) requires different expertise
2. **GPU Dependency**: Fitting service requires NVIDIA GPU (limits cloud provider options)
3. **Complexity**: Docker Compose + Kubernetes learning curve for deployment

### Mitigation Strategies
1. **Team Training**: Provide Python and React training resources
2. **Cloud GPU Providers**: Use AWS (P3 instances), GCP (T4/V100), or Azure (NC-series)
3. **Deployment Automation**: Use Terraform/Ansible for infrastructure as code

## Compliance
- **GDPR**: PostgreSQL encryption at rest, audit logging
- **HIPAA** (optional): Use AWS HIPAA-eligible services, enable CloudTrail
- **Accessibility**: React component library with WCAG 2.1 AA compliance

## Alternatives

### Alternative 1: Full JavaScript Stack (Node.js + TensorFlow.js)
**Rejected Reason**: TensorFlow.js lacks feature parity with PyTorch for Anny model, weaker ML ecosystem

### Alternative 2: Django REST Framework
**Rejected Reason**: Synchronous by default (async support is newer), heavier framework than needed

### Alternative 3: MongoDB for Database
**Rejected Reason**: Weaker consistency guarantees, JSONB in PostgreSQL provides similar flexibility

## References
- [FastAPI Performance Benchmarks](https://fastapi.tiangolo.com/)
- [Three.js Documentation](https://threejs.org/docs/)
- [PostgreSQL JSONB Performance](https://www.postgresql.org/docs/current/datatype-json.html)
- [MediaPipe Solutions](https://google.github.io/mediapipe/)

## Revision History
| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-10 | Architecture Team | Initial decision |
