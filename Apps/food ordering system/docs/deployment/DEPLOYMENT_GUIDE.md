# 🚀 Food Ordering System - Deployment Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Database Setup](#database-setup)
4. [Running the Application](#running-the-application)
5. [Creating Admin User](#creating-admin-user)
6. [Production Deployment](#production-deployment)

---

## Prerequisites

### Required Software
- **Python 3.10+** - [Download](https://www.python.org/downloads/)
- **PostgreSQL 14+** - [Download](https://www.postgresql.org/download/)
- **pip** - Python package manager (comes with Python)
- **virtualenv** - For creating isolated Python environments

### Windows Specific
```powershell
# Install Python packages
pip install virtualenv
```

---

## Local Development Setup

### 1. Create Virtual Environment

**Windows (PowerShell):**
```powershell
# Navigate to project directory
cd "d:\Project\Python\Apps\food ordering system"

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# If you get execution policy error, run:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Linux/macOS:**
```bash
cd /path/to/food-ordering-system
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```powershell
# Install all required packages
pip install -r requirements.txt

# Verify installation
pip list
```

### 3. Configure Environment Variables

```powershell
# Copy example environment file
copy .env.example .env

# Edit .env file with your settings
notepad .env
```

**Important Settings to Update:**
- `SECRET_KEY` - Generate a new secret key
- `DB_PASSWORD` - Your PostgreSQL password
- `EMAIL_HOST_USER` - Your email for notifications
- `EMAIL_HOST_PASSWORD` - Your email password or app password

---

## Database Setup

### 1. Install PostgreSQL

Download and install PostgreSQL from [postgresql.org](https://www.postgresql.org/download/)

### 2. Create Database

**Using pgAdmin:**
1. Open pgAdmin
2. Right-click on "Databases"
3. Select "Create" → "Database"
4. Name: `food_ordering_db`
5. Click "Save"

**Using psql Command Line:**
```sql
-- Connect to PostgreSQL
psql -U postgres

-- Create database
CREATE DATABASE food_ordering_db;

-- Create user (optional)
CREATE USER food_ordering_user WITH PASSWORD 'your-password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE food_ordering_db TO food_ordering_user;

-- Exit
\q
```

### 3. Run Migrations

```powershell
# Create migration files
python manage.py makemigrations

# Apply migrations to database
python manage.py migrate

# Verify migrations
python manage.py showmigrations
```

---

## Running the Application

### 1. Create Superuser

```powershell
# Create admin account
python manage.py createsuperuser

# Follow prompts to enter:
# - Username
# - Email address
# - Password
```

### 2. Collect Static Files

```powershell
python manage.py collectstatic --noinput
```

### 3. Start Development Server

```powershell
# Start Django development server
python manage.py runserver

# Server will start at: http://127.0.0.1:8000/
```

### 4. Access the Application

- **Customer Interface:** http://127.0.0.1:8000/
- **Restaurant Dashboard:** http://127.0.0.1:8000/restaurant/
- **Admin Panel:** http://127.0.0.1:8000/admin/

---

## Creating Admin User

### Method 1: Using createsuperuser command
```powershell
python manage.py createsuperuser
```

### Method 2: Using Django Shell
```powershell
python manage.py shell
```

```python
from django.contrib.auth.models import User

# Create superuser
user = User.objects.create_superuser(
    username='admin',
    email='admin@example.com',
    password='admin123'
)
print(f"Superuser {user.username} created successfully!")
```

---

## Adding Sample Data

### Using Django Admin

1. Login to admin panel: http://127.0.0.1:8000/admin/
2. Add Categories:
   - Appetizers
   - Main Course
   - Desserts
   - Beverages
3. Add Menu Items with prices and images

### Using Django Shell

```powershell
python manage.py shell
```

```python
from menu.models import Category, MenuItem

# Create categories
appetizers = Category.objects.create(
    name='Appetizers',
    description='Start your meal right',
    display_order=1
)

main_course = Category.objects.create(
    name='Main Course',
    description='Our signature dishes',
    display_order=2
)

# Create menu items
MenuItem.objects.create(
    category=appetizers,
    name='Spring Rolls',
    description='Crispy vegetable spring rolls',
    price=120.00,
    dietary_type='veg',
    preparation_time=15
)

MenuItem.objects.create(
    category=main_course,
    name='Butter Chicken',
    description='Creamy tomato-based curry',
    price=350.00,
    dietary_type='non_veg',
    preparation_time=25
)

print("Sample data added successfully!")
```

---

## Production Deployment

### 1. Update Settings

In `.env` file:
```env
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
SECRET_KEY=your-production-secret-key
```

### 2. Use Production Server

```powershell
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn food_ordering.wsgi:application --bind 0.0.0.0:8000
```

### 3. Serve Static Files

```powershell
# Collect all static files
python manage.py collectstatic --noinput

# Configure your web server (Nginx/Apache) to serve from staticfiles/
```

### 4. Security Checklist

- [ ] Change SECRET_KEY to a strong random value
- [ ] Set DEBUG=False
- [ ] Configure ALLOWED_HOSTS
- [ ] Set up HTTPS/SSL
- [ ] Use environment variables for sensitive data
- [ ] Set up database backups
- [ ] Configure firewall rules
- [ ] Enable CSRF protection
- [ ] Set secure cookie flags

---

## Troubleshooting

### Issue: psycopg2 installation fails

**Solution:**
```powershell
# Install binary version
pip install psycopg2-binary
```

### Issue: Port 8000 already in use

**Solution:**
```powershell
# Use different port
python manage.py runserver 8080
```

### Issue: Static files not loading

**Solution:**
```powershell
# Collect static files
python manage.py collectstatic

# Check STATIC_ROOT and STATIC_URL in settings.py
```

### Issue: Database connection error

**Solution:**
1. Verify PostgreSQL is running
2. Check database credentials in .env
3. Ensure database exists
4. Test connection with psql

---

## Useful Commands

```powershell
# Create new app
python manage.py startapp app_name

# Make migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver

# Open Django shell
python manage.py shell

# Check for issues
python manage.py check

# Run tests
python manage.py test

# Show URLs
python manage.py show_urls  # Requires django-extensions
```

---

## Support

For issues and questions:
- Check documentation in `/doc` folder
- Review Django documentation: https://docs.djangoproject.com/
- Check project README.md

---

**Built with Django 4.2 & Tailwind CSS**
