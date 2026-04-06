# Role-Based Login System Documentation

## Overview

This document explains the role-based login implementation for the TravelGuide project. The system uses a single user table with embedded JSON permissions to manage user roles and permissions efficiently.

## User Roles

The system supports the following roles:

- **ADMIN**: Full system access and management capabilities
- **MANAGER**: Management access to specific areas of the system
- **LOCAL_GUIDE**: Content creation and management for destinations
- **TRAVELER**: Standard user access for booking tours and reviewing destinations

## Database Schema

### User Table Fields

The `auth_user` table has been enhanced with the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `role` | VARCHAR | User role (ADMIN, MANAGER, LOCAL_GUIDE, TRAVELER) |
| `permissions` | JSONB | Role-specific permissions stored as JSON |
| `role_assigned_at` | TIMESTAMP | When the role was assigned |
| `role_assigned_by_id` | INTEGER | Foreign key to the admin user who assigned the role |

## Authentication Process

1. A user submits the login form with either username or email
2. The `RoleBasedAuthBackend` authenticates the user:
   - Checks if the input is an email or username
   - Verifies the password
   - Loads the user's role and permissions
3. Upon successful authentication, the user's role is stored in the session
4. The user is redirected based on their role:
   - Admins to the admin dashboard
   - Managers to the management dashboard
   - Local guides to the guides dashboard
   - Travelers to the home page

## Permission System

Permissions are stored in a JSON structure within the user table:

```json
{
  "module_permissions": {
    "destinations": ["read", "create", "update"],
    "tours": ["read"],
    "users": ["read"]
  },
  "object_permissions": {
    "can_create_attraction": true,
    "can_publish_tour": false
  }
}
```

### Permission Checking

The system provides two methods for checking permissions:

1. **Module-level permissions**: Check if a user can perform an action on a module
   ```python
   user.has_module_permission('destinations', 'create')
   ```

2. **Object-level permissions**: Check if a user can perform a specific action
   ```python
   user.has_object_permission('can_create_attraction')
   ```

## Implementation Details

### User Model (accounts/models.py)

- Enhanced with role field, permissions JSONField, and role tracking
- Provides methods for permission checks
- Automatically assigns default permissions based on role

### Authentication Backend (accounts/backends.py)

- Supports login by email or username
- Integrates with Django's permission system
- Enhances security with failed login tracking

### Forms (accounts/forms.py)

- `LoginForm`: Supports both username and email login
- `RegisterForm`: Includes role selection during registration

### Views (accounts/auth_views.py)

- `UserLoginView`: Handles authentication and role-based redirection
- `UserRegisterView`: Creates users with appropriate roles and permissions

## Migration Process

The SQL script `05_user_roles.sql` handles:

1. Adding new columns to the user table if they don't exist
2. Migrating user roles from old tables into the single-table structure
3. Setting up default permissions for each role
4. Removing legacy role tables after migration

## Security Considerations

- Role changes are logged with timestamp and admin user
- Failed login attempts are tracked
- Session-based role storage for UI customization
- Admin role can only be assigned programmatically, not via forms

## Usage Examples

### Checking User Role

```python
if user.is_admin:
    # Admin-specific functionality
elif user.is_local_guide:
    # Guide-specific functionality
```

### Checking Permissions

```python
if user.has_module_permission('destinations', 'update'):
    # Allow destination updates
    
if user.has_object_permission('can_approve_reviews'):
    # Show review approval options
```

### Role-Based UI

```python
{% if request.session.user_role == 'ADMIN' %}
    <!-- Show admin controls -->
{% elif request.session.user_role == 'LOCAL_GUIDE' %}
    <!-- Show guide controls -->
{% endif %}
```

## Further Enhancements

- Role transition workflow and approval process
- Role-based notification system
- Permission inheritance and custom permission sets
- Role-based API access control
