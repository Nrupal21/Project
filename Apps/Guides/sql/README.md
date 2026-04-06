# TravelGuide Database SQL Scripts

This directory contains SQL scripts for setting up and managing the TravelGuide Django project database.

## 📁 Files Overview

### 1. `01_database_structure.sql`
**Purpose**: Creates the complete database schema
- **Creates tables**: destinations, attractions, tours, tour categories, etc.
- **Adds indexes**: For optimal query performance
- **Sets up triggers**: For automatic timestamp updates
- **Establishes relationships**: Foreign keys and constraints

### 2. `02_sample_data.sql`
**Purpose**: Populates the database with comprehensive sample data
- **Regions**: Asia, Europe, Americas, Africa
- **Destinations**: Tokyo, Paris, New York, Santorini, Bali, Dubai
- **Attractions**: 10+ popular tourist attractions
- **Tours**: 6 complete tour packages with detailed information
- **Tour Categories**: Adventure, Cultural, Culinary, Nature, Luxury, Budget, Family, Romance
- **Tour Dates**: Next 6 months of available tour schedules
- **Images**: Sample image references for all content types

### 3. `03_migration_fixes.sql`
**Purpose**: Fixes Django model-database inconsistencies
- **Tours Model Fix**: Renames `title` to `name` column
- **Relationship Fix**: Converts single destination_id to many-to-many relationship
- **Missing Columns**: Adds `is_popular`, `group_size_min`, `group_size_max`, etc.
- **Data Validation**: Fixes orphaned records and constraints

### 4. `04_execute_all.sql`
**Purpose**: Master execution script that runs all scripts in order
- **Complete Setup**: Runs all scripts in the correct sequence
- **Verification**: Displays final database status
- **Instructions**: Provides next steps for Django integration

## 🚀 Quick Start

### Option A: Execute All Scripts at Once
```bash
# Connect to PostgreSQL as superuser
psql -U postgres

# Run the master script
\i sql/04_execute_all.sql
```

### Option B: Execute Scripts Individually
```bash
# 1. Create database structure
psql -U postgres -d guides_db -f sql/01_database_structure.sql

# 2. Insert sample data
psql -U postgres -d guides_db -f sql/02_sample_data.sql

# 3. Apply migration fixes
psql -U postgres -d guides_db -f sql/03_migration_fixes.sql
```

## 🔧 Prerequisites

1. **PostgreSQL** installed and running
2. **Database**: `guides_db` must exist
3. **User**: `postgres` user with appropriate permissions

## 📊 Database Schema Summary

### Core Tables Created:
- `destinations_region` (4 records)
- `destinations_destination` (6 records)
- `destinations_attraction` (10 records)
- `tours_tourcategory` (8 records)
- `tours_tour` (6 records)
- `tours_tourdate` (18 records)
- `tours_tourimage` (12 records)

### Key Features:
- **Featured Content**: Destinations and attractions marked as featured
- **Popular Tours**: Tours marked as popular for home page display
- **Complete Relationships**: All foreign keys and many-to-many relationships
- **Sample Images**: Image references for all content types
- **Tour Schedules**: Available tour dates for next 6 months

## 🎯 Home Page Data Availability

After running these scripts, your home page will have:

✅ **Featured Destinations**: 6 destinations ready for display
✅ **Popular Attractions**: 10+ attractions with categories
✅ **Tours Section**: 6 complete tour packages
✅ **Tour Categories**: 8 categories for filtering
✅ **Images**: Sample images for all content
✅ **Dynamic Content**: No more static fallbacks needed

## 🔨 Django Integration Steps

1. **Run Django Migrations**:
   ```bash
   python manage.py migrate
   ```

2. **Create Superuser**:
   ```bash
   python manage.py createsuperuser
   ```

3. **Test Home Page**:
   ```bash
   python manage.py runserver
   ```

4. **Verify Data in Admin**:
   - Visit `/admin/`
   - Check destinations, attractions, tours
   - Verify relationships are working

## 📝 Data Customization

### Adding More Destinations:
```sql
INSERT INTO destinations_destination (name, slug, description, region_id, price, rating, latitude, longitude, is_featured, is_active) 
VALUES ('Your Destination', 'your-destination', 'Description...', 1, 999.99, 4.5, 0.0, 0.0, true, true);
```

### Adding More Tours:
```sql
INSERT INTO tours_tour (name, slug, short_description, description, duration_days, duration_nights, price, is_featured, is_active, is_popular, category_id) 
VALUES ('Your Tour', 'your-tour', 'Short desc...', 'Full description...', 7, 6, 1599.99, true, true, true, 1);
```

## 🐛 Troubleshooting

### Common Issues:

1. **Permission Denied**:
   ```bash
   GRANT ALL PRIVILEGES ON DATABASE guides_db TO postgres;
   ```

2. **Table Already Exists**:
   - Scripts use `IF NOT EXISTS` and `ON CONFLICT` clauses
   - Safe to run multiple times

3. **Foreign Key Violations**:
   - Run scripts in order: structure → data → fixes
   - Check that referenced tables exist first

## 🔍 Verification Queries

### Check Data Counts:
```sql
SELECT 'destinations' as table_name, COUNT(*) as count FROM destinations_destination
UNION ALL
SELECT 'attractions' as table_name, COUNT(*) as count FROM destinations_attraction
UNION ALL
SELECT 'tours' as table_name, COUNT(*) as count FROM tours_tour;
```

### Check Featured Content:
```sql
SELECT COUNT(*) as featured_destinations FROM destinations_destination WHERE is_featured = true;
SELECT COUNT(*) as featured_attractions FROM destinations_attraction WHERE is_featured = true;
SELECT COUNT(*) as popular_tours FROM tours_tour WHERE is_popular = true;
```

## 🔄 Updates and Maintenance

### To Update Sample Data:
1. Modify `02_sample_data.sql`
2. Run migration fixes if needed
3. Test with Django application

### To Add New Features:
1. Update `01_database_structure.sql`
2. Add corresponding sample data
3. Update Django models accordingly

## 📞 Support

If you encounter issues:
1. Check PostgreSQL logs
2. Verify database permissions
3. Ensure all prerequisites are met
4. Review Django model definitions

---

**Status**: ✅ Ready for Production Use
**Last Updated**: 2025-07-17
**Django Version**: Compatible with Django 4.x+
