# Quick Fix - Docker Build Error

## Problem
Docker build failed with error: `"/processed": not found` and `"/uploads": not found`

## Root Cause
The `.dockerignore` file was excluding the `uploads/` and `processed/` folders from being copied into the Docker image.

## Solution
Updated `.dockerignore` to include these folders.

## What Changed

### Before (in .dockerignore):
```
# Ignore large runtime folders
uploads/
processed/
```

### After (in .dockerignore):
```
# DO NOT IGNORE THESE - REQUIRED FOR DOCKER BUILD
!uploads/
!processed/
!events_data.json
```

## Rebuild Now

```bash
# This should work now
docker build -t picme .

# Then run
docker run -p 8080:8080 picme
```

## Why This Happened

The `.dockerignore` file was originally set up to exclude large folders during development to speed up builds. However, for production deployment, we need these folders to include all the photos and processed data.

## Expected Result

After rebuilding:
- ✅ Build completes successfully
- ✅ All event thumbnails load
- ✅ All group photos load
- ✅ Face recognition works
- ✅ Individual photos load after face scan

## File Sizes

The Docker image will be larger now because it includes:
- Original uploaded photos (`uploads/` folder)
- Processed face-recognized photos (`processed/` folder)
- Face recognition model data (`backend/known_faces.dat`)

This is expected and necessary for the application to work properly.
