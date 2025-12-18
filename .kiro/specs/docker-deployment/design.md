# Design Document

## Overview

This design document outlines the containerization strategy for the PicMe face recognition application using Docker. The solution provides a production-ready container that handles all system dependencies (especially dlib and OpenCV), uses environment-based configuration, and can be deployed to various cloud platforms. The design focuses on creating a minimal, secure, and efficient Docker image that maintains compatibility with the existing application architecture while enabling cloud deployment.

## Architecture

### Container Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Container                      │
│  ┌───────────────────────────────────────────────────┐  │
│  │         Gunicorn WSGI Server (Port 8080)          │  │
│  │                                                    │  │
│  │  ┌──────────────────────────────────────────┐    │  │
│  │  │       Flask Application (app.py)         │    │  │
│  │  │                                           │    │  │
│  │  │  ┌────────────┐  ┌──────────────────┐   │    │  │
│  │  │  │ Face Model │  │  Face Recognition │   │    │  │
│  │  │  │  (dlib)    │  │   (face_utils)    │   │    │  │
│  │  │  └────────────┘  └──────────────────┘   │    │  │
│  │  └──────────────────────────────────────────┘    │  │
│  └───────────────────────────────────────────────────┘  │
│                                                          │
│  File System:                                            │
│  /app/                    - Application code             │
│  /app/uploads/            - Uploaded photos              │
│  /app/processed/          - Processed photos             │
│  /app/known_faces.dat     - Face recognition data        │
│  /app/events_data.json    - Event metadata               │
└─────────────────────────────────────────────────────────┘
         │                           │
         │ Environment Variables     │ Network
         │ - DATABASE_URL            │ Port 8080
         │ - FLASK_SECRET_KEY        │
         │ - PORT                    │
         ▼                           ▼
┌──────────────────┐        ┌──────────────────┐
│  Neon PostgreSQL │        │   Cloud Platform  │
│    (External)    │        │  (Vessel/Railway) │
└──────────────────┘        └──────────────────┘
```

### Deployment Flow

1. **Build Phase**: Docker builds the image with all system and Python dependencies
2. **Configuration Phase**: Environment variables are injected at runtime
3. **Startup Phase**: Application initializes directories and connects to database
4. **Runtime Phase**: Gunicorn serves the Flask application on port 8080

## Components and Interfaces

### 1. Dockerfile

**Purpose**: Defines the container image with all dependencies and configuration

**Key Sections**:
- Base image selection (python:3.10-slim)
- System dependency installation (build-essential, cmake, libgl1, libglib2.0-0)
- Application code copying
- Python package installation
- Port exposure and startup command

**Interface**: Standard Docker build process

### 2. Application Configuration Module

**Purpose**: Manages environment-based configuration

**Configuration Sources**:
- `DATABASE_URL`: PostgreSQL connection string from environment
- `FLASK_SECRET_KEY`: Session encryption key from environment
- `PORT`: Application port (default: 8080)
- File paths: Relative to application directory

**Interface**: Python `os.environ.get()` with fallback defaults

### 3. Gunicorn WSGI Server

**Purpose**: Production-grade HTTP server for Flask application

**Configuration**:
- Bind address: `0.0.0.0:8080` (accepts external connections)
- Worker processes: 4 (configurable via environment)
- Worker class: sync (suitable for I/O-bound operations)
- Timeout: 120 seconds (for face recognition processing)

**Interface**: Command-line invocation in Dockerfile CMD

### 4. Storage Management

**Purpose**: Handles persistent file storage for photos and face data

**Directory Structure**:
```
/app/
├── uploads/
│   └── event_{id}/
│       ├── {photo_files}
│       └── {event_id}_qr.png
├── processed/
│   └── event_{id}/
│       └── person_{id}/
│           ├── individual/
│           └── group/
├── known_faces.dat
└── events_data.json
```

**Interface**: File system operations with automatic directory creation

## Data Models

### Environment Configuration

```python
{
    "DATABASE_URL": "postgresql://user:pass@host/db?sslmode=require",
    "FLASK_SECRET_KEY": "random_secret_key_here",
    "PORT": "8080",
    "GUNICORN_WORKERS": "4",
    "GUNICORN_TIMEOUT": "120"
}
```

### Docker Build Context

```
project_root/
├── Dockerfile              # New: Container definition
├── .dockerignore          # New: Build exclusions
├── backend/
│   ├── app.py
│   ├── face_model.py
│   ├── face_utils.py
│   ├── requirements.txt
│   └── shape_predictor_68_face_landmarks.dat
├── frontend/
│   ├── pages/
│   └── static/
├── uploads/               # Runtime: Created in container
├── processed/             # Runtime: Created in container
└── events_data.json       # Runtime: Created in container
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Container build completeness
*For any* Docker build execution with the provided Dockerfile, the build process should complete successfully without errors and produce a runnable image with all required dependencies installed.
**Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5**

