# Use Python 3.10 slim image as base for minimal size
FROM python:3.10-slim

# Install system dependencies required for dlib, OpenCV, and face recognition
# - build-essential: C++ compiler and build tools for dlib
# - cmake: Build system required by dlib
# - libgl1: OpenGL library required by OpenCV
# - libglib2.0-0: GLib library required by OpenCV
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libgl1 \
    libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

# Set working directory for the application
WORKDIR /app

# Copy backend application code to container
COPY backend /app

# Upgrade pip to latest version and install Python dependencies
# Use --no-cache-dir to reduce image size
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Expose port 8080 for the application
EXPOSE 8080

# Run gunicorn with production configuration
# Configuration includes:
# - 4 workers for handling concurrent requests
# - 120 second timeout for face recognition operations
# - Logging to stdout for container log aggregation
# - Graceful shutdown handling
CMD ["gunicorn", "-c", "gunicorn_config.py", "app:app"]
