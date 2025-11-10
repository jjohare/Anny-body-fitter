# Database Schema Documentation

## Overview

The Anny Body Fitter database schema manages subject data, measurements, model parameters, performance metrics, photo records, and fitting sessions. The schema is designed with privacy, audit trails, and efficient querying in mind.

## Entity Relationship Diagram

```
Subject (1) ──┬── (N) Measurements
              ├── (N) ModelParameters
              ├── (N) PerformanceMetrics
              ├── (N) PhotoRecords
              └── (N) Sessions
```

## Tables

### 1. Subjects
**Primary entity representing a person being fitted.**

| Column | Type | Description | Privacy |
|--------|------|-------------|---------|
| id | Integer | Primary key | - |
| name | String(255) | Subject name | **Encrypted** |
| date_of_birth | DateTime | Date of birth | **Encrypted** |
| is_active | Boolean | Soft delete flag | - |
| notes | Text | Additional notes | - |
| created_at | DateTime | Creation timestamp | - |
| updated_at | DateTime | Last update timestamp | - |

**Indexes:**
- `idx_subject_active_created` on (is_active, created_at)
- Primary key on id
- Index on name

### 2. Measurements
**Body measurements for subjects.**

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| subject_id | Integer | Foreign key to subjects |
| height | Float | Height in cm |
| weight | Float | Weight in kg |
| chest_circumference | Float | Chest circumference in cm |
| waist_circumference | Float | Waist circumference in cm |
| hip_circumference | Float | Hip circumference in cm |
| inseam | Float | Inseam in cm |
| shoulder_width | Float | Shoulder width in cm |
| arm_length | Float | Arm length in cm |
| leg_length | Float | Leg length in cm |
| neck_circumference | Float | Neck circumference in cm |
| custom_measurements | Text | JSON-encoded custom measurements |
| measurement_date | DateTime | When measured |
| measured_by | String(255) | Who performed measurement |
| notes | Text | Additional notes |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

**Indexes:**
- `idx_measurement_subject_date` on (subject_id, measurement_date)
- Foreign key on subject_id with CASCADE delete

### 3. ModelParameters
**Anny phenotype parameters for 3D body modeling.**

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| subject_id | Integer | Foreign key to subjects |
| height_param | Float | Height parameter |
| weight_param | Float | Weight parameter |
| chest_param | Float | Chest parameter |
| waist_param | Float | Waist parameter |
| hip_param | Float | Hip parameter |
| shape_param_1-5 | Float | Shape parameters (PCA or similar) |
| additional_params | Text | JSON-encoded additional parameters |
| model_version | String(50) | Model version identifier |
| confidence_score | Float | Fit confidence (0-1) |
| parameter_date | DateTime | When parameters generated |
| notes | Text | Additional notes |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

**Indexes:**
- `idx_model_param_subject_date` on (subject_id, parameter_date)
- Foreign key on subject_id with CASCADE delete

### 4. PerformanceMetrics
**Quality and performance metrics for fitting process.**

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| subject_id | Integer | Foreign key to subjects |
| fitting_error | Float | Overall fitting error |
| landmark_accuracy | Float | Landmark detection accuracy (0-1) |
| mesh_quality | Float | Mesh quality score (0-1) |
| processing_time | Float | Processing time in seconds |
| convergence_iterations | Integer | Number of iterations to converge |
| height_error | Float | Height error |
| volume_error | Float | Volume error |
| surface_area_error | Float | Surface area error |
| custom_metrics | Text | JSON-encoded custom metrics |
| metric_date | DateTime | When metrics recorded |
| metric_type | String(100) | Type of metric (e.g., 'initial_fit') |
| notes | Text | Additional notes |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

**Indexes:**
- `idx_perf_metric_subject_date` on (subject_id, metric_date)
- Foreign key on subject_id with CASCADE delete

### 5. PhotoRecords
**Metadata for uploaded photos (NOT image data).**

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| subject_id | Integer | Foreign key to subjects |
| filename | String(255) | Original filename |
| file_path | String(512) | Path to stored image |
| file_size | Integer | File size in bytes |
| mime_type | String(100) | MIME type |
| photo_type | String(50) | Type (e.g., 'front', 'side', 'back') |
| resolution | String(50) | Image resolution |
| is_processed | Boolean | Processing status flag |
| processing_status | String(50) | Status (e.g., 'pending', 'completed') |
| file_hash | String(64) | SHA-256 hash for integrity |
| capture_date | DateTime | When photo taken |
| upload_date | DateTime | When photo uploaded |
| notes | Text | Additional notes |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

