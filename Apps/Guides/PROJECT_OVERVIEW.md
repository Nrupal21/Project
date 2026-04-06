# TravelGuide - Project Overview

## Project Description
TravelGuide is a comprehensive travel management platform that connects travelers with local guides, destinations, and tours. The application features a robust approval workflow for destination submissions, user management, booking system, and interactive tour planning.

## Tech Stack

### Backend
- **Framework**: Django 4.2
- **Database**: PostgreSQL
- **Authentication**: Django Allauth with 2FA support
- **API**: Django REST Framework with versioned API (v1)
- **Caching**: Redis
- **Task Queue**: Celery

### Frontend
- **Templating**: Django Templates
- **Styling**: Tailwind CSS with custom indigo/violet theme
- **JavaScript**: Vanilla JS with HTMX for dynamic interactions
- **Responsive Design**: Mobile-first approach with landscape support

### Infrastructure
- **Web Server**: Gunicorn with Nginx
- **Containerization**: Docker
- **CI/CD**: GitHub Actions
- **Monitoring**: Sentry

## Core Features

### 1. Destination Management
- User-submitted destinations with approval workflow
- Rich destination details with images and descriptions
- Region-based organization
- Search and filter functionality

### 2. Tour System
- Tour creation and management
- Booking system with availability tracking
- Tour categories and itineraries
- Review and rating system

### 3. User Management
- Role-based access control (Guides, Travelers, Admins)
- Profile management
- Authentication with 2FA
- Social login integration

### 4. Booking System
- Tour booking and management
- Calendar integration
- Email notifications
- Payment processing (Stripe integration)

### 5. Content Moderation
- Pending destination approval workflow
- Content flagging and reporting
- Admin moderation dashboard

## Project Structure

```
Guides/
├── accounts/           # User authentication and profiles
├── bookings/           # Tour booking logic
├── core/               # Core functionality and utilities
├── destinations/       # Destination management
├── emergency/          # Emergency contact information
├── notifications/      # Email and in-app notifications
├── reviews/            # Review and rating system
├── rewards/            # User rewards program
├── templates/          # HTML templates
├── tests/              # Test suite
├── tours/              # Tour management
└── transportation/     # Transportation options and routing
```

## Key Design Decisions

1. **Approval Workflow**: All user-submitted destinations go through a moderation queue before being published
2. **Responsive Design**: Fully responsive UI with special considerations for mobile landscape mode
3. **Performance**: Implemented caching, database optimization, and lazy loading
4. **Security**: Role-based access control, 2FA, and data validation throughout
5. **Documentation**: Comprehensive code documentation and developer handover guides

## Getting Started

### Prerequisites
- Python 3.10+
- PostgreSQL 13+
- Redis 6+
- Node.js 16+ (for frontend assets)

### Installation
1. Clone the repository
2. Set up a virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Set up environment variables (copy `.env.example` to `.env`)
5. Run migrations: `python manage.py migrate`
6. Start the development server: `python manage.py runserver`

## API Documentation
API documentation is available at `/api/v1/docs/` when running in development mode.

## Testing
Run the test suite with:
```bash
python manage.py test
```

## Deployment
The application is containerized using Docker and can be deployed using the provided `docker-compose.yml` file.

## Contributing
Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments
- Tailwind CSS for the utility-first CSS framework
- Django for the robust web framework
- HTMX for dynamic web interactions
- All contributors who have helped shape this project
