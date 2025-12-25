# Food Ordering System - Project Information

## Project Overview

**Title:** Online Food Ordering System with Restaurant Dashboard  
**Technology Stack:** Django, PostgreSQL, Tailwind CSS  
**Duration:** 20 Days  
**Type:** MCA Mini Project (Individual)

## Project Description

A comprehensive web-based food ordering platform that enables customers to browse menus, place orders online, and allows restaurant staff to manage orders through a dedicated dashboard. The system uses modern web technologies and follows best practices for scalability and maintainability.

## Key Technologies

### Backend
- **Django 4.2.7** - Python web framework
- **PostgreSQL** - Production database (with SQLite fallback for development)
- **Python 3.8+** - Programming language

### Frontend
- **Tailwind CSS** - Utility-first CSS framework
- **HTML5** - Markup language
- **JavaScript** - Client-side interactivity
- **Font Awesome** - Icon library

### Additional Libraries
- **Pillow** - Image processing
- **psycopg2-binary** - PostgreSQL adapter
- **python-decouple** - Environment variable management
- **shortuuid** - Unique order ID generation

## Project Architecture

### Django Apps

1. **core** - Base functionality and utilities
   - TimeStampedModel (abstract base model)
   - ActiveManager (custom model manager)
   - Shared utilities

2. **menu** - Food categories and menu items
   - Category model
   - MenuItem model
   - Menu API endpoints
   - Admin interface for menu management

3. **orders** - Order processing and management
   - Order model
   - OrderItem model
   - Order status tracking
   - Admin interface for order management

4. **customer** - Customer-facing features
   - Home page with featured items
   - Menu browsing with filters
   - Session-based shopping cart
   - Checkout process
   - Order confirmation

5. **restaurant** - Restaurant dashboard
   - Staff authentication
   - Order dashboard with statistics
   - Order detail view
   - Status update functionality

## Database Schema

### Main Models

**Category**
- name, slug, description
- image, is_active, display_order
- Timestamps (created_at, updated_at)

**MenuItem**
- name, slug, description, category
- price, image
- Dietary flags (is_vegetarian, is_vegan, is_spicy)
- Availability flags (is_available, is_featured, is_active)
- preparation_time, calories
- Timestamps

**Order**
- order_id (auto-generated)
- Customer info (name, phone, email, address)
- total_amount, status, special_instructions
- Delivery times (estimated, actual)
- Timestamps

**OrderItem**
- order, menu_item
- quantity, price, subtotal
- special_instructions

## Features Implemented

### Customer Side ✅
- Responsive home page with hero section
- Category browsing
- Featured items showcase
- Menu page with category filters
- Dietary filters (vegetarian, vegan)
- Shopping cart with session storage
- Quantity management in cart
- Checkout with customer details
- Order confirmation page
- Mobile-responsive design

### Restaurant Side ✅
- Secure staff login
- Dashboard with statistics:
  - Today's orders count
  - Pending orders
  - Preparing orders
  - Out for delivery count
- Order list with status filters
- Order detail view
- Status update functionality
- Print-friendly order view
- Real-time order management

### Admin Panel ✅
- Category management
- Menu item management with images
- Order viewing and management
- Staff account creation
- Bulk actions for orders
- Rich admin interface with custom displays

## Security Features

- CSRF protection
- Staff-only authentication for restaurant dashboard
- SQL injection prevention (Django ORM)
- XSS protection
- Secure password hashing
- Environment variable configuration
- Session-based cart (no sensitive data in cookies)

## Code Quality

### Documentation
- Comprehensive comments on all functions
- Docstrings explaining parameters and return values
- HTML comments for template sections
- Inline code documentation

### Best Practices
- DRY (Don't Repeat Yourself) principle
- Model managers for query optimization
- Template inheritance for consistency
- Separation of concerns (apps, models, views)
- Responsive design with Tailwind CSS
- Clean URL patterns

## File Structure

```
food_ordering/
├── core/                      # Core app
│   ├── models.py             # Base models
│   ├── apps.py               # App configuration
│   └── admin.py              # Admin config
├── customer/                  # Customer app
│   ├── views.py              # Customer views
│   ├── urls.py               # Customer URLs
│   ├── cart.py               # Cart management
│   └── context_processors.py # Template context
├── menu/                      # Menu app
│   ├── models.py             # Category, MenuItem
│   ├── views.py              # Menu API views
│   ├── admin.py              # Menu admin
│   └── urls.py               # Menu URLs
├── orders/                    # Orders app
│   ├── models.py             # Order, OrderItem
│   ├── admin.py              # Order admin
│   └── views.py              # Order views
├── restaurant/                # Restaurant app
│   ├── views.py              # Dashboard views
│   ├── urls.py               # Restaurant URLs
│   └── admin.py              # Restaurant admin
├── food_ordering/             # Main project
│   ├── settings.py           # Django settings
│   ├── urls.py               # Root URL config
│   ├── wsgi.py               # WSGI config
│   └── asgi.py               # ASGI config
├── templates/                 # Templates
│   ├── base.html             # Base template
│   ├── customer/             # Customer templates
│   │   ├── home.html
│   │   ├── menu.html
│   │   ├── cart.html
│   │   ├── checkout.html
│   │   └── order_success.html
│   └── restaurant/           # Restaurant templates
│       ├── login.html
│       ├── dashboard.html
│       └── order_detail.html
├── static/                    # Static files
│   ├── css/
│   │   └── custom.css
│   └── js/
│       └── main.js
├── media/                     # User uploads
├── manage.py                  # Django CLI
├── requirements.txt           # Dependencies
├── README.md                  # Project README
├── SETUP_GUIDE.md            # Setup instructions
└── .env.example              # Environment template
```

## Testing Scenarios

### Customer Journey
1. Visit home page → Browse featured items
2. Navigate to menu → Filter by category
3. Add items to cart → Adjust quantities
4. Proceed to checkout → Fill details
5. Place order → View confirmation

### Restaurant Workflow
1. Login to dashboard
2. View pending orders
3. Accept order
4. Update to "Preparing"
5. Update to "Out for Delivery"
6. Mark as "Delivered"

## Performance Optimizations

- Database query optimization with `select_related()` and `prefetch_related()`
- Image optimization support
- Static file caching
- Session-based cart (reduces database queries)
- Indexed database fields for faster lookups

## Future Enhancements (Scope for Expansion)

- Online payment integration (Razorpay, Stripe)
- Email/SMS notifications
- Delivery personnel module
- Order tracking map
- Customer accounts and order history
- Reviews and ratings
- Discount coupons
- Multiple restaurant support
- Real-time order updates (WebSockets)
- Mobile app (React Native/Flutter)

## Learning Outcomes

- Django framework mastery
- Database design and modeling
- Session management
- Authentication and authorization
- REST API design
- Frontend development with Tailwind CSS
- Responsive web design
- Code documentation practices
- Project structure and organization

## Deployment Checklist

- [ ] Set DEBUG=False
- [ ] Configure ALLOWED_HOSTS
- [ ] Set up PostgreSQL database
- [ ] Configure email backend
- [ ] Set up static file serving
- [ ] Configure media file storage
- [ ] Set up HTTPS/SSL
- [ ] Configure domain name
- [ ] Set up backup system
- [ ] Monitor error logs

## Credits

**Developer:** [Your Name]  
**Institution:** [Your College/University]  
**Course:** MCA (Master of Computer Applications)  
**Project Type:** Mini Project  
**Academic Year:** [Year]

## License

This project is developed for educational purposes as part of academic curriculum.

---

**Version:** 1.0  
**Last Updated:** 2024  
**Status:** Production Ready ✅
