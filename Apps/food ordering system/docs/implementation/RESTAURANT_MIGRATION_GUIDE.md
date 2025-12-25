# Restaurant Feature Migration Guide

## Overview
This guide will help you migrate the Food Ordering System to display restaurants on the home page and require user login for cart operations.

## Changes Made

### 1. Database Models
- ✅ **Created Restaurant Model** (`restaurant/models.py`)
  - Added comprehensive restaurant information fields
  - Includes owner, contact details, business hours, pricing, and ratings
  - Added `is_open()` method to check operating hours

- ✅ **Updated MenuItem Model** (`menu/models.py`)
  - Added `restaurant` foreign key to link menu items with restaurants
  - Maintained backward compatibility with nullable restaurant field

### 2. Views and URLs
- ✅ **Updated Home View** (`customer/views.py`)
  - Now displays active restaurants instead of menu categories
  - Shows restaurant cards with ratings, hours, and delivery info

- ✅ **Created Restaurant Detail View** (`customer/views.py`)
  - Shows complete restaurant information
  - Displays menu items filtered by restaurant
  - Supports category filtering within restaurant menu

- ✅ **Added Login Requirements**
  - All cart operations now require user authentication
  - Checkout process requires login
  - Redirects to login page if user is not authenticated

### 3. Templates
- ✅ **Updated home.html**
  - Displays restaurant cards with comprehensive information
  - Shows open/closed status, ratings, and delivery details
  - Links to individual restaurant pages

- ✅ **Created restaurant_detail.html**
  - Full restaurant information display
  - Menu items grid with category filtering
  - Add to cart functionality (login required)

### 4. Admin Interface
- ✅ **Registered Restaurant Model**
  - Comprehensive admin interface for managing restaurants
  - Search, filter, and organize functionality

## Migration Steps

### Step 1: Create Database Migrations

Run the following commands to create migrations for the new Restaurant model and updated MenuItem model:

```bash
python manage.py makemigrations restaurant
python manage.py makemigrations menu
```

### Step 2: Apply Migrations

Apply the migrations to create database tables:

```bash
python manage.py migrate
```

### Step 3: Create Sample Restaurants (via Django Admin)

1. Run the development server:
   ```bash
   python manage.py runserver
   ```

2. Access the admin panel at `http://127.0.0.1:8000/admin/`

3. Login with your superuser credentials

4. Navigate to **Restaurants** and click **Add Restaurant**

5. Create sample restaurants with the following information:

   **Example Restaurant 1:**
   - Name: "The Spice Route"
   - Description: "Authentic Indian cuisine with a modern twist. Serving delicious curries, tandoori items, and regional specialties."
   - Address: "123 Main Street, Downtown"
   - Phone: "+91 98765 43210"
   - Email: "info@spiceroute.com"
   - Opening Time: 09:00
   - Closing Time: 22:00
   - Minimum Order: 200
   - Delivery Fee: 50
   - Rating: 4.5
   - Is Active: ✓

   **Example Restaurant 2:**
   - Name: "Pizza Paradise"
   - Description: "Wood-fired pizzas made with fresh ingredients and authentic Italian recipes."
   - Address: "456 Oak Avenue, City Center"
   - Phone: "+91 98765 43211"
   - Email: "hello@pizzaparadise.com"
   - Opening Time: 11:00
   - Closing Time: 23:00
   - Minimum Order: 150
   - Delivery Fee: 40
   - Rating: 4.7
   - Is Active: ✓

   **Example Restaurant 3:**
   - Name: "Burger Bay"
   - Description: "Gourmet burgers, crispy fries, and refreshing shakes. Fast food done right!"
   - Address: "789 Elm Street, Food Court"
   - Phone: "+91 98765 43212"
   - Email: "orders@burgerbay.com"
   - Opening Time: 10:00
   - Closing Time: 22:30
   - Minimum Order: 100
   - Delivery Fee: 30
   - Rating: 4.3
   - Is Active: ✓

### Step 4: Link Existing Menu Items to Restaurants

You have two options:

**Option A: Via Django Admin**
1. Go to **Menu Items** in the admin panel
2. Edit each menu item
3. Select a restaurant from the dropdown
4. Save

**Option B: Via Django Shell**
```python
python manage.py shell
```

