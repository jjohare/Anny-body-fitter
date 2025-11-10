# ADR 002: Privacy-Preserving Photo Handling Strategy

## Status
**ACCEPTED**

## Context
User photos contain sensitive biometric data. We must process these images to extract measurements and fit 3D models while ensuring:
- Zero retention of photos post-processing
- Compliance with GDPR (EU), CCPA (California), and HIPAA (healthcare)
- Protection against data breaches
- User trust and transparency

**Key Requirements**:
- Photos must never be written to persistent storage
- Photos must be inaccessible after processing completes
- System must prove deletion (audit trail)
- Optional face anonymization for extra privacy

## Decision

### 1. RAM-Only Photo Storage
**Selected Approach**: Store uploaded photos exclusively in RAM (tmpfs/RAM disk)

**Implementation**:
```python
# Backend configuration
UPLOAD_DIR = "/dev/shm/anny_uploads"  # Linux tmpfs (RAM-backed)
MAX_PHOTO_LIFETIME = 300  # 5 minutes max

# On upload
def handle_upload(file):
    # Create temporary file in RAM
    temp_path = f"{UPLOAD_DIR}/{uuid4()}.jpg"
    with open(temp_path, 'wb') as f:
        f.write(file.read())

    # Schedule automatic deletion
    schedule_deletion(temp_path, after_seconds=MAX_PHOTO_LIFETIME)

    return temp_path

# On processing completion
def cleanup_photo(path):
    # Secure deletion (overwrite with zeros)
    file_size = os.path.getsize(path)
    with open(path, 'wb') as f:
        f.write(b'\x00' * file_size)
    os.remove(path)

    # Log deletion event
    audit_log.info(f"Photo deleted: {path}")
```

**Rationale**:
- tmpfs is cleared on reboot (no persistence)
- Fast I/O (memory speed vs disk)
- No recovery possible after overwrite
- Simple cleanup on process crash (file handles closed)

**Alternatives Considered**:
- **Disk-based temp folder**: Rejected (risk of forensic recovery)
- **Encrypted disk storage**: Rejected (adds complexity, still persistent)
- **Streaming processing**: Considered for future (Phase 2)

### 2. EXIF Metadata Stripping
**Implementation**: Strip all EXIF data on upload to remove:
- GPS coordinates
- Camera model and serial number
- Timestamp and date
- Photographer name (if embedded)

```python
from PIL import Image

def strip_exif(image_path):
    img = Image.open(image_path)
    # Create new image without EXIF
    data = list(img.getdata())
    clean_img = Image.new(img.mode, img.size)
    clean_img.putdata(data)
    clean_img.save(image_path)
```

**Rationale**: Prevents accidental PII leakage in metadata

### 3. Optional Face Anonymization
**User Option**: Enable face blurring before processing (checkbox in UI)

**Implementation**:
```python
def anonymize_face(image, landmarks):
    # Use MediaPipe face mesh to detect face region
    face_region = get_face_bounding_box(landmarks)

    # Apply Gaussian blur to face region
    blurred = cv2.GaussianBlur(image[face_region], (99, 99), 30)
    image[face_region] = blurred

    return image
```

**Rationale**: Allows processing body measurements while protecting identity

### 4. Audit Logging (Photos Never Logged)
**Critical Rule**: Never log photo content, file paths must be anonymized

```python
# ❌ BAD: Logs file path
logger.info(f"Processing photo: {photo_path}")

# ✅ GOOD: Logs action without exposing path
logger.info("Photo processing initiated", extra={
    "user_id": user.id,
    "session_id": session.id,
    "action": "photo_upload"
})
```

**Audit Events Logged**:
- Photo uploaded (timestamp, user_id, file_size)
- Processing started (session_id)
- Processing completed (duration)
- Photo deleted (timestamp, session_id)

### 5. No Photo Backups or Replication
**Configuration**:
- tmpfs directory excluded from backup schedules
- Docker volumes for `/dev/shm` are ephemeral
- Database backups contain NO photo data (only metadata)

### 6. Secure Deletion Protocol
**Multi-Step Deletion**:
1. **Overwrite**: Write zeros to file (prevent recovery)
2. **Remove**: Delete file system entry
3. **Audit**: Log deletion event with timestamp
4. **Verify**: Confirm file no longer exists

