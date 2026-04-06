# TravelGuide Project - Comprehensive Handover Documentation

## Project Overview
TravelGuide is a comprehensive travel platform built with Django that connects travelers with local guides, destinations, and tours. The platform features a robust destination management system, tour booking functionality, user authentication, and a reward system.

## Table of Contents
1. [Quick Start Guide](#quick-start-guide)
2. [System Architecture](#system-architecture)
3. [Database Schema](#database-schema)
4. [Key Features](#key-features)
5. [API Endpoints](#api-endpoints)
6. [Authentication & Authorization](#authentication--authorization)
7. [Frontend Structure](#frontend-structure)
8. [Development Workflow](#development-workflow)
9. [Deployment](#deployment)
10. [Troubleshooting](#troubleshooting)
11. [Future Enhancements](#future-enhancements)

## Quick Start Guide

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- Node.js 14+ (for frontend assets)
- Git

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Guides
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-ai.txt  # For AI features
   ```

4. **Database setup**
   ```bash
   createdb -U postgres guides_db
   psql -U postgres -d guides_db -f sql/04_execute_all.sql
   ```

5. **Apply migrations**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py collectstatic
   ```

6. **Run development server**
   ```bash
   python manage.py runserver
   ```
   - Application: http://localhost:8000
   - Admin: http://localhost:8000/admin

## System Architecture

### Technology Stack
- **Backend**: Django 5.0+
- **Frontend**: HTML5, Tailwind CSS, JavaScript
- **Database**: PostgreSQL 12+
- **Caching**: Redis (optional)
- **Search**: Django Haystack with Whoosh (optional)
- **Async Tasks**: Celery with Redis

### Project Structure
```
Guides/
├── accounts/           # User management
├── destinations/       # Destinations and attractions
├── tours/             # Tour management
├── bookings/          # Booking system
├── reviews/           # Review system
├── rewards/           # Loyalty and rewards
├── security/          # Security features
├── core/              # Core functionality
├── static/            # Static files
└── templates/         # HTML templates
```

## Database Schema

### Key Tables
- `accounts_userprofile` - Extended user profiles
- `destinations_destination` - Travel destinations
- `destinations_attraction` - Points of interest
- `tours_tour` - Available tours
- `bookings_booking` - Tour bookings
- `reviews_review` - User reviews
- `rewards_reward` - Reward points system

### Sample Data
Sample data is available in `sql/02_sample_data.sql` with:
- 6 destinations
- 10+ attractions
- 6 tours with 18 tour dates
- 8 tour categories

## Key Features

### 1. Destination Management
- Comprehensive destination information
- Image galleries
- Local guides system
- Pending approval workflow for new destinations

### 2. Tour System
- Tour creation and management
- Booking system
- Availability calendar
- Tour categories and filtering

### 3. User System
- Role-based access control (Guides, Travelers, Admins)
- Two-factor authentication
- Profile management
- Wishlists and favorites

### 4. Rewards System
- Points for contributions
- Badges and achievements
- Referral program

## API Endpoints

### Version 1 (/api/v1/)
- `/destinations/` - Destination listings and details
- `/tours/` - Tour information and booking
- `/reviews/` - User reviews
- `/bookings/` - Booking management
- `/users/` - User profiles and authentication

## Authentication & Authorization

### Authentication Methods
1. Email/Password
2. Social Authentication (Google, Facebook)
3. Two-Factor Authentication (2FA)

### User Roles
1. **Admin**: Full system access
2. **Guide**: Can create/manage tours and destinations
3. **Traveler**: Can book tours and leave reviews

## Frontend Structure

### Key Templates
- `base.html` - Main template with navigation
- `destinations/` - Destination-related templates
- `tours/` - Tour-related templates
- `accounts/` - User account templates
- `components/` - Reusable UI components

### Styling
- **Framework**: Tailwind CSS
- **Color Scheme**: Indigo/Violet palette
- **Responsive Design**: Mobile-first approach

## Development Workflow

### Branching Strategy
- `main` - Production-ready code
- `develop` - Integration branch
- `feature/*` - New features
- `bugfix/*` - Bug fixes
- `hotfix/*` - Critical production fixes

### Code Style
- Follow PEP 8 for Python
- Use Black for code formatting
- Document all functions with docstrings
- Write unit tests for new features

## Deployment

### Production Stack
- **Web Server**: Nginx
- **Application Server**: Gunicorn
- **Database**: PostgreSQL with PgBouncer
- **Caching**: Redis
- **Media Storage**: AWS S3

### Environment Variables
```
DEBUG=False
SECRET_KEY=your-secret-key
DATABASE_URL=postgres://user:pass@localhost:5432/guides_db
REDIS_URL=redis://localhost:6379/0
EMAIL_HOST=smtp.sendgrid.net
DEFAULT_FROM_EMAIL=your-email@example.com
```

## Troubleshooting

### Common Issues
1. **Database Connection Issues**
   - Verify PostgreSQL is running
   - Check database credentials in settings.py

2. **Static Files Not Loading**
   - Run `python manage.py collectstatic`
   - Check STATIC_ROOT and STATIC_URL settings

3. **Email Sending Problems**
   - Verify SMTP settings
   - Check spam folder
   - Test with console email backend first

## Future Enhancements

### Planned Features
1. **Mobile App**
   - React Native application
   - Offline capabilities

2. **AI Recommendations**
   - Personalized destination suggestions
   - Chatbot for travel assistance

3. **Enhanced Analytics**
   - User behavior tracking
   - Revenue and booking analytics

### Technical Debt
1. Refactor legacy views to class-based views
2. Implement comprehensive API documentation with Swagger
3. Add more unit and integration tests

## Support
For any questions or issues, please contact the development team at [team-email@example.com](mailto:team-email@example.com).

---
*Documentation last updated: September 14, 2025*
