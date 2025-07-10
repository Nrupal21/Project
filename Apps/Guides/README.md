# 🏝️ Guides - Multi-Destination Tourism & Booking Platform

A full-featured travel guide and accommodation booking website that operates across multiple destinations, offering detailed insights into destinations, user reviews, accommodations, nearby attractions, transportation options, and customizable travel itineraries.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-4.2-brightgreen.svg)](https://www.djangoproject.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-green.svg)](https://www.mongodb.com/cloud/atlas)

## 📌 Table of Contents
- [Project Overview](#-project-overview)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Installation & Setup](#-installation--setup)
- [Environment Variables](#-environment-variables)
- [Running the Application](#-running-the-application)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [API Documentation](#-api-documentation)
- [Contributing](#-contributing)
- [License](#-license)
- [Acknowledgements](#-acknowledgements)

## 📖 Project Overview
This multi-destination tourism platform helps travelers explore and book experiences across numerous destinations by offering:

- Comprehensive destination profiles with regional grouping, seasonal information, and visitor statistics
- User authentication and authorization with social login (Google, Facebook)
- Secure payment processing for bookings
- Real-time availability checking and booking management
- User reviews and ratings system
- Search and filtering capabilities
- Responsive design for all devices

## 🚀 Features

### 🔐 Authentication & User Management
- User registration and login
- Social authentication (Google, Facebook)
- Password reset and account recovery
- Profile management
- Role-based access control

### 🏨 Accommodation & Booking
- Property listings with detailed information
- Real-time availability calendar
- Booking management
- Review and rating system
- Wishlist and saved items

### 🗺️ Destination Management
- Comprehensive destination information
- Points of interest
- Local events and activities
- Weather information
- Travel guides and tips

### 🚗 Transportation
- Transportation options between destinations
- Route planning
- Booking management
- Real-time tracking

### 📱 Mobile Responsive
- Fully responsive design
- Mobile-first approach
- Touch-friendly interfaces
- Offline capabilities

## 🛠️ Tech Stack

### Backend
- **Framework**: Django 4.2
- **Database**: MongoDB Atlas
- **API**: Django REST Framework
- **Authentication**: Django Allauth
- **Caching**: Redis
- **Task Queue**: Celery
- **Search**: Built-in Django search

### Frontend
- HTML5, CSS3, JavaScript (ES6+)
- Bootstrap 5
- jQuery
- AJAX for dynamic content
- Responsive design

### DevOps & Tools
- Docker
- GitHub Actions (CI/CD)
- Sentry (Error Tracking)
- AWS S3 (Media Storage)
- Heroku/Google Cloud Platform (Deployment)

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8+
- MongoDB Atlas account
-
- Git

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/guides.git
   cd guides
   ```

2. **Create and activate a virtual environment**
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate
   
   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the project root and add the required variables:
   ```env
   DEBUG=True
   SECRET_KEY=your-secret-key-here
   MONGODB_URI=your-mongodb-connection-string
   GOOGLE_OAUTH2_CLIENT_ID=your-google-client-id
   GOOGLE_OAUTH2_CLIENT_SECRET=your-google-client-secret
   FACEBOOK_APP_ID=your-facebook-app-id
   FACEBOOK_APP_SECRET=your-facebook-app-secret
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create a superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the admin panel**
   Visit `http://127.0.0.1:8000/admin/` and log in with your superuser credentials.

## 🌐 Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DEBUG` | Enable debug mode | No | `False` |
| `SECRET_KEY` | Django secret key | Yes | - |
| `MONGODB_URI` | MongoDB connection string | Yes | - |
| `GOOGLE_OAUTH2_CLIENT_ID` | Google OAuth client ID | No | - |
| `GOOGLE_OAUTH2_CLIENT_SECRET` | Google OAuth client secret | No | - |
| `FACEBOOK_APP_ID` | Facebook App ID | No | - |
| `FACEBOOK_APP_SECRET` | Facebook App Secret | No | - |

## 🏃 Running the Application

### Development
```bash
python manage.py runserver
```

### Production
```bash
gunicorn tourism.wsgi:application --bind 0.0.0.0:8000
```

## 🧪 Testing

Run the test suite:
```bash
python manage.py test
```

## 🚀 Deployment

### Heroku
[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

### Docker
Build and run with Docker:
```bash
# Create docker-compose.yml file first
docker-compose up --build
```

Note: Docker configuration file needs to be created. See the project's wiki for details.

## 📚 API Documentation

API documentation is available at `/api/docs/` when running the development server.

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgements

- [Django](https://www.djangoproject.com/)
- [MongoDB](https://www.mongodb.com/)
- [Bootstrap](https://getbootstrap.com/)
- [Font Awesome](https://fontawesome.com/)
- [Unsplash](https://unsplash.com/) for sample images

- **Accommodation System**
  - Dynamic availability calendar with occupancy management
  - Flexible pricing with seasonal adjustments
  - Booking add-ons and custom services
  - Promotion and discount code management
  - Room type classification with amenities

- **Tour & Activity Bookings**
  - Pre-designed tour packages across multiple destinations
  - Activity booking with time slots and capacity management
  - Tour guide profiles with expertise and languages
  - Participant information management

- **Transportation Network**
  - Multi-modal transportation options
  - Route scheduling with stops and timing
  - Fare calculation with variables and discounts
  - Seat availability and booking

- **Emergency Resources**
  - Categorized emergency contacts by destination
  - Medical facility listings with services and hours
  - Safety alerts and notifications

- **Interactive Maps Integration**
  - Location-based recommendations
  - Route visualization and navigation
  - Distance-based filtering

🗓️ Travel Itinerary Builder

👤👍 User Features
- Comprehensive user profiles with travel preferences and interests
- Notification system for bookings, promotions, and travel alerts
- Save favorite destinations, stays, and itineraries 
- Add/read/vote on reviews for destinations and stays
- Upload photos with reviews to share experiences
- Create/edit/share travel itineraries with other users
- Track booking history across destinations
- Personalized recommendations based on interests and travel style

🏨 Stay Booking
Directory of hotels and villas

Filters: location, budget, amenities

Contact or booking links

Show “Verified stays” and user ratings

🔐 Admin Features
Dashboard to manage destinations, stays, reviews

Add/edit/delete content and itinerary templates

View and moderate user-generated itineraries

Analytics: user visits, bookings, review trends

⚙️ Tech Stack
- **Backend Framework**: Django (Python)
- **Database**: mongo atlas
- **Frontend**: HTML, CSS, JavaScript
- **User Authentication**: Django Allauth
- **Media Management**: Django Pillow
- **Form Processing**: Django Forms
- **Phone Validation**: django-phonenumber-field
- **Maps Integration**: Google Maps API (future implementation)
- **Payment Processing**: Integration-ready for Stripe/PayPal
- **Security**: HTTPS (SSL), CSRF protection, secure sessions

💻 Installation & Setup

### Prerequisites
- Python 3.8+
- pip
- virtualenv (recommended)

### Installation Steps
```bash
# Clone the repository
git clone https://github.com/yourusername/guides.git
cd guides

# Create virtual environment
python -m venv venv

# On Windows
venv\Scripts\activate
# On macOS/Linux
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Apply migrations
python manage.py migrate

# Create a superuser
python manage.py createsuperuser

# Run the development server
python manage.py runserver
```

### Environment Configuration
- Create a `.env` file in the project root (for production)
- Set environment variables like SECRET_KEY, DEBUG, DATABASE_URL
- Configure email, storage, and third-party API settings
📁 Folder Structure
guides/
├── tourism/                # Project settings and main configuration
├── templates/             # HTML templates
├── static/                # CSS, JS, images
├── accounts/              # User profiles and authentication
│   └── models.py          # Profile, Interests, TravelPreference, SavedItem, Notification
├── bookings/              # Accommodation and tour booking
│   └── models.py          # Stay, RoomType, Booking, Availability, BookingAddOn, TourPackage, etc.
├── destinations/          # Destination information and management
│   └── models.py          # Destination, Region, Season, Event, GuideProfile, etc.
├── reviews/               # User ratings and feedback system
│   └── models.py          # Review, ReviewImage, ReviewVote, ReviewReplyNotification, etc.
├── emergency/             # Emergency contacts and safety information
│   └── models.py          # EmergencyContact, SafetyAlert, MedicalFacility, etc.
├── itineraries/           # Travel planning and itinerary builder
│   └── models.py          # Itinerary, ItineraryDay, ItineraryItem, ItinerarySharedUser, etc.
├── transportation/         # Transport options and bookings
│   └── models.py          # TransportationType, Route, RouteStop, RouteSchedule, etc.
├── media/                 # User-uploaded content (not in version control)
├── manage.py
└── requirements.txt
📝 Content Management
Accessible via Django admin interface (/admin) for:

- **Destination Management**
  - Adding/editing destinations with regional classification
  - Managing seasonal information and visitor statistics
  - Creating events and maintaining guide profiles
  - Uploading destination documents and images

- **Accommodation Management**
  - Configuring room types and availability calendars
  - Setting up booking add-ons and promotions
  - Managing stays and their facilities
  - Creating tour packages with scheduled dates

- **User & Content Moderation**
  - Reviewing and moderating user-generated content
  - Managing user profiles and preferences
  - Monitoring bookings and payment statuses
  - Configuring transportation routes and schedules

## 🌍 Deployment
- Set up environment variables
- Use GitHub + Heroku/Render for CI/CD
- Enable HTTPS, CSP, and security headers
- Configure MongoDB Atlas for production

🧱 Future Enhancements

- **Payment Integration**
  - Complete payment gateway integration (Stripe/PayPal)
  - Automated booking confirmation and refunds
  - Multi-currency support

- **Advanced Search & Discovery**
  - AI-powered itinerary recommendations
  - Personalized destination matching
  - Voice search capabilities

- **Enhanced User Experience**
  - Progressive Web App (PWA) support
  - Native mobile applications
  - Offline itinerary access

- **Operations & Analytics**
  - Enhanced booking analytics dashboard
  - Dynamic yield management for stays
  - Predictive booking trends

- **Interactive Features**
  - Real-time weather integration
  - AR/VR destination previews
  - Social media sharing integration
  - Live chat support for bookings

📄 License
This project is licensed under the MIT License.

📱 Design and Branding
Travel-themed logo

Warm color palette with natural tones

Clean typography for readability

Custom icons for destinations and features

Mobile-first responsive layout

📲 Mobile-Friendly Design
The platform is fully responsive and optimized for mobile users:

- **Adaptive Interface**
  - Fully responsive design for all device sizes
  - Touch-optimized UI elements and controls
  - Simplified navigation on smaller screens

- **Performance Optimization**
  - Optimized image loading for slower connections
  - Reduced payload size for mobile networks
  - Strategic caching for frequent access

- **Mobile-Specific Features**
  - Geolocation for nearby recommendations
  - Click-to-call emergency contacts
  - Mobile-friendly booking flows
  - Offline access to booked itineraries