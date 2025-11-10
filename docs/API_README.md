# Anny Body Fitter - FastAPI Backend Documentation

## Overview

Comprehensive REST API for the photo-to-3D-model fitting service using the Anny parametric body model. This API provides endpoints for managing subjects, uploading photos, triggering model fitting, and retrieving fitted 3D model parameters.

## Quick Start

### Installation

```bash
# Install API dependencies
pip install -r requirements-api.txt

# Copy environment configuration
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### Running the Server

```bash
# Development mode (with auto-reload)
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Access Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## API Endpoints

### Health & Info

#### `GET /` - API Information
Returns basic API information and status.

**Response:**
```json
{
  "name": "Anny Body Fitter API",
  "version": "1.0.0",
  "status": "operational",
  "docs": "/docs"
}
```

#### `GET /health` - Health Check
Health check endpoint for monitoring.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": 1699632000.0
}
```

---

### Subject Management

#### `POST /api/v1/subjects` - Create Subject

Create a new subject for body fitting.

**Request Body:**
```json
{
  "name": "Subject_001",
  "age": 25,
  "gender": "male",
  "height_cm": 175.0,
  "weight_kg": 70.0,
  "notes": "Athletic build"
}
```

**Response:** `201 Created`
```json
{
  "id": "subj_abc123xyz",
  "name": "Subject_001",
  "age": 25,
  "gender": "male",
  "height_cm": 175.0,
  "weight_kg": 70.0,
  "notes": "Athletic build",
  "photo_count": 0,
  "has_fitted_model": false,
  "created_at": "2025-11-10T10:00:00",
  "updated_at": "2025-11-10T10:00:00"
}
```

#### `GET /api/v1/subjects` - List Subjects

Get paginated list of all subjects.

**Query Parameters:**
- `page` (int, default: 1): Page number
- `page_size` (int, default: 20, max: 100): Items per page
- `search` (string, optional): Search by name

**Response:** `200 OK`
```json
{
  "subjects": [...],
  "total": 42,
  "page": 1,
  "page_size": 20
}
```

#### `GET /api/v1/subjects/{subject_id}` - Get Subject

Retrieve detailed information about a specific subject.

**Response:** `200 OK`
```json
{
  "id": "subj_abc123xyz",
  "name": "Subject_001",
  "age": 25,
  ...
}
```

#### `PATCH /api/v1/subjects/{subject_id}` - Update Subject

Update subject information. Only provided fields will be updated.

**Request Body:**
```json
{
  "age": 26,
  "notes": "Updated notes"
}
```

**Response:** `200 OK`

#### `DELETE /api/v1/subjects/{subject_id}` - Delete Subject

Delete a subject and all associated data.

**Query Parameters:**
- `permanent` (bool, default: false): Permanently delete (bypass soft delete)

**Response:** `204 No Content`

**Note:** By default performs soft delete for data recovery. Set `permanent=true` for GDPR compliance.

---

### Photo Management

#### `POST /api/v1/subjects/{subject_id}/photos` - Upload Photos

Upload one or more photos for model fitting.

**Request:** Multipart form data
- `files`: Image files (JPEG, PNG)
- `metadata`: JSON array of photo metadata

**Example using curl:**
```bash
curl -X POST "http://localhost:8000/api/v1/subjects/subj_123/photos" \
  -F "files=@front.jpg" \
  -F 'metadata=[{"photo_type": "front", "camera_height_cm": 150.0}]'
