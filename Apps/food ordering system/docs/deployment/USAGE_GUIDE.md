# 📖 Food Ordering System - Usage Guide

## Overview
This guide explains how to use the Food Ordering System for both customers and restaurant staff.

---

## Customer Guide

### 1. Browsing Menu

**Home Page:**
- Visit http://127.0.0.1:8000/
- Browse featured categories
- View popular menu items
- Click "Order Now" to see full menu

**Menu Page:**
- Click on category buttons to filter items
- View item details including:
  - Name and description
  - Price
  - Dietary type (Vegetarian/Non-Vegetarian/Vegan)
  - Preparation time
- See availability status

### 2. Adding Items to Cart

**From Menu:**
1. Find item you want to order
2. Click "Add to Cart" button
3. Item is added with quantity 1
4. Success message confirms addition
5. Cart count updates in navbar

**Cart Management:**
- View cart anytime by clicking cart icon (🛒)
- Cart count badge shows total items

### 3. Managing Cart

**Cart Page Features:**
- View all added items with images
- See item details and prices
- Adjust quantities using +/- buttons
- Remove items using 🗑️ Remove button
- View subtotal for each item
- See total order amount

**Quantity Controls:**
- Click **−** to decrease quantity
- Click **+** to increase quantity
- Quantity updates automatically
- Item removed if quantity reaches 0

### 4. Checkout Process

**Step 1: Review Cart**
- Verify all items are correct
- Check quantities and prices
- Click "Proceed to Checkout"

**Step 2: Enter Details**
Fill in required information:
- **Full Name:** Your complete name
- **Phone Number:** Contact number for order confirmation
- **Delivery Address:** Complete delivery address
- **Order Notes:** (Optional) Special instructions

**Step 3: Place Order**
- Review order summary on right side
- See total amount
- Click "Place Order" button
- Payment: Cash on Delivery

### 5. Order Confirmation

**Success Page Shows:**
- ✅ Success message
- **Order ID:** Unique order identifier
- **Customer details:** Name, phone, address
- **Order items:** List with quantities and prices
- **Total amount:** Final order value
- **Order status:** Current status badge
- **Estimated time:** 30-45 minutes delivery

**What Happens Next:**
1. Order sent to restaurant dashboard
2. Restaurant staff will call to confirm
3. Order preparation begins
4. Food delivered to your address

---

## Restaurant Staff Guide

### 1. Logging In

**Login Process:**
1. Go to http://127.0.0.1:8000/restaurant/login/
2. Enter your username and password
3. Click "Login to Dashboard"
4. Redirected to dashboard on success

**Default Credentials:**
- Use superuser account created during setup
- Admin creates staff accounts via Django admin

### 2. Dashboard Overview

**Dashboard Shows:**
- **Total Orders:** All-time order count
- **Pending Orders:** Orders awaiting action
- **Today's Revenue:** Current day's earnings
- **Status Overview:** Distribution of orders by status
- **Recent Orders:** Last 20 orders with details

**Statistics Cards:**
- 📦 Total Orders (Indigo)
- ⏳ Pending Orders (Yellow/Orange)
- 💰 Today's Revenue (Green)

### 3. Managing Orders

**View All Orders:**
1. Click "View All Orders" from dashboard
2. See complete order list
3. Filter by status using dropdown
4. Search by name, phone, or order ID

**Order Details:**
Each row shows:
- Order ID (first 8 characters)
- Customer name and phone
- Number of items
- Total amount
- Current status (color-coded badge)
- Order date and time
- "View Details" button

### 4. Order Status Management

**Available Statuses:**
1. **Pending** (Yellow) - Just received
2. **Accepted** (Blue) - Confirmed by restaurant
3. **Preparing** (Purple) - Food being prepared
4. **Out for Delivery** (Indigo) - On the way
5. **Delivered** (Green) - Successfully delivered
6. **Cancelled** (Red) - Order cancelled

**Update Order Status:**
1. Click "View Details" on any order
2. See complete order information:
   - Customer details
   - Delivery address
   - Order items with images
   - Total amount
   - Current status
3. Select new status from dropdown
4. Click "Update Status" button
5. Confirmation message appears

**Recommended Workflow:**
```
New Order (Pending)
    ↓
Call customer to confirm (Accepted)
    ↓
Start cooking (Preparing)
    ↓
Ready for delivery (Out for Delivery)
    ↓
Successfully delivered (Delivered)
```

### 5. Order Details Page

**Customer Information Section:**
- Customer name
- Phone number (for calling)
- Complete delivery address
- Order notes (special instructions)

**Order Items Section:**
- Item images
- Item names and categories
- Quantities and prices
- Individual subtotals
- Grand total amount

**Status Management Section:**
- Current status display
- Order timestamps
- Status update form
- Status guide reference

### 6. Best Practices

**For Order Processing:**
1. ✅ Check pending orders regularly
2. ✅ Call customer immediately after accepting
3. ✅ Update status in real-time
4. ✅ Note preparation times
5. ✅ Verify address before dispatch

