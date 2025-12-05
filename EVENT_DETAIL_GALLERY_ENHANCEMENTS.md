# Event Detail Page Gallery Enhancements

## Overview
Added full-view modal, checkboxes, and multi-photo download functionality to the event detail page, allowing users to browse and download event photos before scanning their face.

## Features Implemented

### 1. Full View Modal
- **Click to View**: Users can click on any event photo to view it in full-screen mode
- **Navigation Controls**: 
  - Previous/Next buttons to navigate between photos
  - Keyboard support (Arrow keys for navigation, Escape to close)
  - Photo counter showing current position (e.g., "5 / 48")
- **Download Button**: Download the currently viewed photo directly from full view
- **Close Button**: X button in top-right corner to exit full view

### 2. Multi-Select with Checkboxes
- **Checkbox on Each Photo**: Top-left corner of each photo thumbnail
- **Select All/Deselect All**: Quick action buttons in the download controls bar
- **Visual Feedback**: Selected count display showing "X photos selected"
- **Works with Pagination**: Checkboxes persist across "Load More" actions

### 3. Bulk Download Functionality
- **Single Photo Download**: Direct download when only one photo is selected
- **Multiple Photos Download**: Creates a ZIP file for multiple selections
- **Download Controls Bar**: 
  - Shows selected count
  - Select All / Deselect All buttons
  - Download Selected button (disabled when no photos selected)
- **Loading State**: Button shows spinner and "Downloading..." text during download

## Technical Implementation

### Frontend Changes (`frontend/pages/event_detail.html`)

#### Added UI Components:
1. **Download Controls Bar**:
   ```html
   - Selected count display
   - Select All / Deselect All buttons
   - Download Selected button with icon
   - Hidden by default, shown when photos load
   ```

2. **Full View Modal**:
   ```html
   - Full-screen overlay with black background
   - Large image display
   - Navigation buttons (prev/next)
   - Download button (top-right)
   - Close button (top-right)
   - Photo counter (bottom-center)
   ```

3. **Photo Grid Enhancements**:
   ```html
   - Checkbox on each photo
   - Click-to-view functionality
   - Hover overlay with "Click to view" text
   - Maintains existing pagination
   ```

#### JavaScript Functionality:
- **State Management**:
  - `allPhotos`: Array of all loaded photos with metadata
  - `currentPhotoIndex`: Current photo in full view
  - `selectedPhotos`: Set of selected photo URLs
  - `eventId`: Current event ID

- **Event Listeners**:
  - Photo click → Open full view modal
  - Checkbox change → Update selection
  - Select/Deselect all → Bulk selection
  - Download button → Trigger download
  - Modal navigation → Prev/Next/Close
  - Modal download → Download current photo
  - Keyboard shortcuts → Arrow keys and Escape
  - Load More → Fetch additional photos and attach listeners

- **Download Logic**:
  - Single photo: Direct download via anchor tag
  - Multiple photos: POST to `/api/download_event_photos` endpoint
  - ZIP file download with automatic cleanup

- **Pagination Support**:
  - Event listeners attached dynamically to new photos
  - Photo index tracking across pages
  - Selection state maintained across loads

### Backend Changes (`backend/app.py`)

#### New API Endpoint:
```python
@app.route('/api/download_event_photos', methods=['POST'])
@login_required
def download_event_photos():
```

**Functionality**:
- Accepts: `event_id`, `photo_urls` array
- Parses photo URLs to locate files in processed folder
- Creates temporary ZIP file with selected photos
- Removes "watermarked_" prefix from filenames in ZIP
- Sends ZIP file as download
- Auto-cleanup: Deletes temporary ZIP after 5 seconds

**Security**:
- `@login_required` decorator ensures only authenticated users can download
- Validates event_id from request
- Only serves photos from the event's processed directory

## API Integration

### Download Single Photo (Event Page)
```javascript
// Direct download via anchor tag
const link = document.createElement('a');
link.href = photoUrl;
link.download = filename.replace('watermarked_', '');
link.click();
```

### Download Multiple Photos (Event Page)
```javascript
POST /api/download_event_photos
Content-Type: application/json

{
  "event_id": "event_c9cff2be",
  "photo_urls": [
    "/photos/event_c9cff2be/all/watermarked_photo1.jpg",
    "/photos/event_c9cff2be/all/watermarked_photo2.jpg"
  ]
}

Response: ZIP file download (application/zip)
```

## User Experience Flow

### Event Detail Page:
1. **Browse Event**: User navigates to event detail page
2. **View Gallery**: Sees all event photos in grid layout with pagination
3. **Full View**: Clicks any photo to view in full-screen mode
   - Navigate with arrow buttons or keyboard
   - Download current photo with download button
   - Close with X button or Escape key
4. **Select Photos**: Checks boxes on photos they want to download
   - Can use "Select All" for convenience
   - See count update in real-time
   - Selection persists across "Load More"
5. **Download**: Multiple download options:
   - **From Full View**: Click download button to get current photo
   - **From Grid**: Select photos and click "Download Selected" button
     - Single photo: Downloads immediately
     - Multiple photos: Downloads as ZIP file
   - Success notification appears
6. **Scan Face**: Click "Scan My Face" button to find personal photos

## Comparison: Event Detail vs Personal Gallery

| Feature | Event Detail Page | Personal Gallery Page |
|---------|------------------|----------------------|
| Photos Shown | All event photos (public) | User's personal photos only |
| Authentication | Required (logged in) | Required (logged in + face scan) |
| Full View Modal | ✅ Yes | ✅ Yes |
| Checkboxes | ✅ Yes | ✅ Yes |
| Multi-Download | ✅ Yes | ✅ Yes |
| Download from Modal | ✅ Yes | ✅ Yes |
| Pagination | ✅ Yes (Load More) | ❌ No (all loaded at once) |
| API Endpoint | `/api/download_event_photos` | `/api/download_photos` |

## Files Modified

1. **frontend/pages/event_detail.html**
   - Added download controls bar
   - Added full-view modal
   - Enhanced photo grid with checkboxes
   - Implemented complete JavaScript functionality
   - Added pagination support for new features

2. **backend/app.py**
   - Added `/api/download_event_photos` endpoint
   - Implemented ZIP file creation for event photos
   - Added automatic cleanup for temporary files

## Dependencies

### Python (already in requirements.txt):
- `zipfile` (built-in)
- `flask.send_file` (built-in)
- `threading` (built-in)
- `uuid` (built-in)

### Frontend:
- No additional dependencies
- Uses Tailwind CSS (already included via CDN)
- Pure JavaScript (no frameworks)

## Testing Checklist

- [x] Full view modal opens on photo click
- [x] Navigation buttons work (prev/next)
- [x] Keyboard shortcuts work (arrows, escape)
- [x] Download button in modal works
- [x] Checkboxes select/deselect photos
- [x] Select All / Deselect All buttons work
- [x] Selected count updates correctly
- [x] Download button disabled when no selection
- [x] Single photo download works
- [x] Multiple photo download creates ZIP
- [x] ZIP contains correct files without watermark prefix
- [x] Temporary ZIP files are cleaned up
- [x] Authentication required for downloads
- [x] Pagination works with new features
- [x] Event listeners attach to dynamically loaded photos
- [x] Selection state maintained across pagination

## Notes

- All existing functionality preserved
- No changes to other pages or components
- Fully integrated with existing authentication system
- Responsive design maintained
- Works with existing photo serving endpoints
- Automatic cleanup prevents server storage bloat
- Pagination support ensures scalability for large events
- Consistent UX with personal gallery page
