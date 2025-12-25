# Installation and Deployment Guide - Food Ordering System

## Appendix A: Comprehensive Setup Instructions

### Table of Contents
1. [System Requirements](#1-system-requirements)
2. [Environment Setup](#2-environment-setup)
3. [Database Installation](#3-database-installation)
4. [Application Installation](#4-application-installation)
5. [Configuration](#5-configuration)
6. [Deployment Options](#6-deployment-options)
7. [Testing and Validation](#7-testing-and-validation)
8. [Monitoring and Maintenance](#8-monitoring-and-maintenance)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. System Requirements

### 1.1 Minimum Hardware Requirements

#### Development Environment
- **Processor**: Intel i5 or AMD Ryzen 5 (2.5GHz+)
- **Memory**: 8GB RAM (16GB recommended)
- **Storage**: 50GB available SSD space
- **Network**: Stable broadband connection

#### Production Environment (Small Scale)
- **Processor**: 4 vCPU (Intel Xeon or equivalent)
- **Memory**: 16GB RAM
- **Storage**: 200GB SSD (with backup storage)
- **Network**: 1Gbps connection with redundancy
- **Load Balancer**: Application-level load balancing

#### Production Environment (Enterprise Scale)
- **Processor**: 8+ vCPU with auto-scaling
- **Memory**: 32GB+ RAM with auto-scaling
- **Storage**: 500GB+ SSD with cloud storage integration
- **Network**: 10Gbps connection with CDN
- **Load Balancer**: Multi-zone load balancing

### 1.2 Software Requirements

#### Operating Systems
- **Development**: Ubuntu 20.04+ / macOS 10.15+ / Windows 10+
- **Production**: Ubuntu 20.04 LTS (recommended) / CentOS 8+ / RHEL 8+

#### Core Dependencies
- **Python**: 3.9+ (3.11 recommended)
- **Node.js**: 16+ (18+ recommended)
- **Database**: PostgreSQL 13+ (15+ recommended)
- **Cache**: Redis 6+ (7+ recommended)
- **Web Server**: Nginx 1.18+ (1.20+ recommended)

#### Additional Tools
- **Git**: 2.25+ for version control
- **Docker**: 20.10+ for containerization
- **Docker Compose**: 2.0+ for multi-container applications
- **SSL Certificate**: Let's Encrypt or commercial certificate

---

## 2. Environment Setup

### 2.1 Development Environment Setup

#### Step 1: Install Python and Virtual Environment
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev

# macOS (using Homebrew)
brew install python@3.11

# Create virtual environment
python3.11 -m venv food_ordering_env
source food_ordering_env/bin/activate  # Linux/macOS
# food_ordering_env\Scripts\activate  # Windows
```

#### Step 2: Install Node.js and npm
```bash
# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# macOS
brew install node@18

# Verify installation
node --version
npm --version
```

#### Step 3: Install Database and Cache
```bash
# PostgreSQL
sudo apt install postgresql postgresql-contrib

# Redis
sudo apt install redis-server

# Start services
sudo systemctl start postgresql
sudo systemctl start redis-server
sudo systemctl enable postgresql
sudo systemctl enable redis-server
```

### 2.2 Production Environment Setup

#### Step 1: Server Preparation
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y curl wget git vim htop

# Configure firewall
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw --force enable
```

#### Step 2: Create Application User
```bash
# Create dedicated user
sudo adduser foodordering
sudo usermod -aG sudo foodordering

# Switch to application user
su - foodordering
```

---

## 3. Database Installation

### 3.1 PostgreSQL Setup

#### Step 1: Database Installation
```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Secure PostgreSQL
sudo -u postgres psql
\password postgres  # Set strong password
\q
```

#### Step 2: Create Database and User
```bash
# Switch to postgres user
sudo -u postgres psql

# Create database
CREATE DATABASE food_ordering_db;

# Create application user
CREATE USER foodordering_user WITH PASSWORD 'your_strong_password';

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE food_ordering_db TO foodordering_user;

# Grant schema privileges
\c food_ordering_db;
GRANT ALL ON SCHEMA public TO foodordering_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO foodordering_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO foodordering_user;

\q
```

#### Step 3: Configure PostgreSQL
```bash
# Edit PostgreSQL configuration
sudo vim /etc/postgresql/15/main/postgresql.conf

# Key settings to modify:
listen_addresses = 'localhost'
max_connections = 100
shared_buffers = 256MB
effective_cache_size = 1GB

# Edit access control
sudo vim /etc/postgresql/15/main/pg_hba.conf

# Add local connection rule
local   food_ordering_db   foodordering_user   md5

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### 3.2 Redis Setup

#### Step 1: Redis Installation and Configuration
```bash
# Install Redis
sudo apt install redis-server

# Configure Redis
sudo vim /etc/redis/redis.conf

# Key settings:
bind 127.0.0.1
port 6379
requirepass your_redis_password
maxmemory 256mb
maxmemory-policy allkeys-lru

# Restart Redis
sudo systemctl restart redis-server
```

---

## 4. Application Installation

### 4.1 Backend Installation (Django)

#### Step 1: Clone Repository
```bash
# Clone the application
git clone https://github.com/your-org/food-ordering-system.git
cd food-ordering-system

# Create and activate virtual environment
python3.11 -m venv venv
source venv/bin/activate
```

#### Step 2: Install Python Dependencies
```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# Install additional production packages
pip install gunicorn psycopg2-binary redis celery
```

#### Step 3: Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit environment file
vim .env
```

#### Step 4: Database Migration
```bash
# Apply database migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load initial data (optional)
python manage.py loaddata fixtures/initial_data.json
```

#### Step 5: Collect Static Files
```bash
# Collect static files
python manage.py collectstatic --noinput

# Verify installation
python manage.py check
```

### 4.2 Frontend Installation (React)

#### Step 1: Install Node Dependencies
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Install additional production packages
npm install --save-prod react-router-dom axios
```

#### Step 2: Build Frontend
```bash
# Development build
npm run build

# Production build
npm run build:prod
```

---

## 5. Configuration

### 5.1 Environment Variables

#### Backend Configuration (.env)
```bash
# Django Settings
DEBUG=False
SECRET_KEY=your_very_long_secret_key_here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database Configuration
DB_NAME=food_ordering_db
DB_USER=foodordering_user
DB_PASSWORD=your_strong_password
DB_HOST=localhost
DB_PORT=5432

# Redis Configuration
REDIS_URL=redis://:your_redis_password@localhost:6379/0

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_email_password

# Payment Gateway Configuration
STRIPE_PUBLISHABLE_KEY=pk_live_your_stripe_key
STRIPE_SECRET_KEY=sk_live_your_stripe_key

# Security Settings
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
```

#### Frontend Configuration
```javascript
// frontend/src/config.js
export const API_BASE_URL = 'https://api.yourdomain.com';
export const STRIPE_PUBLISHABLE_KEY = 'pk_live_your_stripe_key';
export const GOOGLE_MAPS_API_KEY = 'your_google_maps_key';
export const SENTRY_DSN = 'your_sentry_dsn';
```

### 5.2 Nginx Configuration

#### Create Nginx Configuration File
```bash
sudo vim /etc/nginx/sites-available/foodordering
```

#### Nginx Configuration Content
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;

    # Security Headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Frontend Static Files
    location / {
        root /home/foodordering/food-ordering-system/frontend/build;
        try_files $uri $uri/ /index.html;
    }

    # API Backend
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Django Admin
    location /admin/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static Files
    location /static/ {
        alias /home/foodordering/food-ordering-system/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Media Files
    location /media/ {
        alias /home/foodordering/food-ordering-system/media/;
        expires 1y;
        add_header Cache-Control "public";
    }
}
```

#### Enable Site Configuration
```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/foodordering /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

---

## 6. Deployment Options

### 6.1 Traditional Deployment

#### Step 1: Systemd Service for Django
```bash
# Create systemd service file
sudo vim /etc/systemd/system/foodordering.service
```

#### Service Configuration
```ini
[Unit]
Description=Food Ordering System Django Application
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=foodordering
Group=foodordering
Environment=PATH=/home/foodordering/food-ordering-system/venv/bin
WorkingDirectory=/home/foodordering/food-ordering-system
ExecStart=/home/foodordering/food-ordering-system/venv/bin/gunicorn --workers 3 --timeout 120 --bind 127.0.0.1:8000 foodordering.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

#### Enable and Start Service
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable foodordering

# Start service
sudo systemctl start foodordering

# Check status
sudo systemctl status foodordering
```

#### Step 2: Celery Worker Service
```bash
# Create Celery worker service
sudo vim /etc/systemd/system/celery-worker.service
```

#### Celery Worker Configuration
```ini
[Unit]
Description=Celery Worker Service
After=network.target redis.service

[Service]
Type=forking
User=foodordering
Group=foodordering
Environment=PATH=/home/foodordering/food-ordering-system/venv/bin
WorkingDirectory=/home/foodordering/food-ordering-system
ExecStart=/home/foodordering/food-ordering-system/venv/bin/celery -A foodordering worker --loglevel=info --detach
ExecStop=/bin/kill -s TERM $MAINPID
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

#### Enable Celery Services
```bash
# Enable and start worker
sudo systemctl enable celery-worker
sudo systemctl start celery-worker

# Create and enable beat service for scheduled tasks
sudo vim /etc/systemd/system/celery-beat.service
```

### 6.2 Docker Deployment

#### Step 1: Create Dockerfile
```dockerfile
# Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

# Create static files directory
RUN mkdir -p /app/staticfiles

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "foodordering.wsgi:application"]
```

#### Step 2: Create Docker Compose File
```yaml
# docker-compose.yml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: food_ordering_db
      POSTGRES_USER: foodordering_user
      POSTGRES_PASSWORD: your_strong_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass your_redis_password
    ports:
      - "6379:6379"

  backend:
    build: .
    command: gunicorn --bind 0.0.0.0:8000 foodordering.wsgi:application
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    environment:
      - DEBUG=False
      - DB_HOST=db
      - REDIS_URL=redis://:your_redis_password@redis:6379/0

  celery:
    build: .
    command: celery -A foodordering worker --loglevel=info
    depends_on:
      - db
      - redis
    environment:
      - DB_HOST=db
      - REDIS_URL=redis://:your_redis_password@redis:6379/0

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - static_volume:/app/staticfiles
      - media_volume:/app/media
      - ./ssl:/etc/ssl/certs
    depends_on:
      - backend

volumes:
  postgres_data:
  static_volume:
  media_volume:
```

#### Step 3: Deploy with Docker
```bash
# Build and start containers
docker-compose up -d --build

# Run database migrations
docker-compose exec backend python manage.py migrate

# Create superuser
docker-compose exec backend python manage.py createsuperuser

# Collect static files
docker-compose exec backend python manage.py collectstatic --noinput
```

### 6.3 Cloud Deployment (AWS)

#### Step 1: AWS Infrastructure Setup
```bash
# Using AWS CLI
aws configure

# Create VPC
aws ec2 create-vpc --cidr-block 10.0.0.0/16 --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=food-ordering-vpc}]'

# Create subnets
aws ec2 create-subnet --vpc-id vpc-xxxxxxxx --cidr-block 10.0.1.0/24 --availability-zone us-east-1a
aws ec2 create-subnet --vpc-id vpc-xxxxxxxx --cidr-block 10.0.2.0/24 --availability-zone us-east-1b

# Create RDS instance
aws rds create-db-instance \
    --db-instance-identifier food-ordering-db \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --master-username foodordering_user \
    --master-user-password your_strong_password \
    --allocated-storage 20
```

#### Step 2: Elastic Beanstalk Deployment
```bash
# Install EB CLI
pip install awsebcli

# Initialize EB application
eb init food-ordering-system

# Create environment
eb create production

# Deploy application
eb deploy
```

---

## 7. Testing and Validation

### 7.1 Automated Testing

#### Backend Testing
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test accounts restaurant menu orders

# Run with coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

#### Frontend Testing
```bash
# Run unit tests
npm test

# Run integration tests
npm run test:integration

# Run E2E tests
npm run test:e2e
```

### 7.2 Manual Testing Checklist

#### Functionality Testing
- [ ] User registration and login
- [ ] Restaurant browsing and search
- [ ] Menu item selection and customization
- [ ] Order placement and payment
- [ ] Order tracking and status updates
- [ ] Restaurant owner dashboard
- [ ] Admin panel functionality

#### Performance Testing
- [ ] Page load speed (< 2 seconds)
- [ ] Database query optimization
- [ ] Concurrent user handling (100+ users)
- [ ] Mobile responsiveness
- [ ] Cross-browser compatibility

#### Security Testing
- [ ] SQL injection prevention
- [ ] XSS protection
- [ ] CSRF token validation
- [ ] Authentication and authorization
- [ ] SSL/TLS configuration
- [ ] Data encryption verification

### 7.3 Load Testing

#### Using Apache Bench
```bash
# Install Apache Bench
sudo apt install apache2-utils

# Test API endpoints
ab -n 1000 -c 100 https://yourdomain.com/api/restaurants/

# Test homepage
ab -n 1000 -c 100 https://yourdomain.com/
```

#### Using Locust
```python
# locustfile.py
from locust import HttpUser, task, between

class FoodOrderingUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        self.client.post("/api/login/", json={
            "email": "test@example.com",
            "password": "testpassword"
        })
    
    @task(3)
    def view_restaurants(self):
        self.client.get("/api/restaurants/")
    
    @task(2)
    def view_menu(self):
        self.client.get("/api/restaurants/1/menu/")
    
    @task(1)
    def place_order(self):
        self.client.post("/api/orders/", json={
            "restaurant_id": 1,
            "items": [{"item_id": 1, "quantity": 2}],
            "delivery_address": "123 Test St"
        })
```

#### Run Load Tests
```bash
# Install Locust
pip install locust

# Run load test
locust -f locustfile.py --host=https://yourdomain.com
```

---

## 8. Monitoring and Maintenance

### 8.1 Application Monitoring

#### Setup Application Monitoring
```bash
# Install Sentry for error tracking
pip install sentry-sdk

# Configure Sentry in settings.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn="your_sentry_dsn",
    integrations=[DjangoIntegration()],
    traces_sample_rate=1.0,
    send_default_pii=True
)
```

#### Performance Monitoring
```bash
# Install Django Debug Toolbar (development only)
pip install django-debug-toolbar

# Add to installed apps
INSTALLED_APPS += ['debug_toolbar']

# Configure middleware
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
```

### 8.2 Log Management

#### Configure Logging
```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/foodordering/django.log',
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': '/var/log/foodordering/django_errors.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file', 'error_file'],
        'level': 'INFO',
    },
}
```

#### Log Rotation Setup
```bash
# Create logrotate configuration
sudo vim /etc/logrotate.d/foodordering
```

#### Logrotate Configuration
```
/var/log/foodordering/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 foodordering foodordering
    postrotate
        systemctl reload foodordering
    endscript
}
```

### 8.3 Backup Strategy

#### Database Backup Script
```bash
#!/bin/bash
# backup_database.sh

# Configuration
DB_NAME="food_ordering_db"
DB_USER="foodordering_user"
BACKUP_DIR="/home/foodordering/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Create database backup
pg_dump -h localhost -U $DB_USER -d $DB_NAME > $BACKUP_DIR/db_backup_$DATE.sql

# Compress backup
gzip $BACKUP_DIR/db_backup_$DATE.sql

# Remove backups older than 30 days
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +30 -delete

echo "Database backup completed: $BACKUP_DIR/db_backup_$DATE.sql.gz"
```

#### Automated Backups
```bash
# Make script executable
chmod +x backup_database.sh

# Add to crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /home/foodordering/backup_database.sh
```

#### Media Files Backup
```bash
#!/bin/bash
# backup_media.sh

MEDIA_DIR="/home/foodordering/food-ordering-system/media"
BACKUP_DIR="/home/foodordering/backups/media"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup
rsync -av --delete $MEDIA_DIR/ $BACKUP_DIR/

# Create compressed archive
tar -czf $BACKUP_DIR/media_backup_$DATE.tar.gz -C $BACKUP_DIR .

echo "Media backup completed: $BACKUP_DIR/media_backup_$DATE.tar.gz"
```

---

## 9. Troubleshooting

### 9.1 Common Issues

#### Database Connection Issues
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check connection
psql -h localhost -U foodordering_user -d food_ordering_db

# Check PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-15-main.log
```

#### Application Not Starting
```bash
# Check application logs
sudo journalctl -u foodordering -f

# Check configuration
python manage.py check --deploy

# Check permissions
ls -la /home/foodordering/food-ordering-system/
```

#### Static Files Not Loading
```bash
# Check Nginx configuration
sudo nginx -t

# Check static files
ls -la staticfiles/

# Recollect static files
python manage.py collectstatic --noinput --clear
```

#### Performance Issues
```bash
# Check system resources
htop
df -h
free -h

# Check database performance
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"

# Check slow queries
sudo -u postgres psql -c "SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
```

### 9.2 Error Resolution

#### 502 Bad Gateway Error
```bash
# Check if backend is running
curl http://127.0.0.1:8000

# Restart backend service
sudo systemctl restart foodordering

# Check Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

#### Database Migration Errors
```bash
# Check migration status
python manage.py showmigrations

# Fake migration if needed
python manage.py migrate --fake

# Reset migrations (last resort)
python manage.py migrate app_name zero
python manage.py migrate app_name
```

#### SSL Certificate Issues
```bash
# Check certificate status
sudo certbot certificates

# Renew certificate
sudo certbot renew

# Test Nginx configuration
sudo nginx -t && sudo systemctl reload nginx
```

### 9.3 Performance Optimization

#### Database Optimization
```sql
-- Create indexes for common queries
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_created_at ON orders(created_at);
CREATE INDEX idx_menuitem_restaurant_id ON menuitem(restaurant_id);

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM orders WHERE user_id = 1;

-- Update statistics
ANALYZE;
```

#### Application Caching
```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Cache expensive queries
from django.core.cache import cache

def get_popular_restaurants():
    cache_key = 'popular_restaurants'
    result = cache.get(cache_key)
    if result is None:
        result = Restaurant.objects.filter(rating__gte=4.0).order_by('-rating')[:10]
        cache.set(cache_key, result, 300)  # Cache for 5 minutes
    return result
```

---

## 10. Security Hardening

### 10.1 System Security

#### Firewall Configuration
```bash
# Configure UFW firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

#### SSH Security
```bash
# Edit SSH configuration
sudo vim /etc/ssh/sshd_config

# Recommended settings:
Port 2222  # Change from default 22
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
MaxAuthTries 3

# Restart SSH
sudo systemctl restart ssh
```

### 10.2 Application Security

#### Security Headers
```python
# settings.py
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_SECONDS = 31536000
SECURE_REDIRECT_EXEMPT = []
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = 'DENY'
```

#### Input Validation
```python
# forms.py
from django import forms
from django.core.validators import RegexValidator

class OrderForm(forms.ModelForm):
    phone = forms.CharField(
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="Phone number must be entered in the format: '+999999999'."
        )]
    )
    
    class Meta:
        model = Order
        fields = ['customer_name', 'phone', 'delivery_address']
```

---

## Conclusion

This comprehensive installation and deployment guide provides all necessary instructions for successfully setting up and maintaining the Food Ordering System in both development and production environments. Following these guidelines ensures:

- **Reliable Deployment**: Consistent and repeatable setup process
- **Security Best Practices**: Protection against common vulnerabilities
- **Performance Optimization**: Efficient resource utilization
- **Maintainability**: Easy monitoring and troubleshooting
- **Scalability**: Architecture designed for growth

Regular maintenance, monitoring, and updates are essential for optimal performance and security. Always test changes in a staging environment before deploying to production.

---

**Guide Version: 1.0**  
**Last Updated: December 2024**  
**Technical Support: support@foodordering.com**  
**Emergency Contact: emergency@foodordering.com**
