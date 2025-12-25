# QR Code Table Menu System - Complete Documentation

## Overview

The QR Code Table Menu System allows restaurants to provide contactless menu ordering through QR codes placed on physical tables. Customers scan the QR code with their smartphone camera to instantly access the restaurant's menu optimized for mobile devices.

## Features Implemented

### 1. **RestaurantTable Model** (`restaurant/models.py`)
   - **Fields:**
     - `restaurant`: ForeignKey to Restaurant
     - `table_number`: Unique identifier for each table
     - `capacity`: Number of seats at the table
     - `qr_code`: Auto-generated QR code image
     - `qr_code_uuid`: Unique UUID for secure table identification
     - `is_active`: Status flag for table availability
     - `location_description`: Optional location details

   - **Methods:**
     - `generate_qr_code()`: Automatically generates QR code with table info
     - `regenerate_qr_code()`: Creates new QR code if needed
     - `get_menu_url()`: Returns the full URL for the table's menu
     - `get_table_by_uuid()`: Class method to retrieve table by UUID

### 2. **QR Code Generation**
   - Uses `qrcode` and `Pillow` libraries
   - QR codes include table number and restaurant name
   - High error correction level for damaged codes
   - Saved as PNG images in `media/table_qr_codes/`

### 3. **Customer-Facing Features**

#### **Table Menu View** (`customer/views.py` - `table_menu()`)
   - Accessed via URL: `/table/<uuid>/`
   - Displays restaurant menu filtered by table
   - Mobile-optimized responsive design
   - Features:
     - Category filtering
     - Search functionality
     - Cart integration
     - Restaurant status (open/closed)
     - Table information display

#### **Mobile-Optimized Template** (`templates/customer/table_menu.html`)
   - **Sticky Header:** Shows restaurant info and table number
   - **Search Bar:** Quick menu item search
   - **Category Pills:** Horizontal scrollable category filter
   - **Menu Cards:** Touch-friendly menu item cards
   - **Floating Cart:** Always-visible cart button
   - **Responsive Design:** Optimized for all mobile devices

### 4. **Restaurant Owner Features**

#### **Table Management Views** (`restaurant/views.py`)
   - `table_management()`: List all tables with statistics
   - `add_table()`: Create new table with automatic QR generation
   - `edit_table()`: Update table details
   - `delete_table()`: Remove table and QR code
   - `toggle_table_status()`: Quick activate/deactivate
   - `download_table_qr()`: Download QR code image
   - `regenerate_table_qr()`: Generate new QR code

#### **Admin Interface** (`restaurant/admin.py`)
   - RestaurantTableAdmin with:
     - QR code preview thumbnails
     - Download links for each QR code
     - Bulk actions (activate, deactivate, regenerate QR)
     - Filtering by status and restaurant

### 5. **Form Validation** (`restaurant/forms.py`)
   - **RestaurantTableForm:**
     - Table number validation (alphanumeric + hyphens)
     - Capacity range validation (1-20 seats)
     - Duplicate table number prevention
     - Auto-uppercase table numbers for consistency

## Installation & Setup

### Step 1: Install Required Dependencies
```bash
pip install -r requirements.txt
```

Required packages:
- `qrcode[pil]==7.4.2` - QR code generation
- `Pillow==10.1.0` - Image processing

### Step 2: Run Database Migrations
```bash
python manage.py makemigrations restaurant
python manage.py migrate
```

### Step 3: Collect Static Files (if in production)
```bash
python manage.py collectstatic
```

## Usage Guide

### For Restaurant Owners:

#### 1. **Access Table Management**
   - Navigate to: `/restaurant/tables/`
   - View all tables with QR codes
   - See statistics (total, active, inactive tables)

#### 2. **Create a New Table**
   - Click "Add New Table" button
   - Fill in:
     - **Table Number**: e.g., "T1", "A-5", "101"
     - **Capacity**: Number of seats (1-20)
     - **Active Status**: Enable/disable table
     - **Location** (optional): e.g., "Near window"
   - QR code is automatically generated
   - Click "Save"

