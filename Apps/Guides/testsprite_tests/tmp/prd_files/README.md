# 🌍 Guides - Travel Booking and Itinerary Management System

A comprehensive Django 5.0+ web application that provides a complete solution for travel planning, destination management, and booking services with AI-powered features and a modern, responsive interface.

## 🚀 Project Overview

Guides is a full-featured travel management platform that enables users to discover destinations, book tours, and plan personalized itineraries. The platform includes a robust approval workflow for user-submitted content, ensuring quality and reliability. Built with scalability and user experience in mind, Guides offers a seamless experience across all devices.

## 🆕 Latest Updates

### 🎨 UI/UX Enhancements
- **Modern Design System**: Implemented a cohesive indigo/violet color palette with enhanced visual hierarchy
- **Responsive Layout**: Comprehensive mobile-first design with specific optimizations for landscape orientation
- **Interactive Components**: Enhanced user interface with smooth animations and transitions
- **Theme Support**: Integrated light/dark mode toggle with system preference detection
- **Accessibility**: Improved keyboard navigation and screen reader support

### 🛠️ Technical Improvements
- **Code Quality**: Comprehensive documentation with detailed function-level comments and type hints
- **API Versioning**: Implemented versioned API endpoints (v1) for stable integrations
- **Database Optimization**: Enhanced query performance with optimized indexes and prefetching
- **Security**: Strengthened authentication and data validation
- **Testing**: Expanded test coverage with integration and unit tests

### 🚀 New Features
- **Approval Workflow**: Complete submission and review system for user-generated content
- **Reward System**: Points-based incentives for active contributors
- **Enhanced Search**: Improved search functionality with filters and sorting
- **Real-time Updates**: WebSocket integration for live notifications
- **AI Integration**: Smart recommendations and itinerary generation

## ✨ Key Features

### 🏆 User Management
- **Multi-role System**: Travelers, Local Guides, and Administrators
- **Social Authentication**: Seamless login via Google, Facebook, and more
- **Profile Customization**: Rich user profiles with avatars and preferences
- **Two-Factor Authentication**: Enhanced security with 2FA support

### 🌐 Destination Management
- **Rich Content**: Detailed destination profiles with images and descriptions
- **Interactive Maps**: Integrated mapping with points of interest
- **Seasonal Information**: Best times to visit and weather data
- **User Submissions**: Community-driven content with approval workflow

### 📅 Itinerary Planning
- **AI-Powered Planning**: Smart itinerary generation based on preferences
- **Collaborative Editing**: Share and edit plans with travel companions
- **Real-time Sync**: Changes update across all devices instantly
- **Budget Tracking**: Expense management and cost estimation

### 🎫 Booking System
- **Unified Booking**: Tours, accommodations, and transportation in one place
- **Secure Payments**: Multiple payment gateway integration
- **Instant Confirmation**: Real-time booking status updates
- **Reservation Management**: Easy modifications and cancellations

### ⭐ Review System
- **Verified Reviews**: Authenticated user feedback
- **Rich Media**: Photo and video reviews
- **Response System**: Business owner responses to reviews
- **Moderation Tools**: Flagging and content moderation

### 🚨 Emergency Services
- **Local Emergency Info**: Country-specific emergency numbers
- **Safety Tips**: Destination-specific safety guidelines
- **Crisis Support**: 24/7 assistance for travelers
- **Medical Facilities**: Nearby hospitals and clinics

### 🚆 Transportation Management
- **Multi-modal Options**: Flights, trains, buses, and local transit
- **Route Optimization**: Smart suggestions for efficient travel
- **Real-time Updates**: Live tracking and delay notifications
- **Integrated Booking**: Seamless connection to transportation providers

## 🛠️ Technical Stack

### System Requirements
- **Python**: 3.10+
- **Database**: PostgreSQL 15+
- **Frontend**: Node.js 18+, npm 9+
- **Cache**: Redis 6+
- **Search**: Elasticsearch 8.0+
- **Message Broker**: RabbitMQ 3.10+
- **Web Server**: Nginx 1.21+, Gunicorn 20.1+

