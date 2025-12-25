# Food Ordering System - Automated Setup Script
# Run this script to automatically set up the development environment

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Food Ordering System - Setup Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function to display colored messages
function Write-Step {
    param([string]$Message)
    Write-Host "➤ $Message" -ForegroundColor Green
}

function Write-Error-Message {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

# Step 1: Check Python installation
Write-Step "Step 1: Checking Python installation..."
try {
    $pythonVersion = python --version 2>&1
    Write-Success "Python is installed: $pythonVersion"
} catch {
    Write-Error-Message "Python is not installed. Please install Python 3.10+ from https://www.python.org/"
    exit 1
}

# Step 2: Create virtual environment
Write-Step "Step 2: Creating virtual environment..."
if (Test-Path "venv") {
    Write-Host "Virtual environment already exists. Skipping..." -ForegroundColor Yellow
} else {
    python -m venv venv
    Write-Success "Virtual environment created successfully!"
}

# Step 3: Activate virtual environment
Write-Step "Step 3: Activating virtual environment..."
& ".\venv\Scripts\Activate.ps1"
Write-Success "Virtual environment activated!"

# Step 4: Upgrade pip
Write-Step "Step 4: Upgrading pip..."
python -m pip install --upgrade pip | Out-Null
Write-Success "Pip upgraded successfully!"

# Step 5: Install dependencies
Write-Step "Step 5: Installing dependencies from requirements.txt..."
pip install -r requirements.txt
if ($LASTEXITCODE -eq 0) {
    Write-Success "All dependencies installed successfully!"
} else {
    Write-Error-Message "Failed to install dependencies. Please check requirements.txt"
    exit 1
}

# Step 6: Create .env file if it doesn't exist
Write-Step "Step 6: Setting up environment variables..."
if (Test-Path ".env") {
    Write-Host ".env file already exists. Skipping..." -ForegroundColor Yellow
} else {
    Copy-Item ".env.example" ".env"
    Write-Success ".env file created from .env.example"
    Write-Host "⚠ Please edit .env file with your database credentials!" -ForegroundColor Yellow
}

# Step 7: Database setup reminder
Write-Step "Step 7: Database Setup"
Write-Host ""
Write-Host "Before running migrations, ensure:" -ForegroundColor Yellow
Write-Host "  1. PostgreSQL is installed and running" -ForegroundColor Yellow
Write-Host "  2. Database 'food_ordering_db' is created" -ForegroundColor Yellow
Write-Host "  3. .env file has correct database credentials" -ForegroundColor Yellow
Write-Host ""

$dbSetup = Read-Host "Have you set up the database? (yes/no)"
if ($dbSetup -eq "yes" -or $dbSetup -eq "y") {
    
    # Step 8: Run migrations
    Write-Step "Step 8: Running database migrations..."
    python manage.py migrate
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Migrations completed successfully!"
    } else {
        Write-Error-Message "Migration failed. Check database connection."
        exit 1
    }
    
    # Step 9: Create superuser
    Write-Step "Step 9: Creating superuser account..."
    Write-Host "Please enter superuser details:" -ForegroundColor Cyan
    python manage.py createsuperuser
    
    # Step 10: Collect static files
    Write-Step "Step 10: Collecting static files..."
    python manage.py collectstatic --noinput
    Write-Success "Static files collected!"
    
} else {
    Write-Host ""
    Write-Host "Please set up the database first:" -ForegroundColor Yellow
    Write-Host "  1. Open pgAdmin or use psql" -ForegroundColor Yellow
    Write-Host "  2. Run: CREATE DATABASE food_ordering_db;" -ForegroundColor Yellow
    Write-Host "  3. Edit .env file with your database password" -ForegroundColor Yellow
    Write-Host "  4. Run this script again" -ForegroundColor Yellow
    exit 0
}

# Setup complete
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✓ Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Start the server: python manage.py runserver" -ForegroundColor White
Write-Host "  2. Visit: http://127.0.0.1:8000/" -ForegroundColor White
Write-Host "  3. Admin panel: http://127.0.0.1:8000/admin/" -ForegroundColor White
Write-Host "  4. Add menu items via admin panel" -ForegroundColor White
Write-Host ""
Write-Host "Documentation:" -ForegroundColor Cyan
Write-Host "  - QUICK_START.md - Quick setup guide" -ForegroundColor White
Write-Host "  - DEPLOYMENT_GUIDE.md - Complete deployment guide" -ForegroundColor White
Write-Host "  - USAGE_GUIDE.md - How to use the system" -ForegroundColor White
Write-Host ""
Write-Host "Happy Coding! 🍽️" -ForegroundColor Green