### Property 2: Environment variable configuration
*For any* required environment variable (DATABASE_URL, FLASK_SECRET_KEY, PORT), if it is provided at container runtime, the application should successfully read and use that value for its configuration.
**Validates: Requirements 2.1, 2.2, 2.3**

### Property 3: Directory initialization
*For any* required directory (uploads, processed), when the container starts, the directory should exist and be writable by the application.
**Validates: Requirements 3.1, 3.2**

### Property 4: Port binding
*For any* valid port number specified in the PORT environment variable, when the container starts, Gunicorn should successfully bind to 0.0.0.0:{PORT} and accept incoming connections.
**Validates: Requirements 5.2**

### Property 5: Database connectivity
*For any* valid DATABASE_URL, when the application attempts to connect to the database, the connection should succeed and allow query execution.
**Validates: Requirements 4.4**

### Property 6: Face recognition model loading
*For any* container startup, if the shape_predictor_68_face_landmarks.dat file exists in the application directory, the face recognition system should successfully load the model without errors.
**Validates: Requirements 4.5**

### Property 7: HTTP request handling
*For any* valid HTTP request to the application endpoints, when the container is running, the application should respond with an appropriate HTTP status code and content.
**Validates: Requirements 4.3, 5.4**

### Property 8: File path resolution
*For any* file operation in the application, the system should use paths relative to the application directory (/app) and never reference absolute local paths from the development environment.
**Validates: Requirements 2.5**

## Error Handling

### Build-Time Errors

1. **Missing System Dependencies**
   - Error: Package installation fails during Docker build
   - Handling: Dockerfile includes explicit apt-get update and package list
   - Recovery: Build fails with clear error message indicating missing package

2. **Python Package Installation Failures**
   - Error: pip install fails for dlib or face-recognition
   - Handling: System dependencies installed before Python packages
   - Recovery: Build fails with pip error output for debugging

3. **File Copy Errors**
   - Error: Required files missing during COPY operation
   - Handling: .dockerignore ensures only necessary files are included
   - Recovery: Build fails with "file not found" error

### Runtime Errors

1. **Missing Environment Variables**
   - Error: Required environment variable not set
   - Handling: Application logs clear error message and uses safe defaults where possible
   - Recovery: Container starts but logs warning; DATABASE_URL failure prevents database operations

2. **Database Connection Failures**
   - Error: Cannot connect to Neon PostgreSQL
   - Handling: Connection attempts include error logging with connection string (sanitized)
   - Recovery: Application starts but database-dependent endpoints return 500 errors

3. **Port Binding Failures**
   - Error: Port already in use or permission denied
   - Handling: Gunicorn logs error and exits
   - Recovery: Container exits with non-zero status; orchestrator can restart

4. **File System Permission Errors**
   - Error: Cannot write to uploads or processed directories
   - Handling: Directories created with appropriate permissions at startup
   - Recovery: Application logs error; file upload endpoints return 500 errors

5. **Face Recognition Model Loading Failures**
   - Error: shape_predictor_68_face_landmarks.dat missing or corrupted
   - Handling: Application logs error at startup
   - Recovery: Face recognition endpoints return 500 errors; other endpoints continue working

## Testing Strategy

### Unit Testing

Unit tests will verify specific components and edge cases:

1. **Environment Configuration Tests**
   - Test reading environment variables with valid values
   - Test fallback to default values when variables are missing
   - Test error handling for invalid DATABASE_URL format

2. **Path Resolution Tests**
   - Test that all file paths are relative to application directory
   - Test directory creation logic
   - Test file path sanitization for security

3. **Gunicorn Configuration Tests**
   - Test that gunicorn command is correctly formatted
   - Test port binding with different PORT values
   - Test worker process configuration

### Property-Based Testing

Property-based tests will verify universal properties using **Hypothesis** (Python PBT library). Each test will run a minimum of 100 iterations with randomly generated inputs.

1. **Container Build Property Tests**
   - Generate various Dockerfile configurations
   - Verify all builds complete successfully
   - Verify all required files are present in built image

