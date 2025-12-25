# 🚀 Food Ordering System - Production Deployment Guide

## Table of Contents
1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Environment Configuration](#environment-configuration)
3. [Deployment Options](#deployment-options)
4. [Post-Deployment Steps](#post-deployment-steps)
5. [Monitoring & Maintenance](#monitoring--maintenance)
6. [Troubleshooting](#troubleshooting)

---

## Pre-Deployment Checklist

### ✅ Security Requirements
- [ ] Generate new `SECRET_KEY` for production
- [ ] Set `DEBUG=False` in environment variables
- [ ] Configure `ALLOWED_HOSTS` with your domain
- [ ] Set up SSL/TLS certificates
- [ ] Configure firewall rules
- [ ] Set up database backups
- [ ] Review and update security headers

### ✅ Service Requirements
- [ ] PostgreSQL database (v14+)
- [ ] SMTP email service configured
- [ ] Razorpay LIVE API keys (not test keys)
- [ ] Domain name and DNS configured
- [ ] SSL certificate obtained

### ✅ Application Requirements
- [ ] All migrations created and tested
- [ ] Static files collected
- [ ] Media files storage configured
- [ ] Environment variables configured
- [ ] Dependencies installed

---

## Environment Configuration

### 1. Create Production Environment File

Copy the example environment file:
```bash
cp .env.production.example .env
```

### 2. Configure Production Variables

Edit `.env` with your production values:

```bash
# CRITICAL: Set these first
DEBUG=False
SECRET_KEY=<generate-new-secret-key>
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DB_NAME=food_ordering_production
DB_USER=food_ordering_user
DB_PASSWORD=<strong-password>
DB_HOST=localhost  # or your database host
DB_PORT=5432

# Email (use production SMTP)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=<app-specific-password>
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

# Payment Gateway (LIVE keys)
RAZORPAY_KEY_ID=rzp_live_XXXXXXXXXX
RAZORPAY_KEY_SECRET=<your-live-secret>
```

### 3. Generate Secret Key

Generate a new Django secret key:
```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

---

## Deployment Options

### Option 1: Traditional VPS Deployment (Ubuntu/Debian)

#### Step 1: Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3.12 python3.12-venv python3-pip postgresql postgresql-contrib nginx supervisor

# Install system dependencies
sudo apt install -y libpq-dev python3-dev build-essential
```

#### Step 2: Database Setup

```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE food_ordering_production;
CREATE USER food_ordering_user WITH PASSWORD 'your-strong-password';
ALTER ROLE food_ordering_user SET client_encoding TO 'utf8';
ALTER ROLE food_ordering_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE food_ordering_user SET timezone TO 'Asia/Kolkata';
GRANT ALL PRIVILEGES ON DATABASE food_ordering_production TO food_ordering_user;
\q
```

#### Step 3: Application Setup

```bash
# Create application directory
sudo mkdir -p /var/www/food_ordering
cd /var/www/food_ordering

# Clone or upload your code
# git clone <your-repo> .
# or use scp/rsync to upload files

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file with production settings
nano .env
# (paste your production environment variables)

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput

# Create necessary directories
mkdir -p logs media/menu_items media/restaurants media/table_qr_codes
chmod -R 755 media logs
```

#### Step 4: Gunicorn Configuration

Create Gunicorn systemd service:

```bash
sudo nano /etc/systemd/system/food_ordering.service
```

Add the following content:

```ini
[Unit]
Description=Food Ordering System Gunicorn Daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/food_ordering
Environment="PATH=/var/www/food_ordering/venv/bin"
ExecStart=/var/www/food_ordering/venv/bin/gunicorn \
          --workers 3 \
          --bind unix:/var/www/food_ordering/food_ordering.sock \
          --timeout 120 \
          --access-logfile /var/www/food_ordering/logs/gunicorn_access.log \
          --error-logfile /var/www/food_ordering/logs/gunicorn_error.log \
          food_ordering.wsgi:application

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl start food_ordering
sudo systemctl enable food_ordering
sudo systemctl status food_ordering
```

#### Step 5: Nginx Configuration

Create Nginx configuration:

```bash
sudo nano /etc/nginx/sites-available/food_ordering
```

Add the following (update domain names):

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # SSL Security
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    
    client_max_body_size 10M;
    
    location / {
        proxy_pass http://unix:/var/www/food_ordering/food_ordering.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static/ {
        alias /var/www/food_ordering/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        alias /var/www/food_ordering/media/;
        expires 7d;
        add_header Cache-Control "public";
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/food_ordering /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### Step 6: SSL Certificate (Let's Encrypt)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

---

### Option 2: Docker Deployment

#### Step 1: Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
```

#### Step 2: Configure Environment

```bash
# Create .env file with production settings
cp .env.production.example .env
# Edit .env with your production values
```

#### Step 3: Build and Deploy

```bash
# Build and start containers
docker-compose up -d --build

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# View logs
docker-compose logs -f web
```

#### Step 4: Docker Management Commands

```bash
# Stop containers
docker-compose down

# Restart containers
docker-compose restart

# View running containers
docker-compose ps

# Access Django shell
docker-compose exec web python manage.py shell

# Backup database
docker-compose exec db pg_dump -U postgres food_ordering_db > backup.sql
```

---

### Option 3: Platform-as-a-Service (Heroku, Railway, Render)

#### Heroku Deployment

```bash
# Install Heroku CLI
# https://devcenter.heroku.com/articles/heroku-cli

# Login to Heroku
heroku login

# Create new app
heroku create your-app-name

# Add PostgreSQL addon
heroku addons:create heroku-postgresql:mini

# Set environment variables
heroku config:set DEBUG=False
heroku config:set SECRET_KEY=<your-secret-key>
heroku config:set ALLOWED_HOSTS=your-app-name.herokuapp.com

# Deploy
git push heroku main

# Run migrations
heroku run python manage.py migrate

# Create superuser
heroku run python manage.py createsuperuser

# Open app
heroku open
```

#### Railway Deployment

1. Connect your GitHub repository to Railway
2. Add PostgreSQL database
3. Configure environment variables in Railway dashboard
4. Deploy automatically on push

#### Render Deployment

1. Create new Web Service on Render
2. Connect your repository
3. Add PostgreSQL database
4. Configure environment variables
5. Deploy

---

## Post-Deployment Steps

### 1. Verify Deployment

```bash
# Check health endpoint
curl https://yourdomain.com/health/

# Expected response:
# {"status": "healthy", "checks": {"database": "ok"}}
```

### 2. Create Initial Data

```bash
# Create superuser (if not done)
python manage.py createsuperuser

# Load initial data (if you have fixtures)
python manage.py loaddata initial_data.json
```

### 3. Configure Admin Settings

1. Login to admin panel: `https://yourdomain.com/admin/`
2. Configure site settings
3. Add initial restaurants (if needed)
4. Set up promo codes
5. Configure flash sales

### 4. Test Critical Flows

- [ ] User registration and login
- [ ] Browse restaurants and menu items
- [ ] Add items to cart
- [ ] Checkout process
- [ ] Payment processing (test with Razorpay test mode first)
- [ ] Order confirmation emails
- [ ] Restaurant dashboard access
- [ ] QR code generation

---

## Monitoring & Maintenance

### Application Monitoring

#### Health Checks

```bash
# Health check endpoint
curl https://yourdomain.com/health/

# Readiness check
curl https://yourdomain.com/readiness/

# Liveness check
curl https://yourdomain.com/liveness/
```

#### Log Monitoring

```bash
# Application logs
tail -f /var/www/food_ordering/logs/food_ordering.log

# Gunicorn logs
tail -f /var/www/food_ordering/logs/gunicorn_error.log

# Nginx logs
tail -f /var/log/nginx/food_ordering_error.log

# Security logs
tail -f /var/www/food_ordering/logs/security.log
```

### Database Maintenance

#### Backup Database

```bash
# Create backup
pg_dump -U food_ordering_user -h localhost food_ordering_production > backup_$(date +%Y%m%d).sql

# Restore from backup
psql -U food_ordering_user -h localhost food_ordering_production < backup_20240101.sql
```

#### Automated Backups

Create cron job for daily backups:

```bash
crontab -e

# Add this line for daily backup at 2 AM
0 2 * * * pg_dump -U food_ordering_user food_ordering_production > /backups/db_$(date +\%Y\%m\%d).sql
```

### Media Files Backup

```bash
# Backup media files
tar -czf media_backup_$(date +%Y%m%d).tar.gz /var/www/food_ordering/media/

# Restore media files
tar -xzf media_backup_20240101.tar.gz -C /var/www/food_ordering/
```

### Updates and Maintenance

```bash
# Pull latest code
cd /var/www/food_ordering
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Install new dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Restart application
sudo systemctl restart food_ordering
```

---

## Troubleshooting

### Common Issues

#### 1. Static Files Not Loading

```bash
# Collect static files
python manage.py collectstatic --noinput

# Check Nginx configuration
sudo nginx -t

# Verify file permissions
ls -la /var/www/food_ordering/staticfiles/
```

#### 2. Database Connection Error

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test database connection
psql -U food_ordering_user -h localhost -d food_ordering_production

# Check .env file has correct credentials
cat .env | grep DB_
```

#### 3. 502 Bad Gateway

```bash
# Check Gunicorn is running
sudo systemctl status food_ordering

# Check Gunicorn logs
tail -f /var/www/food_ordering/logs/gunicorn_error.log

# Restart Gunicorn
sudo systemctl restart food_ordering
```

#### 4. Permission Denied Errors

```bash
# Fix ownership
sudo chown -R www-data:www-data /var/www/food_ordering

# Fix permissions
sudo chmod -R 755 /var/www/food_ordering/media
sudo chmod -R 755 /var/www/food_ordering/logs
```

#### 5. SSL Certificate Issues

```bash
# Renew certificate
sudo certbot renew

# Check certificate status
sudo certbot certificates

# Force renewal
sudo certbot renew --force-renewal
```

### Performance Optimization

#### Enable Caching

Add Redis for caching:

```bash
# Install Redis
sudo apt install redis-server

# Update settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

#### Database Optimization

```bash
# Analyze database
python manage.py dbshell
ANALYZE;

# Create indexes (if needed)
CREATE INDEX idx_order_status ON orders_order(status);
CREATE INDEX idx_order_created ON orders_order(created_at);
```

---

## Security Best Practices

### 1. Regular Updates

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Python packages
pip list --outdated
pip install --upgrade <package-name>
```

### 2. Firewall Configuration

```bash
# Enable UFW firewall
sudo ufw enable

# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Check status
sudo ufw status
```

### 3. Fail2Ban Setup

```bash
# Install Fail2Ban
sudo apt install fail2ban

# Configure for Nginx
sudo nano /etc/fail2ban/jail.local

# Add:
[nginx-http-auth]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log

# Restart Fail2Ban
sudo systemctl restart fail2ban
```

### 4. Regular Security Audits

```bash
# Check for security updates
python manage.py check --deploy

# Scan for vulnerabilities
pip install safety
safety check

# Review logs for suspicious activity
grep "Failed" /var/www/food_ordering/logs/security.log
```

---

## Support & Resources

### Documentation
- Django Documentation: https://docs.djangoproject.com/
- PostgreSQL Documentation: https://www.postgresql.org/docs/
- Nginx Documentation: https://nginx.org/en/docs/
- Gunicorn Documentation: https://docs.gunicorn.org/

### Monitoring Tools
- **Sentry**: Error tracking and monitoring
- **New Relic**: Application performance monitoring
- **Datadog**: Infrastructure and application monitoring
- **UptimeRobot**: Uptime monitoring

### Backup Solutions
- **AWS S3**: Cloud storage for backups
- **Backblaze B2**: Cost-effective cloud storage
- **rsync**: Automated file synchronization

---

## Deployment Checklist

### Pre-Launch
- [ ] All tests passing
- [ ] Security audit completed
- [ ] SSL certificate installed
- [ ] Database backups configured
- [ ] Monitoring set up
- [ ] Error tracking configured
- [ ] Performance testing completed
- [ ] Load testing completed

### Launch Day
- [ ] Final database backup
- [ ] Deploy to production
- [ ] Verify all services running
- [ ] Test critical user flows
- [ ] Monitor error logs
- [ ] Check performance metrics

### Post-Launch
- [ ] Monitor for 24 hours
- [ ] Review error logs daily
- [ ] Check performance metrics
- [ ] Gather user feedback
- [ ] Plan for scaling if needed

---

## Contact & Support

For deployment assistance or issues:
- Review logs in `/var/www/food_ordering/logs/`
- Check Django documentation
- Review this deployment guide
- Contact system administrator

---

**Last Updated**: December 2024
**Version**: 1.0.0