```python
def secure_delete(path):
    # Step 1: Overwrite
    file_size = os.path.getsize(path)
    with open(path, 'r+b') as f:
        f.write(b'\x00' * file_size)
        f.flush()
        os.fsync(f.fileno())  # Force write to disk

    # Step 2: Remove
    os.remove(path)

    # Step 3: Audit
    audit_log.info(f"Secure deletion completed: {hash(path)}")

    # Step 4: Verify
    assert not os.path.exists(path), "Deletion verification failed"
```

### 7. WebSocket Progress (No Photo Transmission)
**Design**: Send processing progress without sending photos

```json
// WebSocket message (safe)
{
  "event": "processing_update",
  "session_id": "uuid",
  "stage": "pose_detection",
  "progress": 0.3,
  "message": "Detecting body landmarks..."
}

// ❌ Never send photos over WebSocket
{
  "event": "preview",
  "image_data": "base64..." // FORBIDDEN
}
```

**Rationale**: Prevents accidental photo caching in browser/network logs

## Consequences

### Positive
1. **Strong Privacy Guarantee**: Photos physically cannot be recovered after processing
2. **GDPR Compliance**: Zero retention satisfies "right to be forgotten"
3. **User Trust**: Transparent privacy policy builds confidence
4. **Reduced Liability**: No stored photos = no data breach risk for photos
5. **Simplicity**: No need for complex encryption key management

### Negative
1. **No Debugging Photos**: Cannot inspect uploaded photos after processing (mitigated by logging metadata)
2. **No Re-Processing**: User must re-upload if they want to re-fit (acceptable trade-off)
3. **RAM Constraints**: Large batches of photos require sufficient RAM (mitigated by queue system)

### Mitigation Strategies
1. **Debugging**: Store synthetic test photos in separate directory for development
2. **Re-Processing**: Offer "upload again" option with clear explanation
3. **RAM Management**: Implement upload queue with concurrency limits (max 10 concurrent)

## Compliance Checklist

### GDPR (General Data Protection Regulation)
- [x] Photos are not "stored" (RAM-only, deleted immediately)
- [x] User can request deletion of metadata (subject/model records)
- [x] Audit log for data access
- [x] Privacy policy clearly states photo handling

### CCPA (California Consumer Privacy Act)
- [x] User notified of data collection (photo upload consent)
- [x] User can opt-out of face detection (anonymization option)
- [x] No sale of biometric data

### HIPAA (Optional, for Healthcare Use)
- [x] PHI (photos) encrypted in transit (HTTPS/TLS)
- [x] Access controls (authentication required)
- [x] Audit logging of access
- [x] Business Associate Agreements (BAAs) with cloud providers

## Monitoring & Verification

### Health Checks
```python
# Periodic verification that tmpfs is not full
def check_tmpfs_usage():
    usage = shutil.disk_usage(UPLOAD_DIR)
    if usage.percent > 80:
        alert("tmpfs usage high: {usage.percent}%")
        # Trigger emergency cleanup of old temp files
```

### Audit Reports
- Daily report: Number of photos processed vs deleted (should be 1:1)
- Weekly report: Average photo lifetime (should be <5 minutes)
- Monthly report: Zero persistent photo storage verification

## Alternatives Considered

### Alternative 1: Encrypted Persistent Storage
**Approach**: Store encrypted photos temporarily, delete after 24 hours
**Rejected Reason**: Still requires key management, risk of delayed deletion

### Alternative 2: Client-Side Processing
**Approach**: Run vision models in browser (TensorFlow.js)
**Rejected Reason**: Slower performance, limited model complexity, requires large downloads

### Alternative 3: Streaming Processing
**Approach**: Process photo as HTTP stream without saving to disk
**Status**: Considered for Phase 2 (complex implementation)

## References
- [GDPR Article 17: Right to Erasure](https://gdpr-info.eu/art-17-gdpr/)
- [NIST Guidelines on Secure Deletion](https://csrc.nist.gov/publications/detail/sp/800-88/rev-1/final)
- [tmpfs Documentation](https://www.kernel.org/doc/html/latest/filesystems/tmpfs.html)

## Revision History
| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-10 | Architecture Team | Initial decision |
