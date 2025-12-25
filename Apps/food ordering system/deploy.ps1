# ============================================
# FOOD ORDERING SYSTEM - DEPLOYMENT SCRIPT (PowerShell)
# ============================================
# Automated deployment script for Windows
# Usage: .\deploy.ps1

$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting Food Ordering System Deployment..." -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

function Write-Success {
    param($Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-Error-Custom {
    param($Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Write-Info {
    param($Message)
    Write-Host "ℹ $Message" -ForegroundColor Yellow
}

# Check if .env file exists
if (-not (Test-Path .env)) {
    Write-Error-Custom ".env file not found!"
    Write-Info "Please create .env file from .env.production.example"
    exit 1
}

Write-Success ".env file found"

# Check if virtual environment exists
if (-not (Test-Path venv)) {
    Write-Info "Creating virtual environment..."
    python -m venv venv
    Write-Success "Virtual environment created"
}

# Activate virtual environment
Write-Info "Activating virtual environment..."
& .\venv\Scripts\Activate.ps1
Write-Success "Virtual environment activated"

# Upgrade pip
Write-Info "Upgrading pip..."
python -m pip install --upgrade pip --quiet
Write-Success "Pip upgraded"

# Install dependencies
Write-Info "Installing dependencies..."
pip install -r requirements.txt --quiet
Write-Success "Dependencies installed"

# Check database connection
Write-Info "Checking database connection..."
python manage.py check --database default
Write-Success "Database connection successful"

# Run migrations
Write-Info "Running database migrations..."
python manage.py migrate --noinput
Write-Success "Migrations completed"

# Collect static files
Write-Info "Collecting static files..."
python manage.py collectstatic --noinput --clear
Write-Success "Static files collected"

# Create necessary directories
Write-Info "Creating necessary directories..."
New-Item -ItemType Directory -Force -Path logs | Out-Null
New-Item -ItemType Directory -Force -Path media\menu_items | Out-Null
New-Item -ItemType Directory -Force -Path media\restaurants | Out-Null
New-Item -ItemType Directory -Force -Path media\table_qr_codes | Out-Null
New-Item -ItemType Directory -Force -Path media\placeholders | Out-Null
Write-Success "Directories created"

# Run security checks
Write-Info "Running security checks..."
python manage.py check --deploy
Write-Success "Security checks passed"

# Check for superuser
Write-Info "Checking for superuser..."
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); print('Superuser exists' if User.objects.filter(is_superuser=True).exists() else 'No superuser found')"

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Success "Deployment completed successfully!"
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Info "Next steps:"
Write-Host "1. Create superuser: python manage.py createsuperuser"
Write-Host "2. Start application: python manage.py runserver (development)"
Write-Host "3. Or use: gunicorn food_ordering.wsgi:application (production)"
Write-Host "4. Access admin panel: http://localhost:8000/admin/"
Write-Host ""
Write-Info "For production deployment, refer to PRODUCTION_DEPLOYMENT.md"
