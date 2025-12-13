# Design Document: Download Page Feature

## Overview

The Download Page feature provides users with a centralized interface for managing and downloading their photos from multiple events. The page will integrate with existing facial recognition data to display user-specific photos, offer batch download capabilities with ZIP compression, and maintain download history using browser local storage. The design leverages existing backend APIs while adding new endpoints for fetching user-specific photo collections and managing download history.

## Architecture

### System Components

1. **Frontend Layer**
   - Download Page UI (`frontend/pages/download_page.html`)
   - Client-side JavaScript for photo management and download orchestration
   - Responsive CSS using Tailwind CSS framework

2. **Backend Layer**
   - New API endpoint: `/api/user_photos` - Fetches all photos for authenticated user across events
   - Existing API endpoints: `/api/download_photos`, `/api/download_event_photos`
   - Session-based authentication using Flask sessions

3. **Data Layer**
   - Processed photos directory structure: `processed/{event_id}/{person_id}/{individual|group}/`
   - Events metadata: `events_data.json`
   - Download history: Browser localStorage (client-side)

### Data Flow

1. User navigates to `/download_page`
2. Frontend requests user photos via `/api/user_photos`
3. Backend queries processed folder structure for user's person_id
4. Backend aggregates photos across all events
5. Frontend renders photos organized by event
6. User selects photos and initiates download
7. Frontend calls existing download APIs with selected photos
8. Backend creates ZIP archive and streams to client
9. Frontend records download in localStorage

## Components and Interfaces

### Frontend Components

#### DownloadPage Component
```javascript
// Main page controller
class DownloadPageController {
  constructor() {
    this.selectedPhotos = new Set();
    this.allPhotos = [];
    this.downloadHistory = [];
    this.filters = { event: 'all', type: 'all' };
  }
  
  async loadUserPhotos();
  renderEventCards();
  renderPhotoGrid();
  handlePhotoSelection(photoId);
  handleDownload();
  updateFilters(filterType, value);
  loadDownloadHistory();
  saveDownloadHistory(entry);
}
```

#### PhotoCard Component
```javascript
// Individual photo display with checkbox
{
  photoUrl: string,
  filename: string,
  eventId: string,
  personId: string,
  photoType: 'individual' | 'group',
  selected: boolean
}
```

#### EventCard Component
```javascript
// Event grouping display
{
  eventId: string,
  eventName: string,
  eventDate: string,
  eventLocation: string,
  photoCount: number,
  photos: PhotoCard[],
  expanded: boolean
}
```

### Backend API Interfaces

#### GET /api/user_photos
**Purpose**: Fetch all photos for the authenticated user across all events

**Request**:
```
Headers: Session cookie (automatic)
```

**Response**:
```json
{
  "success": true,
  "events": [
    {
      "event_id": "event_52fee35b",
      "event_name": "Summer Festival 2024",
      "event_date": "2024-06-15",
      "event_location": "Central Park",
      "person_id": "person_abc123",
      "individual_photos": [
        {
          "filename": "photo1.jpg",
          "url": "/photos/event_52fee35b/person_abc123/individual/photo1.jpg"
        }
      ],
      "group_photos": [
        {
          "filename": "watermarked_photo2.jpg",
          "url": "/photos/event_52fee35b/person_abc123/group/watermarked_photo2.jpg"
        }
      ]
    }
  ],
  "total_photos": 15
}
```

**Error Response**:
```json
{
  "success": false,
  "error": "No photos found for user"
}
```

#### POST /api/download_photos (Existing - Enhanced)
**Purpose**: Download selected photos as ZIP

**Request**:
```json
{
  "event_id": "event_52fee35b",
  "person_id": "person_abc123",
  "photos": [
    {
      "filename": "photo1.jpg",
      "photoType": "individual"
    }
  ]
}
```

**Response**: Binary ZIP file stream

## Data Models

### UserPhotoCollection
```python
{
  "user_session_id": str,  # From Flask session
  "events": [
    {
      "event_id": str,
      "event_metadata": EventMetadata,
      "person_id": str,
      "photos": {
        "individual": [PhotoFile],
        "group": [PhotoFile]
      }
    }
  ]
}
```

### PhotoFile
```python
{
  "filename": str,
  "url": str,
  "file_path": str,  # Server-side path
  "size_bytes": int
}
```

