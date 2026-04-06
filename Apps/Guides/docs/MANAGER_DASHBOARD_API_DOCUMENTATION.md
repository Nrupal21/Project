# Manager Dashboard API Documentation

## Overview

This document provides information about the AJAX API endpoints used by the Manager Dashboard for destination approval and rejection functionality. These endpoints are designed to handle AJAX requests and return proper JSON responses for seamless user experience.

## API Endpoints

### Destination Approval API

**Endpoint:** `/api/v1/destinations/admin/approve-destination/<int:pk>/`

**Method:** POST

**Authentication:** Requires user to be authenticated and have manager or admin role

**Description:** Approves a destination and makes it visible on the site

**Request Format:**
```json
{
  // No body required for approval
}
```

**Response Format:**
```json
{
  "success": true,
  "message": "Destination \"Destination Name\" has been approved and is now visible on the site. Notification sent to username.",
  "destination_id": 123,
  "destination_name": "Destination Name",
  "notification_sent": true
}
```

**Error Responses:**
```json
{
  "success": false,
  "message": "Could not approve destination \"Destination Name\". It may already be approved."
}
```

```json
{
  "success": false,
  "message": "You do not have permission to perform this action"
}
```

### Destination Rejection API

**Endpoint:** `/api/v1/destinations/admin/reject-destination/<int:pk>/`

**Method:** POST

**Authentication:** Requires user to be authenticated and have manager or admin role

**Description:** Rejects a destination with a specific reason

**Request Format:**
```json
{
  "rejection_reason": "This destination does not meet our quality standards because..."
}
```

**Response Format:**
```json
{
  "success": true,
  "message": "Destination \"Destination Name\" has been rejected. Notification sent to username.",
  "destination_id": 123,
  "destination_name": "Destination Name",
  "notification_sent": true
}
```

**Error Responses:**
```json
{
  "success": false,
  "message": "Please provide a reason for rejecting the destination."
}
```

```json
{
  "success": false,
  "message": "Could not reject destination \"Destination Name\". It may have already been processed."
}
```

## Implementation Details

### Security Features

1. **Authentication Check**: All endpoints verify that the user is authenticated
2. **Role-Based Access Control**: Only users with manager or admin roles can access these endpoints
3. **CSRF Protection**: All requests require a valid CSRF token
4. **Input Validation**: Rejection reasons are validated before processing

### Error Handling

1. **Detailed Error Messages**: All error responses include descriptive messages
2. **Comprehensive Logging**: All actions are logged for auditing and debugging
3. **Transaction Management**: Database operations use transactions to ensure data integrity

### Frontend Integration

The Manager Dashboard uses fetch API to communicate with these endpoints:

1. **JSON Content Type**: All requests and responses use application/json content type
2. **CSRF Token Handling**: Frontend automatically includes CSRF token in all requests
3. **UI Updates**: Dashboard UI is updated based on API responses without page reload
4. **Notification System**: Success and error messages are displayed to users via notifications

## Troubleshooting

If you encounter issues with the API endpoints:

1. Check browser console for JavaScript errors
2. Verify that the CSRF token is being correctly included in requests
3. Check server logs for detailed error messages
4. Ensure the user has appropriate permissions (manager or admin role)
5. Verify that the destination ID exists and is in a valid state for the requested action
