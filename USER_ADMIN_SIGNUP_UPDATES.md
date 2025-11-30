# User and Admin Signup Updates

## Overview
Updated the signup flows to ensure users and admins are properly separated, with users always going to the `users` table and admins going to the `admins` table.

## Changes Made

### 1. User Signup Page (signup.html)

**Removed:**
- Radio button selection for "Event Attendee" vs "Event Organizer"
- User type selection UI

**Changed:**
- All signups through /signup page now automatically create regular users (user_type = 'user')
- Hidden input field sets userType to 'user' by default
- JavaScript updated to always send userType as 'user'

**Result:**
- Simplified signup process
- All users created through /signup go to `users` table with user_type='user'
- No confusion about organizer vs attendee

### 2. Admin Signup Modal (index.html)

**Added:**
- "Confirm Password" field to admin signup form
- Password matching validation before submission

**Fields in Admin Signup:**
1. Organization Name (required)
2. Email (required)
3. Password (required, min 6 characters)
4. Confirm Password (required, min 6 characters)

**Validation:**
- Checks if password and confirm password match
- Shows error message if passwords don't match
- Prevents submission until passwords match

**JavaScript Updates:**
```javascript
function handleAdminSignup(event) {
    // ... get form values ...
    
    // Validate passwords match
    if (password !== confirmPassword) {
        document.getElementById('adminSignupError').textContent = 'Passwords do not match!';
        document.getElementById('adminSignupError').classList.remove('hidden');
        return;
    }
    
    // ... submit to /admin/register ...
}
```

### 3. Backend Admin Routes (app.py)

**Added Complete Admin Authentication System:**

#### `/admin/register` (POST)
- Accepts: organizationName, email, password
- Validates all fields are present
- Hashes password using werkzeug.security
- Checks if email already exists in `admins` table
- Inserts new admin into `admins` table
- Returns success/error response

#### `/admin/login` (POST)
- Accepts: email, password
- Validates credentials against `admins` table
- Uses password hash verification
- Creates admin session with:
  - `admin_logged_in`: True
  - `admin_id`: admin's ID
  - `admin_email`: admin's email
  - `admin_organization`: organization name
- Redirects to /event_organizer on success

#### `/admin/logout` (GET)
- Clears only admin session keys
- Preserves user session if exists
- Redirects to index page

#### `admin_required` decorator
- Checks for `admin_logged_in` in session
- Redirects to index if not authenticated
- Can be used to protect admin-only routes

## Database Tables

### Users Table
```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    user_type ENUM('user', 'organizer') DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Used for:**
- Regular users signing up through /signup page
- All user_type values are now 'user' by default

### Admins Table
```sql
CREATE TABLE admins (
    id SERIAL PRIMARY KEY,
    organization_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Used for:**
- Administrators signing up through admin modal on index page
- Event organizers who need admin privileges

## User Flows

### Regular User Signup:
1. Click "Get Started" button on index page
2. Fill out signup form:
   - Full Name
   - Email
   - Password
   - Confirm Password
3. Submit → Creates user in `users` table with user_type='user'
4. Redirected to login page
5. Login → Redirected to /homepage

### Admin Signup:
1. Click "Admin" button on index page
2. Click "Sign up" link in admin modal
3. Fill out admin signup form:
   - Organization Name
   - Email
   - Password
   - Confirm Password
4. Passwords must match
5. Submit → Creates admin in `admins` table
6. Success message → Switches to login form
7. Login with admin credentials
8. Redirected to /event_organizer

## Security Features

1. **Separate Tables**: Users and admins completely isolated
2. **Password Hashing**: Both use werkzeug.security
3. **Password Confirmation**: Both user and admin signup require matching passwords
4. **Email Uniqueness**: Checked in respective tables
5. **Session Isolation**: Different session keys for admin vs user
6. **Generic Error Messages**: Don't reveal whether email exists

## Testing Checklist

- [ ] User signup creates entry in `users` table
- [ ] User signup sets user_type to 'user'
- [ ] User signup validates password confirmation
- [ ] Admin signup creates entry in `admins` table
- [ ] Admin signup validates password confirmation
- [ ] Admin signup requires organization name
- [ ] Admin login works with admin credentials
- [ ] Admin login creates admin session
- [ ] Admin logout clears admin session only
- [ ] User and admin can't login with each other's credentials
- [ ] Email uniqueness enforced in each table separately

## Files Modified

1. **frontend/pages/signup.html**
   - Removed user type radio buttons
   - Set userType to always be 'user'
   - Updated JavaScript

2. **frontend/pages/index.html**
   - Added confirm password field to admin signup
   - Added password matching validation
   - Updated handleAdminSignup function

3. **backend/app.py**
   - Added `/admin/register` route
   - Added `/admin/login` route
   - Added `/admin/logout` route
   - Added `admin_required` decorator

4. **backend/sql.txt**
   - Fixed duplicate admin table
   - Added proper users table definition

## Benefits

1. **Clear Separation**: Users and admins are completely separate
2. **Simplified User Signup**: No confusing options for regular users
3. **Professional Admin Signup**: Requires organization name
4. **Better Security**: Password confirmation on both flows
5. **Proper Table Usage**: Each signup goes to correct table
6. **No Conflicts**: Emails can be different in each table
