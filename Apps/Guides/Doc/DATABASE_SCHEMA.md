# Database Schema Analysis - TravelGuide Django Project

## Database Overview
- **Database Name**: guides_db  
- **Database Type**: PostgreSQL
- **Host**: localhost:5432
- **Analysis Date**: 2025-07-17

## Tables Summary

### 1. **Django System Tables**
- `auth_user` - User authentication
- `auth_group` - User groups
- `auth_permission` - Permissions
- `django_migrations` - Migration history
- `django_session` - User sessions
- `django_admin_log` - Admin activity log
- `django_content_type` - Content types
- `django_site` - Site configuration

### 2. **Account Management (django-allauth)**
- `account_emailaddress` - Email verification
- `account_emailconfirmation` - Email confirmation tokens
- `socialaccount_socialaccount` - Social media accounts
- `socialaccount_socialapp` - Social media app configs
- `socialaccount_socialtoken` - Social media tokens
- `authtoken_token` - API tokens

### 3. **Custom User Profiles**
- `accounts_userprofile` - Extended user information
- `accounts_userpreferences` - User preferences
- `accounts_otpdevice` - OTP devices for 2FA
- `accounts_otpsession` - OTP sessions

### 4. **Destinations App** ⭐ **PRIMARY DATA**
- `destinations_destination` - **3 RECORDS** ✅
  - Fields: id, name, slug, description, region_id, price, rating, latitude, longitude, is_featured, is_active, created_at, updated_at
  - **Key for home page**: Featured destinations display

- `destinations_destinationimage` - **1 RECORD** ✅
  - Fields: id, destination_id, image, alt_text, is_primary, created_at
  - **Key for home page**: Destination images

- `destinations_region` - **4 RECORDS** ✅  
  - Fields: id, name, slug, description, created_at, updated_at
  - **Key for home page**: Regional filtering

- `destinations_attraction` - **4 RECORDS** ✅
  - Fields: id, name, description, category, destination_id, is_featured, is_active, created_at, updated_at
  - **Key for home page**: Featured attractions

- `destinations_attractionimage` - Images for attractions
- `destinations_season` - Seasonal information

### 5. **Tours App** ❌ **EMPTY TABLES**
- `tours_tour` - **0 RECORDS** ❌
  - Fields: id, title, slug, short_description, description, duration_days, duration_nights, max_group_size, difficulty, price, discount_price, is_featured, is_active, destination_id, category_id, created_at, updated_at
  - **Issue**: Django model expects `name` field but database has `title`

- `tours_tourcategory` - **0 RECORDS** ❌
  - Fields: id, name, slug, description, is_active, created_at, updated_at

- `tours_tourimage` - **0 RECORDS** ❌
- `tours_tourdate` - **0 RECORDS** ❌  
- `tours_touritinerary` - **0 RECORDS** ❌
- `tours_tourinclusion` - **0 RECORDS** ❌
- `tours_tourreview` - **0 RECORDS** ❌
- `tours_booking` - **0 RECORDS** ❌

## Data Analysis for Home Page

### ✅ **Ready for Dynamic Display**
1. **Destinations**: 3 records available
   - Can be used for "Featured Destinations" section
   - Has featured flag, pricing, ratings
   - Has associated images

2. **Attractions**: 4 records available  
   - Can be used for "Popular Attractions" section
   - Has featured flag, linked to destinations
   - Has category information

3. **Regions**: 4 records available
   - Can be used for filtering and categorization

### ❌ **Needs Data Population**
1. **Tours**: All tour-related tables are empty
   - Currently using static fallback content
   - Need to populate tours_tour table
   - Need to populate tours_tourcategory table
   - Need to add tour images

## Model-Database Mismatch Issues

### Tours Model Inconsistency
- **Django Model Field**: `name` (CharField)
- **Database Column**: `title` (VARCHAR)
- **Solution**: Either update model or migrate database

### Relationships
- **Destination → Region**: Many-to-One (working)
- **Attraction → Destination**: Many-to-One (working)
- **Tour → Destination**: Many-to-One (in DB) vs Many-to-Many (in model)
- **Tour → Category**: Many-to-One (working)

## Recommendations

### Immediate Actions
1. **Fix Tours Model**: Update Django model to match database schema
2. **Focus on Available Data**: Prioritize destinations and attractions
3. **Add Sample Tours**: Populate tours tables with sample data

### Home Page Strategy
1. **Use Destinations**: Display featured destinations from database
2. **Use Attractions**: Display featured attractions from database  
3. **Tours Fallback**: Keep static content until tours data is added
4. **Regional Filtering**: Implement region-based filtering

### Database Population Needed
```sql
-- Sample tours data structure needed
INSERT INTO tours_tourcategory (name, slug, description, is_active) VALUES
('Adventure', 'adventure', 'Adventure and outdoor activities', true),
('Cultural', 'cultural', 'Cultural and historical tours', true),
('Culinary', 'culinary', 'Food and culinary experiences', true);

INSERT INTO tours_tour (title, slug, short_description, description, duration_days, duration_nights, max_group_size, difficulty, price, discount_price, is_featured, is_active, destination_id, category_id) VALUES
('Sample Tour 1', 'sample-tour-1', 'Amazing tour experience', 'Full description...', 7, 6, 20, 'Medium', 1299.00, 999.00, true, true, 1, 1);
```

## Current Status: Ready for Dynamic Display
- **Destinations**: ✅ 3 records ready
- **Attractions**: ✅ 4 records ready  
- **Tours**: ❌ Empty (using static fallback)
- **Home Page**: Can display dynamic destination and attraction data immediately
