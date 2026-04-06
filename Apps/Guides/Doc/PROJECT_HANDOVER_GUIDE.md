# TravelGuide Project - Handover Guide

## Quick Start for New Developers

### Prerequisites
- Python 3.8+ installed
- PostgreSQL 12+ installed
- Git for version control
- Code editor (VS Code recommended)

### Initial Setup (15 minutes)

1. **Clone and Setup Environment**:
```bash
cd d:\Project\Python\Apps\Guides
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

2. **Database Setup**:
```bash
# Create PostgreSQL database
createdb -U postgres guides_db

# Execute database scripts
psql -U postgres -d guides_db -f sql/04_execute_all.sql
```

3. **Django Setup**:
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic
```

4. **Run Development Server**:
```bash
python manage.py runserver
# Access at: http://localhost:8000
# Admin at: http://localhost:8000/admin
```

## Project Architecture Overview

### Technology Stack
- **Backend**: Django 5.0+ with Python 3.8+
- **Database**: PostgreSQL with psycopg2
- **API**: Django REST Framework
- **Authentication**: Django-allauth with 2FA support
- **Frontend**: Django templates with Bootstrap
- **Security**: CSRF, XSS protection, 2FA, rate limiting

### Application Structure
```
TravelGuide/
├── accounts/        # User management, profiles, 2FA
├── destinations/    # Travel destinations and attractions
├── tours/          # Tour packages and booking
├── bookings/       # Reservation and payment system
├── itineraries/    # Trip planning functionality
├── reviews/        # Rating and review system
├── transportation/ # Travel logistics
├── emergency/      # Safety and emergency features
├── security/       # Advanced security features
├── core/          # Shared utilities and components
├── templates/     # HTML templates
├── static/        # CSS, JS, images
├── sql/           # Database scripts and schema
└── docs/          # Documentation
```

## Key Components Deep Dive

### 1. User Management (accounts/)
**What it does**: Complete user lifecycle management
**Key files**: `models.py` (UserProfile), `views.py` (auth logic), `forms.py` (registration)
**Database tables**: `auth_user`, `accounts_userprofile`, `accounts_userfavorite`

**Critical functions to understand**:
```python
# accounts/models.py
class UserProfile(models.Model):
    # Extends Django User with profile info, preferences, location data

# accounts/views.py  
def register_view(request):
    # Handles user registration with email verification

def login_view(request):
    # Custom login with rate limiting and 2FA support
```

### 2. Destinations Management (destinations/)
**What it does**: Manages travel locations and attractions
**Key files**: `models.py` (Region, Destination, Attraction), `views.py` (CRUD operations)
**Database tables**: `destinations_region`, `destinations_destination`, `destinations_attraction`

**Critical functions to understand**:
```python
# destinations/models.py
class Destination(models.Model):
    # Main destination entity with geographic data

# destinations/nearby_destinations.py
def find_nearby_destinations(destination, radius_km=100):
    # Location-based recommendation system
```

### 3. Tour Management (tours/)
**What it does**: Tour packages, scheduling, and booking integration
**Key files**: `models.py` (Tour, TourDate), `views.py` (tour display and booking)
**Database tables**: `tours_tour`, `tours_tourdate`, `tours_tourcategory`

**Critical functions to understand**:
```python
# tours/models.py
class Tour(models.Model):
    # Complete tour package with pricing and scheduling

class TourDate(models.Model):
    # Specific tour instances with availability tracking
```

### 4. Booking System (bookings/)
**What it does**: Handles reservations and payments
**Key files**: `models.py` (Booking, Payment), `views.py` (booking process)
**Database tables**: `bookings_booking`, `bookings_payment`

**Critical functions to understand**:
```python
# bookings/models.py
class Booking(models.Model):
    # Complete booking record with status workflow

def calculate_total_price(self):
    # Pricing calculation with discounts and fees
```

## Database Schema Understanding

### Core Relationships
```
Region (1:Many) → Destination (1:Many) → Attraction
                     ↓ (Many:Many)
                  Tour (1:Many) → TourDate
                     ↓ (1:Many)
                  Booking (1:Many) → Payment

User (1:Many) → UserProfile, Booking, Review
```

### Critical Tables to Monitor
1. **tours_tour**: Main tour data
2. **bookings_booking**: Revenue-generating bookings
3. **destinations_destination**: Core content
4. **auth_user**: User accounts
5. **bookings_payment**: Financial transactions

### Schema Maintenance
- Run `python check_schema.py` to verify Django-DB alignment
- Use `sql/03_migration_fixes.sql` for known model mismatches
- Monitor the tours table name/title field discrepancy

## Common Development Tasks

### Adding New Features

1. **New Django App**:
```bash
python manage.py startapp new_feature
# Add to INSTALLED_APPS in settings.py
# Create models, views, URLs, templates
```

2. **Database Changes**:
```bash
python manage.py makemigrations
python manage.py migrate
# Test with check_db.py script
```

3. **API Endpoints**:
```python
# In views.py
from rest_framework import viewsets
class NewFeatureViewSet(viewsets.ModelViewSet):
    queryset = NewFeature.objects.all()
    serializer_class = NewFeatureSerializer
```

### Testing and Validation

**Run Tests**:
```bash
python manage.py test
python manage.py test accounts  # Specific app
coverage run --source='.' manage.py test
coverage report
```

