# Database and Utilities - Code Explainer

## Overview
This document explains the database configuration, utility scripts, and supporting infrastructure of the TravelGuide project.

## Database Configuration

### Database Setup (guides/settings.py)
The project uses PostgreSQL as the primary database with the following configuration:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',  # PostgreSQL database engine
        'NAME': 'guides_db',                        # Database name
        'USER': 'postgres',                         # Database user
        'PASSWORD': 'Devil',                        # Database password (should be in .env)
        'HOST': 'localhost',                        # Database host
        'PORT': '5432',                            # Database port
        'CONN_MAX_AGE': 600,                       # Connection pooling timeout
        'OPTIONS': {
            'connect_timeout': 10,                  # Connection timeout
        },
    }
}
```

**Key Features**:
- **Connection Pooling**: `CONN_MAX_AGE=600` enables connection reuse
- **Timeout Configuration**: Prevents hanging connections
- **PostgreSQL Specific**: Optimized for PostgreSQL features
- **Environment Variables**: Should use `.env` file for credentials in production

## Database Schema and SQL Scripts

### SQL Directory Structure
```
sql/
├── 01_database_structure.sql    # Complete database schema
├── 02_sample_data.sql          # Sample data for development
├── 03_migration_fixes.sql      # Database migration fixes
├── 04_execute_all.sql          # Master execution script
├── README.md                   # SQL documentation
└── backup/                     # Database backup scripts
```

### 1. Database Structure (01_database_structure.sql)
**Purpose**: Complete database schema definition with all tables, indexes, and constraints.

**Key Components**:
```sql
-- Regional organization
CREATE TABLE destinations_region (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(120) UNIQUE NOT NULL,
    description TEXT,
    country VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    is_featured BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Destination management
CREATE TABLE destinations_destination (
    id SERIAL PRIMARY KEY,
    region_id INTEGER REFERENCES destinations_region(id),
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(120) UNIQUE NOT NULL,
    short_description VARCHAR(255),
    description TEXT,
    latitude DECIMAL(10,6),
    longitude DECIMAL(10,6),
    city VARCHAR(100),
    country VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    is_featured BOOLEAN DEFAULT FALSE,
    price DECIMAL(10,2),
    rating DECIMAL(3,1),
    views INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tour management
CREATE TABLE tours_tour (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,              -- Note: Django model uses 'title' field
    slug VARCHAR(220) UNIQUE NOT NULL,
    category_id INTEGER REFERENCES tours_tourcategory(id),
    short_description VARCHAR(255),
    description TEXT,
    duration_days INTEGER NOT NULL,
    group_size_min INTEGER DEFAULT 1,
    group_size_max INTEGER,
    price DECIMAL(10,2) NOT NULL,
    discount_price DECIMAL(10,2),
    destination_id INTEGER REFERENCES destinations_destination(id),  -- Single destination
    start_location VARCHAR(200),
    end_location VARCHAR(200),
    is_featured BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    difficulty_level VARCHAR(50),
    languages VARCHAR(200),
    inclusions JSONB DEFAULT '{}',
    exclusions JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Key Features**:
- **Complete Schema**: All tables with proper relationships
- **Indexes**: Performance indexes on frequently queried fields
- **Constraints**: Foreign key constraints and data validation
- **JSON Fields**: Flexible data storage for inclusions/exclusions
- **Timestamps**: Automatic timestamp tracking

### 2. Sample Data (02_sample_data.sql)
**Purpose**: Comprehensive sample data for development and testing.

**Key Components**:
```sql
-- Sample regions
INSERT INTO destinations_region (name, slug, description, country, is_featured) VALUES
('Tokyo Metropolitan', 'tokyo-metropolitan', 'Modern metropolis with traditional culture', 'Japan', TRUE),
('Paris Region', 'paris-region', 'City of Light and romance', 'France', TRUE),
('New York Area', 'new-york-area', 'The city that never sleeps', 'USA', TRUE);

-- Sample destinations with coordinates
INSERT INTO destinations_destination (region_id, name, slug, description, latitude, longitude, city, country, is_featured, price, rating) VALUES
(1, 'Tokyo', 'tokyo', 'Vibrant capital city of Japan', 35.6762, 139.6503, 'Tokyo', 'Japan', TRUE, 1200.00, 4.8),
(2, 'Paris', 'paris', 'Capital of France and fashion', 48.8566, 2.3522, 'Paris', 'France', TRUE, 1500.00, 4.7),
(3, 'New York City', 'new-york-city', 'The Big Apple', 40.7128, -74.0060, 'New York', 'USA', TRUE, 1800.00, 4.6);

-- Sample tours with comprehensive data
INSERT INTO tours_tour (name, slug, category_id, description, duration_days, price, destination_id, is_featured) VALUES
('Tokyo Cultural Explorer', 'tokyo-cultural-explorer', 1, 'Discover traditional and modern Tokyo', 7, 2500.00, 1, TRUE),
('Paris Romance Tour', 'paris-romance-tour', 2, 'Romantic journey through Paris', 5, 3200.00, 2, TRUE),
('NYC Urban Adventure', 'nyc-urban-adventure', 3, 'Explore the best of New York City', 6, 2800.00, 3, TRUE);
```

**Features**:
- **7 Complete Tours**: Fully detailed tour packages
- **6 Destinations**: Major tourist destinations with coordinates
- **8 Tour Categories**: Diverse tour types
- **21 Tour Dates**: 6 months of scheduled tours
- **Sample Images**: Tour and destination images
- **Realistic Data**: Production-ready sample content

### 3. Migration Fixes (03_migration_fixes.sql)
**Purpose**: Resolves Django model-database inconsistencies.

**Key Fixes**:
```sql
-- Fix tours table field name inconsistency
-- Django model expects 'name' but database has 'title'
ALTER TABLE tours_tour RENAME COLUMN title TO name;

-- Add missing many-to-many relationship table
CREATE TABLE tours_tour_destinations (
    id SERIAL PRIMARY KEY,
    tour_id INTEGER REFERENCES tours_tour(id) ON DELETE CASCADE,
    destination_id INTEGER REFERENCES destinations_destination(id) ON DELETE CASCADE,
    UNIQUE(tour_id, destination_id)
);

-- Add missing timestamp columns
ALTER TABLE tours_tourcategory ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE tours_tourcategory ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();
```

**Fixes Applied**:
- **Field Name Alignment**: Django model field names match database columns
- **Relationship Tables**: Missing many-to-many relationship tables
- **Timestamp Columns**: Consistent timestamp tracking across all tables
- **Data Type Corrections**: Ensure data types match Django model definitions

### 4. Master Execution Script (04_execute_all.sql)
**Purpose**: Executes all SQL scripts in correct order.

```sql
-- Master script to execute all database setup scripts
-- Execute in order: structure -> data -> fixes

\echo 'Starting database setup...'

-- 1. Create database structure
\i 01_database_structure.sql

-- 2. Insert sample data
\i 02_sample_data.sql

-- 3. Apply migration fixes
\i 03_migration_fixes.sql

\echo 'Database setup completed successfully!'
```

## Utility Scripts

### Database Analysis Scripts

#### 1. check_db.py
**Purpose**: Basic database connectivity and table existence check.

**Key Functions**:
```python
def check_database_connection():
    """
    Test database connectivity and basic operations.
    
    Verifies:
    - Database connection establishment
    - Basic query execution
    - Error handling and reporting
    
    Returns:
        bool: True if database is accessible
    """

def list_all_tables():
    """
    List all tables in the database.
    
    Queries information_schema to get complete table listing
    with row counts and basic metadata.
    
    Returns:
        list: Table names with metadata
    """

def verify_django_models():
    """
    Verify Django models match database schema.
    
    Compares Django model definitions with actual
    database table structure to identify mismatches.
    
    Returns:
        dict: Comparison results and discrepancies
    """
```

#### 2. check_schema.py
**Purpose**: Comprehensive schema validation and model analysis.

**Key Functions**:
```python
def analyze_model_fields(model_class):
    """
    Analyze Django model fields and their database mapping.
    
    Args:
        model_class: Django model class to analyze
        
    Returns:
        dict: Field analysis with database column mapping
    """

def compare_schema_with_database():
    """
    Compare Django models with actual database schema.
    
    Identifies:
    - Missing tables
    - Missing columns
    - Data type mismatches
    - Constraint differences
    
    Returns:
        dict: Comprehensive schema comparison
    """

def suggest_migrations():
    """
    Suggest Django migrations for schema differences.
    
    Analyzes schema differences and generates
    migration suggestions for resolution.
    
    Returns:
        list: Migration suggestions and commands
    """
```

#### 3. check_tours_schema.py
**Purpose**: Specific validation for tours app schema.

**Key Functions**:
```python
def validate_tours_table():
    """
    Validate tours table structure against Django model.
    
    Specifically checks for the name/title field mismatch
    that was identified in the database analysis.
    
    Returns:
        dict: Validation results for tours table
    """

def check_tour_relationships():
    """
    Verify tour relationship tables exist and are correct.
    
    Validates:
    - Tour category relationships
    - Tour destination relationships
    - Tour image relationships
    
    Returns:
        dict: Relationship validation results
    """
```

### Data Analysis Scripts

#### 1. simple_data_check.py
**Purpose**: Quick data availability check across all apps.

**Key Functions**:
```python
def check_data_availability():
    """
    Check if sample data is available in all main tables.
    
    Queries all primary tables to verify data exists
    for proper application functionality.
    
    Returns:
        dict: Data availability status for each table
    """

def count_records_by_app():
    """
    Count records in each Django app's tables.
    
    Provides overview of data distribution across
    different application components.
    
    Returns:
        dict: Record counts organized by app
    """
```

#### 2. inspect_data.py
**Purpose**: Detailed data inspection and analysis.

**Key Functions**:
```python
def inspect_table_data(table_name):
    """
    Detailed inspection of specific table data.
    
    Args:
        table_name: Name of table to inspect
        
    Returns:
        dict: Comprehensive table data analysis
    """

def analyze_data_quality():
    """
    Analyze data quality across all tables.
    
    Checks for:
    - Null values in required fields
    - Data consistency
    - Reference integrity
    
    Returns:
        dict: Data quality report
    """
```

### Schema Generation Scripts

#### 1. full_database_schema.py
**Purpose**: Generate complete database schema documentation.

**Key Functions**:
```python
def generate_schema_documentation():
    """
    Generate comprehensive schema documentation.
    
    Creates detailed documentation including:
    - Table structures
    - Relationships
    - Indexes
    - Constraints
    
    Returns:
        str: Complete schema documentation
    """

def export_schema_to_markdown():
    """
    Export schema documentation to Markdown format.
    
    Creates human-readable documentation suitable
    for project handover and reference.
    
    Returns:
        str: Markdown formatted schema documentation
    """
```

#### 2. get_all_tables.py
**Purpose**: Extract all table information from database.

**Key Functions**:
```python
def get_table_list():
    """
    Get comprehensive list of all database tables.
    
    Returns:
        list: All tables with metadata
    """

def get_table_structure(table_name):
    """
    Get detailed structure of a specific table.
    
    Args:
        table_name: Name of table to analyze
        
    Returns:
        dict: Complete table structure information
    """
```

## Environment Configuration

### Environment Variables (.env)
**Purpose**: Secure configuration management for sensitive data.

**Key Variables**:
```bash
# Database Configuration
DB_NAME=guides_db
DB_USER=postgres
DB_PASSWORD=Devil
DB_HOST=localhost
DB_PORT=5432

# Django Configuration
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# External API Keys
GOOGLE_MAPS_API_KEY=your-google-maps-key
PAYMENT_GATEWAY_KEY=your-payment-key

# Security Settings
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
```

**Security Notes**:
- Environment file should never be committed to version control
- Use strong, unique passwords for database access
- Rotate API keys regularly
- Use HTTPS in production with secure cookie settings

## Database Performance Optimization

### Indexing Strategy
```sql
-- Performance indexes for frequent queries
CREATE INDEX idx_destinations_slug ON destinations_destination(slug);
CREATE INDEX idx_destinations_featured ON destinations_destination(is_featured, is_active);
CREATE INDEX idx_tours_category ON tours_tour(category_id);
CREATE INDEX idx_tours_destination ON tours_tour(destination_id);
CREATE INDEX idx_bookings_user ON bookings_booking(user_id);
CREATE INDEX idx_bookings_status ON bookings_booking(status);
```

### Connection Pooling
```python
# Database connection pooling configuration
DATABASES = {
    'default': {
        'CONN_MAX_AGE': 600,  # Connection reuse for 10 minutes
        'OPTIONS': {
            'MAX_CONNS': 20,   # Maximum connections
            'connect_timeout': 10,
        },
    }
}
```

## Backup and Maintenance

### Database Backup Script
```bash
#!/bin/bash
# backup_database.sh
BACKUP_DIR="/backup/guides_db"
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -U postgres -h localhost guides_db > "$BACKUP_DIR/guides_db_$DATE.sql"
```

### Maintenance Tasks
```python
# Regular maintenance tasks
def cleanup_old_sessions():
    """Remove expired session data."""

def update_search_indexes():
    """Rebuild search indexes for better performance."""

def analyze_database_performance():
    """Analyze slow queries and suggest optimizations."""
```

## Monitoring and Logging

### Database Monitoring
- **Query Performance**: Monitor slow queries and optimization opportunities
- **Connection Usage**: Track database connection pool utilization
- **Storage Growth**: Monitor database size and growth patterns
- **Index Usage**: Analyze index effectiveness and usage patterns

### Application Logging
```python
LOGGING = {
    'version': 1,
    'handlers': {
        'database': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/database.log',
        },
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['database'],
            'level': 'INFO',
        },
    },
}
```

This comprehensive database and utilities structure provides robust data management, analysis capabilities, and maintenance tools for the TravelGuide project.