#### 3. **Download QR Codes**
   - From table list, click "Download QR" button
   - QR code image downloads as PNG file
   - Print and place on physical tables

#### 4. **Manage Tables**
   - **Edit**: Update table details
   - **Delete**: Remove table and QR code
   - **Toggle Status**: Quickly activate/deactivate
   - **Regenerate QR**: Create new QR code if needed

#### 5. **Admin Panel Access**
   - Navigate to: `/admin/restaurant/restauranttable/`
   - Advanced bulk operations
   - QR code preview thumbnails

### For Customers:

#### 1. **Scan QR Code**
   - Open smartphone camera
   - Point at QR code on table
   - Tap notification to open menu

#### 2. **Browse Menu**
   - View all menu items
   - Filter by category (horizontal scroll)
   - Search for specific items
   - See restaurant opening hours

#### 3. **Add Items to Cart**
   - Click "+ Add" on any item
   - Items added to session cart
   - Cart count shows in header
   - Login required to add items

#### 4. **Complete Order**
   - Click "View Cart" floating button
   - Review items and quantities
   - Proceed to checkout
   - Select delivery/takeaway

## URL Patterns

### Customer URLs:
- **Table Menu**: `/table/<uuid>/` - Main menu via QR code
- **Cart**: `/cart/` - View shopping cart
- **Checkout**: `/checkout/` - Complete order

### Restaurant URLs:
- **Table List**: `/restaurant/tables/` - View all tables
- **Add Table**: `/restaurant/tables/add/` - Create new table
- **Edit Table**: `/restaurant/tables/edit/<id>/` - Update table
- **Delete Table**: `/restaurant/tables/delete/<id>/` - Remove table
- **Toggle Status**: `/restaurant/tables/toggle/<id>/` - Activate/deactivate
- **Download QR**: `/restaurant/tables/download-qr/<id>/` - Get QR image
- **Regenerate QR**: `/restaurant/tables/regenerate-qr/<id>/` - New QR code

## Database Schema

```sql
CREATE TABLE restaurant_restauranttable (
    id SERIAL PRIMARY KEY,
    restaurant_id INTEGER REFERENCES restaurant_restaurant(id),
    table_number VARCHAR(20) NOT NULL,
    capacity INTEGER DEFAULT 4,
    qr_code VARCHAR(100),  -- Image path
    qr_code_uuid UUID UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    location_description VARCHAR(200),
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    UNIQUE(restaurant_id, table_number)
);

CREATE INDEX idx_restaurant_table ON restaurant_restauranttable(restaurant_id, table_number);
CREATE INDEX idx_qr_uuid ON restaurant_restauranttable(qr_code_uuid);
CREATE INDEX idx_active ON restaurant_restauranttable(is_active);
```

## QR Code Format

Each QR code contains a URL in this format:
```
http://localhost:8000/table/<uuid>/
```

Example:
```
http://localhost:8000/table/a1b2c3d4-e5f6-7890-abcd-ef1234567890/
```

- **Protocol**: http or https (auto-detected)
- **Domain**: From Django sites framework or fallback
- **UUID**: Unique identifier for the table

## Security Features

1. **UUID-Based Access**: Tables use UUIDs instead of sequential IDs
2. **Active Status Check**: Inactive tables cannot be accessed
3. **Restaurant Validation**: Verifies restaurant is active and approved
4. **Owner Verification**: Only table owners can manage tables
5. **No Login Required**: Customers can browse menu without account

## Mobile Optimization

### Design Features:
- **Touch-Friendly**: Large tap targets (minimum 44x44px)
- **Fast Loading**: Optimized images with lazy loading
- **Smooth Scrolling**: Hardware-accelerated animations
- **Sticky Header**: Always visible restaurant info
- **Floating Actions**: Cart button stays accessible
- **Auto-Hide Search**: Collapses on scroll for more space

### Performance:
- **Lazy Image Loading**: Images load as user scrolls
- **Minimal HTTP Requests**: CDN for external resources
- **Optimized Queries**: Database queries with select_related
- **Caching Ready**: Cart uses session-based caching

## Error Handling