2. **Environment Variable Property Tests**
   - Generate random valid environment variable values
   - Verify application correctly reads and uses each value
   - Verify application handles missing variables gracefully

3. **Directory Initialization Property Tests**
   - Generate random directory names and paths
   - Verify all directories are created successfully
   - Verify directories have correct permissions

4. **Port Binding Property Tests**
   - Generate random valid port numbers (1024-65535)
   - Verify Gunicorn successfully binds to each port
   - Verify application responds to requests on bound port

5. **Database Connection Property Tests**
   - Generate various valid DATABASE_URL formats
   - Verify connection succeeds for all valid formats
   - Verify connection fails gracefully for invalid formats

6. **File Path Property Tests**
   - Generate random file paths and operations
   - Verify all paths are relative to /app
   - Verify no absolute local paths are used

### Integration Testing

Integration tests will verify the complete system:

1. **End-to-End Container Tests**
   - Build Docker image
   - Run container with test environment variables
   - Verify application starts and responds to health check
   - Verify database connection works
   - Verify file upload and processing works
   - Verify face recognition works

2. **Cloud Platform Deployment Tests**
   - Deploy to test environment on target platform (Vessel/Railway)
   - Verify environment variable injection works
   - Verify persistent storage works
   - Verify external database connectivity works
   - Verify application is accessible via HTTPS

### Manual Testing Checklist

1. Build Docker image locally: `docker build -t picme .`
2. Run container with environment variables: `docker run -p 8080:8080 -e DATABASE_URL=... picme`
3. Access application at `http://localhost:8080`
4. Test user registration and login
5. Test event creation
6. Test photo upload
7. Test face recognition
8. Test photo download
9. Verify logs show no errors
10. Verify database contains expected data

## Security Considerations

1. **Environment Variable Security**
   - Never log DATABASE_URL or FLASK_SECRET_KEY
   - Use secrets management in cloud platforms
   - Rotate secrets regularly

2. **Container Security**
   - Use official Python slim image to minimize attack surface
   - Remove build tools after installation to reduce image size
   - Run application as non-root user (future enhancement)

3. **Network Security**
   - Use HTTPS for all external communications
   - Configure cloud platform firewall rules
   - Use SSL/TLS for database connections (sslmode=require)

4. **File System Security**
   - Validate and sanitize all file paths
   - Prevent directory traversal attacks
   - Limit file upload sizes

## Performance Considerations

1. **Image Size Optimization**
   - Use python:3.10-slim instead of full Python image
   - Clean up apt cache after package installation
   - Use .dockerignore to exclude unnecessary files

2. **Application Performance**
   - Use Gunicorn with multiple workers for concurrency
   - Configure appropriate timeout for face recognition operations
   - Use connection pooling for database connections

3. **Resource Limits**
   - Set memory limits appropriate for face recognition workload
   - Set CPU limits to prevent resource exhaustion
   - Monitor container resource usage in production

## Deployment Instructions

### Local Testing

```bash
# Build the Docker image
docker build -t picme .

# Run the container with environment variables
docker run -p 8080:8080 \
  -e DATABASE_URL="postgresql://user:pass@host/db?sslmode=require" \
  -e FLASK_SECRET_KEY="your_secret_key_here" \
  -e PORT=8080 \
  picme

# Test the application
curl http://localhost:8080
```

### Cloud Platform Deployment (Vessel/Railway/Render)

1. **Push code to Git repository**
2. **Connect repository to cloud platform**
3. **Configure environment variables in platform dashboard**:
   - `DATABASE_URL`: Your Neon PostgreSQL connection string
   - `FLASK_SECRET_KEY`: Generate a random secret key
   - `PORT`: Usually auto-configured by platform
4. **Deploy**: Platform will automatically build and deploy the Docker container
5. **Verify**: Access the application URL provided by the platform

### Troubleshooting

1. **Build fails with "dlib not found"**
   - Ensure system dependencies are installed before Python packages
   - Check that cmake and build-essential are in the Dockerfile

2. **Container starts but application doesn't respond**
   - Check logs: `docker logs <container_id>`
   - Verify PORT environment variable matches exposed port
   - Verify Gunicorn is binding to 0.0.0.0, not 127.0.0.1

3. **Database connection fails**
   - Verify DATABASE_URL is correctly formatted
   - Check that sslmode=require is included
   - Verify network connectivity to Neon database

4. **Face recognition fails**
   - Verify shape_predictor_68_face_landmarks.dat is in the image
   - Check that dlib and face-recognition packages installed correctly
   - Review logs for specific error messages