Then run:
```python
from menu.models import MenuItem
from restaurant.models import Restaurant

# Get first restaurant
restaurant = Restaurant.objects.first()

# Assign all existing menu items to this restaurant
if restaurant:
    MenuItem.objects.all().update(restaurant=restaurant)
    print(f"Updated {MenuItem.objects.count()} menu items")
```

### Step 5: Create User Accounts for Testing

Create test user accounts to test the login-required cart functionality:

```bash
python manage.py createsuperuser
```

Or create regular users via Django admin:
1. Navigate to **Users** in admin panel
2. Click **Add User**
3. Create test accounts (e.g., customer1, customer2)

### Step 6: Test the Application

1. **Test Home Page**
   - Visit `http://127.0.0.1:8000/`
   - Verify restaurants are displayed
   - Check rating, hours, and delivery info

2. **Test Restaurant Detail Page**
   - Click on a restaurant card
   - Verify menu items are displayed
   - Test category filtering

3. **Test Login Requirement**
   - Try to add items to cart without logging in
   - Verify redirect to login page
   - Login and add items to cart successfully

4. **Test Cart and Checkout**
   - Add multiple items to cart
   - View cart
   - Proceed to checkout
   - Complete order

## URL Structure

### Before Migration:
- `/` - Home page with categories and popular items
- `/menu/` - All menu items
- `/cart/` - Shopping cart

### After Migration:
- `/` - Home page with restaurants list
- `/restaurant/<id>/` - Restaurant detail with menu
- `/menu/` - All menu items (all restaurants)
- `/cart/` - Shopping cart (login required)

## Authentication Flow

### Before:
- Anyone can add items to cart
- No login required for ordering

### After:
- User must login to add items to cart
- Cart operations require authentication
- Checkout requires login
- Better user tracking and order management

## Configuration Settings

### Update LOGIN_URL in settings.py

Make sure your `settings.py` has the correct login URL:

```python
LOGIN_URL = '/restaurant/login/'
```

This ensures users are redirected to the correct login page when accessing protected views.

## Troubleshooting

### Issue: "relation 'restaurant_restaurant' does not exist"
**Solution:** Run migrations:
```bash
python manage.py migrate
```

### Issue: Menu items not showing on restaurant page
**Solution:** Make sure menu items are assigned to restaurants:
```python
# Via Django shell
from menu.models import MenuItem
from restaurant.models import Restaurant

restaurant = Restaurant.objects.first()
MenuItem.objects.filter(restaurant__isnull=True).update(restaurant=restaurant)
```

### Issue: Login redirect not working
**Solution:** Check `LOGIN_URL` in settings.py and make sure restaurant login URL exists.

### Issue: "Add to Cart" button not showing
**Solution:** Make sure user is authenticated and menu items are marked as available.

## Next Steps

After successful migration, consider these enhancements:

1. **Create Management Command for Sample Data**
   - Create `populate_restaurants.py` command
   - Generate sample restaurants automatically

2. **Add Restaurant Images**
   - Upload images for each restaurant
   - Configure media files settings

3. **Implement User Registration**
   - Create customer registration page
   - Add email verification

4. **Add Search Functionality**
   - Search restaurants by name or cuisine
   - Filter by rating or delivery fee

5. **Implement Reviews**
   - Allow customers to rate restaurants
   - Calculate average ratings automatically

## Summary

✅ **Completed Changes:**
- Restaurant model created
- MenuItem linked to restaurants
- Home page shows restaurants
- Restaurant detail page created
- Login required for cart operations
- Admin interface updated

🔄 **Required Actions:**
1. Run migrations
2. Create sample restaurants
3. Link menu items to restaurants
4. Create test user accounts
5. Test the application

📝 **Files Modified:**
- `restaurant/models.py` - New Restaurant model
- `restaurant/admin.py` - Admin configuration
- `menu/models.py` - Added restaurant field
- `customer/views.py` - Updated views with login requirements
- `customer/urls.py` - Added restaurant detail URL
- `templates/customer/home.html` - Shows restaurants
- `templates/customer/restaurant_detail.html` - New template
- `templates/base.html` - Fixed static tag loading

Your Food Ordering System is now updated with restaurant-based ordering and secure cart operations! 🎉
