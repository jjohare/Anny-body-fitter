# Database Setup Guide

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Or install individually:

```bash
pip install sqlalchemy pydantic pytest cryptography
```

### 2. Configure Database

Set the `DATABASE_URL` environment variable:

```bash
# SQLite (development)
export DATABASE_URL="sqlite:///./anny_body_fitter.db"

# PostgreSQL (production)
export DATABASE_URL="postgresql://user:password@localhost/anny_db"

# MySQL
export DATABASE_URL="mysql+pymysql://user:password@localhost/anny_db"
```

### 3. Initialize Database

```python
from src.database.connection import create_tables

# Create all tables
create_tables()
```

Or use the CLI:

```bash
python -c "from src.database.connection import create_tables; create_tables()"
```

## Quick Start Examples

### Create a Subject

```python
from datetime import datetime
from src.database.connection import DatabaseManager
from src.database.crud import subject
from src.database.schemas import SubjectCreate

# Create subject
with DatabaseManager() as db:
    subject_data = SubjectCreate(
        name="John Doe",  # Will be encrypted in production
        date_of_birth=datetime(1990, 1, 1),
        notes="Initial subject for testing"
    )
    new_subject = subject.create(db, subject_data)
    print(f"Created subject ID: {new_subject.id}")
```

### Add Measurements

```python
from src.database.crud import measurement
from src.database.schemas import MeasurementCreate

with DatabaseManager() as db:
    measurement_data = MeasurementCreate(
        subject_id=1,
        height=180.5,
        weight=75.0,
        chest_circumference=95.0,
        waist_circumference=85.0,
        hip_circumference=100.0,
        measured_by="Dr. Smith"
    )
    new_measurement = measurement.create(db, measurement_data)
```

### Store Model Parameters

```python
from src.database.crud import model_parameter
from src.database.schemas import ModelParameterCreate

with DatabaseManager() as db:
    param_data = ModelParameterCreate(
        subject_id=1,
        height_param=1.0,
        weight_param=0.5,
        chest_param=0.8,
        model_version="v1.0",
        confidence_score=0.95
    )
    params = model_parameter.create(db, param_data)
```

### Create a Fitting Session

```python
from src.database.crud import session as session_crud
from src.database.schemas import SessionCreate

with DatabaseManager() as db:
    session_data = SessionCreate(
        subject_id=1,
        session_name="Initial Fitting",
        session_type="initial",
        session_status="in_progress",
        notes="First fitting session"
    )
    new_session = session_crud.create(db, session_data)
```

## Query Examples

### Get Latest Measurement

```python
from src.database.crud import measurement

with DatabaseManager() as db:
    latest = measurement.get_latest(db, subject_id=1)
    if latest:
        print(f"Height: {latest.height}cm, Weight: {latest.weight}kg")
```

### Get All Sessions for Subject

```python
from src.database.crud import session as session_crud

with DatabaseManager() as db:
    sessions = session_crud.get_by_subject(db, subject_id=1)
    for s in sessions:
        print(f"{s.session_name} - {s.session_status}")
```

### Track Unprocessed Photos

```python
from src.database.crud import photo_record

with DatabaseManager() as db:
    unprocessed = photo_record.get_unprocessed(db)
    for photo in unprocessed:
        print(f"Processing: {photo.filename}")
        # ... process photo ...
        photo_record.mark_processed(db, photo.id)
```

## Testing

### Run All Tests

```bash
pytest tests/test_database.py -v
```

### Run with Coverage

```bash
pytest tests/test_database.py --cov=src/database --cov-report=html
```

### Run Specific Test Class

```bash
pytest tests/test_database.py::TestCRUDSubject -v
```

## Privacy & Security

### Encrypting Sensitive Data

```python
from cryptography.fernet import Fernet
import os

# Generate and store key securely (one-time setup)
key = Fernet.generate_key()
# Store this key in environment variable or secure vault
os.environ['ENCRYPTION_KEY'] = key.decode()

# Encryption utility
class FieldEncryption:
    def __init__(self):
        key = os.getenv('ENCRYPTION_KEY').encode()
        self.cipher = Fernet(key)

    def encrypt(self, value: str) -> str:
        return self.cipher.encrypt(value.encode()).decode()

    def decrypt(self, value: str) -> str:
        return self.cipher.decrypt(value.encode()).decode()

# Usage
encryptor = FieldEncryption()

# Before storing
encrypted_name = encryptor.encrypt("John Doe")
subject_data = SubjectCreate(
    name=encrypted_name,
    date_of_birth=datetime(1990, 1, 1)
)

# After retrieving
decrypted_name = encryptor.decrypt(subject.name)
```

### Database Connection Security

```bash
# Use SSL for production databases
export DATABASE_URL="postgresql://user:pass@host/db?sslmode=require"
```

## Migrations with Alembic

### Setup

```bash
pip install alembic
alembic init alembic
```

Edit `alembic.ini`:
```ini
sqlalchemy.url = driver://user:pass@localhost/dbname
```

Edit `alembic/env.py`:
```python
from src.database.models import Base
target_metadata = Base.metadata
```

### Create Migration

```bash
alembic revision --autogenerate -m "Initial schema"
```

### Apply Migration

```bash
alembic upgrade head
```

### Rollback

```bash
alembic downgrade -1
```

## Performance Optimization

### Connection Pooling

For production with PostgreSQL:

```python
from sqlalchemy import create_engine

engine = create_engine(
    DATABASE_URL,
    pool_size=10,        # Maximum number of connections
    max_overflow=20,     # Maximum overflow connections
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600    # Recycle connections after 1 hour
)
```

### Query Optimization

```python
# Use eager loading for relationships
from sqlalchemy.orm import joinedload

with DatabaseManager() as db:
    subject = db.query(Subject).options(
        joinedload(Subject.measurements),
        joinedload(Subject.sessions)
    ).filter(Subject.id == 1).first()
```

### Indexing

Indexes are already defined in the models. Monitor slow queries and add custom indexes as needed:

```python
# Add custom index in models.py
__table_args__ = (
    Index('idx_custom_query', 'field1', 'field2'),
)
```

## Troubleshooting

### Database Locked (SQLite)

```python
# Increase timeout
engine = create_engine(
    DATABASE_URL,
    connect_args={'timeout': 15}
)
```

### Connection Pool Exhausted

```python
# Increase pool size
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40
)
```

### Migration Conflicts

```bash
# Stamp current state
alembic stamp head

# Create new migration
alembic revision --autogenerate -m "Fix conflicts"
```

## Best Practices

1. **Always use context managers** (`DatabaseManager`) or dependency injection (`get_db()`)
2. **Use transactions** for multi-step operations
3. **Validate data** with Pydantic schemas before database operations
4. **Encrypt sensitive fields** before storage
5. **Use soft deletes** for subjects to preserve history
6. **Regular backups** of production database
7. **Monitor query performance** and add indexes as needed
8. **Use migrations** (Alembic) for schema changes in production