**Database Validation**:
```bash
python check_db.py        # Basic connectivity
python check_schema.py    # Schema validation
python simple_data_check.py  # Data availability
```

**Performance Testing**:
```bash
python manage.py shell
# Use Django ORM to test query performance
# Monitor with django-debug-toolbar
```

## Deployment Guide

### Development Environment
```bash
# Local development
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']
DATABASE = local PostgreSQL

# Run with:
python manage.py runserver
```

### Production Deployment

1. **Environment Configuration**:
```bash
# .env file (DO NOT commit)
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=your-production-key
DB_PASSWORD=secure-password
EMAIL_HOST_PASSWORD=app-password
```

2. **Database Setup**:
```bash
# Production PostgreSQL
createdb -U postgres guides_db_prod
psql -U postgres -d guides_db_prod -f sql/01_database_structure.sql
# Skip sample data for production
```

3. **Static Files**:
```bash
python manage.py collectstatic
# Configure CDN or web server for static file serving
```

4. **Security Checklist**:
- Change DEBUG to False
- Use strong SECRET_KEY
- Configure ALLOWED_HOSTS
- Enable HTTPS
- Set secure cookie flags
- Configure CSRF and XSS protection

### Performance Optimization

**Database Optimization**:
```sql
-- Add production indexes
CREATE INDEX CONCURRENTLY idx_tours_featured ON tours_tour(is_featured, is_active);
CREATE INDEX CONCURRENTLY idx_bookings_date ON bookings_booking(created_at);
-- Run VACUUM ANALYZE regularly
```

**Caching Strategy**:
```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

## Troubleshooting Guide

### Common Issues

1. **Database Connection Errors**:
```bash
# Check PostgreSQL service
pg_ctl status
# Verify credentials in .env
# Check firewall settings
```

2. **Migration Conflicts**:
```bash
python manage.py showmigrations
python manage.py migrate --fake-initial
# Or reset migrations if needed
```

3. **Tours Schema Mismatch**:
```sql
-- Known issue: tours table uses 'name' field but Django expects 'title'
-- Use sql/03_migration_fixes.sql to resolve
```

4. **Static Files Not Loading**:
```bash
python manage.py collectstatic --clear
# Check STATIC_URL and STATIC_ROOT settings
```

### Performance Issues

**Slow Queries**:
```python
# Enable query logging
LOGGING = {
    'loggers': {
        'django.db.backends': {
            'level': 'DEBUG',
        },
    },
}
```

**Memory Usage**:
```python
# Use select_related and prefetch_related
tours = Tour.objects.select_related('category').prefetch_related('dates')
```

## Maintenance Tasks

### Daily Tasks
- Monitor error logs: `tail -f logs/django.log`
- Check backup status
- Monitor application performance

### Weekly Tasks
- Run `python simple_data_check.py` for data integrity
- Review security logs
- Update dependencies: `pip list --outdated`

### Monthly Tasks
- Database maintenance: `VACUUM ANALYZE`
- Review and archive old bookings
- Update documentation
- Security audit

## Security Considerations

### Data Protection
- All user inputs are validated and sanitized
- Passwords use Django's built-in hashing
- Payment data follows PCI compliance guidelines
- Personal data handling follows GDPR requirements

### Access Control
```python
# User permissions
@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_view(request):
    # Admin-only functionality
```

### Monitoring
- Failed login attempts logged
- Payment transactions audited
- Database access monitored
- API rate limiting enabled

## Code Style and Standards

### Django Best Practices
- Follow Django naming conventions
- Use class-based views where appropriate
- Implement proper error handling
- Add docstrings to all functions (as per user requirement)
- Write comprehensive tests

### Database Best Practices
- Use migrations for all schema changes
- Add database constraints for data integrity
- Use appropriate field types
- Index frequently queried fields

## Contact and Support

### Code Documentation
- `CODE_EXPLAINER.md`: Project overview
- `ACCOUNTS_CODE_EXPLAINER.md`: User management details
- `DESTINATIONS_CODE_EXPLAINER.md`: Destination system details
- `TOURS_CODE_EXPLAINER.md`: Tour management details
- `CORE_APPS_CODE_EXPLAINER.md`: Supporting apps details
- `DATABASE_AND_UTILITIES_EXPLAINER.md`: Database and utilities

### Development Resources
- Django Documentation: https://docs.djangoproject.com/
- PostgreSQL Documentation: https://www.postgresql.org/docs/
- Django REST Framework: https://www.django-rest-framework.org/

### Emergency Procedures
1. **Database Corruption**: Use backups in `sql/backup/`
2. **Security Breach**: Disable affected accounts, review logs
3. **Performance Issues**: Enable debugging, check slow queries
4. **Payment Issues**: Verify gateway connectivity, check transaction logs

---

**Welcome to the TravelGuide project!** This comprehensive travel guide and booking platform is ready for further development and customization. The codebase follows Django best practices and includes extensive documentation for smooth handover to new developers.

**Next Steps for New Developers**:
1. Set up local development environment
2. Review code explainer documents
3. Run test suite to verify setup
4. Explore admin interface at `/admin`
5. Review API endpoints at `/api/`
6. Start with small feature additions to familiarize with codebase

The project is well-structured, documented, and ready for production deployment or further feature development.
