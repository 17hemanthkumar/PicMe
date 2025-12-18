# Docker Deployment - Application Structure Analysis

## Overview
This document provides a comprehensive analysis of the PicMe application structure, dependencies, and configuration requirements for Docker containerization.

## Application Architecture

### Technology Stack
- **Backend Framework**: Flask 2.0.1
- **Python Version**: 3.10.13 (specified in runtime.txt)
- **Database**: PostgreSQL (Neon) via psycopg2-binary
- **Face Recognition**: dlib + face-recognition library
- **Image Processing**: OpenCV, NumPy, Pillow
- **Production Server**: Needs Gunicorn (not currently in requirements.txt)

### Directory Structure
```
project_root/
├── backend/                          # Python Flask application
│   ├── app.py                        # Main application file
│   ├── face_model.py                 # Face recognition model
│   ├── face_utils.py                 # Face recognition utilities
│   ├── requirements.txt              # Python dependencies
│   ├── runtime.txt                   # Python version (3.10.13)
│   ├── shape_predictor_68_face_landmarks.dat  # dlib model file (68MB)
│   ├── known_faces.dat               # Face recognition data (runtime)
│   ├── .env                          # Local environment variables (DO NOT COPY)
│   └── test_*.py                     # Test files
├── frontend/                         # Static files and templates
│   ├── pages/                        # HTML templates
│   │   ├── index.html
│   │   ├── login.html
│   │   ├── signup.html
│   │   ├── homepage.html
│   │   ├── event_organizer.html
│   │   ├── event_discovery.html
│   │   ├── event_detail.html
│   │   ├── biometric_authentication_portal.html
│   │   ├── personal_photo_gallery.html
│   │   └── download_page.html
│   ├── main.css                      # Styles
│   ├── gallery.js                    # Gallery functionality
│   ├── qr-scanner.js                 # QR code scanning
│   └── picme.svg                     # Logo
├── uploads/                          # Runtime: uploaded photos (by event_id)
├── processed/                        # Runtime: processed photos (by event_id/person_id)
└── events_data.json                  # Runtime: event metadata
```

## Hardcoded Paths and Configuration Issues

### Current Configuration (app.py lines 38-50)
```python
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app.secret_key = os.environ.get("FLASK_SECRET_KEY", "your_super_secret_key_here")

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://USER:PASSWORD@HOST/DBNAME?sslmode=require"
)

UPLOAD_FOLDER = os.path.join(BASE_DIR, '..', 'uploads')
PROCESSED_FOLDER = os.path.join(BASE_DIR, '..', 'processed')
EVENTS_DATA_PATH = os.path.join(BASE_DIR, '..', 'events_data.json')
KNOWN_FACES_DATA_PATH = os.path.join(BASE_DIR, 'known_faces.dat')
```

### Issues Identified

#### 1. **Relative Path Dependencies** ✅ GOOD
- Uses `BASE_DIR` for relative paths
- Paths are relative to backend directory using `..` notation
- **Status**: Already container-friendly, but needs verification

#### 2. **Environment Variables** ⚠️ NEEDS IMPROVEMENT
- ✅ DATABASE_URL: Uses environment variable with fallback
- ✅ FLASK_SECRET_KEY: Uses environment variable with fallback
- ❌ PORT: Hardcoded to 5000 in `if __name__ == '__main__'` (line 1785)
- ❌ HOST: Hardcoded to '127.0.0.1' (should be '0.0.0.0' for containers)

#### 3. **Missing Environment Variable Validation**
- No validation for required environment variables
- No clear error messages when DATABASE_URL is invalid
- Fallback values are insecure placeholders

#### 4. **Directory Initialization** ✅ GOOD
- Lines 54-55: Creates directories with `os.makedirs(exist_ok=True)`
- Handles uploads and processed folders
- **Status**: Already container-friendly