```

**Response:** `201 Created`
```json
[
  {
    "id": "photo_xyz789",
    "subject_id": "subj_abc123",
    "filename": "photo_xyz789.jpg",
    "photo_type": "front",
    "file_size_bytes": 1048576,
    "width_px": 1920,
    "height_px": 1080,
    "camera_height_cm": 150.0,
    "distance_cm": 300.0,
    "notes": "Good lighting",
    "uploaded_at": "2025-11-10T10:05:00"
  }
]
```

#### `GET /api/v1/subjects/{subject_id}/photos` - List Photos

Get all photos for a subject.

**Response:** `200 OK`
```json
[...]
```

---

### Model Fitting

#### `POST /api/v1/subjects/{subject_id}/fit` - Trigger Fitting

Start background task to fit 3D model to photos.

**Request Body:**
```json
{
  "optimization_iterations": 100,
  "use_shape_prior": true,
  "use_pose_prior": true,
  "lambda_shape": 0.01,
  "lambda_pose": 0.01
}
```

**Response:** `202 Accepted`
```json
{
  "subject_id": "subj_abc123xyz",
  "status": "pending",
  "task_id": "task_xyz789",
  "started_at": "2025-11-10T10:15:00"
}
```

**Note:** This is an asynchronous operation. Use the status endpoint to track progress.

#### `GET /api/v1/subjects/{subject_id}/fit/status` - Get Fitting Status

Check status of ongoing fitting task.

**Response:** `200 OK`
```json
{
  "status": "processing",
  "progress": 45.2,
  "message": null,
  "estimated_time_remaining": 30.5
}
```

**Status Values:**
- `pending`: Task queued
- `processing`: Optimization in progress
- `completed`: Fitting completed successfully
- `failed`: Fitting failed (check message)

#### `GET /api/v1/subjects/{subject_id}/model` - Get Fitted Model

Retrieve fitted 3D model parameters.

**Response:** `200 OK`
```json
{
  "shape_params": [0.1, -0.2, 0.3, ...],
  "pose_params": [0.0, 0.0, ...],
  "global_rotation": [0.0, 0.0, 0.0],
  "global_translation": [0.0, 0.0, 0.0],
  "num_vertices": 13776,
  "num_faces": 27386
}
```

**Note:** Only available after fitting has completed successfully.

---

### Performance Metrics

#### `POST /api/v1/subjects/{subject_id}/metrics` - Add Metrics

Add performance metrics for a fitted model.

**Request Body:**
```json
{
  "metrics": {
    "accuracy_score": 0.95,
    "precision": 0.92,
    "recall": 0.93,
    "f1_score": 0.925,
    "mean_error_cm": 1.2,
    "max_error_cm": 4.5
  },
  "ground_truth_available": true,
  "validation_method": "3D scanner comparison",
  "notes": "High quality validation",
  "custom_metrics": {
    "joint_error": 0.8,
    "volume_difference": 2.3
  }
}
```

**Response:** `201 Created`

**Note:** Requires a fitted model to exist for the subject.

#### `GET /api/v1/subjects/{subject_id}/metrics` - Get Metrics

Get all performance metrics for a subject.

**Response:** `200 OK`
```json
[...]
```

---

## Authentication

### Development Mode

For development, authentication can be disabled by setting:

```bash
DISABLE_AUTH=true
```

### Production Mode

In production, all endpoints (except `/`, `/health`, `/docs`) require JWT authentication.

**Authorization Header:**
```
Authorization: Bearer <your-jwt-token>
```

### Implementing User Authentication

The middleware is ready for JWT authentication. You need to:

1. Implement user registration/login endpoints
2. Use `create_access_token()` to generate tokens
3. Users will include tokens in requests
4. Middleware automatically validates and attaches user info

**Example implementation:**
```python
from src.api.middleware.auth import create_access_token

# In your login endpoint
token = create_access_token(data={"id": user.id, "username": user.username})
```

---

## Features

### Async Request Handling

All endpoints are fully asynchronous for optimal performance:
- Non-blocking database operations
- Concurrent request processing
- Background task support for long-running operations

### File Upload Validation

Photo uploads include comprehensive validation:
- File type checking (JPEG, PNG only)
- Size limits (configurable via environment)
- Image dimension extraction
- Metadata validation

### Background Tasks

Long-running operations (model fitting) run in background:
- Immediate response to client
- Status tracking via task ID
- Error handling and recovery

### CORS Configuration

CORS is enabled for cross-origin requests. Configure allowed origins in `.env`:

```bash
ALLOWED_ORIGINS=http://localhost:3000,https://your-domain.com
```

### Rate Limiting

Built-in rate limiting prevents abuse:
- 60 requests per minute per IP
- 1000 requests per hour per IP
- Configurable via environment variables

**Response Headers:**
```
X-RateLimit-Minute-Limit: 60
X-RateLimit-Minute-Remaining: 45
X-RateLimit-Hour-Limit: 1000
X-RateLimit-Hour-Remaining: 950
```

### Error Handling

Comprehensive error handling with proper HTTP status codes:

- `400 Bad Request`: Invalid input data
- `401 Unauthorized`: Missing/invalid authentication
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

**Error Response Format:**
```json
{
  "error": "Error type",
  "detail": "Detailed error message"
}
```

---

## Database

### SQLite Database

The API uses SQLite for data storage:
- Path: `data/anny_fitter.db` (configurable)
- Automatic schema creation on startup
- Full async support via aiosqlite

### Schema

**Tables:**
- `subjects`: Subject information
- `photos`: Uploaded photos metadata
- `fitting_tasks`: Fitting task tracking
- `model_parameters`: Fitted 3D model parameters
- `metrics`: Performance metrics

### Privacy & GDPR Compliance

- Soft delete by default (recovery possible)
- Hard delete option for permanent removal
- All associated data deleted on subject deletion
- `deleted_at` timestamp for audit trail

---

## Testing

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run all API tests
pytest tests/test_api/ -v

# Run specific test file
pytest tests/test_api/test_subjects.py -v

# Run with coverage
pytest tests/test_api/ --cov=src.api --cov-report=html
```

### Test Coverage

