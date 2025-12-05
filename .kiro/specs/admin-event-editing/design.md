# Design Document: Admin Event Editing with Thumbnail Management

## Overview

This feature extends the existing event management system to support full CRUD operations on events. Admins will be able to edit event details (name, location, date, category) and manage thumbnails both during creation and after. The implementation leverages the existing Flask backend API structure and frontend modal patterns already established in the event organizer dashboard.

The design maintains consistency with the current architecture:
- Backend: Flask API endpoints with session-based authentication
- Frontend: Vanilla JavaScript with Tailwind CSS styling
- Data Storage: JSON file (`events_data.json`) for event metadata, filesystem for thumbnail images
- Security: Session-based admin authentication with ownership validation

## Architecture

### Backend Components

**New API Endpoints:**
- `PUT /api/events/<event_id>` - Update event details
- `POST /api/events/<event_id>/thumbnail` - Upload/update event thumbnail
- `GET /api/events/<event_id>/thumbnail` - Serve event thumbnail

**Modified API Endpoints:**
- `POST /api/create_event` - Enhanced to accept thumbnail upload

**Modified Components:**
- Event creation handler - Add thumbnail processing
- Events data file management - Update event records
- File serving - Serve custom thumbnails

### Frontend Components

**New UI Elements:**
- Edit event modal with form (similar to create event modal)
- Thumbnail upload widget in create form
- Thumbnail preview and change button in edit modal
- Edit button on event cards

**Modified UI Elements:**
- Create event form - Add thumbnail upload field
- Event cards - Add edit button
- Event display components - Use custom thumbnails

### Data Flow

1. **Edit Event Flow:**
   - Admin clicks edit button → Frontend opens modal with current data
   - Admin modifies fields → Frontend sends PUT request
   - Backend validates admin ownership → Updates events_data.json
   - Backend returns success → Frontend updates UI without refresh

2. **Thumbnail Upload Flow (Creation):**
   - Admin selects thumbnail in create form → Frontend previews image
   - Admin submits form → Frontend sends multipart form data
   - Backend saves thumbnail to uploads folder → Updates event record with thumbnail path
   - Backend returns event data → Frontend displays new event with thumbnail

3. **Thumbnail Update Flow:**
   - Admin clicks change thumbnail in edit modal → Frontend opens file picker
   - Admin selects new image → Frontend sends POST request
   - Backend deletes old thumbnail → Saves new thumbnail
   - Backend updates events_data.json → Returns new thumbnail path
   - Frontend updates all event card images

## Components and Interfaces

### Backend API Interfaces

#### Update Event Endpoint
```python
@app.route('/api/events/<event_id>', methods=['PUT'])
@admin_required
def update_event(event_id):
    """
    Update event details
    Request body: {
        "name": str,
        "location": str,
        "date": str (YYYY-MM-DD),
        "category": str
    }
    Response: {
        "success": bool,
        "event": dict,
        "message": str
    }
    """
```

#### Upload Thumbnail Endpoint
```python
@app.route('/api/events/<event_id>/thumbnail', methods=['POST'])
@admin_required
def update_event_thumbnail(event_id):
    """
    Upload or update event thumbnail
    Request: multipart/form-data with 'thumbnail' file
    Response: {
        "success": bool,
        "thumbnail_url": str,
        "message": str
    }
    """
```

#### Modified Create Event Endpoint
```python
@app.route('/api/create_event', methods=['POST'])
def create_event():
    """
    Enhanced to accept optional thumbnail file
    Request: multipart/form-data with:
        - eventName, eventLocation, eventDate, eventCategory (form fields)
        - thumbnail (optional file)
    Response: {
        "success": bool,
        "event_id": str,
        "message": str
    }
    """
```

### Frontend Interfaces

#### Edit Event Modal
```javascript
function showEditModal(eventId, eventData) {
    // Display modal with form pre-populated with eventData
    // Form fields: name, location, date, category
    // Thumbnail preview with change button
}

function submitEventEdit(eventId, formData) {
    // Send PUT request to /api/events/<event_id>
    // Update UI on success
}
```

#### Thumbnail Management
```javascript
function handleThumbnailUpload(eventId, file) {
    // Validate file type
    // Send POST request to /api/events/<event_id>/thumbnail
    // Update thumbnail display
}

function previewThumbnail(file) {
    // Display thumbnail preview before upload
}
```

## Data Models

### Event Object (events_data.json)
```json
{
  "id": "event_xxxxxxxx",
  "name": "Event Name",
  "location": "Event Location",
  "date": "YYYY-MM-DD",
  "category": "Category",
  "image": "/api/events/event_xxxxxxxx/thumbnail",
  "photos_count": 0,
  "qr_code": "/api/qr_code/event_xxxxxxxx",
  "created_by_admin_id": 1,
  "created_by_user_id": null,
  "created_at": "ISO timestamp",
  "sample_photos": [],
  "thumbnail_filename": "thumbnail_xxxxxxxx.jpg"
}
```

### Thumbnail File Naming Convention
- Format: `thumbnail_<uuid>.<extension>`
- Location: `uploads/event_<event_id>/thumbnail_<uuid>.<extension>`
- Allowed extensions: .jpg, .jpeg, .png

## Error Handling

