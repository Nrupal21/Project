# Destination Submission Workflow

## Overview

This document explains the redesigned destination submission workflow for the TravelGuide platform. The workflow ensures that destinations submitted by local guides go through an approval process before being published, while managers and admins retain the ability to directly create and publish destinations.

## Workflow Components

### 1. User Role-Based Flow

- **Local Guides**: Submit destinations through a pending submission workflow
  - Submissions are stored in `PendingDestination` table
  - Require review and approval before publication
  - Receive notification emails about submission status
  - Earn reward points for approved submissions

- **Managers/Admins**: Can directly create and publish destinations
  - Submissions go straight to `Destination` table
  - Have approved status by default
  - No review process required

### 2. Key Classes and Templates

#### Views
- `DestinationCreateView`: Main entry point that routes users based on role
  - Redirects local guides to pending submission workflow
  - Allows direct creation for managers/admins
  - Located in `destinations/views.py`

- `PendingDestinationCreateView`: Handles pending submissions from local guides
  - Creates records in `PendingDestination` table
  - Sets approval status to PENDING
  - Located in `destinations/guide_views.py`

#### Models
- `Destination`: Main model for published destinations
- `PendingDestination`: Staging model for destinations awaiting approval
  - Mirrors fields from `Destination`
  - Includes additional approval workflow fields
  - Has `approve_and_transfer()` method to promote to `Destination`

#### Templates
- `destination_form.html`: Form for direct destination creation/editing
  - Used by managers/admins for direct publishing
  - Contains form for destination details and image uploads
  - Shows submission status notifications

- `pending_destination_form.html`: Form for pending destination submissions
  - Used by local guides
  - Shows approval process information
  - Contains tailored UI elements for review workflow

### 3. Approval Process

1. Local guide submits destination through pending form
2. Submission stored in `PendingDestination` table with PENDING status
3. Email notification sent to managers/admins about new submission
4. Manager/admin reviews submission
5. Upon approval:
   - `approve_and_transfer()` method called
   - Record created in `Destination` table
   - Images transferred to new destination
   - Email notification sent to submitter
   - Reward points awarded to submitter
6. Upon rejection:
   - Feedback provided to submitter
   - Status updated to REJECTED
   - Submitter can edit and resubmit

## Implementation Details

### Routing Logic

The `dispatch()` method in `DestinationCreateView` handles the routing logic:

```python
def dispatch(self, request, *args, **kwargs):
    if request.user.is_authenticated:
        # Check if the user is a local guide (not manager or admin)
        if request.user.role == 'LOCAL_GUIDE' and not (request.user.is_manager or request.user.is_admin):
            # Add a message explaining the redirect
            messages.info(
                request,
                'As a local guide, your destination submissions will be reviewed by our team before publication.'
            )
            # Redirect to the pending destination create view
            return redirect('destinations:pending_destination_create')
    
    # For managers, admins, or if somehow an unauthenticated user got here
    return super().dispatch(request, *args, **kwargs)
```

### Permission Logic

The `test_func()` method in `DestinationCreateView` ensures only managers and admins can access direct creation:

```python
def test_func(self):
    return self.request.user.is_authenticated and (self.request.user.is_manager or self.request.user.is_admin)
```

### UI Components

The destination form includes:
- Review process explanation for local guides
- Status indicators for pending submissions
- Tailored button text based on submission status
- Notification alerts for submission status

## Testing

A comprehensive test suite is available in `tests/test_destination_submission_workflow.py` covering:
- Role-based redirection
- Form submission handling
- Creation of records in correct tables
- Approval process verification
- Notification email sending

## User Experience

### Local Guide Experience
1. Navigate to destination creation
2. Automatically redirected to pending submission form
3. See explanation of review process
4. Submit form with "Submit for Review and Approval" button
5. Receive confirmation message
6. Receive email upon approval/rejection

### Manager/Admin Experience
1. Navigate to destination creation
2. Access direct creation form
3. Submit with "Save Changes" button
4. Destination published immediately

## Additional Considerations

- Images are properly handled and transferred during approval
- Email notifications keep all parties informed
- Reward points system integration rewards contribution
- Clear UI distinctions help users understand the workflow