Comprehensive test suite includes:
- Subject CRUD operations
- Photo upload and validation
- Model fitting workflow
- Metrics management
- Error handling
- Edge cases

---

## Configuration

### Environment Variables

All configuration via `.env` file:

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=false

# Database
DATABASE_PATH=data/anny_fitter.db
PHOTO_STORAGE_PATH=data/photos

# Authentication
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
DISABLE_AUTH=false

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# CORS
ALLOWED_ORIGINS=http://localhost:3000

# Logging
LOG_LEVEL=INFO

# Limits
MAX_UPLOAD_SIZE_MB=10
MAX_PHOTOS_PER_SUBJECT=20
```

---

## Integration with Anny Model

### TODO: Model Fitting Integration

The fitting service includes a placeholder for Anny model integration. To complete:

1. **Load photos from storage**
   ```python
   # In fitting_service.py _run_fitting_task()
   photo_paths = await self._load_subject_photos(subject_id)
   ```

2. **Initialize Anny model**
   ```python
   from anny import AnnyBody
   model = AnnyBody()
   ```

3. **Run optimization**
   ```python
   fitted_params = model.fit_to_images(
       image_paths=photo_paths,
       iterations=fitting_request.optimization_iterations,
       shape_prior=fitting_request.use_shape_prior,
       pose_prior=fitting_request.use_pose_prior
   )
   ```

4. **Extract and save parameters**
   ```python
   model_params = ModelParameters(
       shape_params=fitted_params['beta'].tolist(),
       pose_params=fitted_params['theta'].tolist(),
       ...
   )
   ```

---

## Deployment

### Production Checklist

- [ ] Change `JWT_SECRET_KEY` to secure random value
- [ ] Set `DISABLE_AUTH=false`
- [ ] Configure `ALLOWED_ORIGINS` for your domain
- [ ] Set up HTTPS/TLS
- [ ] Configure proper database backups
- [ ] Set up monitoring and logging
- [ ] Review rate limits for your use case
- [ ] Configure file upload limits
- [ ] Set up reverse proxy (nginx/caddy)

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements-api.txt .
RUN pip install -r requirements-api.txt

COPY src/ ./src/
COPY .env .env

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Systemd Service

```ini
[Unit]
Description=Anny Body Fitter API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/Anny-body-fitter
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/uvicorn src.api.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## API Client Examples

### Python Client

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Create subject
response = requests.post(
    f"{BASE_URL}/subjects",
    json={
        "name": "John Doe",
        "age": 30,
        "height_cm": 180.0
    }
)
subject_id = response.json()["id"]

# Upload photo
with open("photo.jpg", "rb") as f:
    response = requests.post(
        f"{BASE_URL}/subjects/{subject_id}/photos",
        files={"files": f},
        data={"metadata": '[{"photo_type": "front"}]'}
    )

# Trigger fitting
response = requests.post(
    f"{BASE_URL}/subjects/{subject_id}/fit",
    json={"optimization_iterations": 100}
)
task_id = response.json()["task_id"]

# Check status
response = requests.get(f"{BASE_URL}/subjects/{subject_id}/fit/status")
print(response.json())

# Get fitted model
response = requests.get(f"{BASE_URL}/subjects/{subject_id}/model")
model_params = response.json()
```

### JavaScript/TypeScript Client

```typescript
const BASE_URL = 'http://localhost:8000/api/v1';

// Create subject
const response = await fetch(`${BASE_URL}/subjects`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    name: 'Jane Doe',
    age: 28,
    height_cm: 165.0
  })
});
const subject = await response.json();

// Upload photo
const formData = new FormData();
formData.append('files', photoFile);
formData.append('metadata', JSON.stringify([{photo_type: 'front'}]));

await fetch(`${BASE_URL}/subjects/${subject.id}/photos`, {
  method: 'POST',
  body: formData
});

// Trigger fitting
await fetch(`${BASE_URL}/subjects/${subject.id}/fit`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    optimization_iterations: 100,
    use_shape_prior: true
  })
});
```

---

## Performance Considerations

### Database Optimization

- Indexes on frequently queried fields
- Connection pooling for concurrent requests
- Async operations for non-blocking I/O

### File Storage

- Organized by subject ID for easy cleanup
- Configurable storage path
- Image dimension caching in database

### Background Tasks

- Long-running operations don't block requests
- Task status tracking for client updates
- Error recovery and logging

---

## Support & Documentation

- **Interactive API Docs**: http://localhost:8000/docs
- **OpenAPI Spec**: http://localhost:8000/openapi.json
- **Source Code**: `/home/devuser/workspace/Anny-body-fitter/src/api/`
- **Tests**: `/home/devuser/workspace/Anny-body-fitter/tests/test_api/`

---

## License

Copyright (c) 2025 - Same license as Anny Body project (Apache 2.0)
