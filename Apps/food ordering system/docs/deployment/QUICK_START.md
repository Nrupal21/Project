# ⚡ Quick Start Guide - Food Ordering System

## Get Started in 5 Minutes!

### Step 1: Setup Virtual Environment (1 min)
```powershell
# Windows PowerShell
cd "d:\Project\Python\Apps\food ordering system"
python -m venv venv
.\venv\Scripts\Activate.ps1

# If you get an error, run this first:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Step 2: Install Dependencies (1 min)
```powershell
pip install -r requirements.txt
```

### Step 3: Configure Environment (1 min)
```powershell
# Copy and edit .env file
copy .env.example .env
notepad .env
```

**Update these in .env:**
- `DB_PASSWORD` = your PostgreSQL password
- `SECRET_KEY` = any random string

### Step 4: Setup Database (1 min)

**Option A: Using pgAdmin**
1. Open pgAdmin
2. Right-click Databases → Create → Database
3. Name: `food_ordering_db`
4. Click Save

**Option B: Using psql**
```sql
psql -U postgres
CREATE DATABASE food_ordering_db;
\q
```

### Step 5: Initialize Django (1 min)
```powershell
# Run migrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser
# Enter: username, email, password
```

### Step 6: Run Server
```powershell
python manage.py runserver
```

## 🎉 You're Ready!

**Access your application:**
- 🏠 Customer Site: http://127.0.0.1:8000/
- 🏪 Restaurant Login: http://127.0.0.1:8000/restaurant/login/
- ⚙️ Admin Panel: http://127.0.0.1:8000/admin/

---

## Next Steps

### 1. Add Menu Items (Admin Panel)

Login to admin: http://127.0.0.1:8000/admin/

**Create Categories:**
```
1. Click "Categories" → "Add Category"
2. Add:
   - Appetizers (display_order: 1)
   - Main Course (display_order: 2)
   - Desserts (display_order: 3)
   - Beverages (display_order: 4)
```

**Create Menu Items:**
```
1. Click "Menu Items" → "Add Menu Item"
2. For each item, fill:
   - Category, Name, Description
   - Price (e.g., 250.00)
   - Dietary type (Veg/Non-veg/Vegan)
   - Preparation time (minutes)
3. Upload image (optional)
4. Save
```

### 2. Test Customer Flow

1. Go to http://127.0.0.1:8000/
2. Browse menu
3. Add items to cart
4. Checkout with test details
5. View order confirmation

### 3. Test Restaurant Dashboard

1. Go to http://127.0.0.1:8000/restaurant/login/
2. Login with superuser credentials
3. View orders on dashboard
4. Update order status
5. Test order management

---

## Sample Data (Optional)

Want to quickly test? Add sample data via Django shell:

```powershell
python manage.py shell
```

```python
from menu.models import Category, MenuItem

# Create categories
cat1 = Category.objects.create(name='Appetizers', display_order=1)
cat2 = Category.objects.create(name='Main Course', display_order=2)
cat3 = Category.objects.create(name='Desserts', display_order=3)

# Create menu items
MenuItem.objects.create(
    category=cat1, name='Spring Rolls',
    description='Crispy vegetable spring rolls with sweet chili sauce',
    price=120.00, dietary_type='veg', preparation_time=15
)

MenuItem.objects.create(
    category=cat1, name='Chicken Wings',
    description='Spicy buffalo wings with ranch dip',
    price=180.00, dietary_type='non_veg', preparation_time=20
)

MenuItem.objects.create(
    category=cat2, name='Butter Chicken',
    description='Creamy tomato-based curry with tender chicken',
    price=350.00, dietary_type='non_veg', preparation_time=25
)

MenuItem.objects.create(
    category=cat2, name='Paneer Tikka Masala',
    description='Grilled cottage cheese in rich masala gravy',
    price=320.00, dietary_type='veg', preparation_time=25
)

MenuItem.objects.create(
    category=cat2, name='Vegetable Biryani',
    description='Fragrant basmati rice with mixed vegetables',
    price=280.00, dietary_type='veg', preparation_time=30
)

MenuItem.objects.create(
    category=cat3, name='Gulab Jamun',
    description='Soft milk dumplings in sugar syrup',
    price=80.00, dietary_type='veg', preparation_time=5
)

MenuItem.objects.create(
    category=cat3, name='Chocolate Brownie',
    description='Warm chocolate brownie with vanilla ice cream',
    price=120.00, dietary_type='veg', preparation_time=10
)

print("✅ Sample data added! Visit http://127.0.0.1:8000/ to see menu")
```

---

## Troubleshooting

### Problem: Can't activate virtual environment
**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Problem: psycopg2 install fails
**Solution:**
```powershell
pip install psycopg2-binary
```

### Problem: Database connection error
**Solution:**
1. Check PostgreSQL is running
2. Verify DB_PASSWORD in .env
3. Ensure database `food_ordering_db` exists

### Problem: Port 8000 in use
**Solution:**
```powershell
python manage.py runserver 8080
# Then access: http://127.0.0.1:8080/
```

---

## Project Structure Quick Reference

```
food-ordering-system/
├── food_ordering/          # Main project settings
│   ├── settings.py        # Configuration
│   ├── urls.py            # Main URL routing
│   └── wsgi.py            # WSGI application
├── core/                  # Core utilities
├── menu/                  # Menu & categories
│   ├── models.py          # Category, MenuItem
│   └── admin.py           # Admin interface
├── orders/                # Order processing
│   ├── models.py          # Order, OrderItem
│   └── admin.py           # Order management
├── customer/              # Customer interface
│   ├── views.py           # Menu, cart, checkout
│   ├── cart.py            # Cart functionality
│   └── urls.py            # Customer URLs
├── restaurant/            # Restaurant dashboard
│   ├── views.py           # Dashboard, orders
│   └── urls.py            # Restaurant URLs
├── templates/             # HTML templates
│   ├── base.html          # Base template
│   ├── customer/          # Customer templates
│   └── restaurant/        # Restaurant templates
└── static/                # Static files
    ├── css/               # Custom CSS
    └── js/                # JavaScript
```

---

## Useful Commands

```powershell
# Start server
python manage.py runserver

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Open shell
python manage.py shell

# Check for errors
python manage.py check

# Collect static files
python manage.py collectstatic
```

---

## Need More Help?

📚 **Read Full Guides:**
- `DEPLOYMENT_GUIDE.md` - Complete setup instructions
- `USAGE_GUIDE.md` - How to use the system
- `README.md` - Project overview

🔧 **Common Commands:**
- Activate venv: `.\venv\Scripts\Activate.ps1`
- Deactivate venv: `deactivate`
- Stop server: `Ctrl + C`

---

**Ready to order some food? Let's go! 🚀**
