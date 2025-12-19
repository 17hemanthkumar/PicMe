FROM python:3.10-slim

WORKDIR /app

# system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# copy backend
COPY backend /app/backend

# ✅ copy frontend (THIS IS REQUIRED)
COPY frontend /app/frontend

# ✅ copy events_data.json (REQUIRED for events to load)
COPY events_data.json /app/events_data.json

# install dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# create necessary directories first
RUN mkdir -p /app/uploads /app/processed

# ✅ copy uploads and processed folders (REQUIRED for photos to load)
# Copy uploads folder (contains original photos and thumbnails)
COPY --chown=root:root uploads /app/uploads

# Copy processed folder (contains face-recognized photos)
COPY --chown=root:root processed /app/processed

EXPOSE 8080

CMD ["gunicorn", "-c", "backend/gunicorn_config.py", "backend.app:app"]