### Core Dependencies
| Component | Technology |
|-----------|------------|
| Backend Framework | Django 5.0+ |
| REST API | Django REST Framework 3.14+ |
| Frontend | Tailwind CSS 3.3+, Alpine.js |
| Real-time | Django Channels 4.0+ |
| Task Queue | Celery 5.3+ with Redis |
| AI/ML | OpenAI API, LangChain |
| Search | Django Haystack with Elasticsearch |
| Monitoring | Sentry, Silk, Prometheus |

### Development Dependencies
- **Code Quality**: black, isort, flake8, mypy
- **Testing**: pytest, factory-boy, pytest-django
- **Documentation**: Sphinx, MkDocs
- **CI/CD**: GitHub Actions, Docker, Docker Compose

### Project Structure
```
├── accounts/               # User authentication and profiles
├── destinations/           # Destination management
├── tours/                  # Tour packages and booking
├── itineraries/            # Itinerary planning
├── bookings/               # Reservation management
├── reviews/                # User reviews and ratings
├── emergency/              # Emergency services
├── transportation/         # Transportation options
├── core/                   # Core functionality and utilities
├── static/                 # Static files (CSS, JS, images)
├── templates/              # HTML templates
└── tests/                  # Test suite
```

## 🚀 Getting Started

### Prerequisites
- Python 3.10+ with pip
- PostgreSQL 15+ with PostGIS extension
- Redis server
- Node.js 18+ and npm 9+

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/guides.git
   cd guides
   ```

2. **Set up a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-ai.txt  # For AI features
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Set up the database**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

6. **Install frontend dependencies and build assets**
   ```bash
   cd frontend
   npm install
   npm run build
   cd ..
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```

## 🧪 Testing

Run the test suite with:
```bash
pytest
```

## 🛠 Development

### Code Style
- Follow PEP 8 guidelines
- Use Black for code formatting
- Write docstrings for all public functions and classes
- Include type hints for better code clarity

### Git Workflow
1. Create a new branch for your feature/fix
2. Make your changes with clear, atomic commits
3. Write tests for new functionality
4. Update documentation as needed
5. Create a pull request for review

## 🌐 Deployment

The application can be deployed using Docker and Docker Compose:

```bash
docker-compose up -d --build
```

### Production Checklist
- [ ] Set `DEBUG = False` in production
- [ ] Configure proper database backups
- [ ] Set up monitoring and alerting
- [ ] Configure HTTPS with Let's Encrypt
- [ ] Set up regular security updates
## 📚 Additional Documentation

For more detailed information, please refer to:
- [API Documentation](docs/API_DOCUMENTATION.md)
- [Database Schema](docs/DATABASE_SCHEMA.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Development Setup](docs/DEVELOPMENT.md)
## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/guides.git
cd guides
```

### 2. Set Up Python Environment

```bash
# Create and activate virtual environment
python -m venv venv
# Windows
.\venv\Scripts\activate
# Unix/macOS
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
pip install -r requirements-ai.txt  # For AI features
```

### 3. Set Up Frontend

```bash
# Install Node.js dependencies
npm install

# Build frontend assets
npm run build
```

### 4. Set Up Database

1. Create a PostgreSQL database
2. Update database settings in `.env` file
3. Run migrations:
   ```bash
   python manage.py migrate
   ```
4. Create superuser:
   ```bash
   python manage.py createsuperuser
   ```

### 6. Configure Environment

Create a `.env` file in the project root with the following variables:

```
# Django Settings
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
DJANGO_SETTINGS_MODULE=guides.settings

# Database Settings
DB_ENGINE=django.db.backends.postgresql
DB_NAME=guides_db
DB_USER=guides_user
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

# Redis Settings
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Email Settings
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-email-password

# Static Files Settings
STATIC_URL=/static/
STATIC_ROOT=staticfiles
MEDIA_URL=/media/
MEDIA_ROOT=media
```

