#!/bin/bash

# ============================================
# FOOD ORDERING SYSTEM - DEPLOYMENT SCRIPT
# ============================================
# Automated deployment script for production
# Usage: ./deploy.sh

set -e  # Exit on error

echo "🚀 Starting Food Ordering System Deployment..."
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Check if .env file exists
if [ ! -f .env ]; then
    print_error ".env file not found!"
    print_info "Please create .env file from .env.production.example"
    exit 1
fi

print_success ".env file found"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_info "Creating virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate
print_success "Virtual environment activated"

# Upgrade pip
print_info "Upgrading pip..."
pip install --upgrade pip --quiet
print_success "Pip upgraded"

# Install dependencies
print_info "Installing dependencies..."
pip install -r requirements.txt --quiet
print_success "Dependencies installed"

# Check database connection
print_info "Checking database connection..."
python manage.py check --database default
print_success "Database connection successful"

# Run migrations
print_info "Running database migrations..."
python manage.py migrate --noinput
print_success "Migrations completed"

# Collect static files
print_info "Collecting static files..."
python manage.py collectstatic --noinput --clear
print_success "Static files collected"

# Create necessary directories
print_info "Creating necessary directories..."
mkdir -p logs
mkdir -p media/menu_items
mkdir -p media/restaurants
mkdir -p media/table_qr_codes
mkdir -p media/placeholders
chmod -R 755 media logs
print_success "Directories created"

# Run security checks
print_info "Running security checks..."
python manage.py check --deploy
print_success "Security checks passed"

# Create superuser (if needed)
print_info "Checking for superuser..."
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); print('Superuser exists' if User.objects.filter(is_superuser=True).exists() else 'No superuser found')"

echo ""
echo "================================================"
print_success "Deployment completed successfully!"
echo "================================================"
echo ""
print_info "Next steps:"
echo "1. Create superuser: python manage.py createsuperuser"
echo "2. Start application: gunicorn food_ordering.wsgi:application"
echo "3. Access admin panel: http://your-domain/admin/"
echo ""
print_info "For production deployment, refer to PRODUCTION_DEPLOYMENT.md"
