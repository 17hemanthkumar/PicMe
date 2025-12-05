# Implementation Plan

- [x] 1. Add thumbnail upload support to event creation





  - Modify the create event form to include a thumbnail upload field with preview
  - Update the `/api/create_event` endpoint to accept multipart form data with optional thumbnail file
  - Implement thumbnail file validation (format: PNG, JPG, JPEG)
  - Save thumbnail to event's upload folder with naming convention `thumbnail_<uuid>.<ext>`
  - Update events_data.json to store thumbnail_filename and update image path
  - Use default thumbnail path when no thumbnail is provided
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 1.1 Write property test for thumbnail file persistence


  - **Property 4: Thumbnail file persistence**
  - **Validates: Requirements 2.3, 2.4**

- [x] 1.2 Write property test for image format validation


  - **Property 3: Image format validation**
  - **Validates: Requirements 2.2**

- [x] 1.3 Write property test for thumbnail filename uniqueness


  - **Property 10: Thumbnail filename uniqueness**
  - **Validates: Requirements 7.2**

- [x] 1.4 Write property test for filename prefix convention


  - **Property 12: Filename prefix convention**
  - **Validates: Requirements 7.1**

- [x] 2. Create backend API endpoint for updating event details





  - Implement `PUT /api/events/<event_id>` endpoint
  - Add admin authentication and ownership validation
  - Accept JSON payload with name, location, date, category fields
  - Validate all required fields are present
  - Update the event record in events_data.json
  - Return updated event data in response
  - _Requirements: 1.2, 1.4, 6.1, 6.2, 6.3_

- [x] 2.1 Write property test for event update persistence


  - **Property 1: Event update persistence**
  - **Validates: Requirements 1.2, 1.4**

- [x] 2.2 Write property test for unauthenticated request rejection

  - **Property 7: Unauthenticated request rejection**
  - **Validates: Requirements 6.1**


- [x] 2.3 Write property test for authorization enforcement

  - **Property 8: Authorization enforcement**
  - **Validates: Requirements 6.2**


- [x] 2.4 Write property test for authorized edit success





  - **Property 9: Authorized edit success**
  - **Validates: Requirements 6.3**
-

- [x] 3. Create backend API endpoint for updating event thumbnail




  - Implement `POST /api/events/<event_id>/thumbnail` endpoint
  - Add admin authentication and ownership validation
  - Accept multipart form data with thumbnail file
  - Validate image format (PNG, JPG, JPEG)
  - Delete old thumbnail file if it exists
  - Save new thumbnail with unique filename
  - Update events_data.json with new thumbnail path
  - Return new thumbnail URL in response
  - _Requirements: 3.3, 3.4, 7.1, 7.2, 7.4_

- [x] 3.1 Write property test for thumbnail replacement cleanup


  - **Property 5: Thumbnail replacement cleanup**
  - **Validates: Requirements 3.3, 3.4, 7.4**

- [x] 3.2 Write property test for thumbnail path format


  - **Property 11: Thumbnail path format**
  - **Validates: Requirements 7.3**
-

- [x] 4. Create edit event modal in frontend




  - Add "Edit" button to each event card in the event organizer dashboard
  - Create edit modal HTML structure similar to existing modals
  - Implement `showEditModal(eventId, eventData)` function to open modal with pre-populated form
  - Add form fields for name, location, date, category
  - Display current thumbnail with preview
  - Add "Change Thumbnail" button to trigger file picker
  - Implement thumbnail preview when new file is selected
  - Add cancel button that closes modal without saving
  - _Requirements: 1.1, 3.1, 3.2_

- [x] 5. Implement edit form submission logic





  - Create `submitEventEdit(eventId, formData)` function
  - Send PUT request to `/api/events/<event_id>` with form data
  - Handle success response by updating the event card in the DOM without page refresh
  - Handle error responses with appropriate user feedback
  - Close modal on successful update
  - _Requirements: 1.2, 1.3, 1.5_

- [x] 5.1 Write property test for cancel preserves data


  - **Property 2: Cancel preserves data**
  - **Validates: Requirements 1.5**

- [x] 6. Implement thumbnail upload logic in edit modal





  - Create `handleThumbnailChange(eventId, file)` function
  - Validate file type on client side
  - Show thumbnail preview before upload
  - Send POST request to `/api/events/<event_id>/thumbnail` with file
  - Update thumbnail display in modal and event card on success
  - Handle upload errors with user feedback
  - _Requirements: 3.2, 3.3, 3.4, 3.5_

- [x] 7. Update event display components to use custom thumbnails





  - Modify event card rendering to use the `image` field from event data
  - Ensure thumbnail URLs are correctly constructed for API serving
  - Update homepage carousel to display custom thumbnails
  - Update event discovery page to display custom thumbnails
  - Update event detail page to display custom thumbnails
  - Test that default thumbnail displays when no custom thumbnail is set
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [x] 7.1 Write property test for event field consistency across API


  - **Property 6: Event field consistency across API**
  - **Validates: Requirements 4.5, 5.1, 5.2, 5.3, 5.4, 5.5**

- [x] 8. Add thumbnail serving endpoint



  - Implement `GET /api/events/<event_id>/thumbnail` endpoint
  - Serve thumbnail file from event's upload folder
  - Return 404 if thumbnail doesn't exist
  - Use existing file serving infrastructure
  - _Requirements: 7.5_

- [x] 9. Checkpoint - Ensure all tests pass





  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Test edit functionality across all pages





  - Verify edit modal opens with correct pre-populated data
  - Test updating each field individually and in combination
  - Verify changes reflect immediately on event organizer dashboard
  - Navigate to homepage and verify updated event details display correctly
  - Navigate to event discovery and verify updated event details display correctly
  - Navigate to event detail page and verify updated event details display correctly
  - Test with multiple events to ensure correct event is being edited
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 11. Test thumbnail functionality end-to-end





  - Test creating event with thumbnail
  - Test creating event without thumbnail (verify default is used)
  - Test changing thumbnail on existing event
  - Verify old thumbnail file is deleted after replacement
  - Test thumbnail display on all pages
  - Test with various image formats (PNG, JPG, JPEG)
  - Test with invalid file types (verify rejection)
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4_

- [x] 12. Test authorization and security





  - Test that non-authenticated users cannot access edit endpoints
  - Test that admins cannot edit events created by other admins
  - Test that admins can edit their own events
  - Test session expiration handling during edit
  - _Requirements: 6.1, 6.2, 6.3, 6.5_

- [x] 13. Final checkpoint - Ensure all tests pass





  - Ensure all tests pass, ask the user if questions arise.
