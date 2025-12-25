# 🍽️ Food Ordering System

![Project Banner](https://via.placeholder.com/1200x400/4F46E5/FFFFFF?text=Food+Ordering+System)

A modern, responsive web application built with Django and Tailwind CSS that provides a complete solution for online food ordering with a comprehensive restaurant management dashboard.

## ✨ Key Features

### 🛍️ Customer Features
- **Interactive Menu** - Browse food items with filters by category, price, and dietary preferences
- **User Authentication** - Secure signup and login with email verification
- **Shopping Cart** - Add/remove items, adjust quantities, and save for later
- **Order Tracking** - Real-time order status updates
- **Order History** - View past orders and reorder with one click
- **Multiple Payment Options** - Credit/Debit cards, UPI, and cash on delivery
- **Responsive Design** - Seamless experience across all devices

### 🏪 Restaurant Dashboard
- **Order Management** - View, accept, and update order status
- **Menu Management** - Add, edit, or remove menu items and categories
- **Inventory Tracking** - Monitor ingredient levels and receive low stock alerts
- **Sales Analytics** - Visual reports on sales performance and popular items
- **Staff Management** - Manage roles and permissions for restaurant staff
- **Table Reservation** - Manage table bookings and availability

### 👨‍💼 Admin Panel
- **User Management** - Manage customers, restaurants, and staff accounts
- **Content Management** - Update website content, banners, and promotions
- **System Configuration** - Configure delivery zones, payment methods, and tax settings
- **Reports & Analytics** - Comprehensive business intelligence dashboard
- **Support Tickets** - Handle customer and restaurant inquiries

## 🛠 Tech Stack

### Frontend
- **Framework**: HTML5, CSS3, JavaScript (ES6+)
- **UI Framework**: Tailwind CSS 3.x
- **Interactivity**: Alpine.js for reactive components
- **Icons**: Heroicons
- **Build Tool**: Vite.js

### Backend
- **Language**: Python 3.10+
- **Framework**: Django 4.2+
- **Authentication**: Django Allauth with JWT
- **API**: Django REST Framework
- **WebSockets**: Django Channels for real-time updates

### Database
- **Primary**: PostgreSQL 14+
- **Caching**: Redis
- **Search**: PostgreSQL Full-Text Search
- **Sessions**: Database-backed sessions with Redis cache

### DevOps
- **Containerization**: Docker & Docker Compose
- **CI/CD**: GitHub Actions
- **Monitoring**: Sentry for error tracking
- **Hosting**: AWS/GCP ready

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- PostgreSQL 14+
- Node.js 16+
- Redis (for caching and WebSockets)

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/food-ordering-system.git
   cd food-ordering-system
   ```

2. **Set up Python virtual environment**
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate
   
   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements/development.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Install frontend dependencies**
   ```bash
   npm install
   ```

6. **Run database migrations**
   ```bash
   python manage.py migrate
   ```

7. **Create a superuser**
   ```bash
   python manage.py createsuperuser
   ```

8. **Load sample data (optional)**
   ```bash
   python manage.py loaddata fixtures/*.json
   ```

9. **Start development servers**
   ```bash
   # Terminal 1: Django development server
   python manage.py runserver
   
   # Terminal 2: Frontend assets (Vite)
   npm run dev
   
   # Terminal 3: Redis (for caching and WebSockets)
   redis-server
   ```

10. **Access the application**
    - Frontend: http://localhost:3000
    - Admin Panel: http://localhost:8000/admin
    - API Documentation: http://localhost:8000/api/docs/
   - Customer Interface: http://127.0.0.1:8000/
   - Admin Panel: http://127.0.0.1:8000/admin/
   - Restaurant Dashboard: http://127.0.0.1:8000/restaurant/

## 📚 Project Structure

```
food-ordering-system/
├── core/               # Core application (settings, urls, etc.)
├── customer/           # Customer-facing views and models
├── restaurant/         # Restaurant dashboard and management
├── orders/             # Order processing logic
├── menu/               # Menu and food item management
├── static/             # Static files (CSS, JS, images)
│   ├── css/
│   ├── js/
│   └── images/
├── templates/             # Django templates
│   ├── base.html          # Base template
│   ├── includes/          # Reusable template components
│   └── [app_name]/        # App-specific templates
├── tests/                 # Test files
├── .env.example           # Example environment variables
├── manage.py              # Django management script
├── requirements/          # Python requirements
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
└── README.md              # This file
```

## 🧪 Running Tests

```bash
# Run all tests
python manage.py test

# Run specific test module
python manage.py test apps.orders.tests

# Run with coverage report
coverage run manage.py test
coverage report -m
```

## 🚀 Deployment

### Production Deployment with Docker

1. **Build and start containers**
   ```bash
   docker-compose -f docker-compose.prod.yml up --build -d
   ```

2. **Run migrations**
   ```bash
   docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
   ```

3. **Collect static files**
   ```bash
   docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --no-input
   ```

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DEBUG` | Enable debug mode | No | `False` |
| `SECRET_KEY` | Django secret key | Yes | - |
| `DATABASE_URL` | Database connection URL | Yes | - |
| `REDIS_URL` | Redis connection URL | No | `redis://localhost:6379/0` |
| `EMAIL_HOST` | SMTP server | Yes (production) | - |
| `EMAIL_PORT` | SMTP port | Yes (production) | 587 |
| `EMAIL_USE_TLS` | Use TLS for email | No | `True` |
| `DEFAULT_FROM_EMAIL` | Default sender email | Yes (production) | - |

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Django](https://www.djangoproject.com/) - The web framework for perfectionists with deadlines
- [Tailwind CSS](https://tailwindcss.com/) - A utility-first CSS framework
- [PostgreSQL](https://www.postgresql.org/) - The world's most advanced open source database
- [Docker](https://www.docker.com/) - Empowering App Development for Developers
- [Redis](https://redis.io/) - The open source, in-memory data store

## 📞 Support

For support, email support@foodorderingsystem.com or open an issue in the GitHub repository.
