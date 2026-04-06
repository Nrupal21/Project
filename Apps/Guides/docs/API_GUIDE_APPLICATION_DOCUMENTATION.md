# Guide Application API Documentation

## Overview
This document provides detailed information about the Guide Application API endpoints, their expected request/response formats, error handling, and usage examples.

## API Endpoints

### Update Guide Application Status
Updates the status of a guide application or verification fields.

**URL:** `/accounts/api/guide-applications/<application_id>/update-status/`

**Method:** `POST`

**Authentication Required:** Yes (Staff only)

**Content Type:** `application/json`

**Request Headers:**
- `X-CSRFToken`: CSRF token required for POST requests
- `Content-Type`: application/json

### Request Formats

#### 1. Standard Status Update

Used for approving or rejecting guide applications.

```json
{
    "application_id": 123,
    "status": "approve",
    "reason": "Optional reason for rejection"
}
```

**Parameters:**
- `application_id`: ID of the guide application (integer, required)
- `status`: Status to set (string, required). Valid values: "approve", "reject"
- `reason`: Reason for rejection (string, optional, required when status="reject")

#### 2. Verification Status Update

Used for updating verification fields from the review interface.

```json
{
    "field": "id_verification",
    "status": true,
    "action": "update_verification_status"
}
```

**Parameters:**
- `field`: Field to update (string, required). Valid values: "id_verification", "background_check"
- `status`: Boolean status value (boolean, required)
- `action`: Must be "update_verification_status" (string, required)

### Response Format

Successful response:
```json
{
    "success": true,
    "message": "Application approved successfully",
    "new_status": "Approved",
    "status_class": "bg-green-100 text-green-800"
}
```

or for verification updates:
```json
{
    "success": true,
    "message": "ID verification status updated",
    "field": "id_verification",
    "status": true
}
```

Error response:
```json
{
    "success": false,
    "error": "Error message describing what went wrong"
}
```

## Error Codes

- `400 Bad Request`: Missing required parameters or invalid JSON
- `403 Forbidden`: User doesn't have permission to update application
- `404 Not Found`: Guide application not found
- `500 Internal Server Error`: Server-side error

## Client-Side Implementation

The API is typically called from the review interface using fetch:

```javascript
fetch('/accounts/api/guide-applications/123/update-status/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrftoken,
        'X-Requested-With': 'XMLHttpRequest'
    },
    body: JSON.stringify({
        field: 'id_verification',
        status: true,
        action: 'update_verification_status'
    })
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        // Handle success
    } else {
        // Handle error
    }
})
.catch(error => {
    console.error('Error:', error);
});
```

## Best Practices

1. Always include proper error handling for both client and server sides
2. Validate all user inputs before processing
3. Use appropriate HTTP status codes
4. Maintain detailed logging for troubleshooting
5. Include CSRF protection for all POST requests

## Known Issues and Limitations

- The API currently doesn't support bulk updates for multiple applications
- All status changes are logged but not audited with change history
