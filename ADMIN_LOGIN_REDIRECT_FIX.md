# Admin Login Redirect Fix

## Problem
When admin logged in successfully, they were being redirected back to the user login page instead of the event organizer page.

## Root Cause
The `/event_organizer` route had the `@login_required` decorator which only checks for user login (`session.get('logged_in')`), not admin login (`session.get('admin_logged_in')`).

**Before:**
```python
@app.route('/event_organizer')
@login_required  # Only checks for user login!
def serve_event_organizer():
    return render_template('event_organizer.html')
```

When an admin tried to access `/event_organizer`, the `@login_required` decorator would:
1. Check if `session.get('logged_in')` exists
2. Find it doesn't exist (because admin uses `admin_logged_in`)
3. Redirect to login page

## Solution
Removed the `@login_required` decorator and added custom logic to allow both admin and user access.

**After:**
```python
@app.route('/event_organizer')
def serve_event_organizer():
    # Allow access for admins or logged-in users (organizers)
    if not session.get('admin_logged_in') and not session.get('logged_in'):
        return redirect(url_for('serve_index'))
    return render_template('event_organizer.html')
```

## How It Works Now

### For Admins:
1. Admin logs in via admin modal
2. Backend creates admin session with `admin_logged_in=True`
3. Backend returns `redirect: "/event_organizer"`
4. Frontend redirects to `/event_organizer`
5. Route checks: `session.get('admin_logged_in')` ✅ (True)
6. Admin successfully accesses event organizer page

### For Users:
1. User logs in via user login
2. Backend creates user session with `logged_in=True`
3. If user_type is 'organizer', redirects to `/event_organizer`
4. Route checks: `session.get('logged_in')` ✅ (True)
5. User successfully accesses event organizer page

### For Unauthorized:
1. Someone tries to access `/event_organizer` without logging in
2. Route checks both `admin_logged_in` and `logged_in`
3. Both are False
4. Redirects to index page

## Session Keys

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
- `backend/app.py` - Updated `/event_organizer` route

## Testing
- [x] Admin can login successfully
- [x] Admin is redirected to /event_organizer
- [x] Admin can access event organizer page
- [x] User organizers can still access event organizer page
- [x] Unauthorized users are redirected to index