**Indexes:**
- `idx_photo_subject_upload` on (subject_id, upload_date)
- `idx_photo_type_processed` on (photo_type, is_processed)
- Foreign key on subject_id with CASCADE delete

### 6. Sessions
**Fitting sessions linking multiple records.**

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| subject_id | Integer | Foreign key to subjects |
| session_name | String(255) | Session name |
| session_type | String(50) | Type (e.g., 'initial', 'follow_up') |
| session_status | String(50) | Status (e.g., 'in_progress', 'completed') |
| session_date | DateTime | Session date/time |
| duration | Integer | Duration in minutes |
| measurement_ids | Text | Linked measurement IDs (CSV or JSON) |
| model_parameter_ids | Text | Linked model parameter IDs |
| photo_record_ids | Text | Linked photo record IDs |
| performance_metric_ids | Text | Linked performance metric IDs |
| outcome_summary | Text | Summary of outcomes |
| next_steps | Text | Planned next steps |
| notes | Text | Additional notes |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

**Indexes:**
- `idx_session_subject_date` on (subject_id, session_date)
- `idx_session_status` on (session_status)
- Foreign key on subject_id with CASCADE delete

## Privacy Considerations

### Encrypted Fields
The following fields should be encrypted at the application level:
- `subjects.name`
- `subjects.date_of_birth`

### Implementation
Use application-level encryption (e.g., `cryptography.fernet`) before storing and after retrieving these fields.

Example:
```python
from cryptography.fernet import Fernet

# Generate key (store securely!)
key = Fernet.generate_key()
cipher = Fernet(key)

# Encrypt before storing
encrypted_name = cipher.encrypt(name.encode())

# Decrypt after retrieving
decrypted_name = cipher.decrypt(encrypted_name).decode()
```

## Audit Trail

All tables include:
- `created_at`: Automatically set on creation
- `updated_at`: Automatically updated on modification

These fields use `server_default=func.now()` and `onupdate=func.now()` for automatic management.

## Soft Deletes

The `subjects` table supports soft deletes via the `is_active` field. Instead of deleting records, set `is_active = False`.

## Cascade Behavior

All relationships use `CASCADE` delete, meaning:
- Deleting a subject deletes all related records
- This ensures referential integrity
- Use soft deletes on subjects to preserve history

## Database Support

The schema is compatible with:
- SQLite (development)
- PostgreSQL (production recommended)
- MySQL/MariaDB (with minor adjustments)

## Usage Examples

### Creating Tables
```python
from src.database.connection import create_tables

create_tables()
```

### CRUD Operations
```python
from src.database.connection import DatabaseManager
from src.database.crud import subject as subject_crud
from src.database.schemas import SubjectCreate

# Create a subject
with DatabaseManager() as db:
    subject_data = SubjectCreate(
        name="John Doe",
        date_of_birth=datetime(1990, 1, 1)
    )
    new_subject = subject_crud.create(db, subject_data)
    print(f"Created subject: {new_subject.id}")
```

### Querying Related Data
```python
from src.database.connection import DatabaseManager
from src.database.crud import measurement as measurement_crud

# Get all measurements for a subject
with DatabaseManager() as db:
    measurements = measurement_crud.get_by_subject(db, subject_id=1)
    for m in measurements:
        print(f"Height: {m.height}cm, Weight: {m.weight}kg")
```

## Migration Strategy

For production deployments, use Alembic for migrations:

```bash
# Initialize Alembic
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Initial schema"

# Apply migration
alembic upgrade head
```

## Performance Optimization

### Recommended Indexes
All primary indexes are already defined. Consider adding custom indexes for:
- Frequently queried fields
- Fields used in WHERE clauses
- Foreign keys used in JOINs

### Query Optimization
- Use `select_related` equivalents for relationship loading
- Implement pagination for large result sets
- Use `get_latest()` methods for most recent records

## Security Checklist

- [ ] Encrypt sensitive fields (name, DOB)
- [ ] Use secure key storage for encryption keys
- [ ] Implement access controls at application level
- [ ] Use environment variables for DATABASE_URL
- [ ] Enable SSL for database connections in production
- [ ] Regular backups of database
- [ ] Audit log access to sensitive data
- [ ] Use prepared statements (SQLAlchemy ORM handles this)
