# Implementation Plan: Download Page Feature

- [x] 1. Create backend API endpoint for user photos





  - Implement `/api/user_photos` GET endpoint in `backend/app.py`
  - Add authentication check using `@login_required` decorator
  - Query processed folder structure to find all photos for authenticated user's person_id
  - Aggregate photos across all events with event metadata
  - Return JSON response with events, photos, and counts
  - _Requirements: 2.1, 2.2_

- [ ]* 1.1 Write property test for user photos API
  - **Property 2: Photo ownership verification**
  - **Validates: Requirements 2.1**

- [x] 2. Create download page HTML structure





  - Create `frontend/pages/download_page.html` with base layout
  - Add navigation header with Downloads link
  - Implement responsive grid layout using Tailwind CSS
  - Add filter controls section (event and photo type dropdowns)
  - Add download controls section (selected count, download button)
  - Add download history section
  - Add full-size preview modal structure
  - _Requirements: 1.1, 1.2, 5.1, 7.1, 8.1, 8.2, 8.3_

- [x] 3. Implement photo loading and display





  - Add JavaScript to fetch user photos from `/api/user_photos` on page load
  - Implement event card rendering with expand/collapse functionality
  - Implement photo grid rendering with checkboxes
  - Add loading states and error handling
  - Handle empty state when no photos exist
  - _Requirements: 2.1, 2.3, 3.1_

- [ ]* 3.1 Write property test for event display
  - **Property 2: Event field display**
  - **Validates: Requirements 2.2**

- [ ]* 3.2 Write property test for event sorting
  - **Property 3: Event date sorting**
  - **Validates: Requirements 2.4**

- [x] 4. Implement photo selection functionality








  - Add click handlers for photo checkboxes
  - Implement selection state management using Set data structure
  - Add "Select All" button for each event
  - Add "Deselect All" button to clear all selections
  - Update selected count display on selection changes
  - Enable/disable download button based on selection state
  - _Requirements: 3.2, 3.3, 3.4, 3.5, 4.1, 4.2_

- [ ]* 4.1 Write property test for selection state consistency
  - **Property 3: Selection state consistency**
  - **Validates: Requirements 3.3**

- [ ]* 4.2 Write property test for download button state
  - **Property 4: Download button state**
  - **Validates: Requirements 4.1, 4.2**

- [x] 5. Implement download functionality




  - Add click handler for download button
  - Implement single photo direct download
  - Implement multi-photo ZIP download using existing `/api/download_photos` endpoint
  - Add loading state during download
  - Display success message on completion
  - Display error message on failure and preserve selections
  - _Requirements: 4.3, 4.4, 4.5, 4.6, 4.7_

- [ ]* 5.1 Write property test for ZIP filename sanitization
  - **Property 5: ZIP filename sanitization**
  - **Validates: Requirements 4.5**

- [ ]* 5.2 Write property test for download error handling
  - **Property 6: Selection preservation on error**
  - **Validates: Requirements 4.7**

- [x] 6. Implement filter functionality




  - Add event filter dropdown with all events
  - Add photo type filter (All, Individual, Group)
  - Implement filter application logic
  - Update photo grid display based on active filters
  - Preserve photo selections when filters change
  - _Requirements: 5.2, 5.3, 5.4, 5.5, 5.6_

- [ ]* 6.1 Write property test for filter application
  - **Property 6: Filter application**
  - **Validates: Requirements 5.2, 5.3, 5.4**

- [ ]* 6.2 Write property test for filter selection preservation
  - **Property 7: Filter selection preservation**
  - **Validates: Requirements 5.6**

- [x] 7. Implement photo preview modal





  - Add click handler to open modal on photo thumbnail click
  - Implement modal navigation (previous/next photo)
  - Add download button for current photo in modal
  - Implement keyboard navigation (Escape to close, arrows to navigate)
  - Add close button click handler
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ]* 7.1 Write property test for modal keyboard navigation
  - **Property 8: Escape key closes modal**
  - **Validates: Requirements 6.4**

- [x] 8. Implement download history





  - Create localStorage manager for download history
  - Add download history entry on successful download
  - Implement download history display with date, event name, photo count
  - Sort history entries by timestamp descending
  - Limit display to 10 most recent entries
  - Handle empty history state
  - _Requirements: 7.2, 7.3, 7.4, 7.5_

- [ ]* 8.1 Write property test for download history ordering
  - **Property 8: Download history ordering**
  - **Validates: Requirements 7.3**

- [ ]* 8.2 Write property test for download history limit
  - **Property 9: Download history limit**
  - **Validates: Requirements 7.5**

- [x] 9. Add download page route to backend




  - Add route `/download_page` in `backend/app.py`
  - Apply `@login_required` decorator
  - Render `download_page.html` template
  - _Requirements: 1.2, 1.3_

- [ ]* 9.1 Write property test for authentication enforcement
  - **Property 1: Authentication enforcement**
  - **Validates: Requirements 1.3**

- [x] 10. Update navigation menu





  - Add "Downloads" link to navigation in all relevant pages
  - Update `homepage.html`, `event_discovery.html`, `event_detail.html`, `personal_photo_gallery.html`
  - Ensure consistent navigation across all pages
  - _Requirements: 1.1_

- [x] 11. Implement responsive design





  - Test and adjust mobile layout (single column)
  - Test and adjust tablet layout (two columns)
  - Test and adjust desktop layout (four columns)
  - Implement mobile hamburger menu if needed
  - Ensure filter controls stack vertically on mobile
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 12. Add error handling and edge cases











  - Implement network error handling with retry
  - Handle session expiration with redirect
  - Add empty state messages
  - Implement resource limit handling (max ZIP size)
  - Add user-friendly error messages
  - _Requirements: All error handling from design_

- [x] 13. Checkpoint - Ensure all tests pass





  - Ensure all tests pass, ask the user if questions arise.