### 6. Create a Superuser

```bash
python manage.py createsuperuser
```

### 5. Load Sample Data (Optional)

```bash
# Load initial data
python manage.py loaddata initial_data.json

# Or import from SQL (if available)
psql -U your_username -d your_database -f sql/04_execute_all.sql
```

### 6. Run Development Servers

```bash
# Start Redis (in a new terminal)
redis-server

# Start Celery worker (in a new terminal)
celery -A guides worker -l info

# Start Django development server
python manage.py runserver
```

Access the application at http://127.0.0.1:8000/

## 🌟 Features

### 🏞️ Destination Management
- Comprehensive destination database with rich media
- AI-powered destination recommendations
- User-generated content with moderation
- Interactive maps and location services

### 📅 Itinerary Planning
- AI-powered itinerary generation
- Day-by-day planning with drag-and-drop interface
- Budget tracking and optimization
- Offline access and sharing

### 🏨 Booking System
- Tour package booking
- Accommodation reservations
- Transportation options
- Secure payment processing

### 🔒 Security Features
- Two-factor authentication
- Role-based access control
- Data encryption at rest and in transit
- Regular security audits

### 📱 Mobile Responsive
- Fully responsive design
- Progressive Web App (PWA) support
- Offline functionality
- Native app-like experience

## 📚 API Documentation

The API documentation is automatically generated using Swagger/OpenAPI and is available at:
- **Development**: `http://localhost:8000/api/docs/`
- **Production**: `https://yourdomain.com/api/docs/`

### API Versioning
- Current API version: `v1`
- Versioned endpoints: `/api/v1/`
- Deprecation policy: Endpoints will be supported for at least 6 months after deprecation

## 🔒 Security

### Reporting Vulnerabilities
Please report security issues to security@yourdomain.com. We take all security issues seriously and will respond promptly.