**For Customer Service:**
1. ✅ Respond to order notes
2. ✅ Handle dietary restrictions
3. ✅ Call if item unavailable
4. ✅ Confirm delivery completion
5. ✅ Maintain order accuracy

---

## Admin Panel Guide

### 1. Accessing Admin

**Login:**
- URL: http://127.0.0.1:8000/admin/
- Use superuser credentials
- Full access to all models

### 2. Managing Categories

**Add Category:**
1. Click "Categories" under MENU
2. Click "Add Category" button
3. Fill in:
   - Name (e.g., "Appetizers")
   - Description (optional)
   - Display order (for sorting)
   - Is active (checkbox)
4. Click "Save"

**Edit Category:**
- Click on category name
- Modify fields
- Click "Save" or "Save and continue editing"

### 3. Managing Menu Items

**Add Menu Item:**
1. Click "Menu Items" under MENU
2. Click "Add Menu Item"
3. Fill in details:
   - **Category:** Select from dropdown
   - **Name:** Item name
   - **Description:** Detailed description
   - **Price:** In rupees (e.g., 250.00)
   - **Image:** Upload food photo
   - **Is available:** Check if in stock
   - **Dietary type:** Veg/Non-veg/Vegan
   - **Preparation time:** In minutes
4. Click "Save"

**Bulk Actions:**
- Select multiple items
- Use "Action" dropdown:
  - Mark as available/unavailable
  - Delete selected items

### 4. Managing Orders

**View Orders:**
- Click "Orders" under ORDERS
- See all customer orders
- Filter by status, date
- Search by customer name

**Order Details:**
- Click order ID
- View complete order information
- See order items (inline)
- Update status if needed

### 5. User Management

**Create Restaurant Staff:**
1. Click "Users" under AUTHENTICATION
2. Click "Add User"
3. Enter username and password
4. Click "Save and continue"
5. Set permissions:
   - Staff status: ✅ (required)
   - Active: ✅
   - Superuser: ❌ (unless admin)
6. Click "Save"

**Staff Permissions:**
- Staff status: Can access admin
- Superuser: Full admin access
- Regular staff: View/edit orders only

---

## Keyboard Shortcuts

### Customer Interface:
- **Home:** Click logo anywhere
- **Menu:** M key (when in input)
- **Cart:** C key (when in input)

### Restaurant Dashboard:
- **Alt + D:** Dashboard
- **Alt + O:** Orders list
- **Alt + L:** Logout

---

## Tips & Tricks

### For Customers:
1. 💡 Add multiple items before checkout
2. 💡 Check dietary labels for preferences
3. 💡 Use order notes for special requests
4. 💡 Save order ID for reference
5. 💡 Estimated time is 30-45 minutes

### For Restaurant Staff:
1. 💡 Keep dashboard open for new orders
2. 💡 Update status immediately after actions
3. 💡 Use filters to find specific orders
4. 💡 Search by phone number is fastest
5. 💡 Check order notes before preparing

### For Admins:
1. 💡 Regularly update menu with new items
2. 💡 Mark unavailable items instead of deleting
3. 💡 Use display_order for category sorting
4. 💡 Upload high-quality food images
5. 💡 Review orders daily for insights

---

## Common Issues & Solutions

### Customer Issues

**Q: Cart is empty after closing browser**
- A: Cart uses session storage. Items clear after browser closes.
- Solution: Complete order in same session.

**Q: Can't place order**
- A: Check all required fields are filled.
- Solution: Verify name, phone, and address are entered.

**Q: Item says "Unavailable"**
- A: Restaurant marked item as out of stock.
- Solution: Choose different item or contact restaurant.

### Restaurant Staff Issues

**Q: Can't login**
- A: Verify credentials or check staff status.
- Solution: Admin must enable "Staff status" in user settings.

**Q: Orders not showing**
- A: Check filters and search.
- Solution: Clear filters to see all orders.

**Q: Can't update status**
- A: May need permissions.
- Solution: Check user permissions in admin panel.

---

## Workflow Examples

### Complete Customer Order Flow:
```
1. Browse Menu → 2. Add Items → 3. View Cart → 
4. Update Quantities → 5. Checkout → 6. Enter Details → 
7. Place Order → 8. Get Order ID → 9. Await Delivery
```

### Complete Restaurant Flow:
```
1. New Order Arrives → 2. View in Dashboard → 
3. Call Customer → 4. Accept Order → 5. Prepare Food → 
6. Mark Out for Delivery → 7. Deliver → 8. Mark Delivered
```

---

## Contact & Support

For technical issues:
- Check DEPLOYMENT_GUIDE.md
- Review Django documentation
- Check system logs

**System Requirements:**
- Modern web browser (Chrome, Firefox, Edge)
- JavaScript enabled
- Internet connection for Tailwind CSS CDN

---

**Happy Ordering! 🍽️**
