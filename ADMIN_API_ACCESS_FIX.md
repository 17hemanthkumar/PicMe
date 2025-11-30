# Admin API Access Fix

## Problem
When admin tried to create events or perform other API operations, they received "Network error occurred" messages.

## Root Cause
Multiple API routes were using the `@login_required` decorator which only checks for user login (`session.get('logged_in')`), not admin login (`session.get('admin_logged_in')`).

When an admin tried to access these routes:
1. The `@login_required` decorator would check for `session.get('logged_in')`
2. Find it doesn't exist (because admin uses `admin_logged_in`)
3. Redirect to login page or return unauthorized
4. Frontend would show "Network error"

## Routes Fixed

### 1. `/api/create_event` (POST)
**Before:**
```python
@app.route('/api/create_event', methods=['POST'])
@login_required
def create_event():
```

**After:**
```python
@app.route('/api/create_event', methods=['POST'])
def create_event():
    # Allow access for admins or logged-in users
    if not session.get('admin_logged_in') and not session.get('logged_in'):
        return jsonify({"success": False, "error": "Unauthorized"}), 401
```

### 2. `/api/upload_photos/<event_id>` (POST)
**Before:**
```python
@app.route('/api/upload_photos/<event_id>', methods=['POST'])
@login_required
def upload_event_photos(event_id):
```

**After:**
```python
@app.route('/api/upload_photos/<event_id>', methods=['POST'])
def upload_event_photos(event_id):
    # Allow access for admins or logged-in users
    if not session.get('admin_logged_in') and not session.get('logged_in'):
        return jsonify({"success": False, "error": "Unauthorized"}), 401
```

### 3. `/api/my_events` (GET)
**Before:**
```python
@app.route('/api/my_events')
@login_required
def get_my_events():
```

**After:**
```python
@app.route('/api/my_events')
def get_my_events():
    # Allow access for admins or logged-in users
    if not session.get('admin_logged_in') and not session.get('logged_in'):
        return jsonify({"success": False, "error": "Unauthorized"}), 401
```

### 4. `/photos/<event_id>/<person_id>/<photo_type>/<filename>` (GET)
**Before:**
```python
@app.route('/photos/<event_id>/<person_id>/<photo_type>/<filename>')
@login_required
def get_private_photo(event_id, person_id, photo_type, filename):
```

**After:**
```python
@app.route('/photos/<event_id>/<person_id>/<photo_type>/<filename>')
def get_private_photo(event_id, person_id, photo_type, filename):
    # Allow access for admins or logged-in users
    if not session.get('admin_logged_in') and not session.get('logged_in'):
        return "Unauthorized", 401
```

## Routes That Still Use @login_required

These routes are for regular users only and should keep the `@login_required` decorator:

- `/homepage` - User homepage
- `/event_discovery` - Browse events
- `/event_detail` - View event details
- `/biometric_authentication_portal` - Face scan
- `/personal_photo_gallery` - User's personal photos
- `/recognize` - Face recognition API

## How It Works Now

### For Admins:
1. Admin logs in → `admin_logged_in=True` in session
2. Admin tries to create event → `/api/create_event` checks `admin_logged_in` ✅
3. Event created successfully
4. Admin can upload photos, view events, etc.

### For Users:
1. User logs in → `logged_in=True` in session
2. User (if organizer) tries to create event → `/api/create_event` checks `logged_in` ✅
3. Event created successfully
4. User can upload photos, view events, etc.

### For Unauthorized:
1. Someone tries to access API without logging in
2. Route checks both `admin_logged_in` and `logged_in`
3. Both are False
4. Returns 401 Unauthorized error

## Session Keys Reference

### Admin Session:
- `admin_logged_in`: True
- `admin_id`: admin's ID
- `admin_email`: admin's email
- `admin_organization`: organization name

### User Session:
- `logged_in`: True
- `user_id`: user's ID
- `user_email`: user's email
- `user_type`: 'user' or 'organizer'

## Files Modified
- `backend/app.py` - Updated 4 API routes to allow admin access

## Testing Checklist
- [x] Admin can create events
- [x] Admin can upload photos
- [x] Admin can view their events
- [x] Admin can access private photos
- [x] User organizers can still create events
- [x] User organizers can still upload photos
- [x] Unauthorized users get 401 error