#### 5. **Port and Host Configuration** ❌ CRITICAL
```python
# Line 1785 - NEEDS CHANGE
port = int(os.environ.get("PORT", 5000))
app.run(host='127.0.0.1', port=port, debug=True)
```
**Issues**:
- Host '127.0.0.1' only accepts localhost connections (won't work in container)
- Should be '0.0.0.0' to accept external connections
- Debug mode should be disabled in production
- Should use Gunicorn instead of Flask dev server

## Python Dependencies Analysis

### Current requirements.txt
```
flask==2.0.1
face-recognition==1.3.0
numpy==1.21.2
opencv-python==4.5.3.56
pillow==8.3.1
python-dotenv==0.19.0
mysql-connector-python==8.0.27  # UNUSED - can be removed
Werkzeug==2.0.1
pytest==7.4.3
hypothesis==6.92.1
qrcode==7.4.2
psycopg2-binary==2.9.9
```

### Issues and Recommendations

#### 1. **Missing Production Dependencies**
- ❌ **gunicorn**: Required for production deployment (MUST ADD)

#### 2. **Unused Dependencies**
- ⚠️ **mysql-connector-python**: Not used (app uses PostgreSQL)
- Recommendation: Remove to reduce image size

#### 3. **Development Dependencies**
- ⚠️ **pytest, hypothesis**: Only needed for testing
- Recommendation: Keep for now (useful for container testing)

#### 4. **System Dependencies for dlib**
The face-recognition library depends on dlib, which requires:
- **build-essential**: C++ compiler
- **cmake**: Build system
- **libgl1**: OpenGL library (for OpenCV)
- **libglib2.0-0**: GLib library (for OpenCV)

### Updated requirements.txt Needed
```
flask==2.0.1
face-recognition==1.3.0
numpy==1.21.2
opencv-python==4.5.3.56
pillow==8.3.1
python-dotenv==0.19.0
Werkzeug==2.0.1
pytest==7.4.3
hypothesis==6.92.1
qrcode==7.4.2
psycopg2-binary==2.9.9
gunicorn==21.2.0  # ADD THIS
```

## Files Required in Docker Image

### Essential Files (MUST INCLUDE)
```
backend/
├── app.py                            # Main application
├── face_model.py                     # Face recognition model
├── face_utils.py                     # Face utilities
├── requirements.txt                  # Python dependencies
├── shape_predictor_68_face_landmarks.dat  # dlib model (68MB)
└── runtime.txt                       # Python version reference

frontend/
├── pages/*.html                      # All HTML templates
├── main.css                          # Styles
├── gallery.js                        # Gallery functionality
├── qr-scanner.js                     # QR scanner
└── picme.svg                         # Logo
```

### Runtime Files (CREATED AT RUNTIME)
```
uploads/                              # Created by app
processed/                            # Created by app
events_data.json                      # Created by app
backend/known_faces.dat               # Created by app
```

### Files to EXCLUDE (.dockerignore)
```
.git/                                 # Version control
.hypothesis/                          # Test data
backend/.hypothesis/                  # Test data
backend/__pycache__/                  # Python cache
**/__pycache__/                       # Python cache
**/*.pyc                              # Compiled Python
backend/.env                          # Local environment (SECURITY)
.vscode/                              # Editor config
.kiro/                                # Kiro specs
*.md                                  # Documentation
backend/test_*.py                     # Test files (optional)
backend/tempCodeRunnerFile.py         # Temp file
backend/sql.txt                       # SQL reference
uploads/                              # Runtime data
processed/                            # Runtime data
events_data.json                      # Runtime data
```

## Runtime Requirements

### Environment Variables (REQUIRED)
1. **DATABASE_URL**: PostgreSQL connection string
   - Format: `postgresql://user:pass@host:port/dbname?sslmode=require`
   - Example: `postgresql://user:pass@ep-xxx.neon.tech/picme?sslmode=require`

2. **FLASK_SECRET_KEY**: Session encryption key
   - Must be random and secure
   - Example: `python -c "import secrets; print(secrets.token_hex(32))"`

3. **PORT**: Application port (optional, default: 8080)
   - Cloud platforms often set this automatically
   - Example: `8080`

### Volume Mounts (RECOMMENDED)
For persistent data across container restarts:
```
/app/uploads          # Uploaded photos
/app/processed        # Processed photos
/app/events_data.json # Event metadata
/app/backend/known_faces.dat  # Face recognition data
```

### Port Exposure
- Container should expose port 8080 (configurable via PORT env var)
- Gunicorn should bind to `0.0.0.0:8080` to accept external connections

## Code Changes Required

### 1. Update app.py Configuration (Lines 1785-1787)
**Current**:
```python
port = int(os.environ.get("PORT", 5000))
app.run(host='127.0.0.1', port=port, debug=True)
```

**Should be**:
```python
port = int(os.environ.get("PORT", 8080))
app.run(host='0.0.0.0', port=port, debug=False)
```

**Note**: In production, this entire block should be replaced with Gunicorn command.

### 2. Add Environment Variable Validation
Add at application startup (after imports):
```python
# Validate required environment variables
required_env_vars = ['DATABASE_URL', 'FLASK_SECRET_KEY']
missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
if missing_vars:
    print(f"ERROR: Missing required environment variables: {', '.join(missing_vars)}")
    print("Please set these environment variables before starting the application.")
    # In production, you might want to exit here
```

### 3. Update requirements.txt
Add gunicorn:
```
gunicorn==21.2.0
```

Remove unused mysql-connector-python (optional).

## Docker Build Strategy

### Base Image
- Use `python:3.10-slim` for minimal size
- Matches runtime.txt requirement (3.10.13)

### Build Steps
1. Install system dependencies (build-essential, cmake, libgl1, libglib2.0-0)
2. Copy requirements.txt and install Python packages
3. Copy application code (backend/ and frontend/)
4. Create runtime directories (uploads/, processed/)
5. Expose port 8080
6. Set CMD to run Gunicorn

### Gunicorn Configuration
```bash
gunicorn -b 0.0.0.0:8080 \
  --workers 4 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile - \
  app:app
```

**Configuration Rationale**:
- **Workers**: 4 (good for CPU-bound face recognition)
- **Timeout**: 120s (face recognition can take time)
- **Logging**: stdout/stderr (for container log aggregation)
- **Bind**: 0.0.0.0:8080 (accept external connections)

## Security Considerations

### 1. Secrets Management
- ❌ Never commit .env files
- ❌ Never hardcode DATABASE_URL or FLASK_SECRET_KEY
- ✅ Use cloud platform secret management
- ✅ Validate environment variables at startup

### 2. File System Security
- ✅ Validate file paths to prevent directory traversal
- ✅ Sanitize uploaded filenames
- ⚠️ Consider running as non-root user (future enhancement)

### 3. Network Security
- ✅ Use HTTPS in production (handled by cloud platform)
- ✅ Use SSL for database connections (sslmode=require)

## Performance Considerations

### Image Size Optimization
- Use python:3.10-slim (not full python image)
- Clean up apt cache after installing system packages
- Use .dockerignore to exclude unnecessary files
- Expected final image size: ~1.5GB (due to dlib and OpenCV)

### Runtime Performance
- Gunicorn with 4 workers for concurrency
- Face recognition is CPU-intensive (consider worker count)
- Database connection pooling (handled by psycopg2)

## Testing Requirements

### Local Docker Testing
1. Build image: `docker build -t picme .`
2. Run container with env vars
3. Test endpoints:
   - Homepage: `http://localhost:8080`
   - User registration
   - Event creation
   - Photo upload
   - Face recognition

### Cloud Platform Testing
1. Deploy to test environment
2. Verify environment variable injection
3. Test database connectivity
4. Test file uploads and persistence
5. Test face recognition functionality

## Summary of Required Changes

### High Priority (MUST DO)
1. ✅ Add gunicorn to requirements.txt
2. ✅ Update app.py host to '0.0.0.0' (line 1787)
3. ✅ Update app.py default port to 8080 (line 1785)
4. ✅ Create Dockerfile with system dependencies
5. ✅ Create .dockerignore file
6. ✅ Add environment variable validation

### Medium Priority (SHOULD DO)
1. ⚠️ Remove mysql-connector-python from requirements.txt
2. ⚠️ Add logging for missing environment variables
3. ⚠️ Disable debug mode in production

### Low Priority (NICE TO HAVE)
1. 💡 Run as non-root user in container
2. 💡 Multi-stage Docker build for smaller image
3. 💡 Health check endpoint

## Next Steps

1. **Task 2**: Update app.py configuration for containerization
2. **Task 3**: Create Dockerfile with all dependencies
3. **Task 4**: Create .dockerignore file
4. **Task 5**: Update requirements.txt
5. **Task 6**: Create deployment documentation
6. **Task 7**: Test Docker build and deployment locally

---

**Analysis Date**: December 18, 2024
**Analyzed By**: Kiro AI Agent
**Status**: ✅ Complete