### DownloadHistoryEntry (Client-side)
```javascript
{
  "id": string,  // UUID
  "timestamp": string,  // ISO 8601
  "event_name": string,
  "photo_count": number,
  "file_size": string,  // Human-readable (e.g., "2.5 MB")
  "photo_ids": string[]
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Authentication enforcement
*For any* request to the download page or user photos API, if the user is not authenticated, then the system should redirect to the login page or return a 401 error
**Validates: Requirements 1.3**

### Property 2: Photo ownership verification
*For any* photo returned by the user photos API, that photo should exist in a directory matching the authenticated user's person_id
**Validates: Requirements 2.1**

### Property 3: Selection state consistency
*For any* photo selection or deselection operation, the selected count display should equal the size of the selected photos set
**Validates: Requirements 3.3**

### Property 4: Download button state
*For any* state of the selected photos set, the download button should be enabled if and only if the set is non-empty
**Validates: Requirements 4.1, 4.2**

### Property 5: ZIP filename sanitization
*For any* photo included in a ZIP download, if the filename contains "watermarked_" prefix, then the archived filename should have that prefix removed
**Validates: Requirements 4.5**

### Property 6: Filter application
*For any* active filter combination, all displayed photos should match the filter criteria (event and type)
**Validates: Requirements 5.2, 5.3, 5.4, 5.5**

### Property 7: Filter selection preservation
*For any* filter change operation, the set of selected photos should remain unchanged
**Validates: Requirements 5.6**

### Property 8: Download history ordering
*For any* download history display, entries should be sorted by timestamp in descending order
**Validates: Requirements 7.3**

### Property 9: Download history limit
*For any* download history with more than 10 entries, only the 10 most recent entries should be displayed
**Validates: Requirements 7.5**

### Property 10: Responsive grid layout
*For any* viewport width, the photo grid column count should match the breakpoint specification (1 for mobile, 2 for tablet, 4 for desktop)
**Validates: Requirements 8.1, 8.2, 8.3**

## Error Handling

### Client-Side Error Handling

1. **Network Errors**
   - Display user-friendly error message
   - Retry mechanism for transient failures
   - Preserve user selections during errors

2. **Invalid Session**
   - Redirect to login page
   - Clear local state
   - Display session expiration message

3. **Download Failures**
   - Show specific error message
   - Keep photo selections intact
   - Offer retry option

4. **Empty State Handling**
   - Display helpful message when no photos exist
   - Provide link to biometric authentication portal
   - Show instructions for finding photos

### Server-Side Error Handling

1. **Authentication Failures**
   - Return 401 Unauthorized
   - Clear invalid sessions
   - Log security events

2. **File System Errors**
   - Return 500 Internal Server Error
   - Log detailed error information
   - Gracefully handle missing files

3. **ZIP Creation Failures**
   - Clean up partial ZIP files
   - Return descriptive error message
   - Log failure details

4. **Resource Limits**
   - Implement maximum ZIP size limit (100MB)
   - Return 413 Payload Too Large if exceeded
   - Suggest downloading in smaller batches

## Testing Strategy

### Unit Testing

**Framework**: pytest for Python backend, Jest for JavaScript frontend

**Backend Unit Tests**:
- Test `/api/user_photos` endpoint with various user states
- Test photo file path resolution
- Test ZIP creation with different photo combinations
- Test authentication decorator behavior
- Test error handling for missing files

**Frontend Unit Tests**:
- Test photo selection/deselection logic
- Test filter application
- Test download history management
- Test localStorage operations
- Test responsive layout calculations

### Property-Based Testing

**Framework**: Hypothesis for Python

**Property Tests**:
- Each property-based test should run a minimum of 100 iterations
- Each test must be tagged with the format: `**Feature: download-page, Property {number}: {property_text}**`
- Each correctness property must be implemented by a single property-based test

**Test Specifications**:

1. **Authentication Property Test**
   - Generate random session states (authenticated/unauthenticated)
   - Verify redirect behavior matches authentication state
   - Tag: `**Feature: download-page, Property 1: Authentication enforcement**`

2. **Photo Ownership Property Test**
   - Generate random person_ids and photo collections
   - Verify all returned photos belong to the correct person_id
   - Tag: `**Feature: download-page, Property 2: Photo ownership verification**`

3. **Selection Count Property Test**
   - Generate random selection/deselection sequences
   - Verify count display always matches set size
   - Tag: `**Feature: download-page, Property 3: Selection state consistency**`

4. **Download Button State Property Test**
   - Generate random selection states
   - Verify button enabled state matches non-empty condition
   - Tag: `**Feature: download-page, Property 4: Download button state**`

5. **Filename Sanitization Property Test**
   - Generate random filenames with/without watermark prefix
   - Verify ZIP entries have prefix removed
   - Tag: `**Feature: download-page, Property 5: ZIP filename sanitization**`

6. **Filter Application Property Test**
   - Generate random photo collections and filter combinations
   - Verify displayed photos match filter criteria
   - Tag: `**Feature: download-page, Property 6: Filter application**`

7. **Filter Selection Preservation Property Test**
   - Generate random selection states and filter changes
   - Verify selections unchanged after filter application
   - Tag: `**Feature: download-page, Property 7: Filter selection preservation**`

8. **Download History Ordering Property Test**
   - Generate random download history entries
   - Verify entries sorted by timestamp descending
   - Tag: `**Feature: download-page, Property 8: Download history ordering**`

9. **Download History Limit Property Test**
   - Generate download histories of various sizes
   - Verify only 10 most recent entries displayed
   - Tag: `**Feature: download-page, Property 9: Download history limit**`

10. **Responsive Layout Property Test**
    - Generate random viewport widths
    - Verify grid column count matches breakpoint rules
    - Tag: `**Feature: download-page, Property 10: Responsive grid layout**`

### Integration Testing

- Test complete download flow from page load to ZIP download
- Test interaction between frontend and backend APIs
- Test session management across page navigation
- Test concurrent download operations
- Test large photo collections (100+ photos)

### Manual Testing Checklist

- Verify responsive design on mobile, tablet, and desktop
- Test download with slow network conditions
- Verify ZIP file integrity after download
- Test browser compatibility (Chrome, Firefox, Safari, Edge)
- Verify accessibility with screen readers
- Test keyboard navigation
