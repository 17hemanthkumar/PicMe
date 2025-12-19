# Docker Run Guide - PicMe Application

## Quick Start

### 1. Rebuild the Docker Image
```bash
docker build -t picme .
```

### 2. Run the Container
```bash
docker run -p 8080:8080 picme
```

### 3. Access the Application
Open your browser and go to: http://localhost:8080

## What Was Fixed

### Issue 1: Events Not Loading
- **Problem**: `events_data.json` was not being copied into the Docker container
- **Solution**: Added `COPY events_data.json /app/events_data.json` to Dockerfile

### Issue 2: Photos Not Loading
- **Problem**: `uploads` and `processed` folders were not being copied into the Docker container
- **Solution**: Added `COPY uploads /app/uploads` and `COPY processed /app/processed` to Dockerfile
- **Result**: All photos (thumbnails, group photos, individual photos) now load correctly

### Issue 3: Worker Timeout
- **Problem**: ML model loading was taking longer than 120 seconds
- **Solution**: 
  - Increased timeout to 300 seconds (5 minutes)
  - Reduced workers from 4 to 1 to avoid multiple model loads
  - Using gunicorn config file for better control

### Issue 4: API Endpoint Consistency
- **Problem**: Frontend was using `/events` but we added `/api/events`
- **Solution**: Updated homepage.html to use `/api/events` with console logging

## Verify Events and Photos Are Loading

1. Open browser DevTools (F12)
2. Go to Console tab
3. You should see:
   - "Loaded events for carousel: [...]"
   - "Loaded events for grid: [...]"
   - "Loaded events: [...]" (on event discovery page)
4. Check Network tab - no 404 errors for:
   - `/api/events/{event_id}/thumbnail` (event thumbnails)
   - `/api/events/{event_id}/photos` (event photos)
   - `/photos/{event_id}/all/{filename}` (group photos)

## Face Recognition Features

After rebuilding with photos:

1. **View Group Photos**: All group photos visible without authentication
2. **Face Scan**: Use biometric authentication to scan your face
3. **View Individual Photos**: After successful face scan, see your individual photos
4. **Download Photos**: Download your photos after authentication

## Troubleshooting

### If events still don't show:
1. Check if `events_data.json` exists in your project root
2. Verify it contains valid JSON with events
3. Rebuild the image: `docker build -t picme .`
4. Check container logs for errors

### If worker timeout persists:
- The ML model is loading, just wait for the "ML MODEL Loaded X identities" message
- First startup takes longer as the model initializes

## Environment Variables (Optional)

You can customize the deployment:

```bash
docker run -p 8080:8080 \
  -e GUNICORN_WORKERS=2 \
  -e FLASK_SECRET_KEY=your-secret-key \
  picme
```

## Volume Mounting (For Development)

To persist uploads and processed photos:

```bash
docker run -p 8080:8080 \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/processed:/app/processed \
  -v $(pwd)/events_data.json:/app/events_data.json \
  picme
```

This allows you to:
- Keep uploaded photos between container restarts
- Update events_data.json without rebuilding
- Access processed photos from host machine