### Security Features
- Rate limiting on authentication endpoints
- CSRF protection
- XSS protection
- SQL injection prevention
- Secure password hashing
- Content Security Policy (CSP) headers

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Read our [Code of Conduct](CODE_OF_CONDUCT.md)
2. Fork the repository
3. Create your feature branch (`git checkout -b feature/amazing-feature`)
4. Commit your changes (`git commit -m 'Add some amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

### Development Setup
See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed setup instructions.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Django Software Foundation for the amazing web framework
- All contributors who have helped improve this project
- The open-source community for their invaluable tools and libraries

## 📞 Contact

For questions or support, please contact:
- **Email**: support@yourdomain.com
- **Twitter**: [@guidesapp](https://twitter.com/guidesapp)
- **GitHub Issues**: [github.com/yourusername/guides/issues](https://github.com/yourusername/guides/issues)

## 🏗 Architecture

The application follows a clean architecture with the following layers:

### Backend
- **Django 5.0+**: Core web framework
- **Django REST Framework**: REST API implementation
- **Celery & Redis**: Asynchronous task processing
- **PostgreSQL**: Primary database with PostGIS extension
- **Elasticsearch**: Full-text search and analytics

### Frontend
- **Tailwind CSS**: Utility-first CSS framework
- **Alpine.js**: Minimal framework for JavaScript interactivity
- **HTMX**: For dynamic content loading
- **Webpack**: Asset bundling and optimization

## 📈 Performance

### Caching Strategy
- Redis for session storage and caching
- Database query optimization with `select_related` and `prefetch_related`
- Template fragment caching
- CDN integration for static and media files

### Monitoring
- **Sentry**: Error tracking and performance monitoring
- **Prometheus & Grafana**: System and application metrics
- **Uptime Monitoring**: External monitoring service integration
- Booking history and upcoming reservation dashboard
- Invoice and receipt generation for completed bookings

## REST API Documentation

### Overview
The application provides a comprehensive REST API built with Django REST Framework that enables programmatic access to destinations, attractions, bookings, and other features.

### Authentication
- Token-based authentication for secure API access
- Permission classes to control access based on user role

### Available Endpoints

#### Destinations API
- `GET /api/destinations/` - List all destinations with filtering and search
- `GET /api/destinations/{id}/` - Get a specific destination with detailed information
- `POST /api/destinations/` - Create a new destination (admin only)
- `PUT/PATCH /api/destinations/{id}/` - Update a destination (admin only)
- `DELETE /api/destinations/{id}/` - Delete a destination (admin only)

#### Regions API
- `GET /api/regions/` - List all regions
- `GET /api/regions/{id}/` - Get a specific region with its destinations

#### Attractions API
- `GET /api/attractions/` - List all attractions with filtering and search
- `GET /api/attractions/{id}/` - Get a specific attraction
- `POST /api/attractions/` - Create a new attraction (admin only)
- `PUT/PATCH /api/attractions/{id}/` - Update an attraction (admin only)
- `DELETE /api/attractions/{id}/` - Delete an attraction (admin only)

#### Nearby Destinations API
- `GET /api/nearby/?lat=<latitude>&lng=<longitude>&radius=<km>&limit=<n>` - Find destinations near a specified location using Haversine formula

### Important Technical Notes

#### Router Registration
When using Django REST Framework's DefaultRouter for registering ViewSets, ensure that either:
1. Each ViewSet has a class-level `queryset` attribute, or
2. Explicitly specify the `basename` parameter during router registration

Example:
```python
router = DefaultRouter()
router.register(r'api/attractions', AttractionViewSet, basename='attraction')
```

This prevents the common error: `AssertionError: basename argument not specified, and could not automatically determine the name from the viewset`.

### User Reviews
- Comprehensive rating and review system for destinations, tours, and accommodations
- Multi-criteria ratings (cleanliness, service, value, location, etc.)
- Photo and video uploads for review enhancement with automatic moderation
- Review verification system to confirm genuine customer experiences
- Helpful review voting and sorting by relevance
- Review response system for business owners
- Review analytics and reporting for business insights
- User reputation system with badges for frequent reviewers

### Emergency Information
- Local emergency contacts for destinations (police, ambulance, fire, embassy)
- Interactive maps showing nearby hospitals, clinics, and pharmacies
- Health and safety information specific to each destination
- Travel advisories and real-time alerts from official sources
- Natural disaster preparedness guidelines
- Emergency phrase translations in local languages
- Insurance information and claim procedures
- SOS button with location sharing functionality
- Offline access to critical emergency information

### Transportation Management
- Comprehensive transportation options between destinations (air, rail, bus, ferry, private transfer)
- Real-time schedule information and delay notifications
- Integrated booking with ticket generation and e-tickets
- Price comparison across different transport methods
- Route visualization on interactive maps
- Carbon footprint calculation for environmental awareness
- Transfer coordination between different transportation modes
- Airport/station pickup and drop-off arrangements
- Vehicle rental options with comparison and booking

## Development Guidelines

### Code Style
- Follow PEP 8 guidelines for Python code
- Use Django's coding style for templates and models
- Comment all functions and complex code sections for better maintainability
- Use descriptive variable and function names that reflect their purpose
- Organize imports alphabetically and group by standard library, third-party, and local imports
- Limit line length to 88 characters (using Black formatter standards)
- Use consistent indentation (4 spaces, no tabs)
- Document class and method behavior with docstrings in Google or NumPy format
- Add comprehensive comments to every function across all files
- Use detailed JSDoc-style comments for JavaScript functions
- Include HTML comments in template sections explaining their purpose
- Document CSS sections with comments explaining their functionality

### Version Control
- Use feature branches for all new development
- Write clear, descriptive commit messages
- Reference issue numbers in commit messages when applicable
- Create pull requests for code review before merging
- Squash commits before merging to maintain a clean history

### Database Management
- Create and apply migrations for all model changes
- Use Django ORM features instead of raw SQL when possible
- Add appropriate indexes for frequently queried fields
- Set appropriate on_delete behavior for foreign keys
- Use migrations for data transformations when needed
- Use provided SQL scripts in the `sql` directory for database setup:
  - `01_database_structure.sql`: Complete database schema
  - `02_sample_data.sql`: Comprehensive sample data (destinations, attractions, tours)
  - `03_migration_fixes.sql`: Fixes for model-database mismatches
  - `04_execute_all.sql`: Master script to run all SQL files in order

### Testing
- Write tests for all new features
- Run tests before committing changes: `python manage.py test`
- Use test files like `test_dynamic_destinations.py` and `test_rewards_system.py` as examples
- Run database diagnostics with `check_database.py` and `diagnose_destinations.py`

### Documentation
- Document all APIs using docstrings
- Keep README and other documentation updated
- Refer to the comprehensive code explainer files:
  - `CODE_EXPLAINER.md`: Main project overview and architecture
  - `accounts/ACCOUNTS_CODE_EXPLAINER.md`: User management system
  - `destinations/DESTINATIONS_CODE_EXPLAINER.md`: Destinations system
  - `tours/TOURS_CODE_EXPLAINER.md`: Tour management system
  - `CORE_APPS_CODE_EXPLAINER.md`: Supporting apps documentation
  - `DATABASE_AND_UTILITIES_EXPLAINER.md`: Database schema details
  - `PROJECT_HANDOVER_GUIDE.md`: Complete developer handover guide
  - `CODE_DOCUMENTATION_INDEX.md`: Master index of documentation
  - `TEMPLATES_AND_FRONTEND_EXPLAINER.md`: Frontend documentation
  - `FORMS_AND_ADMIN_EXPLAINER.md`: Forms and admin customization
  - `README_2FA.md`: Two-factor authentication implementation

## API Documentation

The project provides a REST API for integration with mobile apps or third-party services. API endpoints are available at `/api/` and require authentication.

### Available Endpoints

#### Authentication
- `POST /api/auth/token/` - Obtain JWT token
- `POST /api/auth/token/refresh/` - Refresh JWT token
- `POST /api/auth/register/` - Register new user

#### Destinations
- `GET /api/destinations/` - List all destinations
- `GET /api/destinations/{id}/` - Get destination details
- `GET /api/destinations/search/` - Search destinations

#### Tours
- `GET /api/tours/` - List all tours
- `GET /api/tours/{id}/` - Get tour details
- `GET /api/tours/search/` - Search tours
- `POST /api/tours/{id}/book/` - Book a tour

#### Itineraries
- `GET /api/itineraries/` - List user itineraries
- `POST /api/itineraries/` - Create new itinerary
- `GET /api/itineraries/{id}/` - Get itinerary details
- `PUT /api/itineraries/{id}/` - Update itinerary
- `DELETE /api/itineraries/{id}/` - Delete itinerary
- `GET /api/itineraries/public/` - List public itineraries

#### Reviews
- `GET /api/reviews/` - List all reviews
- `POST /api/reviews/` - Create new review
- `GET /api/reviews/{id}/` - Get review details

### Authentication
All API endpoints except authentication require a valid JWT token in the Authorization header:
```
Authorization: Bearer <token>
```

### Documentation
Detailed API documentation is available at `/api/docs/` when the server is running.

## Frontend Design

### Responsive Design
- Full responsive design with Tailwind CSS
- Mobile-first approach with specific optimizations for:
  - Mobile phones in portrait mode
  - Mobile phones in landscape orientation (special media queries)
  - Tablets (portrait and landscape)
  - Desktop devices
- Landscape orientation optimizations:
  - Adjusted navbar height and spacing
  - Scrollable mobile menu with proper height constraints
  - Optimized text sizes and padding
  - Improved bottom navigation with reduced height

### Color Scheme
- Primary color palette: Indigo/violet (replaces previous blue theme)
- Gradient combinations: indigo-500/600 to violet-600/700
- Dark mode support with appropriate color variants
- Enhanced visual effects with shadows, transitions, and hover states

### UI Components
- Modern, accessible form controls with appropriate feedback
- Interactive cards with hover effects
- Toast notifications for user feedback
- Responsive navigation with mobile menu and animations
- Theme toggle with light/dark mode support

## Deployment

The following instructions cover deploying the Guides project to various environments.

### Production Deployment Checklist

1. **Update Settings for Production**
   ```python
   # settings.py
   DEBUG = False
   ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']
   
   # Security settings
   SECURE_SSL_REDIRECT = True
   SESSION_COOKIE_SECURE = True
   CSRF_COOKIE_SECURE = True
   SECURE_BROWSER_XSS_FILTER = True
   SECURE_CONTENT_TYPE_NOSNIFF = True
   ```

2. **Set Up Environment Variables**
   - Create a secure `.env` file on the production server
   - Never commit production secrets to version control

3. **Configure Static and Media Files**
   - Run `python manage.py collectstatic`
   - Set up a CDN for serving static files in production

4. **Set Up Database Backup**
   - Configure automated backups
   - Test restoration procedures

### Deployment Options

#### 1. Docker Deployment

A `Dockerfile` and `docker-compose.yml` are included for containerized deployment.

```bash
# Build and start containers
docker-compose up -d --build

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser
```

#### 2. Traditional Hosting

```bash
# Set up Gunicorn as the application server
pip install gunicorn
gunicorn guides.wsgi:application --bind 0.0.0.0:8000

# Configure Nginx as reverse proxy
# Example nginx configuration:
# /etc/nginx/sites-available/guides
```

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /path/to/guides;
    }
    
    location /media/ {
        root /path/to/guides;
    }
    
    location / {
        include proxy_params;
        proxy_pass http://127.0.0.1:8000;
    }
}
```

#### 3. Platform as a Service (PaaS)

##### Heroku Deployment

```bash
# Install Heroku CLI
# Add Procfile to project root
web: gunicorn guides.wsgi --log-file -

# Create and deploy
heroku create guides-app
git push heroku main
heroku run python manage.py migrate
heroku run python manage.py createsuperuser
```

##### AWS Elastic Beanstalk

```bash
# Install EB CLI
pip install awsebcli

# Initialize and deploy
eb init
eb create guides-production
eb deploy
```

## Troubleshooting

### Installation Issues

#### Database Connection Errors
```
django.db.utils.OperationalError: could not connect to server: Connection refused
```
**Solution:** 
- Verify PostgreSQL is running: `pg_ctl status`
- Check database credentials in `.env` file
- Ensure the database exists: `psql -l`
- Confirm database user has proper permissions

#### Migration Errors
```
django.db.utils.ProgrammingError: relation already exists
```
**Solution:**
- Reset migrations with: `python manage.py migrate <app_name> zero`
- Re-apply migrations: `python manage.py migrate <app_name>`
- For complex cases: `python manage.py makemigrations --merge`

#### Static Files Not Loading
**Solution:**
- Run `python manage.py collectstatic`
- Check `STATIC_URL` and `STATIC_ROOT` in settings.py
- Verify file paths and permissions

#### Environment Variables Issues
**Solution:**
- Ensure `.env` file is in the correct location
- Check formatting of environment variables
- Restart the development server after changing variables

### Runtime Issues

#### Performance Problems
**Solution:**
- Check database query optimization
- Add indexing to frequently queried fields
- Enable database query caching
- Use Django debug toolbar to identify bottlenecks

#### Form Validation Errors
**Solution:**
- Check form field constraints match model field constraints
- Review custom form validation methods
- Inspect browser console for JavaScript errors

## License

[Specify your license information here]

## Contributors

[List main contributors here]

## Contact

For questions or support, please contact [Your contact information]
