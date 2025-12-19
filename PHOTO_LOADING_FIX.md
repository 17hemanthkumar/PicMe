# Photo Loading Fix for Docker Container

## Problem
Photos were not loading in the Docker container because the `uploads` and `processed` folders were not being copied into the container.

## Solution
Updated the Dockerfile to copy both folders into the container.

## What Each Folder Contains

### `uploads/` folder
- Original uploaded photos for each event
- Event thumbnails
- QR codes for events
- Structure: `uploads/{event_id}/{photos and thumbnails}`

### `processed/` folder
- Face-recognized and organized photos
- Individual photos (one person per photo)
- Group photos (multiple people, watermarked)
- Structure: `processed/{event_id}/{person_id}/individual/` and `/group/`

### `backend/known_faces.dat`
- ML model data with learned face encodings
- Automatically copied with backend folder
- Contains 13 identities (as shown in your logs)

## Rebuild Instructions

```bash
# Stop current container (Ctrl+C)

# Rebuild with photos
docker build -t picme .

# Run container
docker run -p 8080:8080 picme
```

## Verify Photos Are Working

1. **Event Thumbnails**: Should load on homepage and event discovery page
2. **Group Photos**: Should load on event detail page (no authentication needed)
3. **Face Recognition**: Should work when you scan your face
4. **Individual Photos**: Should load after successful face authentication

## Expected Behavior

### Before Face Scan
- ✅ Event thumbnails visible
- ✅ Group photos visible (watermarked)
- ❌ Individual photos hidden

### After Face Scan
- ✅ Event thumbnails visible
- ✅ Group photos visible (watermarked)
- ✅ Individual photos visible (your photos only)
- ✅ Download button enabled

## Troubleshooting

### If thumbnails still show 404:
1. Check if `uploads/{event_id}/thumbnail_*.jpg` files exist
2. Verify events_data.json has correct `thumbnail_filename` values
3. Rebuild container: `docker build -t picme .`

### If group photos don't load:
1. Check if `processed/{event_id}/{person_id}/group/watermarked_*.jpg` files exist
2. Verify photos were processed (face recognition ran)
3. Check container logs for processing errors

### If face recognition doesn't work:
1. Verify `backend/known_faces.dat` exists and was copied
2. Check logs for "ML MODEL Loaded X identities"
3. Ensure camera permissions are granted in browser

### If individual photos don't load after face scan:
1. Check if `processed/{event_id}/{person_id}/individual/*.jpg` files exist
2. Verify face scan was successful (check console logs)
3. Ensure person_id matches between scan and processed folder

## Development Mode (with live updates)

If you want to update photos without rebuilding:

```bash
docker run -p 8080:8080 \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/processed:/app/processed \
  -v $(pwd)/events_data.json:/app/events_data.json \
  -v $(pwd)/backend/known_faces.dat:/app/backend/known_faces.dat \
  picme
```

This mounts your local folders into the container, so changes are reflected immediately.

## Production Mode (current setup)

Photos are baked into the Docker image:
- ✅ Faster startup (no volume mounting)
- ✅ Portable (image contains everything)
- ❌ Need to rebuild to update photos
- ❌ Larger image size

Choose based on your needs!
