# Requirements Document

## Introduction

This feature enables event organizers (admins) to edit event details after creation and manage event thumbnails. Currently, admins can create events and upload photos, but cannot modify event information once created. This feature adds full CRUD capabilities for event management, including the ability to set custom thumbnails during creation and update them later. All changes must reflect across all pages where event information is displayed (homepage, event discovery, event detail, event organizer dashboard).

## Glossary

- **Admin**: An authenticated user with admin privileges who can create and manage events through the event organizer dashboard
- **Event**: A collection of photos and metadata including name, location, date, category, and thumbnail image
- **Thumbnail**: A representative image for an event displayed in event cards and listings
- **Event Organizer Dashboard**: The admin interface located at `/event_organizer` where admins manage their events
- **Events Data File**: The JSON file at `events_data.json` that stores all event metadata
- **Default Thumbnail**: The placeholder image at `/static/images/default_event.jpg` used when no custom thumbnail is set

## Requirements

### Requirement 1

**User Story:** As an admin, I want to edit event details after creation, so that I can correct mistakes or update information as the event evolves.

#### Acceptance Criteria

1. WHEN an admin clicks an edit button on an event card THEN the system SHALL display a modal with a form pre-populated with current event details
2. WHEN an admin modifies event name, location, date, or category and submits THEN the system SHALL update the event data in the Events Data File
3. WHEN event details are updated THEN the system SHALL reflect the changes immediately on the Event Organizer Dashboard without requiring a page refresh
4. WHEN event details are updated THEN the system SHALL persist the changes to the Events Data File on the server
5. WHEN an admin cancels the edit operation THEN the system SHALL close the modal without saving changes

### Requirement 2

**User Story:** As an admin, I want to upload a custom thumbnail when creating an event, so that my event has a distinctive visual identity from the start.

#### Acceptance Criteria

1. WHEN an admin views the create event form THEN the system SHALL display a thumbnail upload field
2. WHEN an admin selects an image file for the thumbnail THEN the system SHALL validate that the file is an image format (PNG, JPG, JPEG)
3. WHEN an admin submits the create event form with a thumbnail THEN the system SHALL save the thumbnail to the event's upload folder
4. WHEN a thumbnail is uploaded during event creation THEN the system SHALL store the thumbnail path in the Events Data File
5. WHEN no thumbnail is provided during event creation THEN the system SHALL use the Default Thumbnail path

### Requirement 3

**User Story:** As an admin, I want to change an event's thumbnail after creation, so that I can update the visual representation as better photos become available.

#### Acceptance Criteria

1. WHEN an admin opens the edit event modal THEN the system SHALL display the current thumbnail image
2. WHEN an admin clicks a change thumbnail button THEN the system SHALL allow selection of a new image file
3. WHEN an admin uploads a new thumbnail THEN the system SHALL replace the old thumbnail file in the event's upload folder
4. WHEN a thumbnail is updated THEN the system SHALL update the thumbnail path in the Events Data File
5. WHEN a thumbnail is updated THEN the system SHALL display the new thumbnail immediately in all event cards without page refresh

### Requirement 4

**User Story:** As an admin, I want thumbnail changes to appear everywhere the event is displayed, so that users see consistent and up-to-date event information.

#### Acceptance Criteria

1. WHEN an event's thumbnail is updated THEN the system SHALL serve the new thumbnail on the homepage event carousel
2. WHEN an event's thumbnail is updated THEN the system SHALL serve the new thumbnail on the event discovery page
3. WHEN an event's thumbnail is updated THEN the system SHALL serve the new thumbnail on the event detail page
4. WHEN an event's thumbnail is updated THEN the system SHALL serve the new thumbnail on the Event Organizer Dashboard
5. WHEN the system serves event data via the `/events` API endpoint THEN the system SHALL include the current thumbnail path for each event

### Requirement 5

**User Story:** As an admin, I want event detail changes to appear everywhere the event is displayed, so that all users see accurate and current event information.

#### Acceptance Criteria

1. WHEN an event's name is updated THEN the system SHALL display the new name on all pages that show event information
2. WHEN an event's location is updated THEN the system SHALL display the new location on all pages that show event information
3. WHEN an event's date is updated THEN the system SHALL display the new date on all pages that show event information
4. WHEN an event's category is updated THEN the system SHALL display the new category on all pages that show event information
5. WHEN the system serves event data via the `/events` API endpoint THEN the system SHALL include all current event details

### Requirement 6

**User Story:** As an admin, I want the edit functionality to be secure, so that only I can modify my own events.

#### Acceptance Criteria

1. WHEN a non-authenticated user attempts to access the edit event API endpoint THEN the system SHALL return an unauthorized error
2. WHEN an admin attempts to edit an event they did not create THEN the system SHALL return an unauthorized error
3. WHEN an admin edits their own event THEN the system SHALL process the update successfully
4. WHEN the system validates edit permissions THEN the system SHALL check the admin session and match the admin_id with the event's created_by_admin_id
5. WHEN an admin session expires THEN the system SHALL reject edit requests and redirect to the login page

### Requirement 7

**User Story:** As an admin, I want thumbnail files to be stored properly, so that they persist and load correctly across the application.

#### Acceptance Criteria

1. WHEN a thumbnail is uploaded THEN the system SHALL save it to the event's upload folder with a recognizable filename prefix
2. WHEN a thumbnail is uploaded THEN the system SHALL generate a unique filename to prevent conflicts
3. WHEN the system stores a thumbnail path THEN the system SHALL use a relative path format that works with the existing photo serving endpoints
4. WHEN a thumbnail is replaced THEN the system SHALL delete the old thumbnail file from the server
5. WHEN the system serves a thumbnail THEN the system SHALL use the existing photo serving infrastructure to deliver the image file
