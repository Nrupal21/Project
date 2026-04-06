# Reviews App

## Overview
The Reviews app provides a comprehensive review and rating system for the TravelGuide platform. It allows users to leave reviews, upload images, comment on reviews, and mark reviews as helpful.

## Features

### 1. Review System
- Users can leave reviews on various content types (destinations, tours, etc.)
- Star-based rating system (1-5 stars)
- Rich text content with formatting
- Status tracking (pending, approved, rejected)
- Featured reviews highlighting

### 2. Review Images
- Multiple image uploads per review
- Image captions and alt text
- Primary image designation
- Automatic image optimization

### 3. Comments & Discussions
- Threaded comments on reviews
- Official responses from content owners
- Comment moderation
- Like/helpful voting system

### 4. Helpful Votes
- Users can mark reviews as helpful/not helpful
- Vote tracking and analytics
- Prevention of duplicate votes

## Models

### Review
Core model representing a user's review of a piece of content.

### ReviewImage
Stores images associated with reviews.

### ReviewComment
Represents comments on reviews, supporting threaded discussions.

### ReviewHelpful
Tracks user votes on review helpfulness.

## Admin Interface

The admin interface provides comprehensive management capabilities:
- Review moderation
- Image management
- Comment approval
- Helpful vote tracking
- Bulk actions for common tasks

## Signals

- Automatic rating calculation on review save/delete
- Image cleanup on deletion
- Notification triggers for new reviews/comments
- Helpful vote counters

## Templates

Templates are organized in the `templates/reviews/` directory:
- `list.html` - Display paginated list of reviews
- `detail.html` - Single review with comments and voting
- `form.html` - Review submission/editing form
- `_review.html` - Review partial template
- `_comment.html` - Comment partial template

## API Endpoints

All API endpoints are RESTful and require authentication:

- `GET /api/reviews/` - List reviews
- `POST /api/reviews/` - Create a review
- `GET /api/reviews/{id}/` - Retrieve a review
- `PUT/PATCH /api/reviews/{id}/` - Update a review
- `DELETE /api/reviews/{id}/` - Delete a review
- `POST /api/reviews/{id}/helpful/` - Mark as helpful
- `POST /api/reviews/{id}/comments/` - Add a comment

## Permissions

- Only authenticated users can create reviews
- Users can only edit/delete their own reviews
- Staff users can moderate all content
- Content owners can respond to reviews

## Settings

Add to your `settings.py`:

```python
INSTALLED_APPS = [
    # ...
    'reviews.apps.ReviewsConfig',
    # ...
]

# File upload settings
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Maximum number of images per review
REVIEW_MAX_IMAGES = 5

# Maximum image size in bytes (default: 2MB)
REVIEW_MAX_IMAGE_SIZE = 2 * 1024 * 1024

# Allowed image file types
REVIEW_ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif']
```

## Dependencies

- Django 3.2+
- Pillow (for image processing)
- django-crispy-forms (for forms)
- django-filter (for API filtering)

## Running Tests

```bash
python manage.py test reviews
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request