### Validation Errors
- **Missing required fields**: Return 400 with specific field errors
- **Invalid date format**: Return 400 with date format requirements
- **Invalid image format**: Return 400 with supported formats list
- **File too large**: Return 413 with size limit information

### Authorization Errors
- **Not authenticated**: Return 401 and redirect to login
- **Not event owner**: Return 403 with ownership error message
- **Session expired**: Return 401 and clear session

### File Operation Errors
- **Thumbnail upload failed**: Return 500 with error details, rollback changes
- **Old thumbnail deletion failed**: Log warning, continue with update
- **Events data file write failed**: Return 500, attempt recovery

### Data Integrity Errors
- **Event not found**: Return 404 with event ID
- **Corrupted events data**: Return 500, log error for manual recovery
- **Concurrent modification**: Use file locking or timestamp validation

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

After analyzing all acceptance criteria, several redundancies were identified:
- Requirements 1.2 and 1.4 both test data persistence after updates (consolidated into Property 1)
- Requirements 5.1, 5.2, 5.3, 5.4 all test the same behavior for different fields (consolidated into Property 6)
- Requirements 3.3 and 7.4 both test old thumbnail deletion (consolidated into Property 4)

The following properties provide comprehensive coverage without redundancy:

### Property 1: Event update persistence
*For any* event and any valid field modifications (name, location, date, category), when an admin submits an update, the Events Data File should contain the new values and not the old values.
**Validates: Requirements 1.2, 1.4**

### Property 2: Cancel preserves data
*For any* event, when an admin opens the edit modal, modifies fields, and then cancels, the Events Data File should remain unchanged from its state before the modal was opened.
**Validates: Requirements 1.5**

### Property 3: Image format validation
*For any* file with a non-image extension (not .png, .jpg, .jpeg), when an admin attempts to upload it as a thumbnail, the system should reject the upload.
**Validates: Requirements 2.2**

### Property 4: Thumbnail file persistence
*For any* valid image file uploaded as a thumbnail during event creation, the file should exist in the event's upload folder and the thumbnail path should be recorded in the Events Data File.
**Validates: Requirements 2.3, 2.4**

### Property 5: Thumbnail replacement cleanup
*For any* event with an existing thumbnail, when a new thumbnail is uploaded, the old thumbnail file should no longer exist in the filesystem and the Events Data File should reference only the new thumbnail path.
**Validates: Requirements 3.3, 3.4, 7.4**

### Property 6: Event field consistency across API
*For any* event field (name, location, date, category, thumbnail), when the field is updated, the `/events` API endpoint should return the new value for that event.
**Validates: Requirements 4.5, 5.1, 5.2, 5.3, 5.4, 5.5**

### Property 7: Unauthenticated request rejection
*For any* edit or thumbnail upload request without a valid admin session, the system should return a 401 unauthorized error.
**Validates: Requirements 6.1**

### Property 8: Authorization enforcement
*For any* event not created by the requesting admin, when that admin attempts to edit the event, the system should return a 403 forbidden error.
**Validates: Requirements 6.2**

### Property 9: Authorized edit success
*For any* event created by an admin, when that same admin submits valid edits, the system should return a success response and apply the changes.
**Validates: Requirements 6.3**

### Property 10: Thumbnail filename uniqueness
*For any* sequence of thumbnail uploads, the system should generate unique filenames such that no two thumbnails have the same filename.
**Validates: Requirements 7.2**

### Property 11: Thumbnail path format
*For any* thumbnail path stored in the Events Data File, the path should be servable by the existing photo serving endpoints (should match the expected URL format).
**Validates: Requirements 7.3**

### Property 12: Filename prefix convention
*For any* uploaded thumbnail, the saved filename should start with the prefix "thumbnail_".
**Validates: Requirements 7.1**

## Testing Strategy

### Unit Testing Framework
Use pytest for Python backend testing with the following test modules:

**Test Module: test_event_editing.py**
- Test update event endpoint with valid data
- Test update event endpoint with missing fields
- Test update event endpoint with unauthorized user
- Test update event endpoint for non-existent event
- Test thumbnail upload with valid image
- Test thumbnail upload with invalid file type
- Test thumbnail upload with oversized file
- Test thumbnail replacement (old file deletion)
- Test create event with thumbnail
- Test create event without thumbnail (uses default)

**Test Module: test_event_authorization.py**
- Test admin can edit own event
- Test admin cannot edit other admin's event
- Test non-admin cannot access edit endpoints
- Test expired session handling

### Property-Based Testing Framework
Use Hypothesis for Python property-based testing.

**Configuration:**
- Minimum 100 iterations per property test
- Use custom strategies for event data generation
- Test with various image formats and sizes

### Integration Testing
- Test full edit flow from frontend to backend
- Test thumbnail display across all pages
- Test concurrent edit scenarios
- Test file cleanup on thumbnail replacement

### Manual Testing Checklist
- Verify edit modal displays correct current values
- Verify changes reflect on all pages (homepage, discovery, detail, organizer)
- Verify thumbnail preview works correctly
- Verify old thumbnails are deleted when replaced
- Verify default thumbnail is used when none provided
- Test with various image formats and sizes
- Test error messages display correctly
- Test on different browsers