### Table Not Found (404):
- Invalid UUID
- Inactive table
- Deleted table
- **Template**: `customer/table_not_found.html`

### Restaurant Unavailable:
- Restaurant inactive
- Restaurant not approved
- **Template**: `customer/restaurant_unavailable.html`

### QR Code Generation Errors:
- Missing dependencies
- File permission issues
- **Fallback**: Table saved without QR code
- **Solution**: Use regenerate function

## Troubleshooting

### QR Code Not Generating:
```bash
# Install dependencies
pip install qrcode[pil] Pillow

# Check media directory permissions
chmod 755 media/table_qr_codes/

# Regenerate manually via admin or view
```

### QR Code Scan Not Working:
- Verify QR code is clear and undamaged
- Check lighting conditions
- Ensure camera has permission
- Try different QR code scanner apps

### Menu Not Loading:
- Check restaurant is active and approved
- Verify table is active
- Ensure menu items exist and are available
- Check database connection

## Best Practices

### For Restaurant Owners:
1. **Print Quality QR Codes**: Use high-resolution PNG files
2. **Protect QR Codes**: Laminate or use clear covers
3. **Strategic Placement**: Center of table, easy to scan
4. **Keep Active**: Deactivate only when necessary
5. **Regular Updates**: Keep menu items current

### For Developers:
1. **Database Indexes**: Already optimized for UUID lookups
2. **Image Optimization**: QR codes are compact PNGs
3. **Caching Strategy**: Consider Redis for high traffic
4. **Error Logging**: Monitor QR generation failures
5. **Security Updates**: Keep qrcode library updated

## Future Enhancements

### Potential Features:
- [ ] Analytics: Track QR code scans
- [ ] Custom QR Design: Add restaurant logo
- [ ] Multi-language: Translate menu on QR scan
- [ ] Table Orders: Track orders by table
- [ ] Real-time Updates: WebSocket for order status
- [ ] Batch QR Generation: Create multiple tables at once
- [ ] QR Code Templates: Pre-designed printable templates
- [ ] SMS/Email QR: Send QR codes to customers

## Testing Checklist

- [ ] Create new table
- [ ] Generate QR code automatically
- [ ] Download QR code PNG
- [ ] Scan QR code with mobile device
- [ ] View menu on mobile
- [ ] Filter menu by category
- [ ] Search menu items
- [ ] Add items to cart (logged in)
- [ ] View cart from table menu
- [ ] Toggle table status
- [ ] Edit table details
- [ ] Regenerate QR code
- [ ] Delete table
- [ ] Access via admin panel

## API Endpoints (for future development)

Placeholder for REST API endpoints:
```
GET    /api/v1/tables/              - List all tables
POST   /api/v1/tables/              - Create table
GET    /api/v1/tables/<uuid>/       - Get table details
PUT    /api/v1/tables/<uuid>/       - Update table
DELETE /api/v1/tables/<uuid>/       - Delete table
GET    /api/v1/tables/<uuid>/menu/  - Get menu for table
```

## Support & Documentation

- **Main Documentation**: This file
- **Model Documentation**: See docstrings in `restaurant/models.py`
- **View Documentation**: See docstrings in `restaurant/views.py`
- **Form Documentation**: See docstrings in `restaurant/forms.py`

## Version History

**Version 1.0.0** - Initial Release
- RestaurantTable model with QR generation
- Customer-facing table menu view
- Restaurant owner table management
- Admin interface with QR preview
- Mobile-optimized templates
- Comprehensive documentation

---

## Quick Start Commands

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run migrations
python manage.py makemigrations restaurant
python manage.py migrate

# 3. Create superuser (if needed)
python manage.py createsuperuser

# 4. Run development server
python manage.py runserver

# 5. Access admin panel
# Navigate to: http://localhost:8000/admin/

# 6. Create tables
# Navigate to: http://localhost:8000/restaurant/tables/

# 7. Test QR code
# Scan generated QR code with mobile device
```

---

**System Ready!** Restaurant owners can now create tables, generate QR codes, and provide contactless menu ordering to customers.
